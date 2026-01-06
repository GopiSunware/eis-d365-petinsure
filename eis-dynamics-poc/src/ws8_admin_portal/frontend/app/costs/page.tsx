'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Cloud,
  Server,
  AlertTriangle,
  Plus,
  Cpu,
  Zap,
  Database,
  FileText,
  Bot,
} from 'lucide-react';
import { costsApi } from '@/lib/api';
import { formatCurrency, formatPercent, getProviderLabel } from '@/lib/utils';
import { CostTrendChart } from '@/components/costs/CostTrendChart';
import { ServiceCostTable } from '@/components/costs/ServiceCostTable';

type TabType = 'overview' | 'azure' | 'aws' | 'ai-usage' | 'budgets';

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toLocaleString();
}

function ProviderCard({
  provider,
  summary,
  forecast,
}: {
  provider: 'azure' | 'aws';
  summary: any;
  forecast?: any;
}) {
  const Icon = provider === 'azure' ? Cloud : Server;

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <div className="flex items-center">
          <Icon className={`w-5 h-5 mr-2 ${provider === 'azure' ? 'text-blue-500' : 'text-orange-500'}`} />
          <h2 className="font-semibold text-slate-900">{getProviderLabel(provider)}</h2>
        </div>
        <span className="badge-gray">{summary?.currency || 'USD'}</span>
      </div>
      <div className="card-body space-y-4">
        <div>
          <p className="text-sm text-slate-500">Month to Date</p>
          <p className="text-2xl font-bold text-slate-900">
            {formatCurrency(summary?.total_cost || 0)}
          </p>
        </div>
        {forecast && (
          <div className="pt-3 border-t border-slate-100">
            <p className="text-sm text-slate-500">Forecasted (End of Month)</p>
            <p className="text-lg font-semibold text-slate-700">
              {formatCurrency(forecast.forecasted_cost)}
            </p>
          </div>
        )}
        <div className="pt-3 border-t border-slate-100">
          <p className="text-sm font-medium text-slate-700 mb-2">Top Services</p>
          <div className="space-y-2">
            {Object.entries(summary?.by_service || {})
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .slice(0, 3)
              .map(([service, cost]) => (
                <div key={service} className="flex justify-between text-sm">
                  <span className="text-slate-600">{service}</span>
                  <span className="font-medium">{formatCurrency(cost as number)}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function BudgetAlertRow({ alert }: { alert: any }) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-6 py-4">
        <div className="flex items-center">
          {alert.is_critical ? (
            <AlertTriangle className="w-4 h-4 text-danger-500 mr-2" />
          ) : alert.is_warning ? (
            <AlertTriangle className="w-4 h-4 text-warning-500 mr-2" />
          ) : null}
          <span className="font-medium">{alert.name}</span>
        </div>
      </td>
      <td className="px-6 py-4">
        <span className="badge-gray">{alert.provider.toUpperCase()}</span>
      </td>
      <td className="px-6 py-4">{formatCurrency(alert.budget_amount)}</td>
      <td className="px-6 py-4">{formatCurrency(alert.current_spend)}</td>
      <td className="px-6 py-4">
        <div className="flex items-center">
          <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden mr-2">
            <div
              className={`h-full rounded-full ${
                alert.is_critical
                  ? 'bg-danger-500'
                  : alert.is_warning
                  ? 'bg-warning-500'
                  : 'bg-success-500'
              }`}
              style={{ width: `${Math.min(alert.percent_used, 100)}%` }}
            />
          </div>
          <span className="text-sm">{formatPercent(alert.percent_used)}</span>
        </div>
      </td>
      <td className="px-6 py-4">
        {alert.is_active ? (
          <span className="badge-success">Active</span>
        ) : (
          <span className="badge-gray">Inactive</span>
        )}
      </td>
    </tr>
  );
}

function AIUsageCard({
  title,
  icon: Icon,
  tokens,
  cost,
  requests,
  iconColor,
}: {
  title: string;
  icon: any;
  tokens: number;
  cost: number;
  requests?: number;
  iconColor: string;
}) {
  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${iconColor} bg-opacity-10 mr-3`}>
              <Icon className={`w-5 h-5 ${iconColor}`} />
            </div>
            <h3 className="font-medium text-slate-900">{title}</h3>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-slate-500">Tokens</span>
            <span className="font-semibold">{formatNumber(tokens)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-slate-500">Cost</span>
            <span className="font-semibold text-primary-600">{formatCurrency(cost)}</span>
          </div>
          {requests !== undefined && (
            <div className="flex justify-between">
              <span className="text-sm text-slate-500">Requests</span>
              <span className="font-medium">{formatNumber(requests)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PlatformCostBreakdown({ costBreakdown }: { costBreakdown: Record<string, number> }) {
  const total = Object.values(costBreakdown).reduce((sum, val) => sum + val, 0);
  const sortedEntries = Object.entries(costBreakdown).sort(([, a], [, b]) => b - a);

  const getIcon = (category: string) => {
    if (category.toLowerCase().includes('ai') || category.toLowerCase().includes('llm')) return Bot;
    if (category.toLowerCase().includes('document') || category.toLowerCase().includes('ocr')) return FileText;
    if (category.toLowerCase().includes('database') || category.toLowerCase().includes('cosmos')) return Database;
    if (category.toLowerCase().includes('storage')) return Server;
    if (category.toLowerCase().includes('compute')) return Cpu;
    return Zap;
  };

  const getColor = (index: number) => {
    const colors = [
      'bg-blue-500',
      'bg-purple-500',
      'bg-green-500',
      'bg-orange-500',
      'bg-pink-500',
      'bg-cyan-500',
    ];
    return colors[index % colors.length];
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="font-semibold text-slate-900">Platform Cost Breakdown</h2>
      </div>
      <div className="card-body">
        {/* Stacked bar */}
        <div className="h-4 rounded-full overflow-hidden flex mb-4">
          {sortedEntries.map(([category, cost], index) => (
            <div
              key={category}
              className={`${getColor(index)} first:rounded-l-full last:rounded-r-full`}
              style={{ width: `${(cost / total) * 100}%` }}
              title={`${category}: ${formatCurrency(cost)}`}
            />
          ))}
        </div>

        {/* Legend */}
        <div className="space-y-3">
          {sortedEntries.map(([category, cost], index) => {
            const Icon = getIcon(category);
            const percent = total > 0 ? (cost / total) * 100 : 0;
            return (
              <div key={category} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded ${getColor(index)} mr-3`} />
                  <Icon className="w-4 h-4 text-slate-400 mr-2" />
                  <span className="text-sm text-slate-700">{category}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-500">{formatPercent(percent)}</span>
                  <span className="font-medium">{formatCurrency(cost)}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center">
          <span className="font-medium text-slate-700">Total Platform Cost</span>
          <span className="text-xl font-bold text-slate-900">{formatCurrency(total)}</span>
        </div>
      </div>
    </div>
  );
}

