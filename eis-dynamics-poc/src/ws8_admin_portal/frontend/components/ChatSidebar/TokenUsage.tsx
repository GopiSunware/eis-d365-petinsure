'use client';

interface TokenUsageData {
  total: number;
  cost: number;
  history: Array<{ tokens: number; cost: number }>;
}

interface TokenUsageProps {
  usage: TokenUsageData;
}

export default function TokenUsage({ usage }: TokenUsageProps) {
  if (!usage || usage.total === 0) return null;

  const formatNumber = (n: number) => {
    if (n >= 1000) {
      return (n / 1000).toFixed(1) + 'k';
    }
    return n.toString();
  };

  const formatCost = (cost: number) => {
    if (cost < 0.01) {
      return '<$0.01';
    }
    return `$${cost.toFixed(2)}`;
  };

  return (
    <div className="flex-shrink-0 border-t border-gray-200 px-4 py-2 bg-gray-50">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3">
          <span>
            Tokens: {formatNumber(usage.total)}
          </span>
          <span className="text-gray-300">|</span>
          <span>
            Requests: {usage.history.length}
          </span>
        </div>
        <div className="font-medium text-gray-600">
          {formatCost(usage.cost)}
        </div>
      </div>
    </div>
  );
}
