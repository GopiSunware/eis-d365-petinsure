'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bot, Save, History, AlertCircle } from 'lucide-react';
import { aiConfigApi } from '@/lib/api';
import type { AIConfiguration, AIProvider } from '@/lib/types';

const providers: { value: AIProvider; label: string }[] = [
  { value: 'anthropic', label: 'Anthropic (Claude)' },
  { value: 'openai', label: 'OpenAI (GPT)' },
  { value: 'azure_openai', label: 'Azure OpenAI' },
  { value: 'aws_bedrock', label: 'AWS Bedrock' },
];

const modelsByProvider: Record<AIProvider, { value: string; label: string }[]> = {
  anthropic: [
    { value: 'claude-3-opus', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
  ],
  openai: [
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  ],
  azure_openai: [
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' },
  ],
  aws_bedrock: [
    { value: 'anthropic.claude-3-sonnet', label: 'Claude 3 Sonnet' },
    { value: 'amazon.titan-text-express', label: 'Titan Text Express' },
  ],
};

export default function AIConfigPage() {
  const queryClient = useQueryClient();
  const [changeReason, setChangeReason] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const { data: config, isLoading } = useQuery<AIConfiguration>({
    queryKey: ['aiConfig'],
    queryFn: aiConfigApi.get,
  });

  const [formData, setFormData] = useState<Partial<AIConfiguration>>({});

  const updateMutation = useMutation({
    mutationFn: (data: { config: any; reason: string }) =>
      aiConfigApi.update(data.config, data.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aiConfig'] });
      setHasChanges(false);
      setChangeReason('');
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

  const currentConfig = { ...config, ...formData };

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleFeatureToggle = (feature: string) => {
    const currentFeatures = currentConfig.features || {};
    handleChange('features', {
      ...currentFeatures,
      [feature]: !currentFeatures[feature as keyof typeof currentFeatures],
    });
  };

  const handleSubmit = () => {
    if (changeReason.length < 10) {
      alert('Please provide a change reason (at least 10 characters)');
      return;
    }
    updateMutation.mutate({ config: formData, reason: changeReason });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">AI Configuration</h1>
          <p className="text-slate-500">
            Configure AI provider settings and feature toggles
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="btn-secondary flex items-center">
            <History className="w-4 h-4 mr-2" />
            History
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Provider Settings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center">
                <Bot className="w-5 h-5 mr-2" />
                Provider Settings
              </h2>
            </div>
            <div className="card-body space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">AI Provider</label>
                  <select
                    className="select"
                    value={currentConfig.provider}
                    onChange={(e) => handleChange('provider', e.target.value)}
                  >
                    {providers.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Model</label>
                  <select
                    className="select"
                    value={currentConfig.model}
                    onChange={(e) => handleChange('model', e.target.value)}
                  >
                    {modelsByProvider[currentConfig.provider as AIProvider]?.map((m) => (
                      <option key={m.value} value={m.value}>
                        {m.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="label">
                  Temperature: {currentConfig.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={currentConfig.temperature}
                  onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Precise (0)</span>
                  <span>Creative (1)</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Max Tokens</label>
                  <input
                    type="number"
                    className="input"
                    value={currentConfig.max_tokens}
                    onChange={(e) => handleChange('max_tokens', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <label className="label">Timeout (seconds)</label>
                  <input
                    type="number"
                    className="input"
                    value={currentConfig.timeout_seconds}
                    onChange={(e) => handleChange('timeout_seconds', parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div>
                <label className="label">Retry Attempts</label>
                <input
                  type="number"
                  className="input w-32"
                  min="0"
                  max="5"
                  value={currentConfig.retry_attempts}
                  onChange={(e) => handleChange('retry_attempts', parseInt(e.target.value))}
                />
              </div>
            </div>
          </div>

          {/* Feature Toggles */}
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold text-slate-900">Feature Toggles</h2>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                {[
                  { key: 'summarization', label: 'Document Summarization', desc: 'Auto-summarize claim documents' },
                  { key: 'claim_assessment', label: 'AI Claim Assessment', desc: 'Use AI for claim evaluation' },
                  { key: 'fraud_detection', label: 'Fraud Detection', desc: 'AI-powered fraud analysis' },
                  { key: 'customer_interaction', label: 'Customer Interaction', desc: 'AI chat support' },
                  { key: 'document_analysis', label: 'Document Analysis', desc: 'Extract data from documents' },
                ].map((feature) => (
                  <div key={feature.key} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900">{feature.label}</p>
                      <p className="text-sm text-slate-500">{feature.desc}</p>
                    </div>
                    <button
                      onClick={() => handleFeatureToggle(feature.key)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        currentConfig.features?.[feature.key as keyof typeof currentConfig.features]
                          ? 'bg-primary-600'
                          : 'bg-slate-300'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          currentConfig.features?.[feature.key as keyof typeof currentConfig.features]
                            ? 'translate-x-6'
                            : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Current Version */}
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Current Version</h2>
            </div>
            <div className="card-body">
              <p className="text-2xl font-bold text-primary-600">{config?.version}</p>
              <p className="text-sm text-slate-500 mt-1">
                Last updated: {config?.updated_at ? new Date(config.updated_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          {/* Submit Changes */}
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
