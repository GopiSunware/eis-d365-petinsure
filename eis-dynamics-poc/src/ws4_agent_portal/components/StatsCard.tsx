import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { clsx } from "clsx";

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  trend?: string;
  trendUp?: boolean;
  color?: "primary" | "success" | "warning" | "danger";
}

export function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  trendUp,
  color = "primary",
}: StatsCardProps) {
  const colorClasses = {
    primary: "bg-primary-50 text-primary-600",
    success: "bg-success-50 text-success-600",
    warning: "bg-warning-50 text-warning-600",
    danger: "bg-danger-50 text-danger-600",
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div
          className={clsx(
            "h-12 w-12 rounded-lg flex items-center justify-center",
            colorClasses[color]
          )}
        >
          <Icon className="h-6 w-6" />
        </div>
        {trend && (
          <div
            className={clsx(
              "flex items-center text-sm font-medium",
              trendUp ? "text-success-600" : "text-danger-600"
            )}
          >
            {trendUp ? (
              <TrendingUp className="h-4 w-4 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 mr-1" />
            )}
            {trend}
          </div>
        )}
      </div>
      <div className="mt-4">
        <h3 className="text-3xl font-bold text-gray-900">{value}</h3>
        <p className="text-sm text-gray-500 mt-1">{title}</p>
      </div>
    </div>
  );
}
