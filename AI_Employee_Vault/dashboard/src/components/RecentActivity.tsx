'use client';

interface Activity {
  id: string;
  action: string;
  timestamp: string;
  status: string;
}

interface RecentActivityProps {
  activities: Activity[];
}

export default function RecentActivity({ activities }: RecentActivityProps) {
  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return '✅';
      case 'approved': return '👍';
      case 'rejected': return '❌';
      case 'pending': return '⏳';
      case 'error': return '⚠️';
      default: return '📋';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'approved':
        return 'text-green-400';
      case 'rejected':
      case 'error':
        return 'text-red-400';
      case 'pending':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  // Demo data if no activities
  const displayActivities = activities.length > 0 ? activities : [
    { id: '1', action: 'Email draft created for client inquiry', timestamp: new Date().toISOString(), status: 'pending' },
    { id: '2', action: 'LinkedIn post approved and queued', timestamp: new Date(Date.now() - 3600000).toISOString(), status: 'approved' },
    { id: '3', action: 'Weekly CEO briefing generated', timestamp: new Date(Date.now() - 7200000).toISOString(), status: 'completed' },
    { id: '4', action: 'Gmail watcher detected 3 new emails', timestamp: new Date(Date.now() - 10800000).toISOString(), status: 'completed' },
  ];

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-green-400 mb-4">
        📜 Recent Activity
      </h2>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-700">
              <th className="pb-3 font-medium">Action</th>
              <th className="pb-3 font-medium">Time</th>
              <th className="pb-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {displayActivities.map((activity) => (
              <tr key={activity.id} className="border-b border-gray-700/50">
                <td className="py-3 text-gray-300">{activity.action}</td>
                <td className="py-3 text-gray-500 text-sm">
                  {new Date(activity.timestamp).toLocaleString()}
                </td>
                <td className={`py-3 ${getStatusColor(activity.status)}`}>
                  <span className="flex items-center gap-2">
                    {getStatusIcon(activity.status)}
                    <span className="capitalize">{activity.status}</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
