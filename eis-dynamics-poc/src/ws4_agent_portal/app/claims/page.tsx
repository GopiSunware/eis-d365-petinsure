"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Plus, AlertTriangle, Filter } from "lucide-react";
import { clsx } from "clsx";
import { api, Claim } from "@/lib/api";
import { formatDate, formatCurrency, safeNumber } from "@/lib/utils";
import { PageLoader } from "@/components/LoadingBar";

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

export default function ClaimsPage() {
  const router = useRouter();
  const { data: claims, isLoading } = useQuery({
    queryKey: ["claims"],
    queryFn: () => api.getClaims(),
  });

  if (isLoading) {
    return <PageLoader message="Loading claims..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Claims</h1>
          <p className="text-gray-500 mt-1">
            Manage insurance claims and FNOL submissions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="btn-secondary flex items-center">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </button>
          <Link href="/claims/new" className="btn-primary flex items-center">
            <Plus className="h-4 w-4 mr-2" />
            New Claim
          </Link>
        </div>
      </div>

      <div className="card">
        {claims?.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No claims found</p>
            <Link
              href="/claims/new"
              className="text-primary-600 hover:text-primary-700 font-medium mt-2 inline-block"
            >
              Submit a new claim
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Claim Number
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Date of Loss
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Reserve
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Fraud Risk
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody>
                {claims?.map((claim: Claim) => (
                  <tr
                    key={claim.claim_number}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => router.push(`/claims/${claim.claim_number}`)}
                  >
                    <td className="py-3 px-4">
                      <span className="font-medium text-primary-600">
                        {claim.claim_number}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {formatDate(claim.date_of_loss)}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={clsx(
                          "badge",
                          statusColors[claim.status] || "badge-primary"
                        )}
                      >
                        {statusLabels[claim.status] || claim.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {formatCurrency(claim.reserve_amount)}
                    </td>
                    <td className="py-3 px-4">
                      {safeNumber(claim.fraud_score) > 0.5 ? (
                        <span className="badge badge-danger flex items-center w-fit">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          High ({(safeNumber(claim.fraud_score) * 100).toFixed(0)}%)
                        </span>
                      ) : safeNumber(claim.fraud_score) > 0.3 ? (
                        <span className="badge badge-warning">
                          Medium ({(safeNumber(claim.fraud_score) * 100).toFixed(0)}%)
                        </span>
                      ) : (
                        <span className="badge badge-success">
                          Low ({(safeNumber(claim.fraud_score) * 100).toFixed(0)}%)
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 max-w-xs truncate">
                      {claim.loss_description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
