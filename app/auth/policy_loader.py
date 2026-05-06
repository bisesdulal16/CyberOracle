"""
Policy Loader
-------------
Loads RBAC policy configuration from policy.yaml.

This module allows the API gateway to dynamically read roles
and permissions defined in the policy file.
"""

import yaml
from pathlib import Path

# Path to the YAML policy file
POLICY_PATH = Path("docs/threat-modeling/policy.yaml")

# Cache the policy to avoid reading the file on every request
_policy_cache = None


def load_policy():
    """
    Load the YAML policy file and cache it.
    """
    global _policy_cache

    if _policy_cache is None:
        with open(POLICY_PATH, "r") as f:
            _policy_cache = yaml.safe_load(f)

    return _policy_cache


def get_role_permissions(role: str):
    """
    Return the permissions assigned to a role
    based on the loaded policy file.
    """

    policy = load_policy()

    roles = policy.get("roles", {})

    role_data = roles.get(role, {})

    return role_data.get("permissions", [])
