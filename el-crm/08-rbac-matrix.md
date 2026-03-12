# RBAC Matrix

> Roles, capabilities, and data scoping rules.
> elauth owns role/capability definitions. CRM enforces them.

---

## 1. Architecture

```
elauth (source of truth)                    CRM (enforcement)
┌──────────────────────┐                   ┌──────────────────────┐
│ roles table          │                   │ Backend middleware:   │
│ role_capabilities    │──JWT contains────▶│  Extract capabilities│
│ person_role_assign.  │  capabilities     │  Check per endpoint  │
└──────────────────────┘                   │  Inject data scope   │
                                           │                      │
                                           │ Frontend:            │
                                           │  Hide/show UI based  │
                                           │  on capabilities     │
                                           └──────────────────────┘
```

JWT payload includes capabilities array. CRM middleware reads this — no gRPC call needed per request.

---

## 2. CRM Roles

| Role | Description | Home Screen | Typical Count |
|------|-------------|-------------|---------------|
| **Agent** | Front-line sales. Handles conversations, manages own pipeline. | Inbox | 5-50 per workspace |
| **Manager** | Team lead. Monitors performance, reviews pipeline, manages assignments. | Dashboard | 1-5 per workspace |
| **Admin** | Workspace administrator. Configures CRM settings, manages team. | Dashboard | 1-2 per workspace |
| **Super Admin** | elSapiens internal. Cross-workspace access, provisioning. | System Panel | Internal only |

Roles are hierarchical: Admin has all Manager capabilities, Manager has all Agent capabilities.

---

## 3. Complete Capability Matrix

### Inbox & Conversations

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `inbox.view` | View inbox and conversation list | Yes | Yes | Yes |
| `inbox.view_unassigned` | See unassigned conversation queue | No | Yes | Yes |
| `conversations.view_own` | View own assigned conversations | Yes | Yes | Yes |
| `conversations.view_all` | View all workspace conversations | No | Yes | Yes |
| `conversations.reply` | Send messages in conversations | Yes | Yes | Yes |
| `conversations.assign` | Assign/transfer conversations | Own only | Any | Any |
| `conversations.bulk_assign` | Bulk reassign conversations | No | Yes | Yes |
| `conversations.change_stage` | Change conversation stage | Yes | Yes | Yes |
| `conversations.close` | Close a conversation | Yes | Yes | Yes |
| `conversations.reopen` | Reopen a closed conversation | No | Yes | Yes |
| `conversations.delete` | Delete a conversation | No | No | Yes |
| `conversations.internal_notes` | Add internal notes | Yes | Yes | Yes |

### Contacts & Accounts

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `contacts.view_own` | View own assigned contacts | Yes | Yes | Yes |
| `contacts.view_all` | View all workspace contacts | No | Yes | Yes |
| `contacts.create` | Create new contacts | Yes | Yes | Yes |
| `contacts.edit` | Edit contact information | Yes | Yes | Yes |
| `contacts.delete` | Delete contacts | No | No | Yes |
| `contacts.merge` | Merge duplicate contacts | No | Yes | Yes |
| `contacts.import` | Import contacts from CSV | No | Yes | Yes |
| `contacts.export` | Export contacts to CSV/Excel | No | Yes | Yes |
| `accounts.view` | View accounts | Yes | Yes | Yes |
| `accounts.create` | Create accounts | Yes | Yes | Yes |
| `accounts.edit` | Edit accounts | Yes | Yes | Yes |
| `accounts.delete` | Delete accounts | No | No | Yes |

### Pipeline & Opportunities

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `pipeline.view_own` | View own opportunities on pipeline | Yes | Yes | Yes |
| `pipeline.view_all` | View all opportunities on pipeline | No | Yes | Yes |
| `pipeline.forecast` | View pipeline forecast | No | Yes | Yes |
| `opportunities.create` | Create opportunities | Yes | Yes | Yes |
| `opportunities.edit_own` | Edit own opportunities | Yes | Yes | Yes |
| `opportunities.edit_all` | Edit any opportunity | No | Yes | Yes |
| `opportunities.close` | Close won/lost | Yes | Yes | Yes |
| `opportunities.transfer` | Transfer to another agent | Own only | Any | Any |
| `opportunities.delete` | Delete opportunities | No | No | Yes |

