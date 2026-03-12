# User & Role Management

> Role: Admin
> Trigger: Admin needs to add users, assign roles, or manage permissions
> Primary screen: Settings → Team

---

## Flow Summary

User management is split between **elauth** (identity, authentication, workspace membership) and **CRM** (CRM-specific role assignment, capability scoping). Admin uses the CRM settings to manage their team's CRM access.

---

## Architecture: Who Owns What

```
elauth (source of truth for identity)
├── Person identity (name, email, phone)
├── Authentication (password, MFA)
├── Workspace membership (which workspaces a person belongs to)
├── Roles & capabilities (RBAC definitions)
└── Role assignments (person → role in workspace)

CRM (consumes from elauth)
├── Displays team members with CRM role context
├── CRM-specific settings (agent capacity, assignment preferences)
├── Capability-based feature gating in CRM UI
└── Agent availability / online status
```

---

## Flow: Add a New Team Member

```
Admin → Settings → Team → "+ Add Member"
  → Search by email or name
  → Two scenarios:

  A. Person already in elauth (exists in another workspace or service):
      → Search returns match
      → Admin clicks "Invite to Workspace"
      → elauth adds workspace membership
      → Admin assigns CRM role: Agent | Manager | Admin
      → Person receives invite email (via Notification Hub)
      → On first login → person sees this workspace in OrgSwitcher

  B. Person is new to the platform:
      → No search results
      → Admin clicks "Create New User"
      → Form: Name, Email, Phone (optional)
      → Assign role: Agent | Manager | Admin
      → elauth creates: person + credentials + workspace membership + role
      → Person receives welcome email with login link
      → On first login → set password → MFA setup (if required)
```

---

## CRM Roles & Capabilities

Roles are defined in elauth. CRM interprets capabilities for feature access.

### Default CRM Roles

| Role | Description | Key Capabilities |
|------|-------------|-----------------|
| **Agent** | Front-line sales | inbox.view, inbox.reply, contacts.view, contacts.edit, pipeline.view_own, pipeline.manage_own, activities.create, followups.manage_own, reports.view_own |
| **Manager** | Team lead | All agent capabilities + pipeline.view_all, pipeline.manage_all, reports.view_all, assignment.override, team.view, exports.download |
| **Admin** | Workspace admin | All manager capabilities + settings.manage, pipeline.configure, custom_fields.manage, assignment_rules.manage, workflows.manage, channels.configure, team.manage |

### Capability Details

```
Capability Scoping:
  *.view_own    → Agent sees only their assigned conversations/opportunities
  *.view_all    → Manager sees all team data
  *.manage_own  → Agent can modify their own records
  *.manage_all  → Manager can modify any team member's records

Example: pipeline.view_own
  → Agent opens Pipeline → sees only opportunities assigned to them
  → SQL: WHERE workspace_id = ? AND agent_id = ?

Example: pipeline.view_all
  → Manager opens Pipeline → sees all opportunities in workspace
  → SQL: WHERE workspace_id = ?
  → Can filter by agent
```

---

## Team Management View

```
Settings → Team

┌─────────────────────────────────────────────────────────────────┐
│ Team Members (12)                              [+ Add Member]   │
├─────────────────────────────────────────────────────────────────┤
│ Name           Email                  Role      Status   [⚙]   │
│ ─────────────────────────────────────────────────────────────── │
│ Priya Sharma   priya@company.com     Agent     Online   [⚙]   │
│ Ravi Kumar     ravi@company.com      Agent     Offline  [⚙]   │
│ Ankit Patel    ankit@company.com     Agent     Online   [⚙]   │
│ Meera Joshi    meera@company.com     Manager   Online   [⚙]   │
│ Admin User     admin@company.com     Admin     Online   [⚙]   │
│ ...                                                             │
└─────────────────────────────────────────────────────────────────┘

[⚙] per user:
  - Change CRM role
  - Set agent capacity (max open conversations: 50 default)
  - Set assignment preferences (available for auto-assignment: yes/no)
  - View activity summary
  - Deactivate from CRM (keeps elauth account, removes from CRM assignment pool)
```

---

## Flow: Change User Role

```
Admin → Settings → Team → clicks [⚙] on Ravi → "Change Role"
  → Current role: Agent
  → New role: Manager
  → Confirm: "Ravi will gain access to team reports, pipeline overview, and assignment controls."
  → Save
  → elauth gRPC: UpdatePersonRoleAssignment(person_id, workspace_id, new_role)
  → Ravi's next page load reflects new capabilities
  → Ravi sees: Manager dashboard, team reports, full pipeline view
```

---

## Flow: Deactivate Agent

```
Admin → Settings → Team → clicks [⚙] on Ravi → "Deactivate"
  → Warning: "Ravi has 15 open conversations and 8 opportunities assigned."
  → Options:
      ○ Reassign all to: [Select agent/manager ▾]
      ○ Leave unassigned (manager will pick up)
      ○ Distribute via assignment rules
  → Admin selects "Reassign all to: Priya"
  → Confirm
  → System:
      - Bulk reassigns 15 conversations + 8 opportunities to Priya
      - Logs assignment history for each
      - Marks Ravi as inactive in CRM (cannot receive new assignments)
      - Ravi's elauth account remains active (can access other services)
      - Priya notified: "15 conversations transferred from Ravi"
```

---

## Custom Role Creation (Future)

```
Admin → Settings → Team → Roles → "+ Create Role"
  → Role name: "Senior Agent"
  → Base on: Agent (copy capabilities)
  → Add capabilities:
      + reports.view_all (can see team reports)
      + pipeline.view_all (can see full pipeline)
  → Remove capabilities:
      - (none)
  → Save
  → Role available for assignment

Note: Custom roles are defined in elauth via gRPC.
CRM reads capabilities from elauth and enforces in UI + API.
```

---

## Data Flow

```
Admin action in CRM Settings
  → CRM backend calls elauth gRPC:
      AddWorkspaceMember(workspace_id, person_id, role_id)
      UpdatePersonRoleAssignment(person_id, workspace_id, role_id)
      RemoveWorkspaceMember(workspace_id, person_id)
  → elauth updates its PostgreSQL tables
  → CRM stores CRM-specific settings locally:
      agent_settings (workspace_id, person_id, max_capacity, auto_assign, status)
```
