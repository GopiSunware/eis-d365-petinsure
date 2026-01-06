'use client';

import { useQuery } from '@tanstack/react-query';
import { Clock, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { approvalsApi } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import type { Approval, ConfigChangeType } from '@/lib/types';

const typeLabels: Record<ConfigChangeType, string> = {
  ai_config: 'AI Config',
  claims_rules: 'Claims',
  policy_config: 'Policy',
  rating_config: 'Rating',
  system_config: 'System',
};

export function PendingApprovalsWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['pendingApprovals'],
    queryFn: approvalsApi.listPending,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const approvals = data?.approvals?.slice(0, 5) || [];

  if (approvals.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="text-slate-500 text-sm">No pending approvals</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {approvals.map((approval: Approval) => (
        <Link
          key={approval.id}
          href={`/approvals/${approval.id}`}
          className="block p-3 hover:bg-slate-50 rounded-lg transition-colors group"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className="badge-primary text-xs">
                  {typeLabels[approval.change_type]}
                </span>
                <span className="badge-warning text-xs flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  Pending
                </span>
              </div>
              <p className="text-sm font-medium text-slate-900 truncate">
                {approval.change_summary}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                by {approval.requested_by_name} • {formatDateTime(approval.requested_at)}
              </p>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-colors flex-shrink-0 mt-1" />
          </div>
        </Link>
      ))}

      {data?.pending_count > 5 && (
        <Link
          href="/approvals"
          className="block text-center text-sm text-primary-600 hover:text-primary-700 py-2"
        >
          View all {data.pending_count} pending approvals
        </Link>
      )}
    </div>
  );
}