### Activities & Follow-ups

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `activities.view_own` | View own activities | Yes | Yes | Yes |
| `activities.view_all` | View all activities | No | Yes | Yes |
| `activities.create` | Log activities | Yes | Yes | Yes |
| `followups.view_own` | View own follow-ups | Yes | Yes | Yes |
| `followups.view_all` | View team follow-ups | No | Yes | Yes |
| `followups.create` | Create follow-ups | Yes | Yes | Yes |
| `followups.manage_own` | Complete/snooze/cancel own | Yes | Yes | Yes |
| `followups.manage_all` | Manage any agent's follow-ups | No | Yes | Yes |

### Reports & Dashboard

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `dashboard.view` | View manager dashboard | No | Yes | Yes |
| `reports.view_own` | View own performance reports | Yes | Yes | Yes |
| `reports.view_all` | View all reports with team data | No | Yes | Yes |
| `reports.frt` | Access FRT report | No | Yes | Yes |
| `reports.funnel` | Access Sales Funnel report | No | Yes | Yes |
| `reports.aging` | Access Aging report | No | Yes | Yes |
| `reports.activity` | Access Agent Activity report | No | Yes | Yes |
| `reports.outcome` | Access Outcome report | No | Yes | Yes |
| `reports.revenue` | Access Revenue Contribution report | No | Yes | Yes |
| `reports.unqualified` | Access Unqualified Analysis report | No | Yes | Yes |
| `reports.trend` | Access Conversation Trend report | No | Yes | Yes |
| `reports.export` | Export reports to Excel | No | Yes | Yes |

### Assignment

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `assignment.view_history_own` | View own assignment history | Yes | Yes | Yes |
| `assignment.view_history_all` | View all assignment history | No | Yes | Yes |
| `assignment.override` | Override automatic assignment | No | Yes | Yes |
| `assignment.bulk_reassign` | Bulk reassign from one agent | No | Yes | Yes |

### Workflows & Automation

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `workflows.view` | View workflow rules | No | Yes | Yes |
| `workflows.manage` | Create/edit/delete workflow rules | No | No | Yes |
| `workflows.view_logs` | View execution logs | No | Yes | Yes |

### Settings & Configuration

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `settings.view` | View settings pages | No | No | Yes |
| `settings.general` | Edit workspace profile, business hours | No | No | Yes |
| `settings.pipelines` | Configure pipelines and stages | No | No | Yes |
| `settings.custom_fields` | Manage custom field definitions | No | No | Yes |
| `settings.sources` | Manage contact sources | No | No | Yes |
| `settings.dispositions` | Manage disposition/loss reasons | No | No | Yes |
| `settings.assignment_rules` | Configure assignment rules | No | No | Yes |
| `settings.sla` | Configure SLA policies | No | No | Yes |
| `settings.channels` | Configure communication channels | No | No | Yes |
| `settings.templates` | Manage message templates | No | No | Yes |
| `settings.import_export` | Import/export data | No | No | Yes |

### Team Management

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `team.view` | View team members | No | Yes | Yes |
| `team.manage` | Add/remove/change roles | No | No | Yes |
| `team.deactivate` | Deactivate agent | No | No | Yes |

### Notifications

| Capability | Description | Agent | Manager | Admin |
|-----------|-------------|-------|---------|-------|
| `notifications.view_own` | View own notifications | Yes | Yes | Yes |
| `notifications.preferences` | Manage own notification preferences | Yes | Yes | Yes |

---

## 4. Data Scoping Rules

### Agent Scoping

When a user has `*.view_own` but NOT `*.view_all`:

```sql
-- Conversations: only assigned to this agent
SELECT * FROM conversations
WHERE workspace_id = :workspace_id
  AND agent_id = :person_id;

-- Opportunities: only assigned to this agent
SELECT * FROM opportunities
WHERE workspace_id = :workspace_id
  AND agent_id = :person_id;

-- Contacts: only those with conversations/opportunities assigned to this agent
SELECT DISTINCT ch.person_id FROM contact_handles ch
JOIN conversations c ON c.person_id = ch.person_id AND c.workspace_id = ch.workspace_id
WHERE ch.workspace_id = :workspace_id
  AND c.agent_id = :person_id;

-- Follow-ups: only own
SELECT * FROM followups
WHERE workspace_id = :workspace_id
  AND agent_id = :person_id;

-- Activities: only on own conversations/opportunities
SELECT * FROM activities
WHERE workspace_id = :workspace_id
  AND entity_id IN (SELECT id FROM conversations WHERE agent_id = :person_id);
```

