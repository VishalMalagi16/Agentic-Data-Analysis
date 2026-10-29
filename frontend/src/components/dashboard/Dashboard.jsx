// frontend/components/dashboard/Dashboard.jsx

import { DashboardCard } from './DashboardCard';

export const Dashboard = ({ cards }) => {
  if (!cards || cards.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <p>Your generated graphs and insights will appear here.</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {cards.map((card, index) => (
        <DashboardCard key={index} card={card} />
      ))}
    </div>
  );
};