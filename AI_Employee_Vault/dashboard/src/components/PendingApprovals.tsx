'use client';

interface ApprovalItem {
  id: string;
  type: string;
  title: string;
  created: string;
  preview: string;
}

interface PendingApprovalsProps {
  items: ApprovalItem[];
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export default function PendingApprovals({ items, onApprove, onReject }: PendingApprovalsProps) {
  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'email_draft': return '📧';
      case 'linkedin_post': return '💼';
      case 'social_post': return '📱';
      default: return '📋';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'email_draft': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
      case 'linkedin_post': return 'text-sky-400 bg-sky-500/10 border-sky-500/30';
      case 'social_post': return 'text-purple-400 bg-purple-500/10 border-purple-500/30';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-green-400 mb-4 flex items-center gap-2">
        ⏳ Pending Approvals
        {items.length > 0 && (
          <span className="bg-orange-500/20 text-orange-400 text-sm px-2 py-0.5 rounded-full">
            {items.length}
          </span>
        )}
      </h2>

      {items.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="text-4xl mb-2">✅</p>
          <p>No items pending approval</p>
          <p className="text-sm">You're all caught up!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-gray-900/50 rounded-lg border border-gray-700 p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{getTypeIcon(item.type)}</span>
                    <span className={`text-xs px-2 py-0.5 rounded border ${getTypeColor(item.type)}`}>
                      {item.type.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(item.created).toLocaleString()}
                    </span>
                  </div>

                  <h3 className="font-medium text-gray-200 mb-2">{item.title}</h3>

                  <p className="text-sm text-gray-400 line-clamp-2">
                    {item.preview}
                  </p>
                </div>

                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => onApprove(item.id)}
                    className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors flex items-center gap-1"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => onReject(item.id)}
                    className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 border border-red-500/30 rounded-lg transition-colors flex items-center gap-1"
                  >
                    ✗ Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
