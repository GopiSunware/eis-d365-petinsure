"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { clsx } from "clsx";
import {
  Upload,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  Trash2,
  RefreshCw,
  AlertCircle,
  File,
  Archive,
  X,
} from "lucide-react";

import {
  docgenApi,
  BatchListItem,
  ProcessingStatus,
  formatFileSize,
} from "@/lib/docgen-api";

export default function DocGenPage() {
  const router = useRouter();
  const [batches, setBatches] = useState<BatchListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [claimNumber, setClaimNumber] = useState("");
  const [serviceConnected, setServiceConnected] = useState<boolean | null>(null);

  // Check service health
  const checkServiceHealth = async () => {
    try {
      await docgenApi.healthCheck();
      setServiceConnected(true);
    } catch {
      setServiceConnected(false);
    }
  };

  // Load batches
  const loadBatches = async () => {
    try {
      setLoading(true);
      const data = await docgenApi.getBatches(20, 0);
      setBatches(data.batches);
      setError(null);
    } catch (err) {
      setError("Failed to load batches. Is the DocGen service running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkServiceHealth();
    loadBatches();
  }, []);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  }, []);

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  // Remove file from selection
  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Upload files
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress("Uploading...");

    try {
      const response = await docgenApi.uploadDocuments(
        selectedFiles,
        claimNumber || undefined
      );

      setUploadProgress("Processing...");

      // Start processing
      await docgenApi.startProcessing(response.batch_id, false);

      // Navigate to batch details
      router.push(`/docgen/${response.batch_id}`);
    } catch (err) {
      setError("Upload failed. Please try again.");
      console.error(err);
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  // Delete batch
  const handleDelete = async (batchId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this batch?")) return;

    try {
      await docgenApi.deleteBatch(batchId);
      loadBatches();
    } catch (err) {
      console.error("Failed to delete batch:", err);
    }
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
            <CheckCircle className="w-3 h-3" />
            Completed
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
            <XCircle className="w-3 h-3" />
            Failed
          </span>
        );
      case "pending":
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
            <Loader2 className="w-3 h-3 animate-spin" />
            Processing
          </span>
        );
    }
  };

  // Get file icon
  const getFileIcon = (filename: string) => {
    if (filename.endsWith(".zip")) return <Archive className="w-5 h-5 text-purple-500" />;
    if (filename.endsWith(".pdf")) return <FileText className="w-5 h-5 text-red-500" />;
    return <File className="w-5 h-5 text-gray-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">DocGen</h1>
          <p className="text-gray-500 mt-1">
            Upload documents for AI-powered claim processing and export
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Service Status */}
          <div
            className={clsx(
              "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm",
              serviceConnected === true && "bg-green-100 text-green-700",
              serviceConnected === false && "bg-red-100 text-red-700",
              serviceConnected === null && "bg-gray-100 text-gray-500"
            )}
          >
            <span
              className={clsx(
                "w-2 h-2 rounded-full",
                serviceConnected === true && "bg-green-500",
                serviceConnected === false && "bg-red-500",
                serviceConnected === null && "bg-gray-400"
              )}
            />
            {serviceConnected === true && "Service Connected"}
            {serviceConnected === false && "Service Offline"}
            {serviceConnected === null && "Checking..."}
          </div>
          <button
            onClick={loadBatches}
            className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Upload Documents
        </h2>

        {/* Claim Number Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Claim Number (optional)
          </label>
          <input
            type="text"
            value={claimNumber}
            onChange={(e) => setClaimNumber(e.target.value)}
            placeholder="Enter existing claim number or leave empty for new"
            className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isUploading}
          />
        </div>

        {/* Dropzone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={clsx(
            "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
            dragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-gray-400",
            isUploading && "opacity-50 pointer-events-none"
          )}
        >
          <input
            type="file"
            id="file-upload"
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.heic,.doc,.docx,.zip"
            onChange={handleFileChange}
            className="hidden"
            disabled={isUploading}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            {dragActive ? (
              <p className="text-blue-500 font-medium">Drop files here...</p>
            ) : (
              <>
                <p className="text-gray-600 font-medium">
                  Drag & drop documents here
                </p>
                <p className="text-gray-400 text-sm mt-1">
                  or click to browse (PDF, Images, Word, ZIP)
                </p>
                <p className="text-gray-400 text-xs mt-2">
                  ZIP files up to 50MB with max 20 files
                </p>
              </>
            )}
          </label>
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            <h4 className="font-medium text-gray-700">
              Selected Files ({selectedFiles.length})
            </h4>
            <ul className="space-y-2 max-h-48 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <li
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getFileIcon(file.name)}
                    <span className="text-sm text-gray-700">{file.name}</span>
                    <span className="text-xs text-gray-400">
                      ({formatFileSize(file.size)})
                    </span>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-gray-400 hover:text-red-500"
                    disabled={isUploading}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Upload Button */}
        {selectedFiles.length > 0 && (
          <div className="mt-4">
            <button
              onClick={handleUpload}
              disabled={isUploading || serviceConnected === false}
              className={clsx(
                "flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium text-white w-full md:w-auto",
                isUploading || serviceConnected === false
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              )}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {uploadProgress}
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Upload & Process {selectedFiles.length} File
                  {selectedFiles.length > 1 ? "s" : ""}
                </>
              )}
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}
      </div>

      {/* Recent Batches */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Recent Batches
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        ) : batches.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No batches yet</p>
            <p className="text-gray-400 text-sm mt-1">
              Upload documents to get started
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {batches.map((batch) => (
              <Link
                key={batch.batch_id}
                href={`/docgen/${batch.batch_id}`}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <FileText className="w-8 h-8 text-gray-400" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {batch.claim_number || `Batch ${batch.batch_id.slice(0, 8)}`}
                      </span>
                      {getStatusBadge(batch.status)}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {batch.documents_count} document
                      {batch.documents_count !== 1 ? "s" : ""} •{" "}
                      {new Date(batch.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleDelete(batch.batch_id, e)}
                    className="p-2 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
