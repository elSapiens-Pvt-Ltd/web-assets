# API Contracts

> REST endpoints, gRPC definitions, WebSocket events.

---

## 1. Design Principles

- **REST** for frontend ↔ CRM backend communication
- **gRPC + Protobuf** for CRM ↔ elauth and CRM ↔ accounts-api
- **NATS events** for async inter-service (CRM ↔ Communication Gateway)
- **WebSocket** for real-time frontend updates
- **workspace_id** extracted from JWT on every request (never passed by client)
- **Capability-based auth** — each endpoint declares required capability
- **JSON** request/response bodies, `application/json` content type

---

## 2. Authentication

All REST endpoints require `Authorization: Bearer <jwt>` header.

```
Request → Middleware:
  1. Extract JWT from header
  2. Verify HS256 signature (shared secret with elauth)
  3. Check expiry
  4. Extract: person_id, workspace_id, role, capabilities
  5. Set PostgreSQL session: app.current_workspace_id
  6. Attach to request context
  7. Route to handler → handler checks capability
```

---

## 3. Standard Response Format

### Success
```json
{
  "success": true,
  "data": { ... },
  "pagination": {                    // only on list endpoints
    "page": 1,
    "per_page": 25,
    "total": 342,
    "total_pages": 14
  }
}
```

### Error
```json
{
  "success": false,
  "error": {
    "code": "CONVERSATION_NOT_FOUND",
    "message": "Conversation not found",
    "details": {}                    // optional, validation errors etc.
  }
}
```

### HTTP Status Codes
| Code | Usage |
|------|-------|
| 200 | Success (GET, PUT, DELETE) |
| 201 | Created (POST) |
| 400 | Bad request / validation error |
| 401 | JWT invalid or expired |
| 403 | Capability check failed |
| 404 | Resource not found (within workspace) |
| 409 | Conflict (duplicate, concurrent modification) |
| 429 | Rate limited |
| 500 | Server error |

---

## 4. REST API Endpoints

### Conversations

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/conversations` | `conversations.view_own` | List conversations (filtered, paginated) |
| GET | `/api/v1/conversations/:id` | `conversations.view_own` | Get conversation detail |
| PUT | `/api/v1/conversations/:id/stage` | `conversations.change_stage` | Change conversation stage |
| PUT | `/api/v1/conversations/:id/assign` | `conversations.assign` | Assign/transfer conversation |
| PUT | `/api/v1/conversations/:id/close` | `conversations.close` | Close conversation |
| PUT | `/api/v1/conversations/:id/reopen` | `conversations.reopen` | Reopen closed conversation |
| POST | `/api/v1/conversations/bulk-assign` | `conversations.bulk_assign` | Bulk reassign conversations |

**GET /api/v1/conversations** — Query params:
```
status=open|pending|closed   agent_id=uuid   stage_id=uuid
channel=whatsapp|voice|email source_id=uuid  priority=normal|high|urgent
sla_status=ok|warning|breached   unread=true|false
search=text   sort=last_activity|created_at|priority   order=desc|asc
page=1   per_page=25   preset=today|this_week|this_month|...
start_date=2026-03-01   end_date=2026-03-12
```

**PUT /api/v1/conversations/:id/stage** — Request:
```json
{ "stage_id": "uuid", "disposition": "not_interested", "note": "optional" }
```

**PUT /api/v1/conversations/:id/assign** — Request:
```json
{ "agent_id": "uuid", "reason": "agent_overloaded", "note": "Customer prefers Hindi", "notify": true }
```

### Messages

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/conversations/:id/messages` | `conversations.view_own` | List messages (paginated, newest first) |
| POST | `/api/v1/conversations/:id/messages` | `conversations.reply` | Send message |
| PUT | `/api/v1/conversations/:id/messages/read` | `conversations.view_own` | Mark messages as read |

**POST /api/v1/conversations/:id/messages** — Request:
```json
{
  "channel": "whatsapp",
  "content_type": "text",
  "content": { "body": "Hi Rahul! Here's the updated pricing." },
  "is_internal": false
}
```

Template message:
```json
{
  "channel": "whatsapp",
  "content_type": "template",
  "content": {
    "template_id": "uuid",
    "variables": { "1": "Rahul", "2": "Grade A Turmeric" }
  }
}
```

