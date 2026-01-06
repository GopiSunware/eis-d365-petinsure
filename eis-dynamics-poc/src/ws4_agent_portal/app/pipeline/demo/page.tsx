"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { clsx } from "clsx";
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Loader2,
  ArrowLeft,
  Brain,
  FileWarning,
  Stethoscope,
  Building2,
  Pill,
  FileCheck,
  Eye,
  RefreshCw,
} from "lucide-react";
import {
  pipelineApi,
  ValidationScenario,
  ValidationResult,
  FraudPattern,
  FraudCheckResult,
} from "@/lib/pipeline-api";

type TabType = "fraud" | "validation";

const validationTypeIcons: Record<string, typeof Brain> = {
  diagnosis_treatment_mismatch: Stethoscope,
  document_consistency: FileCheck,
  completeness_sequence: FileWarning,
  license_verification: Building2,
  controlled_substance: Pill,
  comprehensive: Brain,
};

const resultColors: Record<string, { bg: string; text: string; border: string }> = {
  FAIL: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
  WARNING: { bg: "bg-yellow-50", text: "text-yellow-700", border: "border-yellow-200" },
  CRITICAL: { bg: "bg-red-100", text: "text-red-800", border: "border-red-300" },
  MANUAL_REVIEW: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
  PASS: { bg: "bg-green-50", text: "text-green-700", border: "border-green-200" },
};

