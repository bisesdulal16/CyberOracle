'use client';

import React, { useRef, useState } from 'react';
import { apiFetch } from '../lib/auth';
import { CloudArrowUpIcon, ArrowDownTrayIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

// Fixed: use the same env var as the rest of the app
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8003';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];
const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];
const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

type Finding = {
  type: string;
  count: number;
};

type SanitizeResult = {
  filename: string;
  file_type: string;
  total_redactions: number;
  findings: Finding[];
  redacted_text: string;
};

type UploadState = 'idle' | 'uploading' | 'done' | 'error';

function Spinner({ className }: { className?: string }) {
  return <ArrowPathIcon className={`animate-spin text-cyan-400 ${className ?? 'w-5 h-5'}`} />;
}

/**
 * Validates the selected file before uploading.
 * Checks extension, MIME type, and file size client-side
 * so the user gets instant feedback without a round trip.
 */
function validateFile(file: File): string | null {
  const nameParts = file.name.split('.');
  const ext = nameParts.length > 1 ? '.' + nameParts.pop()!.toLowerCase() : '';

  if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
    return `Unsupported file type "${ext || 'unknown'}". Please upload a PDF or DOCX file.`;
  }

  if (file.type && !ALLOWED_MIME_TYPES.includes(file.type)) {
    return `Invalid file format. Expected a PDF or DOCX but received "${file.type}".`;
  }

  if (file.size === 0) {
    return 'The selected file is empty.';
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return `File is too large (${sizeMB} MB). Maximum allowed size is ${MAX_FILE_SIZE_MB} MB.`;
  }

  return null; // valid
}

export default function DocumentSanitizerPanel() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [result, setResult] = useState<SanitizeResult | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setResult(null);
    setUploadState('idle');

    if (!file) {
      setSelectedFile(null);
      setErrorMessage('');
      return;
    }

    // Validate immediately on selection for instant feedback
    const validationError = validateFile(file);
    if (validationError) {
      setSelectedFile(null);
      setErrorMessage(validationError);
      setUploadState('error');
      // Reset so the same invalid file can be re-selected after fixing
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setSelectedFile(file);
    setErrorMessage('');
  }

  async function handleScan() {
    if (!selectedFile) return;

    // Re-validate before upload in case something changed
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setErrorMessage(validationError);
      setUploadState('error');
      return;
    }

    setUploadState('uploading');
    setResult(null);
    setErrorMessage('');

    const form = new FormData();
    form.append('file', selectedFile);

    try {
      const res = await apiFetch(`${API_BASE}/api/documents/sanitize`, {
        method: 'POST',
        body: form,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(err.detail ?? `Server error ${res.status}`);
      }

      const data: SanitizeResult = await res.json();
      setResult(data);
      setUploadState('done');
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Upload failed');
      setUploadState('error');
    }
  }

  function handleDownload() {
    if (!result) return;
    const blob = new Blob([result.redacted_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.filename.replace(/\.(pdf|docx)$/i, '_sanitized.txt');
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleReset() {
    setSelectedFile(null);
    setResult(null);
    setErrorMessage('');
    setUploadState('idle');
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  return (
    <div className="mt-4 max-w-3xl">
      <h1 className="text-2xl font-semibold text-slate-100 mb-1">
        Document Sanitizer
      </h1>
      <p className="text-sm text-slate-400 mb-6">
        Upload a PDF or DOCX file. CyberOracle will scan it for sensitive data
        (SSNs, emails, credit cards, API keys) and return a redacted version
        safe to share or send to an LLM.
      </p>

      {/* Upload card */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
        <div
          className="border-2 border-dashed border-slate-700 rounded-lg p-8 text-center cursor-pointer hover:border-cyan-500/50 hover:bg-cyan-500/5 transition"
          onClick={() => fileInputRef.current?.click()}
        >
          <CloudArrowUpIcon className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-300 mb-1">
            Click to select a file
          </p>
          <p className="text-xs text-slate-500">
            PDF or DOCX · Max {MAX_FILE_SIZE_MB} MB
          </p>

          {selectedFile && (
            <p className="mt-3 text-xs font-semibold text-cyan-400 bg-cyan-400/10 border border-cyan-500/20 inline-block px-3 py-1 rounded-full">
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="flex gap-3 mt-4">
          <button
            type="button"
            disabled={!selectedFile || uploadState === 'uploading'}
            onClick={handleScan}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-900 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            {uploadState === 'uploading' ? (
              <>
                <Spinner className="w-3.5 h-3.5" />
                Scanning…
              </>
            ) : (
              'Scan & Redact'
            )}
          </button>

          {(selectedFile || result || errorMessage) && (
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {uploadState === 'error' && errorMessage && (
        <div className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs text-red-400">
          {errorMessage}
        </div>
      )}

      {/* Results */}
      {uploadState === 'done' && result && (
        <>
          {/* Summary row */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
              <p className="text-xs text-slate-400 mb-1">File type</p>
              <p className="text-lg font-semibold text-slate-100">
                {result.file_type}
              </p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
              <p className="text-xs text-slate-400 mb-1">Total redactions</p>
              <p
                className={`text-lg font-semibold ${
                  result.total_redactions > 0 ? 'text-red-400' : 'text-emerald-400'
                }`}
              >
                {result.total_redactions}
              </p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
              <p className="text-xs text-slate-400 mb-1">Types detected</p>
              <p className="text-lg font-semibold text-slate-100">
                {result.findings.length}
              </p>
            </div>
          </div>

          {/* Findings breakdown */}
          {result.findings.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6">
              <h2 className="text-sm font-semibold text-slate-200 mb-3">
                Redaction Breakdown
              </h2>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 bg-slate-800 border-b border-slate-700">
                    <th className="pb-2 pt-2 px-3 font-medium">Entity type</th>
                    <th className="pb-2 pt-2 px-3 font-medium text-right">
                      Occurrences
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {result.findings.map((f) => (
                    <tr
                      key={f.type}
                      className="border-b border-slate-800 last:border-0 hover:bg-slate-800 transition"
                    >
                      <td className="py-2.5 px-3">
                        <span className="inline-block bg-red-400/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full font-semibold text-[10px]">
                          {f.type}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-semibold text-slate-200">
                        {f.count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.total_redactions === 0 && (
            <div className="mb-6 rounded-lg border border-emerald-500/20 bg-emerald-400/5 px-4 py-3 text-xs text-emerald-400">
              No sensitive data detected. This document is clean.
            </div>
          )}

          {/* Redacted text preview */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-200">
                Sanitized Document Preview
              </h2>
              <button
                type="button"
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 transition"
              >
                <ArrowDownTrayIcon className="w-3.5 h-3.5" />
                Download .txt
              </button>
            </div>
            <pre className="font-mono text-xs text-slate-300 bg-slate-800 border border-slate-700 rounded-lg p-4 overflow-auto max-h-64 whitespace-pre-wrap leading-relaxed">
              {result.redacted_text}
            </pre>
          </div>
        </>
      )}
    </div>
  );
}