Media message:
```json
{
  "channel": "whatsapp",
  "content_type": "image",
  "content": {
    "media_url": "https://s3.../quote.pdf",
    "caption": "Here's our latest price list"
  }
}
```

### Contacts (Proxied from accounts-api)

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/contacts` | `contacts.view_own` | List contacts (CRM enriched) |
| GET | `/api/v1/contacts/:personId` | `contacts.view_own` | Get contact detail (enriched) |
| POST | `/api/v1/contacts` | `contacts.create` | Create contact (→ accounts-api) |
| PUT | `/api/v1/contacts/:personId` | `contacts.edit` | Update contact (→ accounts-api) |
| GET | `/api/v1/contacts/:personId/handles` | `contacts.view_own` | List contact handles |
| POST | `/api/v1/contacts/:personId/handles` | `contacts.edit` | Add handle |
| POST | `/api/v1/contacts/merge` | `contacts.merge` | Merge duplicate contacts |
| GET | `/api/v1/contacts/search` | `contacts.view_own` | Search contacts |

### Accounts (Proxied from accounts-api)

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/accounts` | `accounts.view` | List accounts (CRM enriched) |
| GET | `/api/v1/accounts/:entityId` | `accounts.view` | Get account detail |
| POST | `/api/v1/accounts` | `accounts.create` | Create account (→ accounts-api) |
| PUT | `/api/v1/accounts/:entityId` | `accounts.edit` | Update account |

### Pipeline & Opportunities

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/pipelines` | `pipeline.view_own` | List pipelines |
| GET | `/api/v1/pipelines/:id` | `pipeline.view_own` | Get pipeline with stages |
| GET | `/api/v1/pipelines/:id/opportunities` | `pipeline.view_own` | List opportunities in pipeline |
| GET | `/api/v1/pipelines/:id/forecast` | `pipeline.forecast` | Pipeline forecast |
| POST | `/api/v1/opportunities` | `opportunities.create` | Create opportunity |
| PUT | `/api/v1/opportunities/:id` | `opportunities.edit_own` | Update opportunity |
| PUT | `/api/v1/opportunities/:id/stage` | `opportunities.edit_own` | Move to stage |
| PUT | `/api/v1/opportunities/:id/close` | `opportunities.close` | Close won/lost |
| PUT | `/api/v1/opportunities/:id/assign` | `opportunities.transfer` | Transfer opportunity |

**PUT /api/v1/opportunities/:id/close** — Request:
```json
{
  "outcome": "won",
  "won_value": 50000,
  "close_date": "2026-03-12",
  "notes": "PO received"
}
```
Or for lost:
```json
{
  "outcome": "lost",
  "loss_reason": "price_too_high",
  "competitor": "ABC Trading",
  "notes": "Competitor offered 10% lower"
}
```

### Follow-Ups

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/followups` | `followups.view_own` | List follow-ups (filtered) |
| POST | `/api/v1/followups` | `followups.create` | Create follow-up |
| PUT | `/api/v1/followups/:id` | `followups.manage_own` | Update follow-up |
| PUT | `/api/v1/followups/:id/complete` | `followups.manage_own` | Mark complete |
| PUT | `/api/v1/followups/:id/snooze` | `followups.manage_own` | Snooze to new date |
| PUT | `/api/v1/followups/:id/cancel` | `followups.manage_own` | Cancel follow-up |

### Activities

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/activities` | `activities.view_own` | List activities (by entity) |
| POST | `/api/v1/activities` | `activities.create` | Log activity |

### Reports

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/reports/frt/agents` | `reports.frt` | FRT per agent |
| GET | `/api/v1/reports/frt/summary` | `reports.frt` | FRT summary |
| GET | `/api/v1/reports/frt` | `reports.frt` | FRT combined |
| POST | `/api/v1/reports/funnel` | `reports.funnel` | Sales funnel |
| GET | `/api/v1/reports/aging` | `reports.aging` | Aging report |
| POST | `/api/v1/reports/activity` | `reports.activity` | Agent activity |
| POST | `/api/v1/reports/outcome` | `reports.outcome` | Outcome report |
| POST | `/api/v1/reports/revenue` | `reports.revenue` | Revenue contribution |
| POST | `/api/v1/reports/unqualified` | `reports.unqualified` | Unqualified analysis |
| POST | `/api/v1/reports/trend` | `reports.trend` | Conversation trend |

