export const rolePermissions: Record<string, string[]> = {
  admin: [
    "Dashboard",
    "Secure Chat",
    "Document Sanitizer",
    "AI Models",
    "Agents",
    "Knowledge Base",
    "Compliance",
    "Alerts",
    "Audit Log",
    "Reports",
    "Settings"
  ],

  developer: [
    "Dashboard",
    "Secure Chat",
    "Document Sanitizer",
    "Knowledge Base"
  ],

  auditor: [
    "Dashboard",
    "Knowledge Base",
    "Compliance",
    "Alerts",
    "Audit Log",
    "Reports"
  ]
};