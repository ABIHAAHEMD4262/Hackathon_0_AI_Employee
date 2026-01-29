'use client';

interface SystemHealthProps {
  health: {
    gmail: string;
    linkedin: string;
    orchestrator: string;
    approvals: string;
  };
}

export default function SystemHealth({ health }: SystemHealthProps) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
      case 'active':
      case 'healthy':
        return 'bg-green-500';
      case 'warning':
      case 'degraded':
        return 'bg-yellow-500';
      case 'error':
      case 'stopped':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
      case 'active':
      case 'healthy':
        return 'Running';
      case 'warning':
      case 'degraded':
        return 'Warning';
      case 'error':
      case 'stopped':
        return 'Stopped';
      default:
        return 'Unknown';
    }
  };

  const components = [
    { name: 'Gmail Watcher', key: 'gmail', icon: '📧' },
    { name: 'LinkedIn Watcher', key: 'linkedin', icon: '💼' },
    { name: 'Orchestrator', key: 'orchestrator', icon: '🧠' },
    { name: 'Approvals', key: 'approvals', icon: '✅' },
  ];

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-green-400 mb-4">
        🔧 System Health
      </h2>

      <div className="space-y-3">
        {components.map((component) => {
          const status = health[component.key as keyof typeof health] || 'unknown';
          return (
            <div
              key={component.key}
              className="flex items-center justify-between bg-gray-900/50 rounded-lg px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">{component.icon}</span>
                <span className="text-gray-300">{component.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${getStatusColor(status)} animate-pulse`} />
                <span className="text-sm text-gray-400">
                  {getStatusText(status)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
