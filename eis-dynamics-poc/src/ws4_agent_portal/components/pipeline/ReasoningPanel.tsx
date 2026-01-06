"use client";

import { useEffect, useRef, useState } from "react";
import { clsx } from "clsx";
import {
  Brain,
  Lightbulb,
  Eye,
  Zap,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Loader2,
} from "lucide-react";
import { pipelineApi } from "@/lib/pipeline-api";

export interface ReasoningEntry {
  id: string;
  timestamp: string;
  agentName: string;
  type: "analysis" | "decision" | "observation" | "action" | "alert";
  content: string;
}

interface ReasoningPanelProps {
  entries: ReasoningEntry[];
  isLive?: boolean;
  maxHeight?: string;
  runId?: string;
  runStatus?: string;
}

const typeConfig = {
  analysis: {
    icon: Brain,
    color: "text-purple-500",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    label: "Analysis",
  },
  decision: {
    icon: CheckCircle,
    color: "text-green-500",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
    label: "Decision",
  },
  observation: {
    icon: Eye,
    color: "text-blue-500",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    label: "Observation",
  },
  action: {
    icon: Zap,
    color: "text-orange-500",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    label: "Action",
  },
  alert: {
    icon: AlertTriangle,
    color: "text-red-500",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    label: "Alert",
  },
};

const agentColors: Record<string, string> = {
  router: "bg-blue-500",
  bronze: "bg-orange-500",
  silver: "bg-gray-500",
  gold: "bg-yellow-500",
};

export function ReasoningPanel({
  entries,
  isLive = false,
  maxHeight = "400px",
  runId,
  runStatus,
}: ReasoningPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Reset summary when run changes
  useEffect(() => {
    setSummary(null);
    setSummaryError(null);
  }, [runId]);

  // Auto-trigger summary when pipeline completes
  useEffect(() => {
    if (runId && runStatus === "completed" && !summary && !summaryLoading && !summaryError) {
      // Auto-generate summary when pipeline completes
      generateSummaryInternal();
    }
  }, [runId, runStatus]);

  const generateSummaryInternal = async () => {
    if (!runId) return;
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const result = await pipelineApi.generateRunSummary(runId);
      setSummary(result.summary);
    } catch (err) {
      setSummaryError(err instanceof Error ? err.message : "Failed to generate summary");
    } finally {
      setSummaryLoading(false);
    }
  };

  // Manual trigger (for regenerate button)
  const generateSummary = () => generateSummaryInternal();

  const canGenerateSummary = runId && runStatus === "completed";

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries, autoScroll]);

  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      // If user scrolls up, disable auto-scroll
      setAutoScroll(scrollHeight - scrollTop - clientHeight < 50);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-500" />
          <h3 className="font-semibold text-gray-900">Agent Reasoning</h3>
          {isLive && (
            <span className="flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Live
            </span>
          )}
          <span className="text-sm text-gray-500">({entries.length} entries)</span>
        </div>
        <button className="p-1 hover:bg-gray-200 rounded">
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </button>
      </div>

      {/* AI Summary Section */}
      {isExpanded && canGenerateSummary && (
        <div className="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-purple-500 mt-0.5" />
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-gray-900">AI Summary</h4>
                {!summary && !summaryLoading && (
                  <button
                    onClick={generateSummary}
                    className="flex items-center gap-1 px-3 py-1 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <Sparkles className="w-4 h-4" />
                    Generate Summary
                  </button>
                )}
              </div>
              {summaryLoading && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating AI summary...
                </div>
              )}
              {summaryError && (
                <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                  {summaryError}
                </div>
              )}
              {summary && (
                <div className="text-sm text-gray-700 leading-relaxed bg-white/70 p-3 rounded-lg border border-purple-100">
                  {summary}
                </div>
              )}
              {!summary && !summaryLoading && !summaryError && (
                <p className="text-xs text-gray-500">
                  Click to generate an AI-powered executive summary of this claim processing.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {isExpanded && (
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="overflow-y-auto p-4 space-y-3"
          style={{ maxHeight }}
        >
          {entries.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Brain className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>No reasoning entries yet.</p>
              <p className="text-sm">Run a pipeline to see agent thoughts.</p>
            </div>
          ) : (
            entries.map((entry) => {
              const config = typeConfig[entry.type];
              const Icon = config.icon;

              return (
                <div
                  key={entry.id}
                  className={clsx(
                    "p-3 rounded-lg border",
                    config.bgColor,
                    config.borderColor,
                    "animate-fade-in"
                  )}
                >
                  <div className="flex items-start gap-3">
                    <Icon className={clsx("w-5 h-5 mt-0.5", config.color)} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={clsx(
                            "px-2 py-0.5 text-xs font-medium text-white rounded",
                            agentColors[entry.agentName] || "bg-gray-500"
                          )}
                        >
                          {entry.agentName}
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </span>
                        <span
                          className={clsx(
                            "text-xs font-medium",
                            config.color
                          )}
                        >
                          {config.label}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {entry.content}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Auto-scroll indicator */}
      {isExpanded && entries.length > 0 && !autoScroll && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
          <button
            onClick={() => {
              setAutoScroll(true);
              if (scrollRef.current) {
                scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
              }
            }}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Scroll to latest
          </button>
        </div>
      )}
    </div>
  );
}
