'use client';

export default function TaskChart() {
  // Simple bar chart visualization without external library
  const data = [
    { day: 'Mon', completed: 5, pending: 2 },
    { day: 'Tue', completed: 8, pending: 3 },
    { day: 'Wed', completed: 6, pending: 1 },
    { day: 'Thu', completed: 10, pending: 4 },
    { day: 'Fri', completed: 7, pending: 2 },
    { day: 'Sat', completed: 3, pending: 1 },
    { day: 'Sun', completed: 2, pending: 0 },
  ];

  const maxValue = Math.max(...data.map(d => d.completed + d.pending));

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-green-400 mb-4">
        📊 Weekly Tasks
      </h2>

      <div className="flex items-end justify-between gap-2 h-32">
        {data.map((item) => (
          <div key={item.day} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full flex flex-col-reverse gap-0.5">
              {/* Completed bar */}
              <div
                className="w-full bg-green-500 rounded-t"
                style={{
                  height: `${(item.completed / maxValue) * 80}px`,
                }}
              />
              {/* Pending bar */}
              <div
                className="w-full bg-orange-500 rounded-t"
                style={{
                  height: `${(item.pending / maxValue) * 80}px`,
                }}
              />
            </div>
            <span className="text-xs text-gray-500">{item.day}</span>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-6 mt-4 pt-4 border-t border-gray-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded" />
          <span className="text-xs text-gray-400">Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-orange-500 rounded" />
          <span className="text-xs text-gray-400">Pending</span>
        </div>
      </div>
    </div>
  );
}
