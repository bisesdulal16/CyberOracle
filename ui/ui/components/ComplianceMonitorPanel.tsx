'use client';

import React from 'react';
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';

const GRAFANA_URL = process.env.NEXT_PUBLIC_GRAFANA_URL ?? 'http://localhost:3000';
const DASHBOARD_UID = process.env.NEXT_PUBLIC_GRAFANA_DASHBOARD_UID || 'YOUR_UID';

export default function ComplianceMonitorPanel() {
  return (
    <div className="max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-slate-100">
          CyberOracle Compliance Monitor & ISCM
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          This page provides real-time monitoring of HIPAA and FERPA compliance,
          DLP enforcement, and ISCM (Information Security Continuous Monitoring).
        </p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Compliance Overview</h2>
        <p className="text-slate-400 mb-4">
          Monitor the compliance status of your AI systems against regulatory frameworks.
          The dashboard shows real-time metrics for DLP enforcement, compliance scores,
          and security events.
        </p>

        <div className="flex items-center gap-3">
          <a
            href={GRAFANA_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 hover:bg-slate-700 transition"
          >
            <ArrowTopRightOnSquareIcon className="w-4 h-4" />
            Open Compliance Dashboard
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-2">HIPAA Compliance</h3>
          <p className="text-xs text-slate-400">Monitoring data protection and privacy controls</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-2">FERPA Compliance</h3>
          <p className="text-xs text-slate-400">Ensuring student data privacy and access controls</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-2">DLP Enforcement</h3>
          <p className="text-xs text-slate-400">Real-time detection and protection of sensitive data</p>
        </div>
      </div>

      {/* Grafana Dashboard Embed */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Compliance Dashboard</h2>
        <div className="border border-slate-700 rounded-lg overflow-hidden">
          <iframe
            src={`${GRAFANA_URL}/d/${DASHBOARD_UID}?orgId=1&kiosk`}
            width="100%"
            height="900px"
            frameBorder="0"
            title="Compliance Dashboard"
            className="w-full"
          />
        </div>
        <p className="text-xs text-slate-400 mt-2 text-center">
          If dashboard does not load, enable Grafana embedding or open in new tab.
        </p>
      </div>
    </div>
  );
}