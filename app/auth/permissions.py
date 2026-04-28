"""
RBAC Permission Policy
----------------------
Defines which roles are allowed to perform which actions.
Used by the RBAC enforcement layer.
"""

# Role → Allowed Permissions
ROLE_PERMISSIONS = {
    # Full administrative access
    "admin": [
        "ai.query",
        "logs.read",
        "reports.read",
        "metrics.read",
        "documents.manage",
    ],
    # Developers can interact with the AI system
    "developer": ["ai.query", "metrics.read", "documents.read"],
    # Auditors can view logs and reports but cannot interact with AI
    "auditor": ["logs.read", "reports.read", "metrics.read"],
}
