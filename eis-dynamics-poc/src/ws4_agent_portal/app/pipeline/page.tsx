"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { clsx } from "clsx";
import {
  Play,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Activity,
  GitCompare,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Edit3,
  Sparkles,
} from "lucide-react";

import { PipelineCanvas } from "@/components/pipeline/PipelineCanvas";
import { ReasoningPanel, ReasoningEntry } from "@/components/pipeline/ReasoningPanel";
import { PipelineMetricsDisplay } from "@/components/pipeline/MetricsCard";
import { pipelineApi, PipelineRun, PipelineMetrics, Scenario } from "@/lib/pipeline-api";
import { pipelineWs, PipelineEvent } from "@/lib/pipeline-websocket";

type ComplexityLevel = "simple" | "medium" | "complex";
type RunMode = "demo" | "scenario";

export default function PipelinePage() {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentRun, setCurrentRun] = useState<PipelineRun | null>(null);
  const [recentRuns, setRecentRuns] = useState<PipelineRun[]>([]);
  const [reasoningEntries, setReasoningEntries] = useState<ReasoningEntry[]>([]);
  const [selectedComplexity, setSelectedComplexity] = useState<ComplexityLevel>("simple");
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [runMode, setRunMode] = useState<RunMode>("scenario");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [scenarioExpanded, setScenarioExpanded] = useState(false);
  const [editedTreatmentNotes, setEditedTreatmentNotes] = useState<string>("");
  const [isEditingNotes, setIsEditingNotes] = useState(false);

  // Load metrics
  const loadMetrics = async () => {
    try {
      setMetricsLoading(true);
      const data = await pipelineApi.getMetrics();
      setMetrics(data);
    } catch (err) {
      console.error("Failed to load metrics:", err);
    } finally {
      setMetricsLoading(false);
    }
  };

  // Load scenarios
  const loadScenarios = async () => {
    try {
      const data = await pipelineApi.getScenarios();
      setScenarios(data.scenarios);
      if (data.scenarios.length > 0) {
        setSelectedScenario(data.scenarios[0].id);
        setEditedTreatmentNotes(data.scenarios[0].treatment_notes || "");
      }
    } catch (err) {
      console.error("Failed to load scenarios:", err);
    }
  };

  // Handle scenario selection
  const handleScenarioChange = (scenarioId: string) => {
    setSelectedScenario(scenarioId);
    const scenario = scenarios.find(s => s.id === scenarioId);
    if (scenario) {
      setEditedTreatmentNotes(scenario.treatment_notes || "");
      setIsEditingNotes(false);
    }
  };

  // Connect to WebSocket on mount
  useEffect(() => {
    pipelineWs.connect();

    const unsubConnect = pipelineWs.onConnect(() => setIsConnected(true));
    const unsubDisconnect = pipelineWs.onDisconnect(() => setIsConnected(false));

    // Listen to all events
    const unsubEvents = pipelineWs.on("*", handlePipelineEvent);

    // Load recent runs, metrics, and scenarios
    loadRecentRuns();
    loadMetrics();
    loadScenarios();

    return () => {
      unsubConnect();
      unsubDisconnect();
      unsubEvents();
      pipelineWs.disconnect();
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, []);

  // Handle pipeline events - only process events for current run
  const handlePipelineEvent = useCallback((event: PipelineEvent) => {
    // Only process events for the current run to prevent canvas switching
    if (!currentRun || event.run_id !== currentRun.run_id) {
      return;
    }

    // Add reasoning entry
    if (event.event_type === "reasoning" || event.event_type === "decision") {
      const entry: ReasoningEntry = {
        id: `${event.run_id}-${Date.now()}`,
        timestamp: event.timestamp,
        agentName: (event.data as Record<string, unknown>).agent_name as string,
        type: event.event_type === "decision" ? "decision" :
              ((event.data as Record<string, unknown>).reasoning_type as ReasoningEntry["type"]) || "analysis",
        content: (event.data as Record<string, unknown>).content as string ||
                 (event.data as Record<string, unknown>).reasoning as string || "",
      };
      setReasoningEntries((prev) => [...prev, entry]);
    }

    // Update current run on agent events
    if (
      event.event_type === "agent.started" ||
      event.event_type === "agent.completed" ||
      event.event_type === "pipeline.completed"
    ) {
      refreshCurrentRun(event.run_id);
    }
  }, [currentRun]);

  const loadRecentRuns = async () => {
    try {
      // Fetch all available runs (up to 50), sorted desc by started_at from backend
      const runs = await pipelineApi.getRecentRuns(50);
      setRecentRuns(runs);
    } catch (err) {
      console.error("Failed to load recent runs:", err);
    }
  };

  const refreshCurrentRun = async (runId: string) => {
    try {
      const run = await pipelineApi.getPipelineRun(runId);
      setCurrentRun(run);

      if (run.status === "completed" || run.status === "failed") {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        // Small delay to ensure backend has stored the run
        setTimeout(() => {
          loadRecentRuns();
          loadMetrics();
        }, 500);
      }
    } catch (err) {
      console.error("Failed to refresh run:", err);
    }
  };

  const triggerPipeline = async () => {
    setIsLoading(true);
    setError(null);
    setReasoningEntries([]);

    try {
      let response;
      let scenarioName = "";

      if (runMode === "scenario" && selectedScenario) {
        // Trigger using selected scenario with optional edited treatment notes
        const scenario = scenarios.find(s => s.id === selectedScenario);
        const hasEditedNotes = editedTreatmentNotes !== scenario?.treatment_notes;
        response = await pipelineApi.triggerScenario(
          selectedScenario,
          hasEditedNotes ? editedTreatmentNotes : undefined
        );
        scenarioName = scenario?.name || selectedScenario;
      } else {
        // Trigger using demo complexity
        response = await pipelineApi.triggerDemoClaim(selectedComplexity);
        scenarioName = `${selectedComplexity} demo claim`;
      }

      // Add initial reasoning entry
      setReasoningEntries([
        {
          id: `${response.run_id}-start`,
          timestamp: new Date().toISOString(),
          agentName: "system",
          type: "action",
          content: `Pipeline started: ${scenarioName} (${response.claim_id})`,
        },
      ]);

      // Get initial state
      const run = await pipelineApi.getPipelineRun(response.run_id);
      setCurrentRun(run);

      // Start polling for updates (fallback for WebSocket)
      const interval = setInterval(() => refreshCurrentRun(response.run_id), 2000);
      setPollingInterval(interval);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger pipeline");
    } finally {
      setIsLoading(false);
    }
  };

  // Get selected scenario details
  const getSelectedScenarioDetails = () => {
    if (!selectedScenario) return null;
    return scenarios.find(s => s.id === selectedScenario);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
            <CheckCircle className="w-3 h-3" />
            Completed
          </span>
        );
      case "running":
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
            <Loader2 className="w-3 h-3 animate-spin" />
            Running
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
            <XCircle className="w-3 h-3" />
            Failed
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        );
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Pipeline</h1>
          <p className="text-gray-500 mt-1">
            Visualize agent-driven medallion architecture processing
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* AI Demo Link */}
          <Link
            href="/pipeline/demo"
            className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg text-sm font-medium text-white hover:from-purple-600 hover:to-blue-600 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            AI Demo
          </Link>
          {/* Compare Link */}
          <Link
            href="/pipeline/compare"
            className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <GitCompare className="w-4 h-4" />
            Code vs Agent
          </Link>
          {/* Connection Status */}
          <div
            className={clsx(
              "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm",
              isConnected ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
            )}
          >
            <span
              className={clsx(
                "w-2 h-2 rounded-full",
                isConnected ? "bg-green-500 animate-pulse" : "bg-gray-400"
              )}
            />
            {isConnected ? "Connected" : "Disconnected"}
          </div>
        </div>
      </div>

      {/* Metrics */}
      <PipelineMetricsDisplay metrics={metrics} loading={metricsLoading} />

      {/* Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-wrap items-end gap-4">
          {/* Mode Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mode
            </label>
            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
              <button
                onClick={() => setRunMode("scenario")}
                className={clsx(
                  "px-3 py-2 text-sm font-medium transition-colors",
                  runMode === "scenario"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-50"
                )}
              >
                Scenario
              </button>
              <button
                onClick={() => setRunMode("demo")}
                className={clsx(
                  "px-3 py-2 text-sm font-medium transition-colors border-l border-gray-300",
                  runMode === "demo"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-50"
                )}
              >
                Demo
              </button>
            </div>
          </div>

          {/* Scenario Dropdown */}
          {runMode === "scenario" && (
            <div className="flex-1 min-w-[300px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Claim Scenario
              </label>
              <select
                value={selectedScenario}
                onChange={(e) => handleScenarioChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
              >
                {scenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name} - ${scenario.claim_amount.toLocaleString()} ({scenario.claim_type})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Demo Complexity Dropdown */}
          {runMode === "demo" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Claim Complexity
              </label>
              <select
                value={selectedComplexity}
                onChange={(e) => setSelectedComplexity(e.target.value as ComplexityLevel)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
              >
                <option value="simple">Simple (Wellness - $150)</option>
                <option value="medium">Medium (Accident - $4,500)</option>
                <option value="complex">Complex (Emergency - $12,500)</option>
              </select>
            </div>
          )}

          <div className="flex-1" />

          <button
            onClick={triggerPipeline}
            disabled={isLoading}
            className={clsx(
              "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
              isLoading
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700"
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            {isLoading ? "Running..." : "Run Pipeline"}
          </button>
          <button
            onClick={loadRecentRuns}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
            Refresh
          </button>
        </div>

        {/* Scenario Details - Expandable */}
        {runMode === "scenario" && getSelectedScenarioDetails() && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
            {/* Header - Always visible, clickable to expand */}
            <button
              onClick={() => setScenarioExpanded(!scenarioExpanded)}
              className="w-full p-3 flex items-start gap-3 hover:bg-blue-100/50 transition-colors text-left"
            >
              <div className="flex-1">
                <div className="font-medium text-blue-900">
                  {getSelectedScenarioDetails()?.name}
                </div>
                <div className="text-sm text-blue-700 mt-1">
                  {getSelectedScenarioDetails()?.description}
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
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
                  <span className="px-2 py-0.5 text-xs font-medium rounded bg-purple-100 text-purple-700">
                    {getSelectedScenarioDetails()?.claim_category}
                  </span>
                </div>
              </div>
              <div className="text-right flex flex-col items-end gap-2">
                <div className="text-2xl font-bold text-blue-900">
                  ${getSelectedScenarioDetails()?.claim_amount.toLocaleString()}
                </div>
                <div className="text-xs text-blue-600">
                  {getSelectedScenarioDetails()?.line_items?.length || 0} line items
                </div>
                <div className="flex items-center gap-1 text-xs text-blue-600">
                  {scenarioExpanded ? (
                    <>
                      <ChevronUp className="w-4 h-4" />
                      <span>Collapse</span>
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-4 h-4" />
                      <span>Expand Details</span>
                    </>
                  )}
                </div>
              </div>
            </button>

            {/* Expanded Content */}
            {scenarioExpanded && (
              <div className="border-t border-blue-200 p-4 space-y-4 bg-white/50">
                {/* Diagnosis & Provider Info */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Diagnosis
                    </h4>
                    <div className="text-sm">
                      <span className="font-medium text-gray-900">
                        {getSelectedScenarioDetails()?.diagnosis_code}
                      </span>
                      <span className="text-gray-600 ml-2">
                        {getSelectedScenarioDetails()?.diagnosis}
                      </span>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Provider
                    </h4>
                    <div className="text-sm text-gray-900">
                      {getSelectedScenarioDetails()?.provider_name}
                    </div>
                  </div>
                </div>

                {/* Treatment Notes - Editable */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Treatment Notes
                    </h4>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsEditingNotes(!isEditingNotes);
                      }}
                      className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
                    >
                      <Edit3 className="w-3 h-3" />
                      {isEditingNotes ? "Done" : "Edit"}
                    </button>
                  </div>
                  {isEditingNotes ? (
                    <textarea
                      value={editedTreatmentNotes}
                      onChange={(e) => setEditedTreatmentNotes(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[80px]"
                      placeholder="Enter treatment notes..."
                    />
                  ) : (
                    <div className="text-sm text-gray-700 bg-white/70 p-2 rounded border border-gray-200">
                      {editedTreatmentNotes || getSelectedScenarioDetails()?.treatment_notes || "No treatment notes"}
                    </div>
                  )}
                </div>

                {/* Line Items */}
                {getSelectedScenarioDetails()?.line_items && getSelectedScenarioDetails()!.line_items.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Line Items
                    </h4>
                    <div className="bg-white/70 rounded border border-gray-200 divide-y divide-gray-100">
                      {getSelectedScenarioDetails()?.line_items.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center px-3 py-2 text-sm">
                          <span className="text-gray-700">{item.description}</span>
                          <span className="font-medium text-gray-900">
                            ${item.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                      ))}
                      <div className="flex justify-between items-center px-3 py-2 text-sm font-semibold bg-gray-50">
                        <span className="text-gray-700">Total</span>
                        <span className="text-blue-900">
                          ${getSelectedScenarioDetails()?.claim_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Pet & Service Info */}
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Pet:</span>
                    <span className="ml-2 text-gray-900">{getSelectedScenarioDetails()?.pet_name || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Service Date:</span>
                    <span className="ml-2 text-gray-900">{getSelectedScenarioDetails()?.service_date || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Claim Type:</span>
                    <span className="ml-2 text-gray-900">{getSelectedScenarioDetails()?.claim_type}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}
      </div>

      {/* Current Run Info */}
      {currentRun && (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Activity className="w-5 h-5 text-blue-500" />
              <span className="font-medium text-gray-900">Current Run</span>
              <code className="px-2 py-1 bg-gray-100 rounded text-sm text-gray-600">
                {currentRun.run_id}
              </code>
              {getStatusBadge(currentRun.status)}
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-500">
                Claim: <code className="text-gray-700">{currentRun.claim_id}</code>
                {currentRun.total_processing_time_ms > 0 && (
                  <span className="ml-3">
                    Time: {(currentRun.total_processing_time_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
              <Link
                href={`/pipeline/${currentRun.run_id}`}
                target="_blank"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                View Details
                <ExternalLink className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Pipeline Canvas */}
          <PipelineCanvas
            pipelineRun={currentRun}
            onNodeClick={(agentType) => console.log("Clicked:", agentType)}
          />
        </div>
      )}

      {/* Empty State */}
      {!currentRun && (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <Activity className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Pipeline</h3>
          <p className="text-gray-500 mb-4">
            Click &quot;Run Pipeline&quot; to start processing a demo claim
          </p>
        </div>
      )}

      {/* Reasoning Panel */}
      <ReasoningPanel
        entries={reasoningEntries}
        isLive={currentRun?.status === "running"}
        maxHeight="300px"
        runId={currentRun?.run_id}
        runStatus={currentRun?.status}
      />

      {/* Recent Runs */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-gray-900">Recent Runs</h3>
          <button
            onClick={loadRecentRuns}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Refresh
          </button>
        </div>
        {recentRuns.length > 0 ? (
          <div className="space-y-2">
            {recentRuns.map((run) => (
              <div
                key={run.run_id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors group"
                onClick={() => setCurrentRun(run)}
              >
                <div className="flex items-center gap-3">
                  <code className="text-sm text-gray-600">{run.run_id}</code>
                  {getStatusBadge(run.status)}
                  <span
                    className={clsx(
                      "px-2 py-0.5 text-xs font-medium rounded",
                      run.complexity === "simple" && "bg-green-100 text-green-700",
                      run.complexity === "medium" && "bg-yellow-100 text-yellow-700",
                      run.complexity === "complex" && "bg-red-100 text-red-700"
                    )}
                  >
                    {run.complexity}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-sm text-gray-500">
                    {run.total_processing_time_ms > 0 && (
                      <span>{(run.total_processing_time_ms / 1000).toFixed(1)}s</span>
                    )}
                  </div>
                  <Link
                    href={`/pipeline/${run.run_id}`}
                    target="_blank"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                  >
                    Details
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <p className="text-sm">No recent runs yet.</p>
            <p className="text-xs mt-1">Run a pipeline to see it here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
