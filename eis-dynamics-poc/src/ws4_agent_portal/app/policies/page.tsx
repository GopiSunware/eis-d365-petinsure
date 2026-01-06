"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { FileText, CheckCircle, XCircle, Clock } from "lucide-react";
import { clsx } from "clsx";
import { api, Policy } from "@/lib/api";
import { formatDate, formatCurrency } from "@/lib/utils";
import { PageLoader } from "@/components/LoadingBar";

const statusIcons: Record<string, any> = {
  active: CheckCircle,
  expired: XCircle,
  pending_renewal: Clock,
};

const statusColors: Record<string, string> = {
  active: "text-success-600 bg-success-50",
  expired: "text-danger-600 bg-danger-50",
  pending_renewal: "text-warning-600 bg-warning-50",
  cancelled: "text-gray-600 bg-gray-100",
};

export default function PoliciesPage() {
  const router = useRouter();
  const { data: policies, isLoading } = useQuery({
    queryKey: ["policies"],
    queryFn: () => api.getPolicies(),
  });

  if (isLoading) {
    return <PageLoader message="Loading policies..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Policies</h1>
        <p className="text-gray-500 mt-1">View insurance policies from EIS</p>
      </div>

      {policies?.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No policies found</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  Policy Number
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  Insured
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  Type
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  Effective
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  Expiration
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  Premium
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {policies?.map((policy: Policy) => {
                const StatusIcon = statusIcons[policy.status] || FileText;
                return (
                  <tr
                    key={policy.policy_id}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => router.push(`/policies/${policy.policy_id}`)}
                  >
                    <td className="py-3 px-4">
                      <span className="font-medium text-primary-600">
                        {policy.policy_number}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {policy.insured_name}
                    </td>
                    <td className="py-3 px-4">
                      <span className="badge badge-primary capitalize">
                        {policy.policy_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {formatDate(policy.effective_date)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {formatDate(policy.expiration_date)}
                    </td>
                    <td className="py-3 px-4 text-sm font-medium text-gray-900">
                      {formatCurrency(policy.total_premium)}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={clsx(
                          "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize",
                          statusColors[policy.status] || "bg-gray-100 text-gray-600"
                        )}
                      >
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {policy.status.replace("_", " ")}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
