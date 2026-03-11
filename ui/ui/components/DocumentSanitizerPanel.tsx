'use client';

import React, { useRef, useState } from 'react';
import { apiFetch } from '../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

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

export default function DocumentSanitizerPanel() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [result, setResult] = useState<SanitizeResult | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    setResult(null);
    setErrorMessage('');
    setUploadState('idle');
  }

  async function handleScan() {
    if (!selectedFile) return;

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
      <h1 className="text-2xl font-semibold text-slate-900 mb-1">
        Document Sanitizer
      </h1>
      <p className="text-sm text-slate-500 mb-6">
        Upload a PDF or DOCX file. CyberOracle will scan it for sensitive data
        (SSNs, emails, credit cards, API keys) and return a redacted version
        safe to share or send to an LLM.
      </p>

      {/* Upload card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-6">
        <div
          className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center cursor-pointer hover:border-sky-400 hover:bg-sky-50 transition"
          onClick={() => fileInputRef.current?.click()}
        >
          <p className="text-sm font-medium text-slate-700 mb-1">
            Click to select a file
          </p>
          <p className="text-xs text-slate-400">PDF or DOCX · Max 10 MB</p>

          {selectedFile && (
            <p className="mt-3 text-xs font-semibold text-sky-700 bg-sky-100 inline-block px-3 py-1 rounded-full">
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="flex gap-3 mt-4">
          <button
            type="button"
            disabled={!selectedFile || uploadState === 'uploading'}
            onClick={handleScan}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-sky-600 text-white hover:bg-sky-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            {uploadState === 'uploading' ? 'Scanning…' : 'Scan & Redact'}
          </button>

          {(selectedFile || result) && (
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {uploadState === 'error' && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">
          {errorMessage}
        </div>
      )}

      {/* Results */}
      {uploadState === 'done' && result && (
        <>
          {/* Summary row */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm text-center">
              <p className="text-xs text-slate-500 mb-1">File type</p>
              <p className="text-lg font-semibold text-slate-900">
                {result.file_type}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm text-center">
              <p className="text-xs text-slate-500 mb-1">Total redactions</p>
              <p
                className={`text-lg font-semibold ${result.total_redactions > 0 ? 'text-red-600' : 'text-emerald-600'}`}
              >
                {result.total_redactions}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm text-center">
              <p className="text-xs text-slate-500 mb-1">Types detected</p>
              <p className="text-lg font-semibold text-slate-900">
                {result.findings.length}
              </p>
            </div>
          </div>

          {/* Findings breakdown */}
          {result.findings.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-6">
              <h2 className="text-sm font-semibold text-slate-900 mb-3">
                Redaction Breakdown
              </h2>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-100">
                    <th className="pb-2 font-medium">Entity type</th>
                    <th className="pb-2 font-medium text-right">Occurrences</th>
                  </tr>
                </thead>
                <tbody>
                  {result.findings.map((f) => (
                    <tr
                      key={f.type}
                      className="border-b border-slate-50 last:border-0"
                    >
                      <td className="py-2">
                        <span className="inline-block bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-semibold text-[10px]">
                          {f.type}
                        </span>
                      </td>
                      <td className="py-2 text-right font-semibold text-slate-800">
                        {f.count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.total_redactions === 0 && (
            <div className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-700">
              No sensitive data detected. This document is clean.
            </div>
          )}

          {/* Redacted text preview */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-900">
                Sanitized Document Preview
              </h2>
              <button
                type="button"
                onClick={handleDownload}
                className="px-3 py-1.5 text-[11px] font-semibold rounded-lg bg-slate-800 text-white hover:bg-slate-700 transition"
              >
                Download .txt
              </button>
            </div>
            <pre className="text-xs text-slate-700 bg-slate-50 rounded-lg p-4 overflow-auto max-h-64 whitespace-pre-wrap font-mono leading-relaxed border border-slate-100">
              {result.redacted_text}
            </pre>
          </div>
        </>
      )}
    </div>
  );
}
