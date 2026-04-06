# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Node.js for serving (optional, we'll use Python static files)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Test dependencies (installed as root before user switch)
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt

# Copy React build output to static directory
COPY --from=frontend-builder /frontend/dist ./static/dist

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
