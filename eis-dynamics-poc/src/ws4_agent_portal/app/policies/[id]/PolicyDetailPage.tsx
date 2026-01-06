"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  User,
  Calendar,
  DollarSign,
  Shield,
  ArrowLeft,
  CheckCircle,
  Clock,
  XCircle,
  PawPrint,
} from "lucide-react";
import { clsx } from "clsx";
import { api } from "@/lib/api";
import { formatDate, formatCurrency, safeNumber } from "@/lib/utils";
import { PageLoader } from "@/components/LoadingBar";

const statusColors: Record<string, string> = {
  active: "badge-success",
  expired: "badge-danger",
  pending_renewal: "badge-warning",
  cancelled: "badge-secondary",
};

const statusIcons: Record<string, any> = {
  active: CheckCircle,
  expired: XCircle,
  pending_renewal: Clock,
};

export default function PolicyDetailPage() {
  const params = useParams();
  const policyId = params.id as string;

  const { data: policy, isLoading } = useQuery({
    queryKey: ["policy", policyId],
    queryFn: () => api.getPolicy(policyId),
  });

  if (isLoading) {
    return <PageLoader message="Loading policy details..." />;
  }

  if (!policy) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Policy not found</h2>
        <p className="text-gray-500 mt-2">
          The policy {policyId} could not be found.
        </p>
        <Link href="/policies" className="btn-primary mt-4 inline-block">
          Back to Policies
        </Link>
      </div>
    );
  }

  const StatusIcon = statusIcons[policy.status] || FileText;

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <Link
        href="/policies"
        className="inline-flex items-center text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Policies
      </Link>

      {/* Policy Header */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div className="flex items-start">
            <div className="h-16 w-16 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
              <FileText className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {policy.policy_number}
              </h1>
              <p className="text-gray-500">{policy.policy_id}</p>
              <div className="flex items-center space-x-2 mt-2">
                <span
                  className={clsx(
                    "badge capitalize inline-flex items-center",
                    statusColors[policy.status] || "badge-secondary"
                  )}
                >
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {policy.status.replace("_", " ")}
                </span>
                <span className="badge badge-primary capitalize">
                  {policy.policy_type?.replace("_", " ") || "Pet Insurance"}
                </span>
              </div>
            </div>
          </div>
          <div className="flex space-x-3">
            <button className="btn-secondary">Edit Policy</button>
            <button className="btn-primary">Renew Policy</button>
          </div>
        </div>

        {/* Policy Info Grid */}
        <div className="mt-6 pt-6 border-t border-gray-100 grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="flex items-center">
            <User className="h-5 w-5 text-gray-400 mr-3" />
            <div>
              <p className="text-xs text-gray-500">Insured Name</p>
              <p className="font-medium text-gray-900">{policy.insured_name || "N/A"}</p>
            </div>
          </div>
          <div className="flex items-center">
            <Calendar className="h-5 w-5 text-gray-400 mr-3" />
            <div>
              <p className="text-xs text-gray-500">Effective Date</p>
              <p className="font-medium text-gray-900">{formatDate(policy.effective_date)}</p>
            </div>
          </div>
          <div className="flex items-center">
            <Calendar className="h-5 w-5 text-gray-400 mr-3" />
            <div>
              <p className="text-xs text-gray-500">Expiration Date</p>
              <p className="font-medium text-gray-900">{formatDate(policy.expiration_date)}</p>
            </div>
          </div>
          <div className="flex items-center">
            <DollarSign className="h-5 w-5 text-gray-400 mr-3" />
            <div>
              <p className="text-xs text-gray-500">Annual Premium</p>
              <p className="font-medium text-gray-900">{formatCurrency(policy.total_premium)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coverages */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center space-x-2 mb-4">
            <Shield className="h-5 w-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Coverages</h2>
          </div>

          {policy.coverages && policy.coverages.length > 0 ? (
            <div className="space-y-3">
              {policy.coverages.map((coverage: any, index: number) => (
                <div
                  key={coverage.coverage_id || index}
                  className="p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 capitalize">
                        {coverage.coverage_type?.replace("_", " ") || "Coverage"}
                      </p>
                      <p className="text-sm text-gray-500">
                        Limit: {formatCurrency(coverage.limit)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-primary-600">
                        {formatCurrency(coverage.premium)}
                      </p>
                      <p className="text-xs text-gray-500">premium</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Shield className="h-10 w-10 text-gray-300 mx-auto mb-2" />
              <p>No coverage details available</p>
            </div>
          )}
        </div>

        {/* Policy Summary */}
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <DollarSign className="h-5 w-5 text-success-600" />
              <h2 className="text-lg font-semibold text-gray-900">Premium Summary</h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500">Base Premium</span>
                <span className="font-medium text-gray-900">
                  {formatCurrency(policy.total_premium)}
                </span>
              </div>
              <div className="flex justify-between pt-3 border-t border-gray-100">
                <span className="font-medium text-gray-700">Total Annual</span>
                <span className="font-bold text-lg text-gray-900">
                  {formatCurrency(policy.total_premium)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Monthly</span>
                <span className="text-gray-600">
                  {formatCurrency(safeNumber(policy.total_premium) / 12)}/mo
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions</h2>
            <div className="space-y-2">
              <Link href="/claims/new" className="w-full btn-secondary text-left block">
                File a Claim
              </Link>
              <button className="w-full btn-secondary text-left">
                Request Documents
              </button>
              <button className="w-full btn-secondary text-left">
                Contact Support
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
