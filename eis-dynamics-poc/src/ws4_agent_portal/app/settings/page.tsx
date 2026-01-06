"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, AIConfig, AIModel } from "@/lib/api";
import {
  Settings,
  Cpu,
  Zap,
  CheckCircle,
  XCircle,
  Loader2,
  Sparkles,
  Bot,
  Brain,
} from "lucide-react";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(2000);
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  // Fetch current config
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ["aiConfig"],
    queryFn: () => api.getAIConfig(),
  });

  // Fetch available models
  const { data: modelsData, isLoading: modelsLoading } = useQuery({
    queryKey: ["aiModels"],
    queryFn: () => api.getAIModels(),
  });

  // Update config mutation
  const updateConfig = useMutation({
    mutationFn: (newConfig: Partial<AIConfig>) => api.updateAIConfig(newConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aiConfig"] });
    },
  });

  // Initialize form when config loads
  useEffect(() => {
    if (config) {
      setSelectedProvider(config.provider);
      setSelectedModel(config.model_id);
      setTemperature(config.temperature);
      setMaxTokens(config.max_tokens);
    }
  }, [config]);

  // Filter models by provider
  const filteredModels = modelsData?.models.filter(
    (m) => m.provider === selectedProvider
  ) || [];

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    // Select first model of the new provider
    const providerModels = modelsData?.models.filter((m) => m.provider === provider) || [];
    if (providerModels.length > 0) {
      setSelectedModel(providerModels[0].model_id);
    }
  };

  const handleSave = async () => {
    await updateConfig.mutateAsync({
      provider: selectedProvider,
      model_id: selectedModel,
      temperature,
      max_tokens: maxTokens,
    });
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.testAIConnection();
      setTestResult(result);
    } catch (error: any) {
      setTestResult({ status: "error", error: error.message });
    } finally {
      setTesting(false);
    }
  };

  if (configLoading || modelsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Configure AI provider and model for claims processing</p>
        </div>
        <div className="flex items-center space-x-2">
          <Sparkles className="h-6 w-6 text-primary-600" />
          <span className="text-sm text-gray-500">AI-Powered Insurance</span>
        </div>
      </div>

      {/* AI Configuration Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-4">
          <div className="flex items-center space-x-3">
            <Brain className="h-6 w-6 text-white" />
            <h2 className="text-lg font-semibold text-white">AI Configuration</h2>
          </div>
          <p className="text-primary-100 text-sm mt-1">
            Select the AI provider and model for FNOL processing and fraud detection
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              AI Provider
            </label>
            <div className="grid grid-cols-2 gap-4">
              {/* Claude Option */}
              <button
                onClick={() => handleProviderChange("claude")}
                disabled={!config?.provider_status?.claude?.configured}
                className={`relative flex items-center p-4 rounded-lg border-2 transition-all ${
                  selectedProvider === "claude"
                    ? "border-orange-500 bg-orange-50"
                    : "border-gray-200 hover:border-orange-300"
                } ${!config?.provider_status?.claude?.configured ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
              >
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                    <Bot className="h-6 w-6 text-orange-600" />
                  </div>
                </div>
                <div className="ml-4 text-left">
                  <h3 className="text-sm font-semibold text-gray-900">Anthropic Claude</h3>
                  <p className="text-xs text-gray-500">Advanced reasoning & analysis</p>
                </div>
                {selectedProvider === "claude" && (
                  <CheckCircle className="absolute top-2 right-2 h-5 w-5 text-orange-500" />
                )}
                {!config?.provider_status?.claude?.configured && (
                  <span className="absolute top-2 right-2 text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded">
                    Not Configured
                  </span>
                )}
              </button>

              {/* OpenAI Option */}
              <button
                onClick={() => handleProviderChange("openai")}
                disabled={!config?.provider_status?.openai?.configured}
                className={`relative flex items-center p-4 rounded-lg border-2 transition-all ${
                  selectedProvider === "openai"
                    ? "border-green-500 bg-green-50"
                    : "border-gray-200 hover:border-green-300"
                } ${!config?.provider_status?.openai?.configured ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
              >
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                    <Cpu className="h-6 w-6 text-green-600" />
                  </div>
                </div>
                <div className="ml-4 text-left">
                  <h3 className="text-sm font-semibold text-gray-900">Azure OpenAI</h3>
                  <p className="text-xs text-gray-500">GPT-4 powered analysis</p>
                </div>
                {selectedProvider === "openai" && (
                  <CheckCircle className="absolute top-2 right-2 h-5 w-5 text-green-500" />
                )}
                {!config?.provider_status?.openai?.configured && (
                  <span className="absolute top-2 right-2 text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded">
                    Not Configured
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {filteredModels.map((model) => (
                <option key={model.model_id} value={model.model_id}>
                  {model.display_name} - {model.description}
                </option>
              ))}
            </select>
          </div>

          {/* Advanced Settings */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature: {temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Precise (0)</span>
                <span>Creative (1)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <select
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value={1000}>1,000 (Fast)</option>
                <option value={2000}>2,000 (Balanced)</option>
                <option value={4000}>4,000 (Detailed)</option>
                <option value={8000}>8,000 (Maximum)</option>
              </select>
            </div>
          </div>

          {/* Current Configuration Display */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Current Active Configuration</h4>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Provider:</span>
                <span className="ml-2 font-medium capitalize">{config?.provider}</span>
              </div>
              <div>
                <span className="text-gray-500">Model:</span>
                <span className="ml-2 font-medium">{config?.model_id}</span>
              </div>
              <div>
                <span className="text-gray-500">Temperature:</span>
                <span className="ml-2 font-medium">{config?.temperature}</span>
              </div>
              <div>
                <span className="text-gray-500">Max Tokens:</span>
                <span className="ml-2 font-medium">{config?.max_tokens}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <button
              onClick={handleTest}
              disabled={testing}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {testing ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Zap className="h-4 w-4 mr-2" />
              )}
              Test Connection
            </button>

            <button
              onClick={handleSave}
              disabled={updateConfig.isPending}
              className="flex items-center px-6 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {updateConfig.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="h-4 w-4 mr-2" />
              )}
              Save Configuration
            </button>
          </div>

          {/* Test Result */}
          {testResult && (
            <div
              className={`mt-4 p-4 rounded-lg ${
                testResult.status === "success"
                  ? "bg-green-50 border border-green-200"
                  : "bg-red-50 border border-red-200"
              }`}
            >
              <div className="flex items-center">
                {testResult.status === "success" ? (
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500 mr-2" />
                )}
                <span
                  className={`font-medium ${
                    testResult.status === "success" ? "text-green-700" : "text-red-700"
                  }`}
                >
                  {testResult.status === "success" ? "Connection Successful!" : "Connection Failed"}
                </span>
              </div>
              {testResult.response && (
                <p className="mt-2 text-sm text-green-600">{testResult.response}</p>
              )}
              {testResult.error && (
                <p className="mt-2 text-sm text-red-600">{testResult.error}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <Settings className="h-5 w-5 text-blue-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Demo Configuration</h3>
            <p className="mt-1 text-sm text-blue-700">
              This settings page allows you to switch between AI providers (Claude or OpenAI)
              and select different models for the demo. Changes take effect immediately for
              new FNOL submissions and fraud detection analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
