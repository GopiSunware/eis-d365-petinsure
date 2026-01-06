'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, AlertCircle, Eye } from 'lucide-react';
import Link from 'next/link';
import { approvalsApi } from '@/lib/api';
import { formatDateTime, getStatusColor } from '@/lib/utils';
import type { Approval, ApprovalStatus, ConfigChangeType } from '@/lib/types';

const statusOptions: { value: ApprovalStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'expired', label: 'Expired' },
  { value: 'cancelled', label: 'Cancelled' },
];

const changeTypeOptions: { value: ConfigChangeType | ''; label: string }[] = [
  { value: '', label: 'All Types' },
  { value: 'ai_config', label: 'AI Configuration' },
  { value: 'claims_rules', label: 'Claims Rules' },
  { value: 'policy_config', label: 'Policy Configuration' },
  { value: 'rating_config', label: 'Rating Factors' },
  { value: 'system_config', label: 'System Configuration' },
];

function StatusBadge({ status }: { status: ApprovalStatus }) {
  const styles: Record<ApprovalStatus, { bg: string; icon: React.ElementType }> = {
    pending: { bg: 'badge-warning', icon: Clock },
    approved: { bg: 'badge-success', icon: CheckCircle },
    rejected: { bg: 'badge-danger', icon: XCircle },
    expired: { bg: 'badge-gray', icon: AlertCircle },
    cancelled: { bg: 'badge-gray', icon: XCircle },
  };

  const { bg, icon: Icon } = styles[status];

  return (
    <span className={`${bg} flex items-center`}>
      <Icon className="w-3 h-3 mr-1" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function ChangeTypeBadge({ type }: { type: ConfigChangeType }) {
  const labels: Record<ConfigChangeType, string> = {
    ai_config: 'AI Config',
    claims_rules: 'Claims',
    policy_config: 'Policy',
    rating_config: 'Rating',
    system_config: 'System',
  };

  return <span className="badge-primary">{labels[type]}</span>;
}

function ApprovalRow({ approval }: { approval: Approval }) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-6 py-4">
        <div>
          <p className="font-medium text-slate-900">{approval.change_summary}</p>
          <p className="text-sm text-slate-500">{approval.id}</p>
        </div>
      </td>
      <td className="px-6 py-4">
        <ChangeTypeBadge type={approval.change_type} />
      </td>
      <td className="px-6 py-4">
        <StatusBadge status={approval.status} />
      </td>
      <td className="px-6 py-4">
        <div>
          <p className="text-slate-900">{approval.requested_by_name}</p>
          <p className="text-sm text-slate-500">{formatDateTime(approval.requested_at)}</p>
        </div>
      </td>
      <td className="px-6 py-4">
        {approval.approved_by_name ? (
          <div>
            <p className="text-slate-900">{approval.approved_by_name}</p>
            <p className="text-sm text-slate-500">
              {approval.approved_at ? formatDateTime(approval.approved_at) : ''}
            </p>
          </div>
        ) : (
          <span className="text-slate-400">-</span>
        )}
      </td>
      <td className="px-6 py-4">
        <Link
          href={`/approvals/${approval.id}`}
          className="btn-ghost p-2"
        >
          <Eye className="w-4 h-4" />
        </Link>
      </td>
    </tr>
  );
}

export default function ApprovalsPage() {
  const [statusFilter, setStatusFilter] = useState<ApprovalStatus | ''>('');
  const [typeFilter, setTypeFilter] = useState<ConfigChangeType | ''>('');

  const { data, isLoading } = useQuery({
    queryKey: ['approvals', statusFilter, typeFilter],
    queryFn: () =>
      approvalsApi.list({
        status: statusFilter || undefined,
        change_type: typeFilter || undefined,
        limit: 50,
      }),
  });

  const { data: stats } = useQuery({
    queryKey: ['approvalStats'],
    queryFn: approvalsApi.getStats,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Approvals</h1>
        <p className="text-slate-500">Review and manage configuration change requests</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Pending</p>
            <p className="text-2xl font-bold text-warning-600">{stats?.pending_count || 0}</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Approved (This Week)</p>
            <p className="text-2xl font-bold text-success-600">{stats?.approved_this_week || 0}</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Rejected (This Week)</p>
            <p className="text-2xl font-bold text-danger-600">{stats?.rejected_this_week || 0}</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Total Requests</p>
            <p className="text-2xl font-bold text-slate-900">{stats?.total_requests || 0}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div>
          <select
            className="select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ApprovalStatus | '')}
          >
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <select
            className="select"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as ConfigChangeType | '')}
          >
            {changeTypeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1"></div>
        <p className="text-sm text-slate-500">
          Showing {data?.approvals?.length || 0} of {data?.total || 0} requests
        </p>
      </div>

      {/* Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Change</th>
                <th>Type</th>
                <th>Status</th>
                <th>Requested By</th>
                <th>Reviewed By</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data?.approvals?.map((approval: Approval) => (
                <ApprovalRow key={approval.id} approval={approval} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
