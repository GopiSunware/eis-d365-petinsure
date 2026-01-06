"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, FileText, Search, Calculator, RefreshCw, Check, AlertCircle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { clsx } from "clsx";

const linkActions = [
  {
    name: "New Claim",
    description: "Submit a new FNOL",
    href: "/claims/new",
    icon: Plus,
    color: "bg-primary-50 text-primary-600",
  },
  {
    name: "Get Quote",
    description: "Calculate premium",
    href: "/quotes/new",
    icon: Calculator,
    color: "bg-success-50 text-success-600",
  },
  {
    name: "Find Policy",
    description: "Search policies",
    href: "/policies",
    icon: Search,
    color: "bg-warning-50 text-warning-600",
  },
];

export function QuickActions() {
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<"idle" | "success" | "error">("idle");
  const queryClient = useQueryClient();

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus("idle");

    try {
      // Sync all entity types
      await Promise.all([
        api.triggerSync("policies"),
        api.triggerSync("claims"),
        api.triggerSync("customers"),
      ]);

      // Invalidate all queries to refetch fresh data
      await queryClient.invalidateQueries();

      setSyncStatus("success");
      setTimeout(() => setSyncStatus("idle"), 3000);
    } catch (error) {
      console.error("Sync failed:", error);
      setSyncStatus("error");
      setTimeout(() => setSyncStatus("idle"), 3000);
    } finally {
      setSyncing(false);
    }
  };

  const getSyncIcon = () => {
    if (syncStatus === "success") return Check;
    if (syncStatus === "error") return AlertCircle;
    return RefreshCw;
  };

  const getSyncColor = () => {
    if (syncStatus === "success") return "bg-success-50 text-success-600";
    if (syncStatus === "error") return "bg-danger-50 text-danger-600";
    return "bg-gray-100 text-gray-600";
  };

  const SyncIcon = getSyncIcon();

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
      <div className="space-y-3">
        {linkActions.map((action) => (
          <Link
            key={action.name}
            href={action.href}
            className="flex items-center p-3 rounded-lg border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 transition-all group"
          >
            <div
              className={`h-10 w-10 rounded-lg flex items-center justify-center ${action.color}`}
            >
              <action.icon className="h-5 w-5" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 group-hover:text-primary-600">
                {action.name}
              </p>
              <p className="text-xs text-gray-500">{action.description}</p>
            </div>
          </Link>
        ))}

        {/* Sync Data Button */}
        <button
          onClick={handleSync}
          disabled={syncing}
          className={clsx(
            "w-full flex items-center p-3 rounded-lg border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 transition-all group text-left",
            syncing && "opacity-70 cursor-wait"
          )}
        >
          <div
            className={`h-10 w-10 rounded-lg flex items-center justify-center ${getSyncColor()}`}
          >
            <SyncIcon className={clsx("h-5 w-5", syncing && "animate-spin")} />
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900 group-hover:text-primary-600">
              {syncing ? "Syncing..." : syncStatus === "success" ? "Synced!" : syncStatus === "error" ? "Sync Failed" : "Sync Data"}
            </p>
            <p className="text-xs text-gray-500">
              {syncing ? "Refreshing from EIS..." : "Refresh from EIS"}
            </p>
          </div>
        </button>
      </div>
    </div>
  );
}
