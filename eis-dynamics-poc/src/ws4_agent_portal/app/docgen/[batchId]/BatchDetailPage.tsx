"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { clsx } from "clsx";
import {
  ArrowLeft,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  AlertTriangle,
  AlertCircle,
  Info,
  Download,
  RefreshCw,
  Eye,
  ChevronDown,
  ChevronUp,
  DollarSign,
  Shield,
  File,
} from "lucide-react";

import {
  docgenApi,
  ProcessedBatch,
  ProcessingStatus,
  ExportFormat,
  formatFileSize,
} from "@/lib/docgen-api";

export default function BatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const batchId = params.batchId as string;

  const [batch, setBatch] = useState<ProcessedBatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    documents: true,
    claim: true,
    billing: true,
    validation: true,
    fraud: true,  // Open by default to show AI analysis
  });
  const [exporting, setExporting] = useState(false);
  const [selectedFormats, setSelectedFormats] = useState<ExportFormat[]>(["pdf"]);
  const [exportUrls, setExportUrls] = useState<Record<string, string>>({});

  // Load batch
  const loadBatch = useCallback(async () => {
    try {
      const data = await docgenApi.getBatch(batchId);
      setBatch(data);

      // Start polling if processing
      if (
        data.status !== "completed" &&
        data.status !== "failed" &&
        data.status !== "pending"
      ) {
        setPolling(true);
      } else {
        setPolling(false);
      }

      setError(null);
    } catch (err) {
      setError("Failed to load batch");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  useEffect(() => {
    loadBatch();
  }, [loadBatch]);

  // Polling for status updates
  useEffect(() => {
    if (!polling) return;

    const interval = setInterval(loadBatch, 2000);
    return () => clearInterval(interval);
  }, [polling, loadBatch]);

  // Toggle section
  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Toggle export format
  const toggleFormat = (format: ExportFormat) => {
    setSelectedFormats((prev) =>
      prev.includes(format)
        ? prev.filter((f) => f !== format)
        : [...prev, format]
    );
  };

  // Generate exports
  const handleExport = async () => {
    if (selectedFormats.length === 0) return;

    setExporting(true);
    try {
      const response = await docgenApi.generateExports(batchId, selectedFormats);
      setExportUrls(response.download_urls);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setExporting(false);
    }
  };

  // Start processing
  const handleStartProcessing = async () => {
    try {
      await docgenApi.startProcessing(batchId);
      setPolling(true);
      loadBatch();
    } catch (err) {
      console.error("Failed to start processing:", err);
    }
  };

  // Reprocess
  const handleReprocess = async () => {
    try {
      await docgenApi.reprocessBatch(batchId);
      setPolling(true);
      loadBatch();
    } catch (err) {
      console.error("Failed to reprocess:", err);
    }
  };

  // Get status badge
  const getStatusBadge = (status: ProcessingStatus) => {
    switch (status) {
      case "completed":
        return (
          <span className="flex items-center gap-2 px-3 py-1.5 bg-green-100 text-green-700 text-sm font-medium rounded-full">
            <CheckCircle className="w-4 h-4" />
            Completed
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-2 px-3 py-1.5 bg-red-100 text-red-700 text-sm font-medium rounded-full">
            <XCircle className="w-4 h-4" />
            Failed
          </span>
        );
      case "pending":
        return (
          <span className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm font-medium rounded-full">
            <Clock className="w-4 h-4" />
            Pending
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
            <Loader2 className="w-4 h-4 animate-spin" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        );
    }
  };

  // Get risk badge
  const getRiskBadge = (riskLevel: string) => {
    const colors = {
      low: "bg-green-100 text-green-700",
      medium: "bg-yellow-100 text-yellow-700",
      high: "bg-orange-100 text-orange-700",
      critical: "bg-red-100 text-red-700",
    };
    return (
      <span
        className={clsx(
          "px-2 py-1 text-xs font-medium rounded-full",
          colors[riskLevel as keyof typeof colors] || "bg-gray-100 text-gray-700"
        )}
      >
        {riskLevel.toUpperCase()} RISK
      </span>
    );
  };

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-orange-500" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !batch) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-400 mb-4" />
        <p className="text-gray-600">{error || "Batch not found"}</p>
        <Link
          href="/docgen"
          className="text-blue-600 hover:text-blue-700 mt-4 inline-block"
        >
          ← Back to Doc Processing
        </Link>
      </div>
    );
  }

  const claim = batch.mapped_claim || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/docgen"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">
                {batch.claim_number || `Batch ${batchId.slice(0, 8)}`}
              </h1>
              {getStatusBadge(batch.status)}
            </div>
            <p className="text-gray-500 mt-1">
              {batch.documents.length} document
              {batch.documents.length !== 1 ? "s" : ""} •{" "}
              Created {new Date(batch.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {batch.status === "pending" && (
            <button
              onClick={handleStartProcessing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
            >
              <Loader2 className="w-4 h-4" />
              Start Processing
            </button>
          )}
          {(batch.status === "completed" || batch.status === "failed") && (
            <button
              onClick={handleReprocess}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
              Reprocess
            </button>
          )}
        </div>
      </div>

      {/* Agent Steps (while processing or completed/failed) */}
      {(polling || batch.agent_steps?.length > 0) && (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              {polling && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
              <span className="text-sm font-semibold text-gray-700">
                Agent Processing Steps
              </span>
            </div>
            <span className="text-sm text-gray-500">{batch.progress.toFixed(0)}% complete</span>
          </div>

          {/* Agent Steps List */}
          <div className="space-y-2">
            {(batch.agent_steps || []).map((step, idx) => (
              <div
                key={step.step_id || idx}
                className={clsx(
                  "flex items-center gap-3 p-3 rounded-lg transition-all",
                  step.status === "running" && "bg-blue-50 border border-blue-200",
                  step.status === "completed" && step.result === "pass" && "bg-green-50",
                  step.status === "completed" && step.result === "fail" && "bg-red-50",
                  step.status === "completed" && step.result === "warning" && "bg-yellow-50",
                  step.status === "completed" && step.result === "skip" && "bg-gray-50",
                  step.status === "pending" && "bg-gray-50 opacity-50"
                )}
              >
                {/* Status Icon */}
                <div className="flex-shrink-0">
                  {step.status === "running" && (
                    <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                  )}
                  {step.status === "completed" && step.result === "pass" && (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                  {step.status === "completed" && step.result === "fail" && (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  {step.status === "completed" && step.result === "warning" && (
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                  )}
                  {step.status === "completed" && step.result === "skip" && (
                    <div className="w-5 h-5 rounded-full border-2 border-gray-300 flex items-center justify-center">
                      <span className="text-xs text-gray-400">—</span>
                    </div>
                  )}
                  {step.status === "pending" && (
                    <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                  )}
                </div>

                {/* Step Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      "text-sm font-medium",
                      step.status === "running" && "text-blue-700",
                      step.status === "completed" && step.result === "pass" && "text-green-700",
                      step.status === "completed" && step.result === "fail" && "text-red-700",
                      step.status === "completed" && step.result === "warning" && "text-yellow-700",
                      step.status === "completed" && step.result === "skip" && "text-gray-500",
                      step.status === "pending" && "text-gray-400"
                    )}>
                      {step.message}
                    </span>
                    {step.status === "running" && (
                      <span className="text-xs text-blue-500 animate-pulse">Processing...</span>
                    )}
                  </div>
                  {step.details && (
                    <p className={clsx(
                      "text-xs mt-0.5 truncate",
                      step.result === "pass" && "text-green-600",
                      step.result === "fail" && "text-red-600",
                      step.result === "warning" && "text-yellow-600",
                      step.result === "skip" && "text-gray-400"
                    )}>
                      {step.details}
                    </p>
                  )}
                </div>

                {/* Step Type Badge */}
                <span className="flex-shrink-0 text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600">
                  {step.step_type.replace(/_/g, " ")}
                </span>
              </div>
            ))}
          </div>

          {polling && (
            <p className="text-xs text-gray-400 mt-3">
              The AI agent is processing your document. This typically takes 30-60 seconds.
            </p>
          )}
        </div>
      )}

      {/* Error Display */}
      {batch.error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center gap-2 text-red-700">
            <XCircle className="w-5 h-5" />
            <span className="font-medium">
              {batch.error.includes("DUPLICATE") ? "Duplicate Document Detected" : "Processing Error"}
            </span>
          </div>
          <div className="text-red-600 text-sm mt-2 space-y-1">
            {batch.error.split(/\\n|\n/).map((line, idx) => (
              <p key={idx} className={line.trim().startsWith('•') ? 'pl-2' : ''}>
                {line.trim() || '\u00A0'}
              </p>
            ))}
          </div>
          {batch.error_stage && (
            <p className="text-red-500 text-xs mt-2">Stage: {batch.error_stage}</p>
          )}
        </div>
      )}

      {/* Documents Section */}
      <div className="bg-white rounded-xl border border-gray-200">
        <button
          onClick={() => toggleSection("documents")}
          className="w-full flex items-center justify-between p-4 text-left"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-gray-500" />
            <span className="font-semibold text-gray-900">
              Documents ({batch.documents.length})
            </span>
          </div>
          {expandedSections.documents ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>
        {expandedSections.documents && (
          <div className="border-t border-gray-200 p-4">
            <div className="space-y-2">
              {batch.documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <File className="w-5 h-5 text-gray-400" />
                    <div>
                      <div className="font-medium text-gray-900">
                        {doc.original_filename}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatFileSize(doc.file_size)} •{" "}
                        {doc.document_type || "Unknown type"}
                        {doc.from_zip && ` • From ZIP: ${doc.zip_source}`}
                      </div>
                    </div>
                  </div>
                  {batch.extractions[doc.id] && (
                    <span className="text-xs text-green-600">
                      Extracted ({(batch.extractions[doc.id].confidence_score * 100).toFixed(0)}% confidence)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Claim Data Section (only if completed) */}
      {batch.status === "completed" && batch.mapped_claim && (
        <div className="bg-white rounded-xl border border-gray-200">
          <button
            onClick={() => toggleSection("claim")}
            className="w-full flex items-center justify-between p-4 text-left"
          >
            <div className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-gray-500" />
              <span className="font-semibold text-gray-900">Claim Data</span>
            </div>
            {expandedSections.claim ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.claim && (
            <div className="border-t border-gray-200 p-4">
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">
                    Claim Type
                  </label>
                  <div className="text-gray-900">{claim.claim_type || "N/A"}</div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">
                    Category
                  </label>
                  <div className="text-gray-900">{claim.claim_category || "N/A"}</div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">
                    Severity
                  </label>
                  <div className="text-gray-900">{claim.severity || "N/A"}</div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">
                    Pet Name
                  </label>
                  <div className="text-gray-900">{claim.pet_name || "N/A"}</div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">
                    Provider
                  </label>
                  <div className="text-gray-900">{claim.provider_name || "N/A"}</div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">
                    Service Date
                  </label>
                  <div className="text-gray-900">{claim.service_date || "N/A"}</div>
                </div>
                <div className="md:col-span-2 lg:col-span-3">
                  <label className="text-xs font-medium text-gray-500 uppercase">
                    Diagnosis
                  </label>
                  <div className="text-gray-900">
                    {claim.diagnosis_description || "N/A"}
                    {claim.diagnosis_code && (
                      <span className="ml-2 text-gray-500">({claim.diagnosis_code})</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Line Items */}
              {Array.isArray(claim.line_items) && claim.line_items.length > 0 && (
                <div className="mt-4">
                  <label className="text-xs font-medium text-gray-500 uppercase mb-2 block">
                    Line Items
                  </label>
                  <div className="bg-gray-50 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-100">
                          <th className="text-left p-2 font-medium text-gray-700">Description</th>
                          <th className="text-right p-2 font-medium text-gray-700">Qty</th>
                          <th className="text-right p-2 font-medium text-gray-700">Unit Price</th>
                          <th className="text-right p-2 font-medium text-gray-700">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {claim.line_items.map((item: Record<string, unknown>, idx: number) => (
                          <tr key={idx} className="border-t border-gray-200">
                            <td className="p-2 text-gray-900">{item.description as string}</td>
                            <td className="p-2 text-right text-gray-700">{item.quantity as number}</td>
                            <td className="p-2 text-right text-gray-700">
                              ${(item.unit_price as number).toFixed(2)}
                            </td>
                            <td className="p-2 text-right text-gray-900 font-medium">
                              ${(item.total_amount as number).toFixed(2)}
                            </td>
                          </tr>
                        ))}
                        <tr className="border-t-2 border-gray-300 bg-gray-100">
                          <td colSpan={3} className="p-2 text-right font-semibold text-gray-900">
                            Total
                          </td>
                          <td className="p-2 text-right font-bold text-gray-900">
                            ${(claim.claim_amount as number)?.toFixed(2) || "0.00"}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Billing Section */}
      {batch.status === "completed" && batch.billing && (
        <div className="bg-white rounded-xl border border-gray-200">
          <button
            onClick={() => toggleSection("billing")}
            className="w-full flex items-center justify-between p-4 text-left"
          >
            <div className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-gray-500" />
              <span className="font-semibold text-gray-900">Billing Summary</span>
            </div>
            {expandedSections.billing ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.billing && (
            <div className="border-t border-gray-200 p-4">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Claim Amount</span>
                    <span className="font-medium">${batch.billing.claim_amount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Deductible Applied</span>
                    <span className="text-red-600">-${batch.billing.deductible_applied.toFixed(2)}</span>
                  </div>
                  {batch.billing.out_of_network_reduction > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Out-of-Network Reduction</span>
                      <span className="text-red-600">
                        -${batch.billing.out_of_network_reduction.toFixed(2)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">
                      Covered Amount ({batch.billing.reimbursement_percentage}%)
                    </span>
                    <span className="font-medium">${batch.billing.covered_amount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between pt-3 border-t border-gray-200">
                    <span className="font-semibold text-gray-900">Estimated Payout</span>
                    <span className="font-bold text-green-600 text-lg">
                      ${batch.billing.final_payout.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Customer Responsibility</h4>
                  <div className="text-2xl font-bold text-gray-900">
                    ${batch.billing.customer_responsibility.toFixed(2)}
                  </div>
                  <p className="text-sm text-gray-500 mt-2">{batch.billing.explanation}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Validation Issues */}
      {batch.status === "completed" && batch.validation_issues.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200">
          <button
            onClick={() => toggleSection("validation")}
            className="w-full flex items-center justify-between p-4 text-left"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <span className="font-semibold text-gray-900">
                Validation Issues ({batch.validation_issues.length})
              </span>
            </div>
            {expandedSections.validation ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.validation && (
            <div className="border-t border-gray-200 p-4 space-y-2">
              {batch.validation_issues.map((issue) => (
                <div
                  key={issue.issue_id}
                  className={clsx(
                    "flex items-start gap-3 p-3 rounded-lg",
                    issue.severity === "critical" && "bg-red-50",
                    issue.severity === "error" && "bg-orange-50",
                    issue.severity === "warning" && "bg-yellow-50",
                    issue.severity === "info" && "bg-blue-50"
                  )}
                >
                  {getSeverityIcon(issue.severity)}
                  <div>
                    <div className="font-medium text-gray-900">{issue.message}</div>
                    {issue.suggestion && (
                      <div className="text-sm text-gray-600 mt-1">{issue.suggestion}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Fraud Analysis */}
      {batch.status === "completed" && (
        <div className="bg-white rounded-xl border border-gray-200">
          <button
            onClick={() => toggleSection("fraud")}
            className="w-full flex items-center justify-between p-4 text-left"
          >
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-gray-500" />
              <span className="font-semibold text-gray-900">Fraud Analysis</span>
              {getRiskBadge(batch.risk_level)}
              <span className="text-sm text-gray-500">
                Score: {batch.fraud_score.toFixed(1)}/100
              </span>
            </div>
            {expandedSections.fraud ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.fraud && (
            <div className="border-t border-gray-200 p-4">
              {batch.fraud_indicators.length > 0 ? (
                <div className="space-y-2">
                  {batch.fraud_indicators.map((indicator) => (
                    <div
                      key={indicator.indicator_id}
                      className="flex items-start gap-3 p-3 bg-red-50 rounded-lg"
                    >
                      <AlertCircle className="w-4 h-4 text-red-500 mt-0.5" />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {indicator.indicator}
                          </span>
                          <span className="text-xs text-red-600">
                            +{indicator.score_impact} pts
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">{indicator.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <CheckCircle className="w-8 h-8 mx-auto text-green-400 mb-2" />
                  No fraud indicators detected
                </div>
              )}

              {/* AI Decision */}
              {batch.ai_decision && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">AI Recommendation</h4>
                  <div className="flex items-center gap-2">
                    <span
                      className={clsx(
                        "px-3 py-1 text-sm font-medium rounded-full",
                        batch.ai_decision === "auto_approve" && "bg-green-100 text-green-700",
                        batch.ai_decision === "standard_review" && "bg-blue-100 text-blue-700",
                        batch.ai_decision === "manual_review" && "bg-yellow-100 text-yellow-700",
                        batch.ai_decision === "investigation" && "bg-red-100 text-red-700",
                        batch.ai_decision === "deny" && "bg-red-100 text-red-700"
                      )}
                    >
                      {batch.ai_decision.replace("_", " ").toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-500">
                      ({(batch.ai_confidence * 100).toFixed(0)}% confidence)
                    </span>
                  </div>
                  {batch.ai_reasoning && (
                    <div className="text-sm text-gray-600 mt-2 space-y-1">
                      {batch.ai_reasoning.split(/\\n|\n/).map((line, idx) => (
                        <p key={idx} className={line.trim().startsWith('•') ? 'pl-2' : ''}>
                          {line.trim() || '\u00A0'}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Export Section */}
      {batch.status === "completed" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Export</h2>
          <div className="flex flex-wrap gap-3 mb-4">
            {(["pdf", "docx", "csv"] as ExportFormat[]).map((format) => (
              <button
                key={format}
                onClick={() => toggleFormat(format)}
                className={clsx(
                  "px-4 py-2 rounded-lg border-2 font-medium transition-colors",
                  selectedFormats.includes(format)
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-200 text-gray-600 hover:border-gray-300"
                )}
              >
                {format.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleExport}
              disabled={exporting || selectedFormats.length === 0}
              className={clsx(
                "flex items-center gap-2 px-6 py-2 rounded-lg font-medium text-white",
                exporting || selectedFormats.length === 0
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-green-600 hover:bg-green-700"
              )}
            >
              {exporting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Generate Export
                </>
              )}
            </button>

            {/* Download Links */}
            {Object.keys(exportUrls).length > 0 && (
              <div className="flex items-center gap-2">
                {Object.entries(exportUrls).map(([format, url]) => {
                  // Extract export_id from URL like "/api/v1/docgen/export/{export_id}/download"
                  const urlParts = url.split("/");
                  const downloadIdx = urlParts.indexOf("download");
                  const exportId = downloadIdx > 0 ? urlParts[downloadIdx - 1] : urlParts[urlParts.length - 2];
                  return (
                    <a
                      key={format}
                      href={docgenApi.getDownloadUrl(exportId)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700"
                    >
                      <Download className="w-4 h-4" />
                      {format.toUpperCase()}
                    </a>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
