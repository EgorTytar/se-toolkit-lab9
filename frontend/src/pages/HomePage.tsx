import { useState } from 'react';
import LatestRaceTab from '../components/tabs/LatestRaceTab';
import BrowseSeasonsTab from '../components/tabs/BrowseSeasonsTab';
import StandingsTab from '../components/tabs/StandingsTab';
import RemindersTab from '../components/tabs/RemindersTab';

type TabKey = 'latest' | 'browse' | 'standings' | 'reminders';

const tabs: { key: TabKey; label: string }[] = [
  { key: 'latest', label: 'Latest Race' },
  { key: 'browse', label: 'Browse Seasons' },
  { key: 'standings', label: 'Standings' },
  { key: 'reminders', label: 'Reminders' },
];

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<TabKey>('latest');

  return (
    <div>
      {/* Tab Navigation */}
      <div className="border-b border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === tab.key
                  ? 'border-red-500 text-red-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-500'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'latest' && <LatestRaceTab />}
      {activeTab === 'browse' && <BrowseSeasonsTab />}
      {activeTab === 'standings' && <StandingsTab />}
      {activeTab === 'reminders' && <RemindersTab />}
    </div>
  );
}
