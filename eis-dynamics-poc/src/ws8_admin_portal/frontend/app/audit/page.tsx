'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Filter, Calendar, Search } from 'lucide-react';
import { auditApi } from '@/lib/api';
import { formatDateTime, getRoleLabel } from '@/lib/utils';
import type { AuditLog } from '@/lib/types';

function AuditLogRow({ log }: { log: AuditLog }) {
  const getActionColor = (action: string) => {
    const colors: Record<string, string> = {
      create: 'badge-success',
      update: 'badge-primary',
      delete: 'badge-danger',
      approve: 'badge-success',
      reject: 'badge-danger',
      login: 'badge-gray',
      logout: 'badge-gray',
    };
    return colors[action] || 'badge-gray';
  };

  return (
    <tr className="hover:bg-slate-50">
      <td className="px-6 py-4 text-sm text-slate-500">
        {formatDateTime(log.timestamp)}
      </td>
      <td className="px-6 py-4">
        <span className={getActionColor(log.action)}>{log.action}</span>
      </td>
      <td className="px-6 py-4">
        <span className="badge-gray">{log.category}</span>
      </td>
      <td className="px-6 py-4">
        <div>
          <p className="font-medium text-slate-900">{log.user_name}</p>
          <p className="text-sm text-slate-500">{getRoleLabel(log.user_role)}</p>
        </div>
      </td>
      <td className="px-6 py-4">
        <div>
          <p className="text-slate-900">{log.entity_type}</p>
          <p className="text-sm text-slate-500 truncate max-w-[200px]">{log.entity_id}</p>
        </div>
      </td>
      <td className="px-6 py-4">
        <p className="text-sm text-slate-600 truncate max-w-[250px]">
          {log.change_summary || '-'}
        </p>
      </td>
      <td className="px-6 py-4">
        {log.success ? (
          <span className="badge-success">Success</span>
        ) : (
          <span className="badge-danger">Failed</span>
        )}
      </td>
    </tr>
  );
}

export default function AuditPage() {
  const [filters, setFilters] = useState({
    action: '',
    category: '',
    user_id: '',
    start_date: '',
    end_date: '',
  });

  const { data: actionTypes } = useQuery({
    queryKey: ['auditActionTypes'],
    queryFn: auditApi.getActionTypes,
  });

  const { data: stats } = useQuery({
    queryKey: ['auditStats'],
    queryFn: auditApi.getStats,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['auditLogs', filters],
    queryFn: () =>
      auditApi.getLogs({
        action: filters.action || undefined,
        category: filters.category || undefined,
        user_id: filters.user_id || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
        limit: 100,
      }),
  });

  const handleExport = async () => {
    try {
      const result = await auditApi.exportLogs({
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
        format: 'csv',
      });

      // Create download
      const blob = new Blob([result.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Audit Logs</h1>
          <p className="text-slate-500">Track all administrative actions</p>
        </div>
        <button onClick={handleExport} className="btn-secondary flex items-center">
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Total Logs</p>
            <p className="text-2xl font-bold text-slate-900">{stats?.total_logs || 0}</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Actions Today</p>
            <p className="text-2xl font-bold text-slate-900">{stats?.actions_today || 0}</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Config Changes (Week)</p>
            <p className="text-2xl font-bold text-slate-900">{stats?.config_changes_this_week || 0}</p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Pending Approvals</p>
            <p className="text-2xl font-bold text-warning-600">{stats?.approvals_pending || 0}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="card-body">
          <div className="flex items-center space-x-4 flex-wrap gap-y-4">
            <div className="flex items-center">
              <Filter className="w-4 h-4 text-slate-400 mr-2" />
              <span className="text-sm font-medium text-slate-700">Filters:</span>
            </div>
            <select
              className="select w-40"
              value={filters.action}
              onChange={(e) => setFilters((f) => ({ ...f, action: e.target.value }))}
            >
              <option value="">All Actions</option>
              {actionTypes?.actions?.map((action: string) => (
                <option key={action} value={action}>
                  {action}
                </option>
              ))}
            </select>
            <select
              className="select w-44"
              value={filters.category}
              onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
            >
              <option value="">All Categories</option>
              {actionTypes?.categories?.map((cat: string) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-slate-400" />
              <input
                type="date"
                className="input w-40"
                value={filters.start_date}
                onChange={(e) => setFilters((f) => ({ ...f, start_date: e.target.value }))}
              />
              <span className="text-slate-400">to</span>
              <input
                type="date"
                className="input w-40"
                value={filters.end_date}
                onChange={(e) => setFilters((f) => ({ ...f, end_date: e.target.value }))}
              />
            </div>
            <button
              onClick={() => setFilters({ action: '', category: '', user_id: '', start_date: '', end_date: '' })}
              className="btn-ghost text-sm"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Category</th>
                  <th>User</th>
                  <th>Entity</th>
                  <th>Summary</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data?.logs?.map((log: AuditLog) => (
                  <AuditLogRow key={log.id} log={log} />
                ))}
              </tbody>
            </table>
          )}
        </div>
        {data?.logs?.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <p className="text-slate-500">No audit logs found</p>
          </div>
        )}
      </div>
    </div>
  );
}
