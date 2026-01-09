'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  User,
  Calendar,
  FileText,
} from 'lucide-react';
import Link from 'next/link';
import { approvalsApi } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import type { Approval } from '@/lib/types';

function DiffViewer({ current, proposed }: { current: any; proposed: any }) {
  const renderValue = (value: any, depth = 0): JSX.Element => {
    if (value === null || value === undefined) {
      return <span className="text-slate-400">null</span>;
    }
    if (typeof value === 'boolean') {
      return <span className={value ? 'text-success-600' : 'text-danger-600'}>{String(value)}</span>;
    }
    if (typeof value === 'number') {
      return <span className="text-blue-600">{value}</span>;
    }
    if (typeof value === 'string') {
      return <span className="text-green-600">"{value}"</span>;
    }
    if (Array.isArray(value)) {
      return (
        <span>
          [{value.map((v, i) => (
            <span key={i}>
              {i > 0 && ', '}
              {renderValue(v, depth + 1)}
            </span>
          ))}]
        </span>
      );
    }
    if (typeof value === 'object') {
      return (
        <div className="ml-4">
          {Object.entries(value).map(([k, v]) => (
            <div key={k}>
              <span className="text-slate-600">{k}:</span> {renderValue(v, depth + 1)}
            </div>
          ))}
        </div>
      );
    }
    return <span>{String(value)}</span>;
  };

  const findChanges = (curr: any, prop: any, path = ''): { path: string; current: any; proposed: any }[] => {
    const changes: { path: string; current: any; proposed: any }[] = [];

    const allKeys = new Set([...Object.keys(curr || {}), ...Object.keys(prop || {})]);

    allKeys.forEach((key) => {
      const currentVal = curr?.[key];
      const proposedVal = prop?.[key];
      const currentPath = path ? `${path}.${key}` : key;

      if (JSON.stringify(currentVal) !== JSON.stringify(proposedVal)) {
        if (typeof currentVal === 'object' && typeof proposedVal === 'object' && !Array.isArray(currentVal)) {
          changes.push(...findChanges(currentVal, proposedVal, currentPath));
        } else {
          changes.push({ path: currentPath, current: currentVal, proposed: proposedVal });
        }
      }
    });

    return changes;
  };

  const changes = findChanges(current, proposed);

  return (
    <div className="space-y-3">
      {changes.length === 0 ? (
        <p className="text-slate-500">No changes detected</p>
      ) : (
        changes.map((change, idx) => (
          <div key={idx} className="p-3 bg-slate-50 rounded-lg">
            <p className="text-sm font-medium text-slate-700 mb-2">{change.path}</p>
            <div className="grid grid-cols-2 gap-4 text-sm font-mono">
              <div className="p-2 bg-danger-50 rounded border border-danger-100">
                <p className="text-xs text-danger-600 mb-1">Current</p>
                {renderValue(change.current)}
              </div>
              <div className="p-2 bg-success-50 rounded border border-success-100">
                <p className="text-xs text-success-600 mb-1">Proposed</p>
                {renderValue(change.proposed)}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default function ApprovalDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const queryClient = useQueryClient();

  const [rejectReason, setRejectReason] = useState('');
  const [approvalComment, setApprovalComment] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);

  const { data: approval, isLoading } = useQuery<Approval>({
    queryKey: ['approval', id],
    queryFn: () => approvalsApi.get(id),
  });

  const approveMutation = useMutation({
    mutationFn: () => approvalsApi.approve(id, approvalComment || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval', id] });
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      router.push('/approvals');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => approvalsApi.reject(id, rejectReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval', id] });
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      router.push('/approvals');
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!approval) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Approval not found</p>
        <Link href="/approvals" className="btn-primary mt-4">
          Back to Approvals
        </Link>
      </div>
    );
  }

  const isPending = approval.status === 'pending';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link href="/approvals" className="btn-ghost p-2 mr-4">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Approval Request</h1>
            <p className="text-slate-500">{approval.id}</p>
          </div>
        </div>
        {isPending && (
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowRejectModal(true)}
              className="btn-danger flex items-center"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Reject
            </button>
            <button
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
              className="btn-success flex items-center"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              {approveMutation.isPending ? 'Approving...' : 'Approve'}
            </button>
          </div>
        )}
      </div>

      {/* Status Banner */}
      <div
        className={`p-4 rounded-lg ${
          approval.status === 'pending'
            ? 'bg-warning-50 border border-warning-200'
            : approval.status === 'approved'
            ? 'bg-success-50 border border-success-200'
            : 'bg-danger-50 border border-danger-200'
        }`}
      >
        <div className="flex items-center">
          {approval.status === 'pending' ? (
            <Clock className="w-5 h-5 text-warning-600 mr-2" />
          ) : approval.status === 'approved' ? (
            <CheckCircle className="w-5 h-5 text-success-600 mr-2" />
          ) : (
            <XCircle className="w-5 h-5 text-danger-600 mr-2" />
          )}
          <span className="font-medium capitalize">{approval.status}</span>
          {approval.approved_by_name && (
            <span className="text-slate-600 ml-2">
              by {approval.approved_by_name} on{' '}
              {approval.approved_at ? formatDateTime(approval.approved_at) : ''}
            </span>
          )}
        </div>
        {approval.rejection_reason && (
          <p className="mt-2 text-sm text-danger-700">
            Reason: {approval.rejection_reason}
          </p>
        )}
        {approval.approval_comment && (
          <p className="mt-2 text-sm text-success-700">
            Comment: {approval.approval_comment}
          </p>
        )}
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Change Summary */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900 flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Change Summary
              </h2>
            </div>
            <div className="card-body">
              <p className="text-lg font-medium text-slate-900">{approval.change_summary}</p>
              <p className="mt-2 text-slate-600">{approval.change_reason}</p>
            </div>
          </div>

          {/* Diff View */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Configuration Changes</h2>
            </div>
            <div className="card-body">
              <DiffViewer current={approval.current_value} proposed={approval.proposed_value} />
            </div>
          </div>

          {/* Approval Comment (for pending) */}
          {isPending && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Approval Comment (Optional)</h2>
              </div>
              <div className="card-body">
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Add a comment for this approval..."
                  value={approvalComment}
                  onChange={(e) => setApprovalComment(e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Request Info */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Request Details</h2>
            </div>
            <div className="card-body space-y-4">
              <div className="flex items-center">
                <User className="w-4 h-4 text-slate-400 mr-2" />
                <div>
                  <p className="text-sm text-slate-500">Requested By</p>
                  <p className="font-medium">{approval.requested_by_name}</p>
                </div>
              </div>
              <div className="flex items-center">
                <Calendar className="w-4 h-4 text-slate-400 mr-2" />
                <div>
                  <p className="text-sm text-slate-500">Requested At</p>
                  <p className="font-medium">{formatDateTime(approval.requested_at)}</p>
                </div>
              </div>
              <div className="flex items-center">
                <Clock className="w-4 h-4 text-slate-400 mr-2" />
                <div>
                  <p className="text-sm text-slate-500">Expires At</p>
                  <p className="font-medium">{formatDateTime(approval.expires_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Tags */}
          {approval.tags && approval.tags.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Tags</h2>
              </div>
              <div className="card-body">
                <div className="flex flex-wrap gap-2">
                  {approval.tags.map((tag: string) => (
                    <span key={tag} className="badge-gray">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Reject Request</h3>
            <div className="mb-4">
              <label className="label">Rejection Reason *</label>
              <textarea
                className="input"
                rows={4}
                placeholder="Provide a reason for rejection (min 10 characters)..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowRejectModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() => rejectMutation.mutate()}
                disabled={rejectReason.length < 10 || rejectMutation.isPending}
                className="btn-danger"
              >
                {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
