'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileCheck, Save, AlertCircle, Shield, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { claimsRulesApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import type { ClaimsRulesConfig } from '@/lib/types';

export default function ClaimsRulesPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'auto' | 'fraud' | 'escalation'>('auto');
  const [changeReason, setChangeReason] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [formData, setFormData] = useState<any>({});

  const { data: config, isLoading } = useQuery<ClaimsRulesConfig>({
    queryKey: ['claimsRules'],
    queryFn: claimsRulesApi.get,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { config: any; reason: string }) =>
      claimsRulesApi.update(data.config, data.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claimsRules'] });
      setHasChanges(false);
      setChangeReason('');
      setFormData({});
      alert('Configuration change submitted for approval');
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const currentConfig = {
    auto_adjudication: { ...config?.auto_adjudication, ...formData.auto_adjudication },
    fraud_detection: { ...config?.fraud_detection, ...formData.fraud_detection },
  };

  const handleAutoChange = (field: string, value: any) => {
    setFormData((prev: any) => ({
      ...prev,
      auto_adjudication: { ...prev.auto_adjudication, [field]: value },
    }));
    setHasChanges(true);
  };

  const handleFraudChange = (field: string, value: any) => {
    setFormData((prev: any) => ({
      ...prev,
      fraud_detection: { ...prev.fraud_detection, [field]: value },
    }));
    setHasChanges(true);
  };

  const handleSubmit = () => {
    if (changeReason.length < 10) {
      alert('Please provide a change reason (at least 10 characters)');
      return;
    }
    updateMutation.mutate({ config: formData, reason: changeReason });
  };

  const tabs = [
    { id: 'auto', label: 'Auto-Adjudication', icon: FileCheck },
    { id: 'fraud', label: 'Fraud Detection', icon: Shield },
    { id: 'escalation', label: 'Escalation Rules', icon: AlertTriangle },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Claims Rules</h1>
        <p className="text-slate-500">Configure claims processing and fraud detection</p>
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === 'auto' && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Auto-Adjudication Settings</h2>
              </div>
              <div className="card-body space-y-4">
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="font-medium">Enable Auto-Adjudication</p>
                    <p className="text-sm text-slate-500">Automatically process eligible claims</p>
                  </div>
                  <button
                    onClick={() => handleAutoChange('enabled', !currentConfig.auto_adjudication?.enabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      currentConfig.auto_adjudication?.enabled ? 'bg-primary-600' : 'bg-slate-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        currentConfig.auto_adjudication?.enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div>
                  <label className="label">Max Auto-Approve Amount</label>
                  <div className="flex items-center">
                    <span className="text-slate-500 mr-2">$</span>
                    <input
                      type="number"
                      className="input w-40"
                      value={currentConfig.auto_adjudication?.max_auto_approve_amount || 500}
                      onChange={(e) => handleAutoChange('max_auto_approve_amount', parseFloat(e.target.value))}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Claims below this amount may be auto-approved</p>
                </div>

                <div>
                  <label className="label">Require Human Review Above</label>
                  <div className="flex items-center">
                    <span className="text-slate-500 mr-2">$</span>
                    <input
                      type="number"
                      className="input w-40"
                      value={currentConfig.auto_adjudication?.require_human_review_above || 2500}
                      onChange={(e) => handleAutoChange('require_human_review_above', parseFloat(e.target.value))}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Claims above this amount always require human review</p>
                </div>

                {/* Auto-Approve Conditions */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="font-medium text-slate-900 mb-3">Auto-Approve Conditions</p>
                  <div className="space-y-2">
                    {(config?.auto_adjudication?.auto_approve_conditions || []).map((condition: any, idx: number) => (
                      <div key={condition.name || idx} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                        <div className="flex items-center">
                          {condition.enabled ? (
                            <CheckCircle className="w-4 h-4 text-success-500 mr-2" />
                          ) : (
                            <XCircle className="w-4 h-4 text-slate-400 mr-2" />
                          )}
                          <div>
                            <span className="text-sm font-medium">{condition.name?.replace(/_/g, ' ')}</span>
                            <p className="text-xs text-slate-500">{condition.description}</p>
                          </div>
                        </div>
                        {condition.value && (
                          <span className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded">
                            {condition.value}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Auto-Deny Conditions */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="font-medium text-slate-900 mb-3">Auto-Deny Conditions</p>
                  <div className="space-y-2">
                    {(config?.auto_adjudication?.auto_deny_conditions || []).map((condition: any, idx: number) => (
                      <div key={condition.name || idx} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                        <div className="flex items-center">
                          {condition.enabled ? (
                            <XCircle className="w-4 h-4 text-danger-500 mr-2" />
                          ) : (
                            <XCircle className="w-4 h-4 text-slate-400 mr-2" />
                          )}
                          <div>
                            <span className="text-sm font-medium">{condition.name?.replace(/_/g, ' ')}</span>
                            <p className="text-xs text-slate-500">{condition.description}</p>
                          </div>
                        </div>
                        {condition.value && (
                          <span className="text-xs bg-danger-100 text-danger-700 px-2 py-1 rounded">
                            {condition.value}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'fraud' && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Fraud Detection Settings</h2>
              </div>
              <div className="card-body space-y-4">
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="font-medium">Enable Fraud Detection</p>
                    <p className="text-sm text-slate-500">AI-powered fraud analysis</p>
                  </div>
                  <button
                    onClick={() => handleFraudChange('enabled', !currentConfig.fraud_detection?.enabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      currentConfig.fraud_detection?.enabled ? 'bg-primary-600' : 'bg-slate-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        currentConfig.fraud_detection?.enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="label">
                      Flag Threshold: {((currentConfig.fraud_detection?.flag_threshold || 0.5) * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={currentConfig.fraud_detection?.flag_threshold || 0.5}
                      onChange={(e) => handleFraudChange('flag_threshold', parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="label">
                      Escalate Threshold: {((currentConfig.fraud_detection?.escalate_threshold || 0.7) * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={currentConfig.fraud_detection?.escalate_threshold || 0.7}
                      onChange={(e) => handleFraudChange('escalate_threshold', parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="label">
                      Deny Threshold: {((currentConfig.fraud_detection?.deny_threshold || 0.85) * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={currentConfig.fraud_detection?.deny_threshold || 0.85}
                      onChange={(e) => handleFraudChange('deny_threshold', parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>
                </div>

                {/* Velocity Checks */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="font-medium text-slate-900 mb-3">Velocity Checks</p>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Max Claims/Month</p>
                      <p className="text-lg font-bold text-primary-600">
                        {config?.fraud_detection?.velocity_check?.max_claims_per_month || 3}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Max Claims/Year</p>
                      <p className="text-lg font-bold text-primary-600">
                        {config?.fraud_detection?.velocity_check?.max_claims_per_year || 12}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Same Condition Cooldown</p>
                      <p className="text-lg font-bold text-primary-600">
                        {config?.fraud_detection?.velocity_check?.same_condition_cooldown_days || 30} days
                      </p>
                    </div>
                  </div>
                </div>

                {/* Duplicate Detection */}
                <div className="pt-4 border-t border-slate-200">
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium">Duplicate Detection</p>
                      <p className="text-sm text-slate-500">Detect duplicate claims</p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded ${
                      config?.fraud_detection?.duplicate_detection_enabled
                        ? 'bg-success-100 text-success-700'
                        : 'bg-slate-200 text-slate-500'
                    }`}>
                      {config?.fraud_detection?.duplicate_detection_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>

                {/* Suspicious Patterns */}
                <div className="pt-4 border-t border-slate-200">
                  <p className="font-medium text-slate-900 mb-3">Suspicious Patterns</p>
                  <div className="space-y-2">
                    {(config?.fraud_detection?.suspicious_patterns || []).map((pattern: any, idx: number) => (
                      <div key={pattern.name || idx} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                        <div className="flex items-center">
                          <AlertTriangle className={`w-4 h-4 mr-2 ${pattern.enabled ? 'text-warning-500' : 'text-slate-400'}`} />
                          <div>
                            <span className="text-sm font-medium">{pattern.name?.replace(/_/g, ' ')}</span>
                            <p className="text-xs text-slate-500">{pattern.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {pattern.threshold_days && (
                            <span className="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded">
                              {pattern.threshold_days} days
                            </span>
                          )}
                          <span className={`text-xs px-2 py-1 rounded ${
                            pattern.enabled ? 'bg-success-100 text-success-700' : 'bg-slate-200 text-slate-500'
                          }`}>
                            {pattern.enabled ? 'On' : 'Off'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'escalation' && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Escalation Rules</h2>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  {(config?.escalation_rules?.rules || []).map((rule: any, idx: number) => (
                    <div key={rule.name || idx} className="p-4 bg-slate-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium capitalize">{rule.name?.replace(/_/g, ' ')}</span>
                        <span className={`text-xs px-2 py-1 rounded ${rule.enabled ? 'bg-success-100 text-success-700' : 'bg-slate-200 text-slate-500'}`}>
                          {rule.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 mb-2">
                        {rule.description}
                      </p>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">
                          Escalate to: <span className="font-medium text-primary-600 capitalize">{rule.escalate_to?.replace(/_/g, ' ')}</span>
                        </span>
                        {rule.threshold && (
                          <span className="text-slate-500">
                            Threshold: <span className="font-medium text-slate-700">{rule.threshold}</span>
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-slate-500 mt-4">
                  Contact support to modify escalation rules.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Configuration Version</h2>
            </div>
            <div className="card-body">
              <p className="text-2xl font-bold text-primary-600">{config?.version || 1}</p>
              <p className="text-sm text-slate-500 mt-1">
                Last updated: {config?.updated_at ? new Date(config.updated_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          {/* Processing Settings Card */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Processing Settings</h2>
            </div>
            <div className="card-body space-y-3">
              <div className="flex justify-between p-2 bg-slate-50 rounded">
                <span className="text-sm text-slate-600">Require Vet Invoice</span>
                <span className={`text-xs px-2 py-1 rounded ${config?.require_vet_invoice ? 'bg-success-100 text-success-700' : 'bg-slate-200 text-slate-500'}`}>
                  {config?.require_vet_invoice ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between p-2 bg-slate-50 rounded">
                <span className="text-sm text-slate-600">Require Diagnosis</span>
                <span className={`text-xs px-2 py-1 rounded ${config?.require_diagnosis ? 'bg-success-100 text-success-700' : 'bg-slate-200 text-slate-500'}`}>
                  {config?.require_diagnosis ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between p-2 bg-slate-50 rounded">
                <span className="text-sm text-slate-600">Allow Partial Payment</span>
                <span className={`text-xs px-2 py-1 rounded ${config?.allow_partial_payment ? 'bg-success-100 text-success-700' : 'bg-slate-200 text-slate-500'}`}>
                  {config?.allow_partial_payment ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between p-2 bg-slate-50 rounded">
                <span className="text-sm text-slate-600">Max Processing Days</span>
                <span className="text-sm font-medium">{config?.max_processing_days || 5} days</span>
              </div>
            </div>
          </div>

          {hasChanges && (
            <div className="card border-warning-200 bg-warning-50">
              <div className="card-header border-warning-200">
                <h2 className="font-semibold text-slate-900 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-2 text-warning-600" />
                  Unsaved Changes
                </h2>
              </div>
              <div className="card-body space-y-4">
                <div>
                  <label className="label">Change Reason *</label>
                  <textarea
                    className="input"
                    rows={3}
                    placeholder="Describe why you're making this change..."
                    value={changeReason}
                    onChange={(e) => setChangeReason(e.target.value)}
                  />
                </div>
                <button
                  onClick={handleSubmit}
                  disabled={updateMutation.isPending}
                  className="btn-primary w-full flex items-center justify-center"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {updateMutation.isPending ? 'Submitting...' : 'Submit for Approval'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
