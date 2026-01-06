"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  User,
  DollarSign,
  Shield,
  Lightbulb,
  ArrowLeft,
  X,
  Loader2,
  Calendar,
  Phone,
  Mail,
  ClipboardList,
  AlertCircle,
} from "lucide-react";
import { clsx } from "clsx";
import { api } from "@/lib/api";
import { formatDate, formatDateTime, formatCurrency, safeNumber } from "@/lib/utils";
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

const statusOptions = [
  { value: "fnol_received", label: "FNOL Received" },
  { value: "under_investigation", label: "Under Investigation" },
  { value: "pending_info", label: "Pending Info" },
  { value: "approved", label: "Approved" },
  { value: "denied", label: "Denied" },
  { value: "closed_paid", label: "Closed - Paid" },
];

// Toast notification component
function Toast({ message, type, onClose }: { message: string; type: "success" | "error" | "info"; onClose: () => void }) {
  const bgColor = type === "success" ? "bg-success-50 border-success-200" : type === "error" ? "bg-danger-50 border-danger-200" : "bg-primary-50 border-primary-200";
  const textColor = type === "success" ? "text-success-700" : type === "error" ? "text-danger-700" : "text-primary-700";
  const Icon = type === "success" ? CheckCircle : type === "error" ? AlertCircle : Clock;

  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center p-4 rounded-lg border ${bgColor} shadow-lg animate-slide-in`}>
      <Icon className={`h-5 w-5 ${textColor} mr-3`} />
      <span className={`${textColor} font-medium`}>{message}</span>
      <button onClick={onClose} className={`ml-4 ${textColor} hover:opacity-70`}>
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

// Modal component
function Modal({ isOpen, onClose, title, children }: { isOpen: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
        <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="h-5 w-5" />
            </button>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

export default function ClaimDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const claimNumber = params.id as string;

  // State for modals and toasts
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [showActionModal, setShowActionModal] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState("");
  const [statusNote, setStatusNote] = useState("");
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  const showToast = (message: string, type: "success" | "error" | "info" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const { data: claim, isLoading } = useQuery({
    queryKey: ["claim", claimNumber],
    queryFn: () => api.getClaim(claimNumber),
  });

  // Mutation for status update (mock - just shows success)
  const updateStatusMutation = useMutation({
    mutationFn: async ({ status, note }: { status: string; note: string }) => {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return { status, note };
    },
    onSuccess: (data) => {
      showToast(`Status updated to "${statusLabels[data.status]}"`, "success");
      setShowStatusModal(false);
      setSelectedStatus("");
      setStatusNote("");
      queryClient.invalidateQueries({ queryKey: ["claim", claimNumber] });
    },
    onError: () => {
      showToast("Failed to update status", "error");
    },
  });

  // Action handlers
  const handleAction = (action: string) => {
    setShowActionModal(null);
    showToast(`${action} request submitted successfully`, "success");
  };

  if (isLoading) {
    return <PageLoader message="Loading claim details..." />;
  }

  if (!claim) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Claim not found</h2>
        <p className="text-gray-500 mt-2">
          The claim {claimNumber} could not be found.
        </p>
        <Link href="/claims" className="btn-primary mt-4 inline-block">
          Back to Claims
        </Link>
      </div>
    );
  }

  const fraudScore = safeNumber(claim.fraud_score);
  const fraudRiskLevel =
    fraudScore > 0.5
      ? "high"
      : fraudScore > 0.3
      ? "medium"
      : "low";

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {/* Back Link */}
      <Link
        href="/claims"
        className="inline-flex items-center text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Claims
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-gray-900">
              {claim.claim_number}
            </h1>
            <span
              className={clsx(
                "badge",
                statusColors[claim.status] || "badge-primary"
              )}
            >
              {statusLabels[claim.status] || claim.status}
            </span>
          </div>
          <p className="text-gray-500 mt-1">
            Reported on {formatDateTime(claim.date_reported)}
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            className="btn-secondary"
            onClick={() => setShowDocumentModal(true)}
          >
            Request Documents
          </button>
          <button
            className="btn-primary"
            onClick={() => {
              setSelectedStatus(claim.status);
              setShowStatusModal(true);
            }}
          >
            Update Status
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Claim Details */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Claim Details
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Date of Loss</p>
                <p className="font-medium text-gray-900">
                  {formatDate(claim.date_of_loss, "MMMM d, yyyy")}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Policy ID</p>
                <Link
                  href={`/policies/${claim.policy_id}`}
                  className="font-medium text-primary-600 hover:text-primary-700 hover:underline"
                >
                  {claim.policy_id}
                </Link>
              </div>
              <div>
                <p className="text-sm text-gray-500">Severity</p>
                <p className="font-medium text-gray-900 capitalize">
                  {claim.severity || "Pending Assessment"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Reserve Amount</p>
                <p className="font-medium text-gray-900">
                  {formatCurrency(claim.reserve_amount)}
                </p>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-sm text-gray-500 mb-2">Loss Description</p>
              <p className="text-gray-900">{claim.loss_description}</p>
            </div>
          </div>

          {/* AI Analysis */}
          {claim.ai_recommendation && (
            <div className="card bg-gradient-to-br from-primary-50 to-white border-primary-100">
              <div className="flex items-center space-x-2 mb-4">
                <div className="h-8 w-8 rounded-lg bg-primary-100 flex items-center justify-center">
                  <Lightbulb className="h-5 w-5 text-primary-600" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900">
                  AI Recommendation
                </h2>
              </div>
              <p className="text-gray-700">{claim.ai_recommendation}</p>
            </div>
          )}

          {/* Timeline */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Activity Timeline
            </h2>
            <div className="space-y-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                    <FileText className="h-4 w-4 text-primary-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">
                    FNOL Submitted
                  </p>
                  <p className="text-sm text-gray-500">
                    {formatDateTime(claim.date_reported)}
                  </p>
                </div>
              </div>
              <div className="flex">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-success-100 flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-success-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-900">
                    AI Analysis Complete
                  </p>
                  <p className="text-sm text-gray-500">
                    Fraud score: {(fraudScore * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Summary */}
        <div className="space-y-6">
          {/* Fraud Risk */}
          <div
            className={clsx(
              "card",
              fraudRiskLevel === "high" && "border-danger-200 bg-danger-50",
              fraudRiskLevel === "medium" && "border-warning-200 bg-warning-50"
            )}
          >
            <div className="flex items-center space-x-2 mb-4">
              <Shield
                className={clsx(
                  "h-5 w-5",
                  fraudRiskLevel === "high" && "text-danger-600",
                  fraudRiskLevel === "medium" && "text-warning-600",
                  fraudRiskLevel === "low" && "text-success-600"
                )}
              />
              <h2 className="text-lg font-semibold text-gray-900">
                Fraud Risk Assessment
              </h2>
            </div>
            <div className="text-center py-4">
              <div
                className={clsx(
                  "text-4xl font-bold",
                  fraudRiskLevel === "high" && "text-danger-600",
                  fraudRiskLevel === "medium" && "text-warning-600",
                  fraudRiskLevel === "low" && "text-success-600"
                )}
              >
                {(fraudScore * 100).toFixed(0)}%
              </div>
              <p
                className={clsx(
                  "text-sm mt-1 capitalize",
                  fraudRiskLevel === "high" && "text-danger-600",
                  fraudRiskLevel === "medium" && "text-warning-600",
                  fraudRiskLevel === "low" && "text-success-600"
                )}
              >
                {fraudRiskLevel} Risk
              </p>
            </div>
            {fraudRiskLevel === "high" && (
              <div className="flex items-start mt-4 pt-4 border-t border-danger-200">
                <AlertTriangle className="h-5 w-5 text-danger-600 flex-shrink-0 mt-0.5" />
                <p className="ml-2 text-sm text-danger-700">
                  This claim has been flagged for additional review due to
                  elevated fraud indicators.
                </p>
              </div>
            )}
          </div>

          {/* Financial Summary */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <DollarSign className="h-5 w-5 text-gray-400" />
              <h2 className="text-lg font-semibold text-gray-900">
                Financial Summary
              </h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500">Reserve</span>
                <span className="font-medium text-gray-900">
                  {formatCurrency(claim.reserve_amount)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Paid</span>
                <span className="font-medium text-gray-900">
                  {formatCurrency(claim.paid_amount)}
                </span>
              </div>
              <div className="flex justify-between pt-3 border-t border-gray-100">
                <span className="font-medium text-gray-700">Outstanding</span>
                <span className="font-bold text-gray-900">
                  {formatCurrency(safeNumber(claim.reserve_amount) - safeNumber(claim.paid_amount))}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Actions
            </h2>
            <div className="space-y-2">
              <button
                className="w-full btn-secondary text-left flex items-center"
                onClick={() => setShowActionModal("Schedule Inspection")}
              >
                <Calendar className="h-4 w-4 mr-2" />
                Schedule Inspection
              </button>
              <button
                className="w-full btn-secondary text-left flex items-center"
                onClick={() => setShowActionModal("Contact Claimant")}
              >
                <Phone className="h-4 w-4 mr-2" />
                Contact Claimant
              </button>
              <button
                className="w-full btn-secondary text-left flex items-center"
                onClick={() => setShowActionModal("Request Additional Info")}
              >
                <Mail className="h-4 w-4 mr-2" />
                Request Additional Info
              </button>
              <button
                className="w-full btn-secondary text-left text-danger-600 flex items-center"
                onClick={() => setShowActionModal("Escalate to SIU")}
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Escalate to SIU
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Status Update Modal */}
      <Modal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        title="Update Claim Status"
      >
        <div className="space-y-4">
          <div>
            <label className="label">New Status</label>
            <select
              className="input"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Notes (Optional)</label>
            <textarea
              className="input resize-none"
              rows={3}
              placeholder="Add any notes about this status change..."
              value={statusNote}
              onChange={(e) => setStatusNote(e.target.value)}
            />
          </div>
          <div className="flex justify-end space-x-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowStatusModal(false)}
            >
              Cancel
            </button>
            <button
              className="btn-primary flex items-center"
              onClick={() => updateStatusMutation.mutate({ status: selectedStatus, note: statusNote })}
              disabled={updateStatusMutation.isPending}
            >
              {updateStatusMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                "Update Status"
              )}
            </button>
          </div>
        </div>
      </Modal>

      {/* Request Documents Modal */}
      <Modal
        isOpen={showDocumentModal}
        onClose={() => setShowDocumentModal(false)}
        title="Request Documents"
      >
        <div className="space-y-4">
          <p className="text-gray-600">Select documents to request from the claimant:</p>
          <div className="space-y-2">
            {["Veterinary Records", "Treatment Invoices", "Pet Medical History", "Proof of Ownership", "Photos of Injury"].map((doc) => (
              <label key={doc} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input type="checkbox" className="mr-3" />
                <span className="text-gray-700">{doc}</span>
              </label>
            ))}
          </div>
          <div className="flex justify-end space-x-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowDocumentModal(false)}
            >
              Cancel
            </button>
            <button
              className="btn-primary"
              onClick={() => {
                setShowDocumentModal(false);
                showToast("Document request sent to claimant", "success");
              }}
            >
              Send Request
            </button>
          </div>
        </div>
      </Modal>

      {/* Action Confirmation Modal */}
      <Modal
        isOpen={!!showActionModal}
        onClose={() => setShowActionModal(null)}
        title={showActionModal || ""}
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            {showActionModal === "Escalate to SIU"
              ? "Are you sure you want to escalate this claim to the Special Investigations Unit? This action will flag the claim for fraud investigation."
              : `Confirm ${showActionModal?.toLowerCase()} for claim ${claim.claim_number}?`
            }
          </p>
          {showActionModal === "Escalate to SIU" && (
            <div>
              <label className="label">Reason for Escalation</label>
              <textarea
                className="input resize-none"
                rows={3}
                placeholder="Describe why this claim should be escalated..."
              />
            </div>
          )}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowActionModal(null)}
            >
              Cancel
            </button>
            <button
              className={clsx(
                "btn-primary",
                showActionModal === "Escalate to SIU" && "bg-danger-600 hover:bg-danger-700"
              )}
              onClick={() => handleAction(showActionModal || "")}
            >
              {showActionModal === "Escalate to SIU" ? "Escalate" : "Confirm"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