All report endpoints accept: `start_date`, `end_date`, `preset`, `agent_ids[]`, `source_ids[]`.

### Report Exports

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| POST | `/api/v1/exports/:reportType` | `reports.export` | Generate Excel (returns file path) |
| POST | `/api/v1/exports/download` | `reports.export` | Download generated file |

Report types: `frt`, `funnel`, `aging`, `activity`, `outcome`, `revenue`, `unqualified`, `trend`.

### Dashboard

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/dashboard/summary` | `dashboard.view` | All dashboard widgets |
| GET | `/api/v1/dashboard/pipeline` | `dashboard.view` | Pipeline summary |
| GET | `/api/v1/dashboard/frt` | `dashboard.view` | FRT overview |
| GET | `/api/v1/dashboard/activity` | `dashboard.view` | Team activity today |
| GET | `/api/v1/dashboard/sla` | `dashboard.view` | SLA compliance |

### Settings

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/settings/:key` | `settings.view` | Get config by key |
| PUT | `/api/v1/settings/:key` | `settings.*` | Update config |
| GET | `/api/v1/settings/pipelines` | `settings.pipelines` | List pipelines with stages |
| POST | `/api/v1/settings/pipelines` | `settings.pipelines` | Create pipeline |
| PUT | `/api/v1/settings/pipelines/:id` | `settings.pipelines` | Update pipeline |
| DELETE | `/api/v1/settings/pipelines/:id` | `settings.pipelines` | Delete pipeline |
| POST | `/api/v1/settings/pipelines/:id/stages` | `settings.pipelines` | Add stage |
| PUT | `/api/v1/settings/pipelines/:id/stages/:sid` | `settings.pipelines` | Update stage |
| PUT | `/api/v1/settings/pipelines/:id/stages/reorder` | `settings.pipelines` | Reorder stages |
| GET | `/api/v1/settings/custom-fields` | `settings.custom_fields` | List field definitions |
| POST | `/api/v1/settings/custom-fields` | `settings.custom_fields` | Create field |
| PUT | `/api/v1/settings/custom-fields/:id` | `settings.custom_fields` | Update field |
| DELETE | `/api/v1/settings/custom-fields/:id` | `settings.custom_fields` | Delete field |
| GET | `/api/v1/settings/sources` | `settings.sources` | List contact sources |
| POST | `/api/v1/settings/sources` | `settings.sources` | Create source |
| PUT | `/api/v1/settings/sources/:id` | `settings.sources` | Update source |
| GET | `/api/v1/settings/assignment-rules` | `settings.assignment_rules` | List rules |
| POST | `/api/v1/settings/assignment-rules` | `settings.assignment_rules` | Create rule |
| PUT | `/api/v1/settings/assignment-rules/:id` | `settings.assignment_rules` | Update rule |
| PUT | `/api/v1/settings/assignment-rules/reorder` | `settings.assignment_rules` | Reorder rules |
| GET | `/api/v1/settings/workflows` | `workflows.view` | List workflow rules |
| POST | `/api/v1/settings/workflows` | `workflows.manage` | Create workflow rule |
| PUT | `/api/v1/settings/workflows/:id` | `workflows.manage` | Update workflow rule |
| DELETE | `/api/v1/settings/workflows/:id` | `workflows.manage` | Delete workflow rule |
| POST | `/api/v1/settings/workflows/:id/dry-run` | `workflows.manage` | Test rule |
| GET | `/api/v1/settings/workflows/:id/logs` | `workflows.view_logs` | Execution logs |
| GET | `/api/v1/settings/channels` | `settings.channels` | List channels |
| PUT | `/api/v1/settings/channels/:type` | `settings.channels` | Update channel config |
| POST | `/api/v1/settings/channels/:type/test` | `settings.channels` | Test channel |
| GET | `/api/v1/settings/templates` | `settings.templates` | List templates |
| POST | `/api/v1/settings/templates` | `settings.templates` | Create template |
| PUT | `/api/v1/settings/templates/:id` | `settings.templates` | Update template |
| GET | `/api/v1/settings/team` | `team.view` | List team members |
| POST | `/api/v1/settings/team` | `team.manage` | Invite member |
| PUT | `/api/v1/settings/team/:personId` | `team.manage` | Update member settings |
| PUT | `/api/v1/settings/team/:personId/deactivate` | `team.deactivate` | Deactivate agent |
| GET | `/api/v1/settings/audit-log` | `settings.view` | Config change audit log |

