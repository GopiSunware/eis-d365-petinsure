"use client";

import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  Users,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Clock,
} from "lucide-react";
import { StatsCard } from "@/components/StatsCard";
import { RecentClaimsList } from "@/components/RecentClaimsList";
import { QuickActions } from "@/components/QuickActions";
import { api } from "@/lib/api";

export default function Dashboard() {
  const { data: claims } = useQuery({
    queryKey: ["claims"],
    queryFn: () => api.getClaims(),
  });

  const { data: policies } = useQuery({
    queryKey: ["policies"],
    queryFn: () => api.getPolicies(),
  });

  const stats = {
    totalPolicies: policies?.length || 0,
    activeClaims: claims?.filter((c: any) => c.status !== "closed_paid").length || 0,
    pendingReview: claims?.filter((c: any) => c.status === "fnol_received").length || 0,
    highFraudRisk: claims?.filter((c: any) => c.fraud_score > 0.5).length || 0,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Welcome to the EIS-D365 Agent Portal
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Active Policies"
          value={stats.totalPolicies}
          icon={FileText}
          trend="+12%"
          trendUp={true}
        />
        <StatsCard
          title="Open Claims"
          value={stats.activeClaims}
          icon={Users}
          trend="-5%"
          trendUp={false}
        />
        <StatsCard
          title="Pending Review"
          value={stats.pendingReview}
          icon={Clock}
          color="warning"
        />
        <StatsCard
          title="High Fraud Risk"
          value={stats.highFraudRisk}
          icon={AlertTriangle}
          color="danger"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentClaimsList claims={claims || []} />
        </div>
        <div>
          <QuickActions />
        </div>
      </div>
    </div>
  );
}
