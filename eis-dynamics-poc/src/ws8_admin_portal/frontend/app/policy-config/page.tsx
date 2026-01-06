'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, Clock, XCircle, CheckCircle } from 'lucide-react';
import { policyConfigApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import type { PolicyPlansConfig } from '@/lib/types';

export default function PolicyConfigPage() {
  const [activeTab, setActiveTab] = useState<'plans' | 'waiting' | 'exclusions'>('plans');

  const { data: config, isLoading } = useQuery<PolicyPlansConfig>({
    queryKey: ['policyConfig'],
    queryFn: policyConfigApi.get,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const tabs = [
    { id: 'plans', label: 'Plans', icon: Shield },
    { id: 'waiting', label: 'Waiting Periods', icon: Clock },
    { id: 'exclusions', label: 'Exclusions', icon: XCircle },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Policy Configuration</h1>
        <p className="text-slate-500">Manage insurance plans and coverage rules</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'plans' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {(config?.plans || []).map((plan: any, idx: number) => (
            <div key={plan.plan_id || idx} className="card">
              <div className="card-header">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg">{plan.name}</h3>
                  <span className={`badge-${plan.plan_id === 'premium' || plan.plan_id === 'unlimited' ? 'primary' : plan.plan_id === 'standard' ? 'success' : 'gray'}`}>
                    {plan.plan_id}
                  </span>
                </div>
              </div>
              <div className="card-body space-y-4">
                <div>
                  <p className="text-sm text-slate-500">Description</p>
                  <p className="text-sm text-slate-700">{plan.description}</p>
                </div>

                <div>
                  <p className="text-sm text-slate-500">Annual Limit</p>
                  <p className="text-xl font-bold text-primary-600">
                    {plan.limits?.annual_limit ? formatCurrency(plan.limits.annual_limit) : 'Unlimited'}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-slate-500">Premium Factor</p>
                  <p className="font-medium">{plan.premium_factor}x</p>
                </div>

                {plan.deductible_options && plan.deductible_options.length > 0 && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Deductible Options</p>
                    <div className="flex flex-wrap gap-1">
                      {plan.deductible_options.map((d: number) => (
                        <span key={d} className="badge-gray">{formatCurrency(d)}</span>
                      ))}
                    </div>
                  </div>
                )}

                {plan.reimbursement_options && plan.reimbursement_options.length > 0 && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Reimbursement Options</p>
                    <div className="flex flex-wrap gap-1">
                      {plan.reimbursement_options.map((r: number) => (
                        <span key={r} className="badge-gray">{r}%</span>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <p className="text-sm text-slate-500 mb-2">Coverage</p>
                  <div className="grid grid-cols-2 gap-1 text-xs">
                    {plan.covers_accidents && <span className="flex items-center"><CheckCircle className="w-3 h-3 text-success-500 mr-1" />Accidents</span>}
                    {plan.covers_illnesses && <span className="flex items-center"><CheckCircle className="w-3 h-3 text-success-500 mr-1" />Illnesses</span>}
                    {plan.covers_wellness && <span className="flex items-center"><CheckCircle className="w-3 h-3 text-success-500 mr-1" />Wellness</span>}
                    {plan.covers_dental && <span className="flex items-center"><CheckCircle className="w-3 h-3 text-success-500 mr-1" />Dental</span>}
                    {plan.covers_behavioral && <span className="flex items-center"><CheckCircle className="w-3 h-3 text-success-500 mr-1" />Behavioral</span>}
                    {plan.covers_hereditary && <span className="flex items-center"><CheckCircle className="w-3 h-3 text-success-500 mr-1" />Hereditary</span>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'waiting' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Waiting Periods</h2>
            </div>
            <div className="card-body">
              <table className="table">
                <thead>
                  <tr>
                    <th>Condition Type</th>
                    <th>Waiting Period</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="flex items-center">
                      <Clock className="w-4 h-4 text-slate-400 mr-2" />
                      Accidents
                    </td>
                    <td>{config?.waiting_periods?.accidents_days ?? 0} days</td>
                  </tr>
                  <tr>
                    <td className="flex items-center">
                      <Clock className="w-4 h-4 text-slate-400 mr-2" />
                      Illnesses
                    </td>
                    <td>{config?.waiting_periods?.illnesses_days ?? 14} days</td>
                  </tr>
                  <tr>
                    <td className="flex items-center">
                      <Clock className="w-4 h-4 text-slate-400 mr-2" />
                      Orthopedic Conditions
                    </td>
                    <td>{config?.waiting_periods?.orthopedic_days ?? 180} days</td>
                  </tr>
                  <tr>
                    <td className="flex items-center">
                      <Clock className="w-4 h-4 text-slate-400 mr-2" />
                      Cancer
                    </td>
                    <td>{config?.waiting_periods?.cancer_days ?? 30} days</td>
                  </tr>
                  <tr>
                    <td className="flex items-center">
                      <Clock className="w-4 h-4 text-slate-400 mr-2" />
                      Dental
                    </td>
                    <td>{config?.waiting_periods?.dental_days ?? 30} days</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Coverage Rules</h2>
            </div>
            <div className="card-body space-y-4">
              <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-600">Pre-existing Lookback</span>
                <span className="font-medium">
                  {config?.coverage_rules?.pre_existing_lookback_months ?? 18} months
                </span>
              </div>
              <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-600">Min Enrollment Age</span>
                <span className="font-medium">
                  {config?.coverage_rules?.min_enrollment_age_weeks ?? 8} weeks
                </span>
              </div>
              <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-600">Max Enrollment Age (Dogs)</span>
                <span className="font-medium">
                  {config?.coverage_rules?.max_enrollment_age_dogs_years ?? 14} years
                </span>
              </div>
              <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-600">Max Enrollment Age (Cats)</span>
                <span className="font-medium">
                  {config?.coverage_rules?.max_enrollment_age_cats_years ?? 16} years
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'exclusions' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Global Exclusions</h2>
            </div>
            <div className="card-body">
              {(config?.exclusions?.global_exclusions || []).length > 0 ? (
                <ul className="space-y-2">
                  {(config?.exclusions?.global_exclusions || []).map((exclusion: string, idx: number) => (
                    <li key={idx} className="flex items-start p-3 bg-slate-50 rounded-lg">
                      <XCircle className="w-4 h-4 text-danger-500 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-sm">{exclusion}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-500 text-sm">No global exclusions defined</p>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Breed-Specific Exclusions</h2>
            </div>
            <div className="card-body">
              {config?.exclusions?.breed_exclusions && Object.keys(config.exclusions.breed_exclusions).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(config.exclusions.breed_exclusions).map(([breed, exclusions]: [string, any]) => (
                    <div key={breed} className="p-3 bg-slate-50 rounded-lg">
                      <p className="font-medium text-slate-900 capitalize mb-2">{breed.replace(/_/g, ' ')}</p>
                      <ul className="space-y-1">
                        {(exclusions || []).map((exclusion: string, idx: number) => (
                          <li key={idx} className="flex items-center text-sm text-slate-600">
                            <XCircle className="w-3 h-3 text-danger-500 mr-2" />
                            {exclusion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-sm">No breed-specific exclusions defined</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Version Info */}
      <div className="card max-w-sm">
        <div className="card-body">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Configuration Version</p>
              <p className="text-xl font-bold text-primary-600">{config?.version}</p>
            </div>
            <p className="text-sm text-slate-500">
              Updated: {config?.updated_at ? new Date(config.updated_at).toLocaleDateString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
