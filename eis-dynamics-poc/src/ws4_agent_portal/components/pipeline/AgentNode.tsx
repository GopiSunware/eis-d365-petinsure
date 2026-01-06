"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { clsx } from "clsx";
import {
  Router,
  Database,
  Sparkles,
  Trophy,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";

export type AgentStatus = "pending" | "running" | "completed" | "failed";

export interface AgentNodeData {
  label: string;
  agentType: "router" | "bronze" | "silver" | "gold";
  status: AgentStatus;
  processingTime?: number;
  decision?: string;
  confidence?: number;
  qualityScore?: number;
  riskLevel?: string;
  complexity?: string;
  [key: string]: unknown;
}

interface AgentNodeProps {
  data: AgentNodeData;
  selected?: boolean;
}

const agentConfig = {
  router: {
    icon: Router,
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    activeColor: "bg-blue-500",
    textColor: "text-blue-700",
    ringColor: "ring-blue-400",
  },
  bronze: {
    icon: Database,
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    activeColor: "bg-orange-500",
    textColor: "text-orange-700",
    ringColor: "ring-orange-400",
  },
  silver: {
    icon: Sparkles,
    bgColor: "bg-gray-50",
    borderColor: "border-gray-300",
    activeColor: "bg-gray-500",
    textColor: "text-gray-700",
    ringColor: "ring-gray-400",
  },
  gold: {
    icon: Trophy,
    bgColor: "bg-yellow-50",
    borderColor: "border-yellow-300",
    activeColor: "bg-yellow-500",
    textColor: "text-yellow-700",
    ringColor: "ring-yellow-400",
  },
};

const statusConfig = {
  pending: {
    icon: Clock,
    color: "text-gray-400",
    label: "Pending",
    animate: false,
  },
  running: {
    icon: Loader2,
    color: "text-blue-500",
    label: "Running",
    animate: true,
  },
  completed: {
    icon: CheckCircle2,
    color: "text-green-500",
    label: "Completed",
    animate: false,
  },
  failed: {
    icon: XCircle,
    color: "text-red-500",
    label: "Failed",
    animate: false,
  },
};

function AgentNodeComponent({ data, selected }: AgentNodeProps) {
  const config = agentConfig[data.agentType];
  const statusInfo = statusConfig[data.status];
  const Icon = config.icon;
  const StatusIcon = statusInfo.icon;

  return (
    <div
      className={clsx(
        "relative px-4 py-3 rounded-xl border-2 shadow-lg min-w-[180px] transition-all duration-300",
        config.bgColor,
        config.borderColor,
        selected && `ring-2 ${config.ringColor}`,
        data.status === "running" && "animate-pulse"
      )}
    >
      {/* Input Handle */}
      {data.agentType !== "router" && (
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 !bg-gray-400 border-2 border-white"
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <div
          className={clsx(
            "p-2 rounded-lg",
            data.status === "running" ? config.activeColor : "bg-white"
          )}
        >
          <Icon
            className={clsx(
              "w-5 h-5",
              data.status === "running" ? "text-white" : config.textColor
            )}
          />
        </div>
        <div>
          <h3 className={clsx("font-semibold text-sm", config.textColor)}>
            {data.label}
          </h3>
          <div className="flex items-center gap-1">
            <StatusIcon
              className={clsx(
                "w-3 h-3",
                statusInfo.color,
                statusInfo.animate && "animate-spin"
              )}
            />
            <span className="text-xs text-gray-500">{statusInfo.label}</span>
          </div>
        </div>
      </div>

      {/* Content based on agent type */}
      <div className="space-y-1 text-xs">
        {data.agentType === "router" && data.complexity && (
          <div className="flex justify-between">
            <span className="text-gray-500">Complexity:</span>
            <span
              className={clsx(
                "font-medium px-2 py-0.5 rounded",
                data.complexity === "simple" && "bg-green-100 text-green-700",
                data.complexity === "medium" && "bg-yellow-100 text-yellow-700",
                data.complexity === "complex" && "bg-red-100 text-red-700"
              )}
            >
              {data.complexity}
            </span>
          </div>
        )}

        {data.agentType === "bronze" && data.decision && (
          <>
            <div className="flex justify-between">
              <span className="text-gray-500">Decision:</span>
              <span
                className={clsx(
                  "font-medium px-2 py-0.5 rounded",
                  data.decision === "accept" && "bg-green-100 text-green-700",
                  data.decision === "quarantine" && "bg-yellow-100 text-yellow-700",
                  data.decision === "reject" && "bg-red-100 text-red-700"
                )}
              >
                {data.decision}
              </span>
            </div>
            {data.qualityScore !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Quality:</span>
                <span className="font-medium">{(data.qualityScore * 100).toFixed(0)}%</span>
              </div>
            )}
          </>
        )}

        {data.agentType === "silver" && data.status === "completed" && (
          <div className="flex justify-between">
            <span className="text-gray-500">Enriched:</span>
            <span className="font-medium text-green-600">Yes</span>
          </div>
        )}

        {data.agentType === "gold" && (
          <>
            {data.decision && (
              <div className="flex justify-between">
                <span className="text-gray-500">Decision:</span>
                <span
                  className={clsx(
                    "font-medium px-2 py-0.5 rounded text-[10px]",
                    data.decision === "auto_approve" && "bg-green-100 text-green-700",
                    data.decision === "standard_review" && "bg-blue-100 text-blue-700",
                    data.decision === "manual_review" && "bg-yellow-100 text-yellow-700",
                    data.decision === "investigation" && "bg-red-100 text-red-700"
                  )}
                >
                  {data.decision.replace("_", " ")}
                </span>
              </div>
            )}
            {data.riskLevel && (
              <div className="flex justify-between">
                <span className="text-gray-500">Risk:</span>
                <span
                  className={clsx(
                    "font-medium",
                    data.riskLevel === "low" && "text-green-600",
                    data.riskLevel === "medium" && "text-yellow-600",
                    data.riskLevel === "high" && "text-orange-600",
                    data.riskLevel === "critical" && "text-red-600"
                  )}
                >
                  {data.riskLevel}
                </span>
              </div>
            )}
          </>
        )}

        {data.processingTime !== undefined && data.status === "completed" && (
          <div className="flex justify-between text-gray-400 pt-1 border-t border-gray-200">
            <span>Time:</span>
            <span>{(data.processingTime / 1000).toFixed(1)}s</span>
          </div>
        )}
      </div>

      {/* Output Handle */}
      {data.agentType !== "gold" && (
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 !bg-gray-400 border-2 border-white"
        />
      )}
    </div>
  );
}

export const AgentNode = memo(AgentNodeComponent);
