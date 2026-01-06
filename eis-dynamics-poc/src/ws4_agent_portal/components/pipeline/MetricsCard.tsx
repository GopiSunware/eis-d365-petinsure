"use client";

import { clsx } from "clsx";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  Activity,
  Zap,
  Target,
} from "lucide-react";

export interface MetricData {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: "clock" | "check" | "error" | "activity" | "zap" | "target";
  color?: "blue" | "green" | "red" | "yellow" | "gray";
}

interface MetricsCardProps {
  title: string;
  metrics: MetricData[];
  className?: string;
}

const iconMap = {
  clock: Clock,
  check: CheckCircle,
  error: XCircle,
  activity: Activity,
  zap: Zap,
  target: Target,
};

const colorMap = {
  blue: {
    bg: "bg-blue-50",
    text: "text-blue-700",
    iconBg: "bg-blue-100",
  },
  green: {
    bg: "bg-green-50",
    text: "text-green-700",
    iconBg: "bg-green-100",
  },
  red: {
    bg: "bg-red-50",
    text: "text-red-700",
    iconBg: "bg-red-100",
  },
  yellow: {
    bg: "bg-yellow-50",
    text: "text-yellow-700",
    iconBg: "bg-yellow-100",
  },
  gray: {
    bg: "bg-gray-50",
    text: "text-gray-700",
    iconBg: "bg-gray-100",
  },
};

export function MetricsCard({ title, metrics, className }: MetricsCardProps) {
  return (
    <div
      className={clsx(
        "bg-white rounded-xl border border-gray-200 p-6",
        className
      )}
    >
      <h3 className="font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, index) => {
          const Icon = metric.icon ? iconMap[metric.icon] : Activity;
          const colors = colorMap[metric.color || "gray"];

          return (
            <div
              key={index}
              className={clsx("p-4 rounded-xl", colors.bg)}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={clsx("p-1.5 rounded-lg", colors.iconBg)}>
                  <Icon className={clsx("w-4 h-4", colors.text)} />
                </div>
                <span className="text-sm text-gray-600">{metric.label}</span>
              </div>
              <div className="flex items-end gap-2">
                <span className={clsx("text-2xl font-bold", colors.text)}>
                  {metric.value}
                </span>
                {metric.change !== undefined && (
                  <div
                    className={clsx(
                      "flex items-center gap-0.5 text-sm",
                      metric.change >= 0 ? "text-green-600" : "text-red-600"
                    )}
                  >
                    {metric.change >= 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    <span>
                      {metric.change > 0 ? "+" : ""}
                      {metric.change}%
                    </span>
                  </div>
                )}
              </div>
              {metric.changeLabel && (
                <p className="text-xs text-gray-500 mt-1">{metric.changeLabel}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface PipelineMetrics {
  total_runs: number;
  active_runs: number;
  completed_runs: number;
  failed_runs: number;
  average_processing_time_ms: number;
}

interface PipelineMetricsDisplayProps {
  metrics?: PipelineMetrics | null;
  loading?: boolean;
}

export function PipelineMetricsDisplay({
  metrics,
  loading,
}: PipelineMetricsDisplayProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-5 w-32 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-100 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  const metricsData: MetricData[] = [
    {
      label: "Total Runs",
      value: metrics.total_runs,
      icon: "activity",
      color: "blue",
    },
    {
      label: "Completed",
      value: metrics.completed_runs,
      icon: "check",
      color: "green",
    },
    {
      label: "Failed",
      value: metrics.failed_runs,
      icon: "error",
      color: "red",
    },
    {
      label: "Avg Time",
      value:
        metrics.average_processing_time_ms > 0
          ? `${(metrics.average_processing_time_ms / 1000).toFixed(1)}s`
          : "-",
      icon: "clock",
      color: "yellow",
    },
  ];

  return <MetricsCard title="Pipeline Metrics" metrics={metricsData} />;
}
