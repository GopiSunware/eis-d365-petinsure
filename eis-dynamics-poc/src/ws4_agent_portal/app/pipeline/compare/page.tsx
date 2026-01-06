"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { clsx } from "clsx";
import {
  ArrowLeft,
  Code2,
  Bot,
  Zap,
  Clock,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Play,
  Shield,
  FileWarning,
  FileText,
} from "lucide-react";
import { pipelineApi, Scenario, ComparisonResult } from "@/lib/pipeline-api";

export default function ComparisonPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [quickMode, setQuickMode] = useState<"simple" | "medium" | "complex">("medium");

  // Load scenarios
  useEffect(() => {
    const loadScenarios = async () => {
      try {
        const data = await pipelineApi.getScenarios();
        setScenarios(data.scenarios);
        if (data.scenarios.length > 0) {
          setSelectedScenario(data.scenarios[0].id);
        }
      } catch (err) {
        console.error("Failed to load scenarios:", err);
      }
    };
    loadScenarios();
  }, []);

  const runComparison = async () => {
    setIsLoading(true);
    setError(null);
    setComparisonResult(null);

    try {
      let result: ComparisonResult;
      if (selectedScenario) {
        result = await pipelineApi.runScenarioComparison(selectedScenario);
      } else {
        result = await pipelineApi.runQuickComparison(quickMode);
      }
      setComparisonResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setIsLoading(false);
    }
  };

  const runQuickComparison = async (complexity: "simple" | "medium" | "complex") => {
    setQuickMode(complexity);
    setIsLoading(true);
    setError(null);
    setComparisonResult(null);

    try {
      const result = await pipelineApi.runQuickComparison(complexity);
      setComparisonResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setIsLoading(false);
    }
  };

  const getSelectedScenarioDetails = () => {
    return scenarios.find((s) => s.id === selectedScenario);
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatCurrency = (amount: number | undefined | null) => {
    if (amount === undefined || amount === null || isNaN(amount)) return "N/A";
    return `$${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatScore = (score: unknown, decimals: number = 1) => {
    if (score === undefined || score === null) return "N/A";
    const num = Number(score);
    if (isNaN(num)) return "N/A";
    return num.toFixed(decimals);
  };

  const formatPercentage = (value: unknown) => {
    if (value === undefined || value === null) return "N/A";
    const num = Number(value);
    if (isNaN(num)) return "N/A";
    return `${(num * 100).toFixed(0)}%`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/pipeline"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Code vs Agent: 1-to-1 Comparison
          </h1>
          <p className="text-gray-500 mt-1">
            Run the same claim through both pipelines and compare results
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-wrap items-end gap-4">
          {/* Scenario Selection */}
          <div className="flex-1 min-w-[300px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Claim Scenario
            </label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            >
              {/* Fraud Scenarios */}
              <optgroup label="FRAUD DETECTION (AI vs Rules)">
                {scenarios.filter(s => s.id.startsWith("FRAUD")).map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name} - ${scenario.claim_amount?.toLocaleString() || 0}
                  </option>
                ))}
              </optgroup>
              {/* Validation Scenarios */}
              <optgroup label="DATA VALIDATION (AI Detection)">
                {scenarios.filter(s => s.id.startsWith("VAL")).map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name} - ${scenario.claim_amount?.toLocaleString() || 0}
                  </option>
                ))}
              </optgroup>
              {/* Normal Scenarios */}
              <optgroup label="Standard Claims">
                {scenarios.filter(s => s.id.startsWith("SCN")).map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name} - ${scenario.claim_amount?.toLocaleString() || 0} ({scenario.claim_type})
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          <button
            onClick={runComparison}
            disabled={isLoading || !selectedScenario}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
              isLoading || !selectedScenario
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700"
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            {isLoading ? "Running..." : "Run Comparison"}
          </button>
        </div>

        {/* Quick Compare Buttons */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quick Compare (Demo Data)
          </label>
          <div className="flex gap-2">
            {(["simple", "medium", "complex"] as const).map((level) => (
              <button
                key={level}
                onClick={() => runQuickComparison(level)}
                disabled={isLoading}
                className={clsx(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  isLoading
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : level === "simple"
                    ? "bg-green-100 text-green-700 hover:bg-green-200"
                    : level === "medium"
                    ? "bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
                    : "bg-red-100 text-red-700 hover:bg-red-200"
                )}
              >
                {level === "simple" && "Simple (~$500)"}
                {level === "medium" && "Medium (~$3,000)"}
                {level === "complex" && "Complex (~$8,500)"}
              </button>
            ))}
          </div>
        </div>

        {/* Scenario Details */}
        {getSelectedScenarioDetails() && (
          <div className={clsx(
            "mt-4 p-3 rounded-lg border",
            selectedScenario.startsWith("FRAUD") && "bg-red-50 border-red-200",
            selectedScenario.startsWith("VAL") && "bg-orange-50 border-orange-200",
            selectedScenario.startsWith("SCN") && "bg-blue-50 border-blue-200"
          )}>
            <div className="flex items-start gap-3">
              {/* Icon based on type */}
              <div className={clsx(
                "p-2 rounded-lg shrink-0",
                selectedScenario.startsWith("FRAUD") && "bg-red-100",
                selectedScenario.startsWith("VAL") && "bg-orange-100",
                selectedScenario.startsWith("SCN") && "bg-blue-100"
              )}>
                {selectedScenario.startsWith("FRAUD") && <Shield className="w-5 h-5 text-red-600" />}
                {selectedScenario.startsWith("VAL") && <FileWarning className="w-5 h-5 text-orange-600" />}
                {selectedScenario.startsWith("SCN") && <FileText className="w-5 h-5 text-blue-600" />}
              </div>
              <div className="flex-1">
                <div className={clsx(
                  "font-medium",
                  selectedScenario.startsWith("FRAUD") && "text-red-900",
                  selectedScenario.startsWith("VAL") && "text-orange-900",
                  selectedScenario.startsWith("SCN") && "text-blue-900"
                )}>
                  {getSelectedScenarioDetails()?.name}
                </div>
                <div className={clsx(
                  "text-sm mt-1",
                  selectedScenario.startsWith("FRAUD") && "text-red-700",
                  selectedScenario.startsWith("VAL") && "text-orange-700",
                  selectedScenario.startsWith("SCN") && "text-blue-700"
                )}>
                  {getSelectedScenarioDetails()?.description}
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {/* Expected Results for Fraud/Validation */}
                  {(selectedScenario.startsWith("FRAUD") || selectedScenario.startsWith("VAL")) && (
                    <>
                      <span className="px-2 py-0.5 text-xs font-medium rounded bg-green-100 text-green-700">
                        Rules: {String((getSelectedScenarioDetails() as unknown as Record<string, unknown>)?.expected_rule_result || "APPROVED")}
                      </span>
                      <span className="px-2 py-0.5 text-xs font-medium rounded bg-red-100 text-red-700">
                        AI: {String((getSelectedScenarioDetails() as unknown as Record<string, unknown>)?.expected_ai_result || "FLAGGED")}
                      </span>
                    </>
                  )}
                  <span className={clsx(
                    "px-2 py-0.5 text-xs font-medium rounded",
                    getSelectedScenarioDetails()?.is_emergency
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-700"
                  )}>
                    {getSelectedScenarioDetails()?.is_emergency ? "Emergency" : "Non-Emergency"}
                  </span>
                  <span className={clsx(
                    "px-2 py-0.5 text-xs font-medium rounded",
                    getSelectedScenarioDetails()?.is_in_network
                      ? "bg-green-100 text-green-700"
                      : "bg-orange-100 text-orange-700"
                  )}>
                    {getSelectedScenarioDetails()?.is_in_network ? "In-Network" : "Out-of-Network"}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className={clsx(
                  "text-2xl font-bold",
                  selectedScenario.startsWith("FRAUD") && "text-red-900",
                  selectedScenario.startsWith("VAL") && "text-orange-900",
                  selectedScenario.startsWith("SCN") && "text-blue-900"
                )}>
                  ${getSelectedScenarioDetails()?.claim_amount?.toLocaleString() || 0}
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            {error}
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Loader2 className="w-12 h-12 mx-auto text-blue-500 animate-spin mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Running Both Pipelines...
          </h3>
          <p className="text-gray-500">
            Processing claim through Code and Agent pipelines simultaneously.
            <br />
            Agent processing may take 30-120 seconds.
          </p>
        </div>
      )}

      {/* Comparison Results */}
      {comparisonResult && !isLoading && (
        <>
          {/* Summary Cards */}
          <div className="grid md:grid-cols-3 gap-4">
            {/* Time Comparison */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Clock className="w-4 h-4" />
                <span className="text-sm font-medium">Processing Time</span>
              </div>
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-xs text-gray-500">Code</div>
                  <div className="text-lg font-bold text-green-600">
                    {formatTime(comparisonResult.code_driven.processing_time_ms)}
                  </div>
                </div>
                <div className="text-gray-400">vs</div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">Agent</div>
                  <div className="text-lg font-bold text-blue-600">
                    {formatTime(comparisonResult.agent_driven.processing_time_ms)}
                  </div>
                </div>
              </div>
              <div className="text-xs text-center mt-2 text-gray-500">
                Agent {comparisonResult.comparison_metrics.time_comparison.agent_slower_by} slower
              </div>
            </div>

            {/* Decision Comparison */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Zap className="w-4 h-4" />
                <span className="text-sm font-medium">Final Decision</span>
              </div>
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-xs text-gray-500">Code</div>
                  <div className="text-sm font-bold text-gray-900">
                    {comparisonResult.code_driven.final_decision}
                  </div>
                </div>
                <div className={clsx(
                  "px-2 py-1 rounded text-xs font-medium",
                  comparisonResult.comparison_metrics.decision_match
                    ? "bg-green-100 text-green-700"
                    : "bg-orange-100 text-orange-700"
                )}>
                  {comparisonResult.comparison_metrics.decision_match ? "Match" : "Different"}
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">Agent</div>
                  <div className="text-sm font-bold text-blue-900">
                    {comparisonResult.agent_driven.final_decision || "N/A"}
                  </div>
                </div>
              </div>
            </div>

            {/* Payout Comparison */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Estimated Payout</span>
              </div>
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-xs text-gray-500">Code</div>
                  <div className="text-lg font-bold text-gray-900">
                    {formatCurrency(comparisonResult.code_driven.estimated_payout)}
                  </div>
                </div>
                <div className="text-gray-400">vs</div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">Agent</div>
                  <div className="text-lg font-bold text-blue-900">
                    {formatCurrency(comparisonResult.agent_driven.estimated_payout)}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Side-by-Side */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Code-Driven Results */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-gray-200 rounded-lg">
                    <Code2 className="w-5 h-5 text-gray-700" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Code-Driven</h3>
                    <p className="text-xs text-gray-500">Traditional rule-based processing</p>
                  </div>
                </div>
              </div>
              <div className="p-4 space-y-4">
                {/* Bronze */}
                <div className="border-l-4 border-orange-400 pl-3">
                  <h4 className="font-medium text-orange-700 text-sm">Bronze Layer</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    <div>Decision: <span className="font-medium">{String(comparisonResult.code_driven.bronze?.decision || '')}</span></div>
                    <div>Quality Score: <span className="font-medium">{formatScore(comparisonResult.code_driven.bronze?.quality_score as number)}</span></div>
                  </div>
                </div>

                {/* Silver */}
                <div className="border-l-4 border-gray-400 pl-3">
                  <h4 className="font-medium text-gray-700 text-sm">Silver Layer</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    <div>Reimbursement: <span className="font-medium">{formatCurrency(comparisonResult.code_driven.silver?.estimated_reimbursement as number)}</span></div>
                    <div>Priority: <span className="font-medium">{String(comparisonResult.code_driven.silver?.processing_priority || '')}</span></div>
                  </div>
                </div>

                {/* Gold */}
                <div className="border-l-4 border-yellow-400 pl-3">
                  <h4 className="font-medium text-yellow-700 text-sm">Gold Layer</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    <div>Risk Level: <span className={clsx(
                      "font-medium",
                      comparisonResult.code_driven.gold?.risk_level === "HIGH" && "text-red-600",
                      comparisonResult.code_driven.gold?.risk_level === "MEDIUM" && "text-yellow-600",
                      comparisonResult.code_driven.gold?.risk_level === "LOW" && "text-green-600"
                    )}>{String(comparisonResult.code_driven.gold?.risk_level || '')}</span></div>
                    <div>Risk Score: <span className="font-medium">{String(comparisonResult.code_driven.gold?.risk_score || '')}</span></div>
                  </div>
                </div>

                {/* No Reasoning for Code */}
                <div className="mt-4 p-3 bg-gray-100 rounded-lg">
                  <p className="text-sm text-gray-500 italic">
                    No reasoning available - code-driven processing uses deterministic rules
                  </p>
                </div>
              </div>
            </div>

            {/* Agent-Driven Results */}
            <div className="bg-white rounded-xl border border-blue-200 overflow-hidden bg-blue-50/30">
              <div className="p-4 border-b border-blue-200 bg-blue-100/50">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-blue-200 rounded-lg">
                    <Bot className="w-5 h-5 text-blue-700" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-blue-900">Agent-Driven</h3>
                    <p className="text-xs text-blue-600">LangGraph AI agents with reasoning</p>
                  </div>
                </div>
              </div>
              <div className="p-4 space-y-4">
                {/* Bronze */}
                <div className="border-l-4 border-orange-400 pl-3">
                  <h4 className="font-medium text-orange-700 text-sm">Bronze Agent</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    <div>Decision: <span className="font-medium">{String(comparisonResult.agent_driven.bronze?.decision || '')}</span></div>
                    <div>Quality Score: <span className="font-medium">{formatScore(comparisonResult.agent_driven.bronze?.quality_score as number)}</span></div>
                  </div>
                </div>

                {/* Silver */}
                <div className="border-l-4 border-gray-400 pl-3">
                  <h4 className="font-medium text-gray-700 text-sm">Silver Agent</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    <div>Reimbursement: <span className="font-medium">{formatCurrency(comparisonResult.agent_driven.silver?.estimated_reimbursement as number)}</span></div>
                    <div>Priority: <span className="font-medium">{String(comparisonResult.agent_driven.silver?.processing_priority || '')}</span></div>
                  </div>
                </div>

                {/* Gold */}
                <div className="border-l-4 border-yellow-400 pl-3">
                  <h4 className="font-medium text-yellow-700 text-sm">Gold Agent</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    <div>Risk Level: <span className={clsx(
                      "font-medium",
                      comparisonResult.agent_driven.gold?.risk_level === "HIGH" && "text-red-600",
                      comparisonResult.agent_driven.gold?.risk_level === "MEDIUM" && "text-yellow-600",
                      comparisonResult.agent_driven.gold?.risk_level === "LOW" && "text-green-600"
                    )}>{String(comparisonResult.agent_driven.gold?.risk_level || '')}</span></div>
                    <div>Confidence: <span className="font-medium">{formatPercentage(comparisonResult.agent_driven.gold?.confidence as number)}</span></div>
                  </div>
                </div>

                {/* Insights */}
                {comparisonResult.agent_driven.insights && comparisonResult.agent_driven.insights.length > 0 && (
                  <div className="mt-4 p-3 bg-blue-100 rounded-lg">
                    <h4 className="text-sm font-medium text-blue-900 mb-2">AI Insights</h4>
                    <ul className="text-sm text-blue-800 space-y-1">
                      {comparisonResult.agent_driven.insights.map((insight, i) => (
                        <li key={i}>• {typeof insight === 'string' ? insight : JSON.stringify(insight)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Advantages */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Code2 className="w-4 h-4" />
                Code Advantages
              </h3>
              <ul className="space-y-2">
                {comparisonResult.comparison_metrics.code_advantages.map((adv, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    {adv}
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
              <h3 className="font-medium text-blue-900 mb-3 flex items-center gap-2">
                <Bot className="w-4 h-4" />
                Agent Advantages
              </h3>
              <ul className="space-y-2">
                {comparisonResult.comparison_metrics.agent_advantages.map((adv, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-blue-800">
                    <CheckCircle className="w-4 h-4 text-blue-500" />
                    {adv}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!comparisonResult && !isLoading && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="flex justify-center gap-4 mb-4">
            <Code2 className="w-12 h-12 text-gray-300" />
            <span className="text-3xl text-gray-300">vs</span>
            <Bot className="w-12 h-12 text-gray-300" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ready to Compare
          </h3>
          <p className="text-gray-500 mb-4">
            Select a scenario and click &quot;Run Comparison&quot; to process the same claim
            through both pipelines and see the results side-by-side.
          </p>
        </div>
      )}
    </div>
  );
}