export default function AIDemoPage() {
  const [activeTab, setActiveTab] = useState<TabType>("fraud");
  const [fraudPatterns, setFraudPatterns] = useState<FraudPattern[]>([]);
  const [validationScenarios, setValidationScenarios] = useState<ValidationScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Running validation state
  const [runningScenario, setRunningScenario] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<Record<string, ValidationResult>>({});

  // Running fraud check state
  const [runningFraud, setRunningFraud] = useState<string | null>(null);
  const [fraudResults, setFraudResults] = useState<Record<string, FraudCheckResult>>({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [fraudData, validationData] = await Promise.all([
        pipelineApi.getFraudPatterns(),
        pipelineApi.getValidationScenarios(),
      ]);
      setFraudPatterns(fraudData.patterns || []);
      setValidationScenarios(validationData.validation_scenarios || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo data");
    } finally {
      setLoading(false);
    }
  };

  const runValidationScenario = async (scenarioId: string) => {
    setRunningScenario(scenarioId);
    try {
      const result = await pipelineApi.runValidationScenario(scenarioId);
      setValidationResults((prev) => ({ ...prev, [scenarioId]: result }));
    } catch (err) {
      console.error("Failed to run validation:", err);
    } finally {
      setRunningScenario(null);
    }
  };

  const runFraudCheck = async (pattern: FraudPattern) => {
    setRunningFraud(pattern.pattern_id);
    try {
      // Use sample data based on pattern
      const sampleData = getFraudSampleData(pattern.pattern_id);
      const result = await pipelineApi.checkFraudIndicators(sampleData);
      setFraudResults((prev) => ({ ...prev, [pattern.pattern_id]: result }));
    } catch (err) {
      console.error("Failed to run fraud check:", err);
    } finally {
      setRunningFraud(null);
    }
  };

  const getFraudSampleData = (patternId: string) => {
    const samples: Record<string, {
      customer_id: string;
      pet_id: string;
      provider_id: string;
      claim_amount: number;
      diagnosis_code: string;
      service_date: string;
    }> = {
      chronic_condition_gaming: {
        customer_id: "CUST-023",
        pet_id: "PET-034",
        provider_id: "PROV-011",
        claim_amount: 1600,
        diagnosis_code: "S83.5",
        service_date: "2024-12-15",
      },
      provider_collusion: {
        customer_id: "CUST-067",
        pet_id: "PET-100",
        provider_id: "PROV-045",
        claim_amount: 4800,
        diagnosis_code: "K59.9",
        service_date: "2024-12-10",
      },
      staged_timing: {
        customer_id: "CUST-089",
        pet_id: "PET-133",
        provider_id: "PROV-025",
        claim_amount: 3200,
        diagnosis_code: "G95.89",
        service_date: "2024-12-17",
      },
    };
    return samples[patternId] || samples.chronic_condition_gaming;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/pipeline"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Capabilities Demo</h1>
            <p className="text-gray-500 mt-1">
              See what AI catches that rule-based systems cannot
            </p>
          </div>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab("fraud")}
          className={clsx(
            "px-4 py-3 font-medium text-sm border-b-2 transition-colors",
            activeTab === "fraud"
              ? "border-red-500 text-red-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          )}
        >
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Fraud Detection (3 Patterns)
          </div>
        </button>
        <button
          onClick={() => setActiveTab("validation")}
          className={clsx(
            "px-4 py-3 font-medium text-sm border-b-2 transition-colors",
            activeTab === "validation"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          )}
        >
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Data Validation (10 Scenarios)
          </div>
        </button>
      </div>

      {/* Fraud Patterns Tab */}
      {activeTab === "fraud" && (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-4">
            <h3 className="font-semibold text-red-900 mb-2">What AI Catches That Rules Miss</h3>
            <p className="text-sm text-red-700">
              Rule-based systems approve each claim individually. AI detects patterns across
              multiple claims, customer history, and provider relationships.
            </p>
          </div>

          <div className="grid gap-4">
            {fraudPatterns.map((pattern) => (
              <div
                key={pattern.pattern_id}
                className="bg-white rounded-xl border border-gray-200 overflow-hidden"
              >
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-red-100 rounded-lg">
                        <AlertTriangle className="w-5 h-5 text-red-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{pattern.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{pattern.description}</p>
                      </div>
                    </div>
                    <span
                      className={clsx(
                        "px-2 py-1 text-xs font-medium rounded",
                        pattern.risk_level === "HIGH"
                          ? "bg-red-100 text-red-700"
                          : pattern.risk_level === "MEDIUM"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-green-100 text-green-700"
                      )}
                    >
                      {pattern.risk_level} RISK
                    </span>
                  </div>

                  {/* Indicators */}
                  <div className="mt-4">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                      Detection Indicators
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {pattern.indicators?.map((indicator, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                        >
                          {indicator}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Comparison */}
                  <div className="mt-4 grid md:grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <XCircle className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-600">Rule-Based Result</span>
                      </div>
                      <p className="text-sm text-gray-900">
                        <span className="text-green-600 font-medium">APPROVED</span> - Each claim
                        passes individual threshold checks
                      </p>
                    </div>
                    <div className="p-3 bg-red-50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Brain className="w-4 h-4 text-red-500" />
                        <span className="text-sm font-medium text-red-700">AI Result</span>
                      </div>
                      <p className="text-sm text-red-900">
                        <span className="text-red-600 font-medium">FLAGGED</span> - Pattern detected
                        across {pattern.affected_claims || 3}+ claims
                      </p>
                    </div>
                  </div>

                  {/* Run Button & Result */}
                  <div className="mt-4 flex items-center justify-between">
                    <button
                      onClick={() => runFraudCheck(pattern)}
                      disabled={runningFraud === pattern.pattern_id}
                      className={clsx(
                        "flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors",
                        runningFraud === pattern.pattern_id
                          ? "bg-gray-100 text-gray-400"
                          : "bg-red-600 text-white hover:bg-red-700"
                      )}
                    >
                      {runningFraud === pattern.pattern_id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                      Test Detection
                    </button>

                    {fraudResults[pattern.pattern_id] && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">Fraud Score:</span>
                        <span
                          className={clsx(
                            "px-2 py-1 text-sm font-bold rounded",
                            fraudResults[pattern.pattern_id].fraud_score >= 50
                              ? "bg-red-100 text-red-700"
                              : fraudResults[pattern.pattern_id].fraud_score >= 30
                              ? "bg-yellow-100 text-yellow-700"
                              : "bg-green-100 text-green-700"
                          )}
                        >
                          {fraudResults[pattern.pattern_id].fraud_score}
                        </span>
                        <span className={clsx(
                          "px-2 py-0.5 text-xs font-medium rounded uppercase",
                          fraudResults[pattern.pattern_id].risk_level === "critical" && "bg-red-100 text-red-700",
                          fraudResults[pattern.pattern_id].risk_level === "high" && "bg-orange-100 text-orange-700",
                          fraudResults[pattern.pattern_id].risk_level === "medium" && "bg-yellow-100 text-yellow-700",
                          fraudResults[pattern.pattern_id].risk_level === "low" && "bg-green-100 text-green-700"
                        )}>
                          {fraudResults[pattern.pattern_id].risk_level}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Fraud Detection Results */}
                  {fraudResults[pattern.pattern_id] && fraudResults[pattern.pattern_id].indicators && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-gray-500 uppercase">
                          AI Detected Indicators
                        </span>
                        <span className={clsx(
                          "px-2 py-0.5 text-xs font-medium rounded",
                          fraudResults[pattern.pattern_id].requires_manual_review
                            ? "bg-red-100 text-red-700"
                            : "bg-green-100 text-green-700"
                        )}>
                          {fraudResults[pattern.pattern_id].recommendation}
                        </span>
                      </div>
                      {fraudResults[pattern.pattern_id].indicators.length > 0 ? (
                        <ul className="space-y-2">
                          {fraudResults[pattern.pattern_id].indicators.map((ind, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm">
                              <span className={clsx(
                                "px-1.5 py-0.5 text-xs font-medium rounded shrink-0 mt-0.5",
                                ind.severity === "critical" && "bg-red-100 text-red-700",
                                ind.severity === "high" && "bg-orange-100 text-orange-700",
                                ind.severity === "medium" && "bg-yellow-100 text-yellow-700",
                                ind.severity === "low" && "bg-gray-100 text-gray-600"
                              )}>
                                +{ind.score_impact}
                              </span>
                              <span className="text-gray-700">{ind.description}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-gray-500">No fraud indicators detected</p>
                      )}
                      <p className="mt-3 text-sm text-gray-600 italic">
                        {fraudResults[pattern.pattern_id].reasoning}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Scenarios Tab */}
      {activeTab === "validation" && (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">AI-Powered Data Quality Validation</h3>
            <p className="text-sm text-blue-700">
              Detect issues rules cannot catch: diagnosis-treatment mismatches, document
              inconsistencies, missing prerequisites, license verification, and controlled
              substance compliance.
            </p>
          </div>

          {/* Validation Type Legend */}
          <div className="flex flex-wrap gap-3">
            {Object.entries(validationTypeIcons).map(([type, Icon]) => (
              <div key={type} className="flex items-center gap-1.5 text-xs text-gray-600">
                <Icon className="w-3.5 h-3.5" />
                <span className="capitalize">{type.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>

          {/* Scenarios Grid */}
          <div className="grid md:grid-cols-2 gap-4">
            {validationScenarios.map((scenario) => {
              const Icon = validationTypeIcons[scenario.validation_type] || Brain;
              const result = validationResults[scenario.scenario_id];
              const colors = resultColors[scenario.expected_result] || resultColors.WARNING;

              return (
                <div
                  key={scenario.scenario_id}
                  className={clsx(
                    "bg-white rounded-xl border overflow-hidden",
                    result?.passed === false ? "border-red-300" : "border-gray-200"
                  )}
                >
                  <div className="p-4">
                    <div className="flex items-start gap-3">
                      <div className={clsx("p-2 rounded-lg", colors.bg)}>
                        <Icon className={clsx("w-5 h-5", colors.text)} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-gray-400">
                            {scenario.scenario_id}
                          </span>
                          <span
                            className={clsx(
                              "px-1.5 py-0.5 text-xs font-medium rounded",
                              colors.bg,
                              colors.text
                            )}
                          >
                            {scenario.expected_result}
                          </span>
                        </div>
                        <h3 className="font-medium text-gray-900 mt-1">{scenario.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{scenario.description}</p>
                      </div>
                    </div>

                    {/* Claim Data Preview */}
                    <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                      <span className="font-medium">Diagnosis:</span>{" "}
                      {(scenario.claim_data as Record<string, unknown>).diagnosis_code} |{" "}
                      <span className="font-medium">Procedures:</span>{" "}
                      {((scenario.claim_data as Record<string, unknown>).procedure_codes as string[])?.join(", ") || "N/A"}
                    </div>

                    {/* Run Button & Result */}
                    <div className="mt-3 flex items-center justify-between">
                      <button
                        onClick={() => runValidationScenario(scenario.scenario_id)}
                        disabled={runningScenario === scenario.scenario_id}
                        className={clsx(
                          "flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium text-sm transition-colors",
                          runningScenario === scenario.scenario_id
                            ? "bg-gray-100 text-gray-400"
                            : "bg-blue-600 text-white hover:bg-blue-700"
                        )}
                      >
                        {runningScenario === scenario.scenario_id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                        Run Test
                      </button>

                      {result && (
                        <div className="flex items-center gap-2">
                          {result.match ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-500" />
                          )}
                          <span
                            className={clsx(
                              "text-sm font-medium",
                              result.match ? "text-green-600" : "text-red-600"
                            )}
                          >
                            {result.match ? "Test Passed" : "Test Failed"}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Validation Result Details */}
                    {result && result.actual_result && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-700">Expected:</span>
                          <span
                            className={clsx(
                              "px-2 py-0.5 text-xs font-medium rounded",
                              resultColors[result.expected_result]?.bg || "bg-gray-100",
                              resultColors[result.expected_result]?.text || "text-gray-700"
                            )}
                          >
                            {result.expected_result}
                          </span>
                        </div>
                        {result.actual_result.issues && result.actual_result.issues.length > 0 && (
                          <div className="mt-2">
                            <span className="text-xs text-gray-500">Issues Detected:</span>
                            <ul className="mt-1 space-y-1">
                              {result.actual_result.issues.map((issue, idx) => (
                                <li key={idx} className="text-xs text-red-600">
                                  [{issue.severity}] {issue.message}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {result.actual_result.recommendations && result.actual_result.recommendations.length > 0 && (
                          <div className="mt-2">
                            <span className="text-xs text-gray-500">Recommendations:</span>
                            <ul className="mt-1 space-y-1">
                              {result.actual_result.recommendations.map((rec, idx) => (
                                <li key={idx} className="text-xs text-blue-600">
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
