"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, CheckCircle, Loader2, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function NewClaimPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    policy_number: "",
    date_of_loss: "",
    description: "",
    contact_phone: "",
    contact_email: "",
  });

  // Fetch existing policies for dropdown
  const { data: policies, isLoading: loadingPolicies } = useQuery({
    queryKey: ["policies"],
    queryFn: api.getPolicies,
  });

  const mutation = useMutation({
    mutationFn: api.submitFNOL,
    onSuccess: (data) => {
      router.push(`/claims/${data.claim_number}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  // Get selected policy details
  const selectedPolicy = policies?.find(
    (p) => p.policy_number === formData.policy_number
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Submit New Claim</h1>
        <p className="text-gray-500 mt-1">
          First Notice of Loss (FNOL) Submission
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        {/* Policy Selection */}
        <div>
          <label htmlFor="policy_number" className="label">
            Select Policy *
          </label>
          <div className="relative">
            <select
              id="policy_number"
              required
              className="input appearance-none pr-10"
              value={formData.policy_number}
              onChange={(e) =>
                setFormData({ ...formData, policy_number: e.target.value })
              }
              disabled={loadingPolicies}
            >
              <option value="">
                {loadingPolicies ? "Loading policies..." : "Select a policy"}
              </option>
              {policies?.map((policy) => (
                <option key={policy.policy_id} value={policy.policy_number}>
                  {policy.policy_number} - {policy.insured_name || "Pet Insurance"} ({policy.status})
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
          </div>
          {selectedPolicy && (
            <div className="mt-2 p-3 bg-gray-50 rounded-lg text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-gray-500">Type:</span>{" "}
                  <span className="font-medium capitalize">
                    {selectedPolicy.policy_type?.replace("_", " ") || "Pet Insurance"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Status:</span>{" "}
                  <span className="font-medium capitalize">{selectedPolicy.status}</span>
                </div>
                <div>
                  <span className="text-gray-500">Effective:</span>{" "}
                  <span className="font-medium">{formatDate(selectedPolicy.effective_date)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Expires:</span>{" "}
                  <span className="font-medium">{formatDate(selectedPolicy.expiration_date)}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Date of Loss */}
        <div>
          <label htmlFor="date_of_loss" className="label">
            Date of Loss *
          </label>
          <input
            type="date"
            id="date_of_loss"
            required
            className="input"
            max={new Date().toISOString().split("T")[0]}
            value={formData.date_of_loss}
            onChange={(e) =>
              setFormData({ ...formData, date_of_loss: e.target.value })
            }
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="label">
            Description of Incident *
          </label>
          <textarea
            id="description"
            required
            rows={6}
            placeholder="Please describe what happened in detail. Include information about your pet (name, breed, age), the injury or illness, veterinary care received, estimated treatment costs, and any other relevant details..."
            className="input resize-none"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
          />
          <p className="text-sm text-gray-500 mt-1">
            AI will analyze this description to extract key details and assess
            the claim
          </p>
        </div>

        {/* Contact Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="contact_phone" className="label">
              Contact Phone
            </label>
            <input
              type="tel"
              id="contact_phone"
              placeholder="555-123-4567"
              className="input"
              value={formData.contact_phone}
              onChange={(e) =>
                setFormData({ ...formData, contact_phone: e.target.value })
              }
            />
          </div>
          <div>
            <label htmlFor="contact_email" className="label">
              Contact Email
            </label>
            <input
              type="email"
              id="contact_email"
              placeholder="john@example.com"
              className="input"
              value={formData.contact_email}
              onChange={(e) =>
                setFormData({ ...formData, contact_email: e.target.value })
              }
            />
          </div>
        </div>

        {/* Error Message */}
        {mutation.isError && (
          <div className="flex items-center p-4 bg-danger-50 rounded-lg text-danger-600">
            <AlertCircle className="h-5 w-5 mr-2" />
            <span>
              Failed to submit claim. Please check your information and try
              again.
            </span>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-100">
          <button
            type="button"
            onClick={() => router.back()}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending || !formData.policy_number}
            className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Submit FNOL
              </>
            )}
          </button>
        </div>
      </form>

      {/* AI Processing Info */}
      <div className="bg-primary-50 rounded-lg p-4">
        <h3 className="font-medium text-primary-900">AI-Powered Processing</h3>
        <p className="text-sm text-primary-700 mt-1">
          When you submit this claim, our AI will automatically:
        </p>
        <ul className="text-sm text-primary-700 mt-2 space-y-1 list-disc list-inside">
          <li>Extract structured incident details (pet info, injury type, vet details)</li>
          <li>Assess claim severity (minor, moderate, severe)</li>
          <li>Analyze for potential fraud indicators</li>
          <li>Recommend triage actions and assign priority</li>
        </ul>
      </div>
    </div>
  );
}
