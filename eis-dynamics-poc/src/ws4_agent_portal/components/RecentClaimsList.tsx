"use client";

import Link from "next/link";
import { AlertTriangle, ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import { formatDate, safeNumber } from "@/lib/utils";

interface Claim {
  claim_number: string;
  policy_id: string;
  date_of_loss: string;
  status: string;
  severity?: string;
  fraud_score: number;
  loss_description: string;
}

interface RecentClaimsListProps {
  claims: Claim[];
}

const statusColors: Record<string, string> = {
  fnol_received: "badge-primary",
  under_investigation: "badge-warning",
  pending_info: "badge-warning",
  approved: "badge-success",
  denied: "badge-danger",
  closed_paid: "badge-success",
};

const statusLabels: Record<string, string> = {
  fnol_received: "FNOL Received",
  under_investigation: "Under Investigation",
  pending_info: "Pending Info",
  approved: "Approved",
  denied: "Denied",
  closed_paid: "Closed - Paid",
};

export function RecentClaimsList({ claims }: RecentClaimsListProps) {
  const recentClaims = claims.slice(0, 5);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Recent Claims</h2>
        <Link
          href="/claims"
          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          View all
        </Link>
      </div>

      {recentClaims.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No claims found</p>
      ) : (
        <div className="space-y-3">
          {recentClaims.map((claim) => (
            <Link
              key={claim.claim_number}
              href={`/claims/${claim.claim_number}`}
              className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 transition-all group"
            >
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <span className="font-medium text-gray-900">
                    {claim.claim_number}
                  </span>
                  <span
                    className={clsx("badge", statusColors[claim.status] || "badge-primary")}
                  >
                    {statusLabels[claim.status] || claim.status}
                  </span>
                  {safeNumber(claim.fraud_score) > 0.5 && (
                    <span className="badge badge-danger flex items-center">
                      <AlertTriangle className="h-3 w-3 mr-1" />
                      High Risk
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-1 truncate max-w-md">
                  {claim.loss_description}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Loss Date: {formatDate(claim.date_of_loss)}
                </p>
              </div>
              <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