### Notifications

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/notifications` | `notifications.view_own` | List notifications |
| PUT | `/api/v1/notifications/:id/read` | `notifications.view_own` | Mark as read |
| PUT | `/api/v1/notifications/read-all` | `notifications.view_own` | Mark all as read |
| GET | `/api/v1/notifications/preferences` | `notifications.preferences` | Get preferences |
| PUT | `/api/v1/notifications/preferences` | `notifications.preferences` | Update preferences |

### Search

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/search` | `inbox.view` | Global search (contacts, conversations, accounts) |

Query params: `q=search term`, `type=all|contacts|conversations|accounts`, `limit=10`.

### Uploads

| Method | Path | Capability | Description |
|--------|------|-----------|-------------|
| GET | `/api/v1/uploads/presigned-url` | `conversations.reply` | Get S3 presigned upload URL |

---

## 5. gRPC Services

### CRM Exposes (for other services to call)

```protobuf
service CRMService {
  rpc GetConversation(GetConversationRequest) returns (Conversation);
  rpc GetConversationByHandle(GetConversationByHandleRequest) returns (Conversation);
  rpc CreateConversation(CreateConversationRequest) returns (Conversation);
  rpc GetContactCRMData(GetContactCRMDataRequest) returns (ContactCRMData);
}
```

### CRM Consumes

**From elauth** (port 6000): ValidateToken, GetPerson, GetPersonRoles, GetWorkspaceMembers, AddWorkspaceMember, UpdatePersonRole, RemoveWorkspaceMember, ListWorkspaces.

**From accounts-api** (port 21001): GetPerson, GetPersons, SearchPersons, CreatePerson, UpdatePerson, GetPersonByHandle, GetEntity, GetEntities, CreateEntity, UpdateEntity, CreateMembership, MergePersons.

**From Communication Gateway** (port 6002): GetTemplates, GetChannelHealth, TestChannel.

---

## 6. WebSocket Events

### Connection

```
ws://crm.example.com/ws?token=<jwt>

On connect:
  → Server validates JWT
  → Subscribes client to workspace_id channel
  → Subscribes to agent-specific events (for their person_id)
```

### Events Pushed to Frontend

| Event | Payload | When |
|-------|---------|------|
| `conversation.new_message` | `{ conversation_id, message }` | New inbound/outbound message |
| `conversation.updated` | `{ conversation_id, changes }` | Stage change, assignment, close |
| `conversation.new` | `{ conversation }` | New conversation created |
| `message.status_updated` | `{ message_id, status }` | Delivery status change |
| `notification.new` | `{ notification }` | New notification |
| `call.incoming` | `{ conversation_id, caller }` | Inbound call ringing |
| `agent.presence` | `{ person_id, status }` | Agent online/offline |
| `followup.due` | `{ followup }` | Follow-up became due |

### Client Actions

| Action | Payload | Purpose |
|--------|---------|---------|
| `subscribe` | `{ conversation_id }` | Subscribe to specific conversation updates |
| `unsubscribe` | `{ conversation_id }` | Unsubscribe from conversation |
| `typing` | `{ conversation_id, is_typing }` | Typing indicator (future) |
| `presence` | `{ status: "online" }` | Update agent presence |

---

## 7. Pagination

All list endpoints support:
```
?page=1&per_page=25

Default: page=1, per_page=25
Max per_page: 100
```

Response includes:
```json
{
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 342,
    "total_pages": 14,
    "has_next": true,
    "has_prev": false
  }
}
```

### Cursor-Based (for messages)

Messages use cursor pagination for efficient infinite scroll:
```
GET /api/v1/conversations/:id/messages?before=<message_uuid>&limit=50
```
