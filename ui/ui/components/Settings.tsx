'use client';

import React, { useState } from 'react';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('Profile');
  const [twoFactor, setTwoFactor] = useState(true);
  const [emailNotif, setEmailNotif] = useState(true);

  const tabs = ['Profile', 'Notifications', 'Security', 'Appearance', 'Integrations', 'System'];

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-100 mb-1">Settings</h1>
      <p className="text-sm text-slate-400 mb-6">
        Manage your account and platform settings
      </p>

      <div className="flex gap-6">
        {/* LEFT SIDEBAR */}
        <div className="w-64 bg-slate-900 border border-slate-800 rounded-xl p-3">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition ${
                activeTab === tab
                  ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-500/20'
                  : 'text-slate-400 hover:bg-slate-800'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* MAIN PANEL */}
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-8">
          <h2 className="text-xl font-semibold text-slate-100 mb-6">
            Profile Settings
          </h2>

          <h3 className="text-sm font-semibold text-slate-200 mb-4">
            Personal Information
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <LabeledInput label="Full Name" defaultValue="Olivia Carter" />
            <LabeledInput label="Email Address" defaultValue="olivia.carter@cyberoracle.com" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <LabeledSelect label="Role" options={['Admin','Manager','Analyst','Developer']} />
            <LabeledSelect label="Department" options={['Engineering','Security','Operations','Compliance']} />
          </div>

          <h3 className="text-sm font-semibold text-slate-200 mb-4">
            Preferences
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <LabeledSelect label="Language" options={['English','Spanish','French']} />
            <LabeledSelect label="Timezone" options={['UTC','EST','CST','PST']} />
          </div>

          <div className="space-y-6 mb-8">
            <Toggle
              title="Two-Factor Authentication"
              description="Enable two-factor authentication for your account"
              enabled={twoFactor}
              onToggle={() => setTwoFactor(!twoFactor)}
            />

            <Toggle
              title="Email Notifications"
              description="Receive email notifications for important updates"
              enabled={emailNotif}
              onToggle={() => setEmailNotif(!emailNotif)}
            />
          </div>

          <button className="bg-cyan-500 hover:bg-cyan-600 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

function LabeledInput({ label, defaultValue }: { label: string; defaultValue: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-200 mb-1">{label}</label>
      <input
        defaultValue={defaultValue}
        className="w-full border border-slate-700 bg-slate-950 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
      />
    </div>
  );
}

function LabeledSelect({ label, options }: { label: string; options: string[] }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-200 mb-1">{label}</label>
      <select className="w-full border border-slate-700 bg-slate-950 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500">
        {options.map((opt) => (
          <option key={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}

function Toggle({ title, description, enabled, onToggle }: any) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-slate-100">{title}</p>
        <p className="text-xs text-slate-400">{description}</p>
      </div>

      <button
        onClick={onToggle}
        className={`w-11 h-6 rounded-full transition ${
          enabled ? 'bg-cyan-500' : 'bg-slate-700'
        }`}
      >
        <div
          className={`h-5 w-5 bg-white rounded-full shadow transform transition ${
            enabled ? 'translate-x-5' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
}