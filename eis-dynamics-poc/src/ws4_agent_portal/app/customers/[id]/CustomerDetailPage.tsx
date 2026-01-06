"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  User,
  Mail,
  Phone,
  MapPin,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Shield,
  Calendar,
  ArrowLeft,
} from "lucide-react";
import { clsx } from "clsx";
import { api, Customer, Policy, Claim } from "@/lib/api";
import { formatDate, formatDateTime, formatCurrency, safeNumber } from "@/lib/utils";
import { PageLoader } from "@/components/LoadingBar";

const policyStatusColors: Record<string, string> = {
  active: "badge-success",
  expired: "badge-danger",
  pending_renewal: "badge-warning",
  cancelled: "badge-secondary",
};

const claimStatusColors: Record<string, string> = {
  fnol_received: "badge-primary",
  under_investigation: "badge-warning",
  pending_info: "badge-warning",
  approved: "badge-success",
  denied: "badge-danger",
  closed_paid: "badge-success",
};

export default function CustomerDetailPage() {
  const params = useParams();
  const customerId = params.id as string;

  const { data: customer, isLoading: customerLoading } = useQuery({
    queryKey: ["customer", customerId],
    queryFn: () => api.getCustomer(customerId),
  });

  const { data: policies, isLoading: policiesLoading } = useQuery({
    queryKey: ["customer-policies", customerId],
    queryFn: () => api.getCustomerPolicies(customerId),
  });

  const { data: claims, isLoading: claimsLoading } = useQuery({
    queryKey: ["customer-claims", customerId],
    queryFn: () => api.getCustomerClaims(customerId),
  });

  const isLoading = customerLoading || policiesLoading || claimsLoading;

  if (isLoading) {
    return <PageLoader message="Loading customer details..." />;
  }

  if (!customer) {
    return (
      <div className="text-center py-12">
        <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Customer not found</h2>
        <p className="text-gray-500 mt-2">
          The customer {customerId} could not be found.
        </p>
        <Link href="/customers" className="btn-primary mt-4 inline-block">
          Back to Customers
        </Link>
      </div>
    );
  }

  const activePolicies = policies?.filter((p) => p.status === "active") || [];
  const totalPremium = activePolicies.reduce((sum, p) => sum + safeNumber(p.total_premium), 0);
  const openClaims = claims?.filter((c) => !["closed_paid", "denied"].includes(c.status)) || [];
  const totalClaimAmount = claims?.reduce((sum, c) => sum + safeNumber(c.reserve_amount), 0) || 0;

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <Link
        href="/customers"
        className="inline-flex items-center text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Customers
      </Link>

      {/* Customer Header */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div className="flex items-start">
            <div className="h-16 w-16 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <span className="text-primary-600 font-bold text-2xl">
                {customer.first_name[0]}
                {customer.last_name[0]}
              </span>
            </div>
            <div className="ml-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {customer.first_name} {customer.last_name}
              </h1>
              <p className="text-gray-500">{customer.customer_id}</p>
              <span className="badge badge-primary mt-2 capitalize">
                {customer.customer_type?.replace("_", " ") || "Individual"}
              </span>
            </div>
          </div>
          <div className="flex space-x-3">
            <button className="btn-secondary">Edit Customer</button>
            <button className="btn-primary">New Policy</button>
          </div>
        </div>

        {/* Contact Info */}
        <div className="mt-6 pt-6 border-t border-gray-100 grid grid-cols-1 md:grid-cols-3 gap-4">
          {customer.email && (
            <div className="flex items-center">
              <Mail className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <p className="text-xs text-gray-500">Email</p>
                <p className="text-gray-900">{customer.email}</p>
              </div>
            </div>
          )}
          {customer.phone && (
            <div className="flex items-center">
              <Phone className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <p className="text-xs text-gray-500">Phone</p>
                <p className="text-gray-900">{customer.phone}</p>
              </div>
            </div>
          )}
          {customer.address && (
            <div className="flex items-center">
              <MapPin className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <p className="text-xs text-gray-500">Address</p>
                <p className="text-gray-900">{customer.address}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <FileText className="h-5 w-5 text-primary-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-gray-500">Active Policies</p>
              <p className="text-xl font-bold text-gray-900">{activePolicies.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-lg bg-success-100 flex items-center justify-center">
              <DollarSign className="h-5 w-5 text-success-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-gray-500">Total Premium</p>
              <p className="text-xl font-bold text-gray-900">
                {formatCurrency(totalPremium)}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-lg bg-warning-100 flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-warning-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-gray-500">Open Claims</p>
              <p className="text-xl font-bold text-gray-900">{openClaims.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-lg bg-danger-100 flex items-center justify-center">
              <Shield className="h-5 w-5 text-danger-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-gray-500">Claims Reserve</p>
              <p className="text-xl font-bold text-gray-900">
                {formatCurrency(totalClaimAmount)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Policies Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Policies</h2>
            <Link href="/quotes/new" className="text-primary-600 text-sm hover:underline">
              New Quote
            </Link>
          </div>
          {policies?.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-10 w-10 text-gray-300 mx-auto mb-2" />
              <p className="text-gray-500">No policies found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {policies?.map((policy: Policy) => (
                <Link
                  key={policy.policy_id}
                  href={`/policies/${policy.policy_id}`}
                  className="block p-3 border border-gray-100 rounded-lg hover:border-primary-200 hover:bg-primary-50/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-primary-600">
                        {policy.policy_number}
                      </p>
                      <p className="text-sm text-gray-500 capitalize">
                        {policy.policy_type}
                      </p>
                    </div>
                    <span
                      className={clsx(
                        "badge capitalize",
                        policyStatusColors[policy.status] || "badge-secondary"
                      )}
                    >
                      {policy.status.replace("_", " ")}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-sm">
                    <div className="flex items-center text-gray-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      {formatDate(policy.effective_date)} - {formatDate(policy.expiration_date)}
                    </div>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(policy.total_premium)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Claims Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Claims History</h2>
            <Link href="/claims/new" className="text-primary-600 text-sm hover:underline">
              File FNOL
            </Link>
          </div>
          {claims?.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-10 w-10 text-gray-300 mx-auto mb-2" />
              <p className="text-gray-500">No claims found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {claims?.map((claim: Claim) => (
                <Link
                  key={claim.claim_id}
                  href={`/claims/${claim.claim_number}`}
                  className="block p-3 border border-gray-100 rounded-lg hover:border-primary-200"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-primary-600">
                        {claim.claim_number}
                      </p>
                      <p className="text-sm text-gray-500 truncate max-w-[200px]">
                        {claim.loss_description}
                      </p>
                    </div>
                    <span
                      className={clsx(
                        "badge capitalize",
                        claimStatusColors[claim.status] || "badge-secondary"
                      )}
                    >
                      {claim.status.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-sm">
                    <div className="flex items-center text-gray-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      {formatDate(claim.date_of_loss)}
                    </div>
                    <div className="flex items-center">
                      {safeNumber(claim.fraud_score) > 0.5 && (
                        <span className="text-danger-600 text-xs mr-2 flex items-center">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          High Risk
                        </span>
                      )}
                      <span className="font-medium text-gray-900">
                        {formatCurrency(claim.reserve_amount)}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Customer Notes / Activity */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                <User className="h-4 w-4 text-primary-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-900">Customer Created</p>
              <p className="text-sm text-gray-500">
                {formatDateTime(customer.created_at, "Unknown date")}
              </p>
            </div>
          </div>
          {activePolicies.length > 0 && (
            <div className="flex">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-success-100 flex items-center justify-center">
                  <CheckCircle className="h-4 w-4 text-success-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">
                  {activePolicies.length} Active {activePolicies.length === 1 ? "Policy" : "Policies"}
                </p>
                <p className="text-sm text-gray-500">
                  Total annual premium: {formatCurrency(totalPremium)}
                </p>
              </div>
            </div>
          )}
          {openClaims.length > 0 && (
            <div className="flex">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-warning-100 flex items-center justify-center">
                  <Clock className="h-4 w-4 text-warning-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">
                  {openClaims.length} Open {openClaims.length === 1 ? "Claim" : "Claims"}
                </p>
                <p className="text-sm text-gray-500">
                  Requires attention
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
