"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { clsx } from "clsx";
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Router,
  Database,
  Sparkles,
  Trophy,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
} from "lucide-react";

import { pipelineApi, PipelineRun } from "@/lib/pipeline-api";

interface AgentOutput {
  status: string;
  processing_time_ms: number;
  output: Record<string, unknown>;
  error?: string;
}

export default function PipelineRunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.id as string;

  const [run, setRun] = useState<PipelineRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["router", "bronze", "silver", "gold"])
  );
  const [copiedField, setCopiedField] = useState<string | null>(null);

  useEffect(() => {
    loadRun();
    // Poll for updates if running
    const interval = setInterval(() => {
      if (run?.status === "running") {
        loadRun();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [runId, run?.status]);

  const loadRun = async () => {
    try {
      const data = await pipelineApi.getPipelineRun(runId);
      setRun(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run");
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "running":
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      completed: "bg-green-100 text-green-700",
      running: "bg-blue-100 text-blue-700",
      failed: "bg-red-100 text-red-700",
      pending: "bg-gray-100 text-gray-700",
    };
    return (
      <span
        className={clsx(
          "px-3 py-1 rounded-full text-sm font-medium",
          styles[status as keyof typeof styles] || styles.pending
        )}
      >
        {status}
      </span>
    );
  };

  const agentConfigs = [
    {
      key: "router",
      name: "Router Agent",
      icon: Router,
      color: "blue",
      state: run?.router_state,
    },
    {
      key: "bronze",
      name: "Bronze Agent",
      icon: Database,
      color: "orange",
      state: run?.bronze_state,
    },
    {
      key: "silver",
      name: "Silver Agent",
      icon: Sparkles,
      color: "gray",
      state: run?.silver_state,
    },
    {
      key: "gold",
      name: "Gold Agent",
      icon: Trophy,
      color: "yellow",
      state: run?.gold_state,
    },
  ];

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-red-400 mb-4" />
          <h2 className="text-lg font-medium text-red-700 mb-2">
            Failed to Load Run
          </h2>
          <p className="text-red-600 mb-4">{error || "Run not found"}</p>
          <button
            onClick={() => router.push("/pipeline")}
            className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
          >
            Back to Pipeline
          </button>
        </div>
      </div>
    );
  }

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
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">Pipeline Run Detail</h1>
          <div className="flex items-center gap-2 mt-1">
            <code className="text-sm text-gray-500">{run.run_id}</code>
            <button
              onClick={() => copyToClipboard(run.run_id, "runId")}
              className="p-1 hover:bg-gray-100 rounded"
            >
              {copiedField === "runId" ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-gray-400" />
              )}
            </button>
          </div>
        </div>
        {getStatusBadge(run.status)}
      </div>

      {/* Summary Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Run Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Claim ID</p>
            <p className="font-medium text-gray-900">{run.claim_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Complexity</p>
            <span
              className={clsx(
                "inline-block px-2 py-0.5 rounded text-sm font-medium",
                run.complexity === "simple" && "bg-green-100 text-green-700",
                run.complexity === "medium" && "bg-yellow-100 text-yellow-700",
                run.complexity === "complex" && "bg-red-100 text-red-700"
              )}
            >
              {run.complexity}
            </span>
          </div>
          <div>
            <p className="text-sm text-gray-500">Current Stage</p>
            <p className="font-medium text-gray-900 capitalize">
              {run.current_stage}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Time</p>
            <p className="font-medium text-gray-900">
              {run.total_processing_time_ms > 0
                ? `${(run.total_processing_time_ms / 1000).toFixed(1)}s`
                : "-"}
            </p>
          </div>
        </div>
      </div>

      {/* Agent Outputs */}
      <div className="space-y-4">
        <h2 className="font-semibold text-gray-900">Agent Outputs</h2>
        {agentConfigs.map((agent) => {
          const isExpanded = expandedSections.has(agent.key);
          const Icon = agent.icon;
          const state = agent.state as AgentOutput | null;
          const colorMap = {
            blue: {
              bg: "bg-blue-50",
              border: "border-blue-200",
              text: "text-blue-700",
              iconBg: "bg-blue-100",
            },
            orange: {
              bg: "bg-orange-50",
              border: "border-orange-200",
              text: "text-orange-700",
              iconBg: "bg-orange-100",
            },
            gray: {
              bg: "bg-gray-50",
              border: "border-gray-200",
              text: "text-gray-700",
              iconBg: "bg-gray-100",
            },
            yellow: {
              bg: "bg-yellow-50",
              border: "border-yellow-200",
              text: "text-yellow-700",
              iconBg: "bg-yellow-100",
            },
          };
          const colors = colorMap[agent.color as keyof typeof colorMap];

          return (
            <div
              key={agent.key}
              className={clsx(
                "rounded-xl border-2 overflow-hidden",
                colors.bg,
                colors.border
              )}
            >
              <button
                onClick={() => toggleSection(agent.key)}
                className="w-full px-4 py-3 flex items-center gap-3 hover:bg-white/50 transition-colors"
              >
                <div className={clsx("p-2 rounded-lg", colors.iconBg)}>
                  <Icon className={clsx("w-5 h-5", colors.text)} />
                </div>
                <span className={clsx("font-medium", colors.text)}>
                  {agent.name}
                </span>
                <div className="flex-1" />
                {state && (
                  <>
                    {getStatusIcon(state.status)}
                    {state.processing_time_ms > 0 && (
                      <span className="text-sm text-gray-500">
                        {(state.processing_time_ms / 1000).toFixed(1)}s
                      </span>
                    )}
                  </>
                )}
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </button>
              {isExpanded && state && (
                <div className="px-4 pb-4 bg-white/50">
                  {state.error ? (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                      {state.error}
                    </div>
                  ) : state.output ? (
                    <pre className="p-3 bg-gray-900 text-gray-100 rounded-lg text-sm overflow-auto max-h-[400px]">
                      {JSON.stringify(state.output, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-sm text-gray-500 italic">
                      No output yet
                    </p>
                  )}
                </div>
              )}
              {isExpanded && !state && (
                <div className="px-4 pb-4 bg-white/50">
                  <p className="text-sm text-gray-500 italic">
                    Agent not started
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Raw Data */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Raw Pipeline Data</h2>
        <pre className="p-4 bg-gray-900 text-gray-100 rounded-lg text-sm overflow-auto max-h-[400px]">
          {JSON.stringify(run, null, 2)}
        </pre>
      </div>
    </div>
  );
}