export default function CostsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['costDashboard'],
    queryFn: costsApi.getDashboard,
  });

  const { data: forecastData } = useQuery({
    queryKey: ['costForecast'],
    queryFn: () => costsApi.getForecast('all', 30),
  });

  const { data: aiUsageData } = useQuery({
    queryKey: ['aiUsage'],
    queryFn: () => costsApi.getAIUsage(),
  });

  const { data: platformUsageData } = useQuery({
    queryKey: ['platformUsage'],
    queryFn: () => costsApi.getPlatformUsage(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'azure', label: 'Azure' },
    { id: 'aws', label: 'AWS' },
    { id: 'ai-usage', label: 'AI Usage' },
    { id: 'budgets', label: 'Budget Alerts' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Cost Monitor</h1>
          <p className="text-slate-500">Track and manage cloud spending</p>
        </div>
        {(dashboardData?.is_mock_data || aiUsageData?.is_mock_data) && (
          <span className="badge-warning">Demo Data</span>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="card">
              <div className="card-body">
                <p className="text-sm text-slate-500">Combined Total (MTD)</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(dashboardData?.combined_total || 0)}
                </p>
                <div className="flex items-center mt-2">
                  {dashboardData?.cost_change_percent > 0 ? (
                    <TrendingUp className="w-4 h-4 text-danger-500 mr-1" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-success-500 mr-1" />
                  )}
                  <span
                    className={`text-sm ${
                      dashboardData?.cost_change_percent > 0
                        ? 'text-danger-600'
                        : 'text-success-600'
                    }`}
                  >
                    {formatPercent(Math.abs(dashboardData?.cost_change_percent || 0))}
                  </span>
                  <span className="text-sm text-slate-500 ml-1">vs last month</span>
                </div>
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <p className="text-sm text-slate-500">Forecasted (EOM)</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(dashboardData?.current_month_forecast?.forecasted_cost || 0)}
                </p>
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <p className="text-sm text-slate-500">AI/LLM Tokens</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatNumber(aiUsageData?.total_tokens || 0)}
                </p>
                <p className="text-sm text-primary-600 mt-1">
                  {formatCurrency(aiUsageData?.total_cost || 0)} spent
                </p>
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <p className="text-sm text-slate-500">AI Requests</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatNumber(aiUsageData?.total_requests || 0)}
                </p>
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <p className="text-sm text-slate-500">Active Alerts</p>
                <p className="text-2xl font-bold text-slate-900">
                  {dashboardData?.triggered_alerts?.length || 0}
                </p>
              </div>
            </div>
          </div>

          {/* Platform Cost Breakdown - Only show when there's cost data */}
          {platformUsageData?.cost_breakdown && Object.keys(platformUsageData.cost_breakdown).length > 0 && (
            <PlatformCostBreakdown costBreakdown={platformUsageData.cost_breakdown} />
          )}

          {/* Provider Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ProviderCard
              provider="azure"
              summary={dashboardData?.azure_summary}
              forecast={forecastData?.forecasts?.find((f: any) => f.provider === 'azure')}
            />
            <ProviderCard
              provider="aws"
              summary={dashboardData?.aws_summary}
              forecast={forecastData?.forecasts?.find((f: any) => f.provider === 'aws')}
            />
          </div>

          {/* Cost Trend */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Cost Trend (Daily)</h2>
            </div>
            <div className="card-body">
              <CostTrendChart
                azureData={dashboardData?.azure_summary?.daily_breakdown || []}
                awsData={dashboardData?.aws_summary?.daily_breakdown || []}
              />
            </div>
          </div>

          {/* Top Services */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Top Services by Cost</h2>
            </div>
            <div className="card-body">
              <ServiceCostTable services={dashboardData?.top_services || []} />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ai-usage' && (
        <div className="space-y-6">
          {/* AI Usage Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card bg-gradient-to-br from-blue-50 to-white">
              <div className="card-body">
                <div className="flex items-center mb-2">
                  <Bot className="w-5 h-5 text-blue-500 mr-2" />
                  <p className="text-sm text-slate-500">Total Tokens Used</p>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  {formatNumber(aiUsageData?.total_tokens || 0)}
                </p>
                <div className="mt-2 text-sm text-slate-500">
                  <span className="text-green-600">{formatNumber(aiUsageData?.total_input_tokens || 0)} input</span>
                  {' / '}
                  <span className="text-orange-600">{formatNumber(aiUsageData?.total_output_tokens || 0)} output</span>
                </div>
              </div>
            </div>
            <div className="card bg-gradient-to-br from-green-50 to-white">
              <div className="card-body">
                <div className="flex items-center mb-2">
                  <DollarSign className="w-5 h-5 text-green-500 mr-2" />
                  <p className="text-sm text-slate-500">Total AI Cost</p>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(aiUsageData?.total_cost || 0)}
                </p>
              </div>
            </div>
            <div className="card bg-gradient-to-br from-purple-50 to-white">
              <div className="card-body">
                <div className="flex items-center mb-2">
                  <Zap className="w-5 h-5 text-purple-500 mr-2" />
                  <p className="text-sm text-slate-500">Total Requests</p>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  {formatNumber(aiUsageData?.total_requests || 0)}
                </p>
              </div>
            </div>
            <div className="card bg-gradient-to-br from-orange-50 to-white">
              <div className="card-body">
                <div className="flex items-center mb-2">
                  <TrendingUp className="w-5 h-5 text-orange-500 mr-2" />
                  <p className="text-sm text-slate-500">Avg Cost/Request</p>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(aiUsageData?.avg_cost_per_request || 0)}
                </p>
              </div>
            </div>
          </div>

          {/* Usage by Provider */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Usage by Provider</h2>
            </div>
            <div className="card-body">
              {Object.keys(aiUsageData?.by_provider || {}).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(aiUsageData?.by_provider || {}).map(([provider, data]: [string, any]) => (
                    <AIUsageCard
                      key={provider}
                      title={provider}
                      icon={provider.toLowerCase().includes('azure') ? Cloud : Server}
                      tokens={data.tokens || 0}
                      cost={data.cost || 0}
                      requests={data.requests}
                      iconColor={provider.toLowerCase().includes('azure') ? 'text-blue-500' : 'text-orange-500'}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">
                  No AI/LLM API usage detected. Usage will appear here when Azure OpenAI or AWS Bedrock services are used.
                </p>
              )}
            </div>
          </div>

          {/* Usage by Model */}
          {Object.keys(aiUsageData?.by_model || {}).length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Usage by Model</h2>
              </div>
              <div className="card-body">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th className="text-right">Tokens</th>
                      <th className="text-right">Requests</th>
                      <th className="text-right">Avg Tokens/Request</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(aiUsageData?.by_model || {}).map(([model, data]: [string, any]) => (
                      <tr key={model} className="hover:bg-slate-50">
                        <td>
                          <div className="flex items-center">
                            <Bot className="w-4 h-4 text-slate-400 mr-2" />
                            {model}
                          </div>
                        </td>
                        <td className="text-right font-medium">{formatNumber(data.tokens || 0)}</td>
                        <td className="text-right">{formatNumber(data.requests || 0)}</td>
                        <td className="text-right text-slate-500">
                          {data.requests > 0 ? formatNumber(Math.round((data.tokens || 0) / data.requests)) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Platform Usage (Document Intelligence, Database) - Only shown when data exists */}
          {platformUsageData && (platformUsageData.document_usage || platformUsageData.database_usage) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Document Intelligence */}
              {platformUsageData.document_usage && (
                <div className="card">
                  <div className="card-header flex items-center">
                    <FileText className="w-5 h-5 text-purple-500 mr-2" />
                    <h2 className="font-semibold text-slate-900">Document Intelligence</h2>
                  </div>
                  <div className="card-body space-y-3">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Pages Processed</span>
                      <span className="font-medium">{formatNumber(platformUsageData.document_usage.total_pages_processed)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Successful Extractions</span>
                      <span className="font-medium text-success-600">{formatNumber(platformUsageData.document_usage.successful_extractions)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Failed Extractions</span>
                      <span className="font-medium text-danger-600">{formatNumber(platformUsageData.document_usage.failed_extractions)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Success Rate</span>
                      <span className="font-medium">{formatPercent(platformUsageData.document_usage.success_rate)}</span>
                    </div>
                    <div className="pt-3 border-t border-slate-100 flex justify-between">
                      <span className="font-medium text-slate-700">Total Cost</span>
                      <span className="font-bold text-primary-600">{formatCurrency(platformUsageData.document_usage.total_cost)}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Database Usage */}
              {platformUsageData.database_usage && (
                <div className="card">
                  <div className="card-header flex items-center">
                    <Database className="w-5 h-5 text-green-500 mr-2" />
                    <h2 className="font-semibold text-slate-900">Database (Cosmos DB)</h2>
                  </div>
                  <div className="card-body space-y-3">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Total RU Consumed</span>
                      <span className="font-medium">{formatNumber(platformUsageData.database_usage.total_ru_consumed)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Storage</span>
                      <span className="font-medium">{platformUsageData.database_usage.storage_gb.toFixed(2)} GB</span>
                    </div>
                    {Object.entries(platformUsageData.database_usage.ru_by_operation || {}).map(([op, ru]: [string, any]) => (
                      <div key={op} className="flex justify-between text-sm">
                        <span className="text-slate-400 ml-2">- {op}</span>
                        <span>{formatNumber(ru)} RU</span>
                      </div>
                    ))}
                    <div className="pt-3 border-t border-slate-100 flex justify-between">
                      <span className="font-medium text-slate-700">Total Cost</span>
                      <span className="font-bold text-primary-600">{formatCurrency(platformUsageData.database_usage.total_cost)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'budgets' && (
        <div className="space-y-6">
          <div className="flex justify-end">
            <button className="btn-primary flex items-center">
              <Plus className="w-4 h-4 mr-2" />
              Create Budget Alert
            </button>
          </div>

          <div className="card">
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Provider</th>
                    <th>Budget</th>
                    <th>Current Spend</th>
                    <th>Usage</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData?.active_alerts?.map((alert: any) => (
                    <BudgetAlertRow key={alert.id} alert={alert} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {(activeTab === 'azure' || activeTab === 'aws') && (
        <div className="space-y-6">
          <ProviderCard
            provider={activeTab}
            summary={activeTab === 'azure' ? dashboardData?.azure_summary : dashboardData?.aws_summary}
            forecast={forecastData?.forecasts?.find((f: any) => f.provider === activeTab)}
          />

          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Service Breakdown</h2>
            </div>
            <div className="card-body">
              <table className="table">
                <thead>
                  <tr>
                    <th>Service</th>
                    <th className="text-right">Cost</th>
                    <th className="text-right">% of Total</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(
                    (activeTab === 'azure'
                      ? dashboardData?.azure_summary?.by_service
                      : dashboardData?.aws_summary?.by_service) || {}
                  )
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([service, cost]) => {
                      const total =
                        activeTab === 'azure'
                          ? dashboardData?.azure_summary?.total_cost
                          : dashboardData?.aws_summary?.total_cost;
                      const percent = total ? ((cost as number) / total) * 100 : 0;
                      return (
                        <tr key={service}>
                          <td>{service}</td>
                          <td className="text-right">{formatCurrency(cost as number)}</td>
                          <td className="text-right">{formatPercent(percent)}</td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
