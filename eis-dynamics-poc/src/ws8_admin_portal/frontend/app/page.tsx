'use client';

import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  AlertTriangle,
  Activity,
  Bot,
} from 'lucide-react';
import { costsApi, approvalsApi, auditApi } from '@/lib/api';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { CostTrendChart } from '@/components/costs/CostTrendChart';
import { PendingApprovalsWidget } from '@/components/approval/PendingApprovalsWidget';
import { ServiceCostTable } from '@/components/costs/ServiceCostTable';

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  color = 'primary',
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}) {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    danger: 'bg-danger-50 text-danger-600',
  };

  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
            {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
            {trend && trendValue && (
              <div className="mt-2 flex items-center">
                {trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-danger-500 mr-1" />
                ) : trend === 'down' ? (
                  <TrendingDown className="w-4 h-4 text-success-500 mr-1" />
                ) : null}
                <span
                  className={`text-sm font-medium ${
                    trend === 'up' ? 'text-danger-600' : 'text-success-600'
                  }`}
                >
                  {trendValue}
                </span>
                <span className="text-sm text-slate-500 ml-1">vs last month</span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>
  );
}

function BudgetAlertCard({ alert }: { alert: any }) {
  const getAlertStyle = () => {
    if (alert.is_critical) return 'border-danger-200 bg-danger-50';
    if (alert.is_warning) return 'border-warning-200 bg-warning-50';
    return 'border-slate-200 bg-white';
  };

  return (
    <div className={`rounded-lg border p-4 ${getAlertStyle()}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          {alert.is_critical ? (
            <AlertTriangle className="w-5 h-5 text-danger-500 mr-2" />
          ) : alert.is_warning ? (
            <AlertTriangle className="w-5 h-5 text-warning-500 mr-2" />
          ) : (
            <CheckCircle className="w-5 h-5 text-success-500 mr-2" />
          )}
          <div>
            <p className="font-medium text-slate-900">{alert.name}</p>
            <p className="text-sm text-slate-500">{alert.provider.toUpperCase()}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="font-medium text-slate-900">
            {formatPercent(alert.percent_used)}
          </p>
          <p className="text-sm text-slate-500">
            {formatCurrency(alert.current_spend)} / {formatCurrency(alert.budget_amount)}
          </p>
        </div>
      </div>
      <div className="mt-3 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            alert.is_critical
              ? 'bg-danger-500'
              : alert.is_warning
              ? 'bg-warning-500'
              : 'bg-success-500'
          }`}
          style={{ width: `${Math.min(alert.percent_used, 100)}%` }}
        />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: costData, isLoading: costLoading } = useQuery({
    queryKey: ['costDashboard'],
    queryFn: costsApi.getDashboard,
  });

  const { data: approvalStats } = useQuery({
    queryKey: ['approvalStats'],
    queryFn: approvalsApi.getStats,
  });

  const { data: auditStats } = useQuery({
    queryKey: ['auditStats'],
    queryFn: auditApi.getStats,
  });

  if (costLoading) {
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
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500">
          Overview of your EIS Pet Insurance Platform
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Monthly Spend"
          value={formatCurrency(costData?.combined_total || 0)}
          icon={DollarSign}
          trend={costData?.cost_change_percent > 0 ? 'up' : 'down'}
          trendValue={formatPercent(Math.abs(costData?.cost_change_percent || 0))}
          color="primary"
        />
        <StatCard
          title="Pending Approvals"
          value={String(approvalStats?.pending_count || 0)}
          subtitle="Awaiting review"
          icon={Clock}
          color={approvalStats?.pending_count > 0 ? 'warning' : 'success'}
        />
        <StatCard
          title="AI/ML Costs"
          value={formatCurrency(costData?.ai_ml_total || 0)}
          subtitle="This month"
          icon={Bot}
          color="primary"
        />
        <StatCard
          title="Actions Today"
          value={String(auditStats?.actions_today || 0)}
          subtitle="Audit events"
          icon={Activity}
          color="primary"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost Trend Chart */}
        <div className="lg:col-span-2 card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-slate-900">Cost Trend</h2>
          </div>
          <div className="card-body">
            <CostTrendChart
              azureData={costData?.azure_summary?.daily_breakdown || []}
              awsData={costData?.aws_summary?.daily_breakdown || []}
            />
          </div>
        </div>

        {/* Budget Alerts */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-slate-900">Budget Alerts</h2>
          </div>
          <div className="card-body space-y-3">
            {costData?.active_alerts?.length > 0 ? (
              costData.active_alerts.map((alert: any) => (
                <BudgetAlertCard key={alert.id} alert={alert} />
              ))
            ) : (
              <p className="text-slate-500 text-sm">No active budget alerts</p>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Services */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-slate-900">Top Services by Cost</h2>
          </div>
          <div className="card-body">
            <ServiceCostTable services={costData?.top_services || []} />
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Pending Approvals</h2>
            <a
              href="/approvals"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              View all
            </a>
          </div>
          <div className="card-body">
            <PendingApprovalsWidget />
          </div>
        </div>
      </div>
    </div>
  );
}
