"""Background scheduler for checking and sending race reminders."""

import logging
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session
from db.models import Reminder, User, PushSubscription
from services.ergast_client import ErgastClient
from services.push_service import send_push_notification

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "f1-assistant@example.com")


scheduler = AsyncIOScheduler()


def _send_email(to_email: str, subject: str, body: str) -> None:
    """Send an email notification."""
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        logger.info("Reminder email sent to %s for race: %s", to_email, subject)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)


async def check_and_notify() -> None:
    """Check for reminders that should fire and send notifications."""
    now = datetime.datetime.utcnow()

    # Find the next scheduled race from Ergast
    ergast = ErgastClient()
    try:
        latest = await ergast.get_latest_race()
    except Exception:
        logger.warning("Could not fetch latest race for reminder check")
        return

    async with async_session() as db:
        # Find all enabled reminders for upcoming races
        result = await db.execute(select(Reminder).where(Reminder.enabled))
        reminders = result.scalars().all()

        for reminder in reminders:
            # Check if race is upcoming and within notification window
            try:
                race_data = await ergast.get_race_by_year_round(
                    reminder.race_year, reminder.race_round
                )
                race_date = datetime.datetime.strptime(race_data["date"], "%Y-%m-%d")
                hours_until = (race_date - now).total_seconds() / 3600

                if 0 <= hours_until <= reminder.notify_before_hours:
                    # Calculate relative time for the email
                    if hours_until >= 24:
                        days = int(hours_until // 24)
                        time_desc = f"{days} day{'s' if days != 1 else ''}"
                    else:
                        time_desc = f"{int(hours_until)} hour{'s' if hours_until != 1 else ''}"

                    # Get user email
                    user_result = await db.execute(
                        select(User).where(User.id == reminder.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user and user.email:
                        subject = f"🏎️ Reminder: {race_data['race_name']}"
                        body = (
                            f"Hi {user.display_name},\n\n"
                            f"The {race_data['race_name']} starts in about {time_desc}!\n"
                            f"Circuit: {race_data['circuit']}\n\n"
                            f"See you at the track!"
                        )

                        # Send email if method includes email
                        if reminder.method in ('email', 'all'):
                            _send_email(user.email, subject, body)

                        # Send push notifications if method includes push
                        if reminder.method in ('push', 'all'):
                            subs_result = await db.execute(
                                select(PushSubscription).where(PushSubscription.user_id == user.id)
                            )
                            subs = subs_result.scalars().all()
                            if subs:
                                push_title = f"🏎️ {race_data['race_name']}"
                                push_body = f"Starts in {time_desc} at {race_data['circuit']}!"
                                expired_subs = []
                                for sub in subs:
                                    success = await send_push_notification(
                                        endpoint=sub.endpoint,
                                        p256dh=sub.p256dh,
                                        auth=sub.auth,
                                        title=push_title,
                                        body=push_body,
                                    )
                                    if not success:
                                        expired_subs.append(sub)

                                for expired in expired_subs:
                                    await db.delete(expired)
                                    logger.info(
                                        "Removed expired push subscription for user %s", user.id
                                    )
                                if expired_subs:
                                    await db.commit()
                        # Legacy: old reminders with method='email' won't get push, which is correct
            except Exception as e:
                logger.warning(
                    "Reminder check failed for user %s, race %s/%s: %s",
                    reminder.user_id,
                    reminder.race_year,
                    reminder.race_round,
                    e,
                )


def start_scheduler() -> None:
    """Start the background reminder scheduler."""
    # Check every hour
    scheduler.add_job(check_and_notify, "interval", hours=1, id="race_reminders")
    scheduler.start()
    logger.info("Race reminder scheduler started (checking every hour)")


def stop_scheduler() -> None:
    """Shut down the scheduler."""
    scheduler.shutdown()
