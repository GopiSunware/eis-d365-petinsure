'use client';

import { formatCurrency } from '@/lib/utils';

interface ServiceCost {
  name: string;
  cost: number;
  provider: string;
}

interface ServiceCostTableProps {
  services: ServiceCost[];
}

export function ServiceCostTable({ services }: ServiceCostTableProps) {
  if (!services || services.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        No service cost data available
      </div>
    );
  }

  const total = services.reduce((sum, s) => sum + s.cost, 0);

  return (
    <div className="space-y-3">
      {services.map((service, idx) => {
        const percent = total > 0 ? (service.cost / total) * 100 : 0;
        const providerColor = service.provider === 'azure' ? 'bg-sky-500' : 'bg-orange-500';

        return (
          <div key={idx} className="flex items-center">
            <div className="w-2 h-2 rounded-full mr-3" style={{
              backgroundColor: service.provider === 'azure' ? '#0ea5e9' : '#f97316'
            }} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-slate-900 truncate">
                  {service.name}
                </span>
                <span className="text-sm font-medium text-slate-900 ml-2">
                  {formatCurrency(service.cost)}
                </span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${providerColor}`}
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