### Manager/Admin Scoping

When a user has `*.view_all`:

```sql
-- All workspace data, with optional agent filter
SELECT * FROM conversations
WHERE workspace_id = :workspace_id
  AND (:agent_filter IS NULL OR agent_id = :agent_filter);
```

### Implementation

```go
// In CRM Go backend
func (r *ConversationRepository) List(ctx context.Context, filters Filters) ([]Conversation, error) {
    reqCtx := middleware.GetContext(ctx)

    query := r.db.Where("workspace_id = ?", reqCtx.WorkspaceID)

    // Data scoping based on capabilities
    if !reqCtx.HasCapability("conversations.view_all") {
        query = query.Where("agent_id = ?", reqCtx.PersonID)
    }

    // Apply user filters
    if filters.AgentID != "" {
        query = query.Where("agent_id = ?", filters.AgentID)
    }
    // ... more filters

    return query.Find(&conversations)
}
```

---

## 5. API Enforcement

Every CRM API endpoint declares required capabilities:

```go
// Route registration
crm := router.Group("/api/v1")
crm.Use(AuthMiddleware())  // Validates JWT, sets context

// Conversations
convGroup := crm.Group("/conversations")
convGroup.GET("", RequireCapability("conversations.view_own"), h.ListConversations)
convGroup.POST("/:id/messages", RequireCapability("conversations.reply"), h.SendMessage)
convGroup.PUT("/:id/assign", RequireCapability("conversations.assign"), h.AssignConversation)
convGroup.PUT("/:id/stage", RequireCapability("conversations.change_stage"), h.ChangeStage)

// Reports
reportsGroup := crm.Group("/reports", RequireCapability("reports.view_all"))
reportsGroup.GET("/frt", RequireCapability("reports.frt"), h.FRTReport)

// Settings
settingsGroup := crm.Group("/settings", RequireCapability("settings.view"))
settingsGroup.PUT("/pipelines/:id", RequireCapability("settings.pipelines"), h.UpdatePipeline)
```

If capability check fails → HTTP 403 Forbidden.

---

## 6. UI Enforcement

Frontend uses elsdk's capability checking to conditionally render UI:

```tsx
import { useAuth } from '@elsapiens/hooks';

function InboxPage() {
  const { hasCapability } = useAuth();

  return (
    <div>
      {/* Agent filter only visible to managers */}
      {hasCapability('conversations.view_all') && (
        <AgentFilter />
      )}

      {/* Assign button only for those with permission */}
      {hasCapability('conversations.assign') && (
        <AssignButton />
      )}

      {/* Settings link in sidebar */}
      {hasCapability('settings.view') && (
        <SidebarItem to="/settings" icon="gear" label="Settings" />
      )}
    </div>
  );
}
```

**Important**: UI enforcement is for UX only (hide irrelevant features). API enforcement is the security boundary. Even if UI is bypassed, API will reject unauthorized requests.

---

## 7. Custom Roles (Future)

Admins will be able to create custom roles by selecting individual capabilities:

```
Settings → Team → Roles → [+ Create Custom Role]
  Name: "Senior Agent"
  Base: Agent (pre-selects all Agent capabilities)
  Add: reports.view_all, pipeline.view_all, contacts.export
  Save

→ Creates role in elauth via gRPC
→ Available for assignment to team members
```

---

## 8. Super Admin (elSapiens Internal)

| Capability | Description |
|-----------|-------------|
| `superadmin.workspace_create` | Provision new workspaces |
| `superadmin.workspace_suspend` | Suspend/reactivate workspaces |
| `superadmin.cross_workspace_view` | View data across workspaces |
| `superadmin.system_config` | Modify system-level configuration |
| `superadmin.impersonate` | Act as any user for debugging |

Super Admin bypasses workspace_id RLS by using a special database role. Not exposed in CRM UI — separate admin panel.
