import { rolePermissions } from "../lib/rbac"

describe("Frontend RBAC", () => {

  test("admin should have access to all sections", () => {
    const adminSections = rolePermissions["admin"]

    expect(adminSections).toContain("Dashboard")
    expect(adminSections).toContain("Secure Chat")
    expect(adminSections).toContain("Document Sanitizer")
    expect(adminSections).toContain("AI Models")
    expect(adminSections).toContain("Agents")
    expect(adminSections).toContain("Knowledge Base")
    expect(adminSections).toContain("Compliance")
    expect(adminSections).toContain("Alerts")
    expect(adminSections).toContain("Audit Log")
    expect(adminSections).toContain("Reports")
    expect(adminSections).toContain("Settings")
  })

  test("developer should only see allowed sections", () => {
    const developerSections = rolePermissions["developer"]

    expect(developerSections).toContain("Dashboard")
    expect(developerSections).toContain("Secure Chat")
    expect(developerSections).toContain("Document Sanitizer")
    expect(developerSections).toContain("Knowledge Base")

    expect(developerSections).not.toContain("Settings")
    expect(developerSections).not.toContain("Agents")
    expect(developerSections).not.toContain("Reports")
  })

  test("auditor should only see monitoring sections", () => {
    const auditorSections = rolePermissions["auditor"]

    expect(auditorSections).toContain("Dashboard")
    expect(auditorSections).toContain("Knowledge Base")
    expect(auditorSections).toContain("Compliance")
    expect(auditorSections).toContain("Alerts")
    expect(auditorSections).toContain("Audit Log")
    expect(auditorSections).toContain("Reports")

    expect(auditorSections).not.toContain("Secure Chat")
    expect(auditorSections).not.toContain("Document Sanitizer")
    expect(auditorSections).not.toContain("Settings")
  })

})