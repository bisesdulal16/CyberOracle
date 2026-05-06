import { rolePermissions } from "./rbac"
import { getRole } from "./auth"

/**
 * Check if the current user has a permission
 */
export function can(permission: string): boolean {
  const role = getRole()

  if (!role) return false

  return rolePermissions[role]?.includes(permission) ?? false
}