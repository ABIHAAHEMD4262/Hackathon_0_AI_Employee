'use client';

interface StatsCardsProps {
  stats: {
    needsAction: number;
    inProgress: number;
    pendingApproval: number;
    completedToday: number;
  };
}

export default function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Needs Action',
      value: stats.needsAction,
      icon: '📥',
      color: 'from-red-500 to-red-600',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30',
    },
    {
      title: 'In Progress',
      value: stats.inProgress,
      icon: '⚡',
      color: 'from-yellow-500 to-yellow-600',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/30',
    },
    {
      title: 'Pending Approval',
      value: stats.pendingApproval,
      icon: '⏳',
      color: 'from-orange-500 to-orange-600',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/30',
    },
    {
      title: 'Completed Today',
      value: stats.completedToday,
      icon: '✅',
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.title}
          className={`${card.bgColor} ${card.borderColor} border rounded-xl p-6 transition-all hover:scale-105`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">{card.title}</p>
              <p className={`text-4xl font-bold bg-gradient-to-r ${card.color} bg-clip-text text-transparent`}>
                {card.value}
              </p>
            </div>
            <span className="text-4xl">{card.icon}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
