# Integration Map

> How el-CRM connects to all ecosystem services.
> Protocols, data flows, sequence diagrams.

---

## 1. Service Topology

```
                            ┌─────────────────┐
                            │   API Gateway    │
                            │ JWT validation   │
                            │ Rate limiting    │
                            │ Routing          │
                            └────────┬────────┘
                                     │ HTTP
                     ┌───────────────┼───────────────┐
                     │               │               │
              ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
              │  CRM Service │ │  Comm GW    │ │ Other Svcs  │
              │  Go          │ │  Go         │ │             │
              │  HTTP :8090  │ │  HTTP :8091 │ │             │
              │  gRPC :6001  │ │  gRPC :6002 │ │             │
              │  WS   :8092  │ │             │ │             │
              └──────┬───┬──┘ └──────┬──────┘ └─────────────┘
                     │   │           │
          ┌──────────┘   │           │
          │ gRPC         │ gRPC      │ Channel APIs
          ▼              ▼           ▼
   ┌──────────┐   ┌──────────┐   ┌──────────────────┐
   │ elauth   │   │accounts  │   │ WhatsApp Cloud API│
   │ Go       │   │-api      │   │ Smartflo Voice    │
   │ gRPC:6000│   │NestJS    │   │ SES Email         │
   │ HTTP:8080│   │gRPC:21001│   │ JustDial/FB/IM    │
   │ PgSQL    │   │HTTP:11001│   └──────────────────┘
   └──────────┘   │MongoDB   │
                  └──────────┘

   ┌──────────────────────────────────────────┐
   │              NATS Event Bus              │
   │  CRM ←→ Comm GW ←→ Notification Hub    │
   │  CRM ←→ Commerce ←→ Ops Management     │
   └──────────────────────────────────────────┘

   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ PgSQL    │   │ Redis    │   │ S3       │
   │ CRM data │   │ Cache    │   │ Files    │
   │ + RLS    │   │ Sessions │   │ Media    │
   └──────────┘   └──────────┘   └──────────┘
```

---

## 2. elauth Integration

### Purpose
Authentication, authorization, user management, workspace management.

### Protocol
gRPC on port 6000. CRM implements an `auth-bridge` client.

### JWT Validation Flow

```
Request arrives at CRM
  │
  ├─ Extract Authorization: Bearer <token> header
  │
  ├─ Decode JWT (HS256, shared secret with elauth)
  │  Payload: {
  │    "sub": "person_uuid",
  │    "workspace_id": "ws_uuid",
  │    "reseller_id": "reseller_uuid",
  │    "role": "agent",
  │    "capabilities": ["inbox.view", "contacts.view", ...],
  │    "exp": 1741900800
  │  }
  │
  ├─ Verify: signature valid, not expired, workspace_id present
  │
  ├─ Set request context:
  │    ctx.PersonID = sub
  │    ctx.WorkspaceID = workspace_id
  │    ctx.Role = role
  │    ctx.Capabilities = capabilities
  │
  ├─ Set PostgreSQL session variable:
  │    SET app.current_workspace_id = 'ws_uuid'
  │    (enables RLS policies)
  │
  └─ Proceed to handler
```

### gRPC Calls CRM Makes to elauth

| Method | When | Purpose |
|--------|------|---------|
| `ValidateToken(token)` | Optional — if CRM doesn't share JWT secret | Server-side token validation |
| `GetPersonRoles(person_id, workspace_id)` | On role check | Get current roles and capabilities |
| `GetWorkspaceMembers(workspace_id)` | Team management page | List all users in workspace |
| `AddWorkspaceMember(workspace_id, person_id, role_id)` | Admin adds user | Add person to workspace |
| `UpdatePersonRole(person_id, workspace_id, role_id)` | Admin changes role | Update role assignment |
| `RemoveWorkspaceMember(workspace_id, person_id)` | Admin deactivates user | Remove from workspace |
| `GetPerson(person_id)` | Display agent name | Get person details |
| `ListWorkspaces(person_id)` | Workspace switcher | Get person's workspaces |

### Capability Check in CRM

```go
// Middleware extracts capabilities from JWT
func RequireCapability(cap string) gin.HandlerFunc {
    return func(c *gin.Context) {
        ctx := GetRequestContext(c)
        if !ctx.HasCapability(cap) {
            c.AbortWithStatus(403)
            return
        }
        c.Next()
    }
}

// Usage on route
r.GET("/reports/frt", RequireCapability("reports.view"), handlers.GetFRTReport)
```

---

## 3. accounts-api Integration

### Purpose
Contact (person), account (entity), and membership management. CRM does NOT own this data.

### Protocol
gRPC on port 21001. CRM implements a `contact-bridge` client.

### Key Concept: Workspace Divergence

accounts-api stores base person data and per-workspace overrides:
```
Base Person (MongoDB):
  { _id: "person_123", name: "Rahul Verma", email: "rahul@acme.com" }

Workspace Override (MongoDB):
  { person_id: "person_123", workspace_id: "ws_456", designation: "Procurement Manager" }

Merged result (what CRM sees):
  { id: "person_123", name: "Rahul Verma", email: "rahul@acme.com", designation: "Procurement Manager" }
```

### gRPC Calls CRM Makes to accounts-api

| Method | When | Purpose |
|--------|------|---------|
| `GetPerson(person_id, workspace_id)` | Contact detail, inbox | Get merged person data |
| `GetPersons(person_ids[], workspace_id)` | Contact list, bulk loading | Batch person lookup |
| `SearchPersons(query, workspace_id)` | Global search, contact search | Search by name/phone/email |
| `CreatePerson(data, workspace_id)` | New contact from inbound message | Create new person |
| `UpdatePerson(person_id, data, workspace_id)` | Edit contact | Update person fields |
| `GetPersonByHandle(handle_type, handle_value, workspace_id)` | Inbound message resolution | Find person by phone/email |
| `GetEntity(entity_id, workspace_id)` | Account detail | Get company data |
| `GetEntities(entity_ids[], workspace_id)` | Account list | Batch entity lookup |
| `CreateEntity(data, workspace_id)` | New account | Create company |
| `UpdateEntity(entity_id, data, workspace_id)` | Edit account | Update company fields |
| `CreateMembership(person_id, entity_id)` | Link contact to account | Create person↔entity link |
| `MergePersons(primary_id, secondary_id)` | Merge duplicates | Merge two person records |

### Contact Resolution Flow (Inbound Message)

```
Inbound message with handle_value = "+919876543210"
  │
  ├─ CRM queries local: contact_handles WHERE workspace_id = ? AND handle_value = ?
  │
  ├─ FOUND (person_id exists locally):
  │    └─ Use person_id, skip accounts-api call for resolution
  │       (fetch full person data lazily when needed for display)
  │
  └─ NOT FOUND:
       ├─ gRPC accounts-api: GetPersonByHandle("phone", "+919876543210", workspace_id)
       │
       ├─ FOUND in accounts-api:
       │    ├─ Create local contact_handle record (cache the mapping)
       │    └─ Use returned person_id
       │
       └─ NOT FOUND anywhere:
            ├─ gRPC accounts-api: CreatePerson({ phone: "+919876543210" }, workspace_id)
            ├─ Get new person_id
            ├─ Create local contact_handle record
            └─ Use new person_id
```

### Caching Strategy

CRM caches person data locally in Redis (TTL: 5 minutes) to avoid per-request gRPC calls:
- Cache key: `person:{workspace_id}:{person_id}`
- Invalidate on: `accounts.person.updated` event from NATS
- Batch pre-warming: when loading conversation list, batch-fetch all person_ids

---

## 4. Communication Gateway Integration

### Purpose
All channel communication. CRM never talks to WhatsApp/Smartflo/SES directly.

### Protocol
NATS events (async) + gRPC (sync for template listing, health checks).

### Inbound Message Flow

```
Channel Provider (WhatsApp) → Webhook → Communication Gateway
  │
  ├─ GW validates webhook signature
  ├─ GW parses channel-specific payload
  ├─ GW normalizes to UnifiedMessage
  │
  ├─ GW publishes NATS event:
  │    Subject: comm.message.received
  │    Payload: {
  │      workspace_id, channel, direction: "inbound",
  │      handle_type: "phone", handle_value: "+919876543210",
  │      content_type: "text", content: { body: "Hello" },
  │      external_message_id: "wamid.abc123",
  │      metadata: { profile_name: "Rahul" },
  │      timestamp: "2026-03-12T10:30:00Z"
  │    }
  │
  CRM subscribes to comm.message.received
  │
  ├─ Resolve contact (see Contact Resolution Flow above)
  ├─ Find/create conversation
  ├─ Store message in conversation_messages
  ├─ Run assignment rules (if new conversation)
  ├─ Notify agent via WebSocket
  └─ Evaluate workflow rules
```

### Outbound Message Flow

```
Agent clicks Send in Inbox composer
  │
  ├─ CRM stores message in conversation_messages (status: queued)
  │
  ├─ CRM publishes NATS event:
  │    Subject: comm.message.send
  │    Payload: {
  │      workspace_id, channel: "whatsapp",
  │      handle_value: "+919876543210",
  │      content_type: "text", content: { body: "Hi Rahul!" },
  │      crm_message_id: "uuid",
  │      metadata: {}
  │    }
  │
  Communication Gateway subscribes to comm.message.send
  │
  ├─ GW looks up workspace channel config (WhatsApp credentials)
  ├─ GW calls WhatsApp Cloud API
  ├─ GW receives response (success/failure)
  │
  ├─ GW publishes NATS event:
  │    Subject: comm.message.status
  │    Payload: {
  │      crm_message_id: "uuid",
  │      external_message_id: "wamid.xyz789",
  │      status: "sent",
  │      timestamp: "2026-03-12T10:30:01Z"
  │    }
  │
  CRM subscribes to comm.message.status
  │
  ├─ Update conversation_messages.delivery_status = "sent"
  ├─ Update conversation_messages.external_message_id
  └─ Push status update to agent via WebSocket
```

### Delivery Status Updates

```
WhatsApp sends delivery webhook → Communication Gateway
  │
  ├─ GW publishes: comm.message.status
  │    { crm_message_id, status: "delivered" / "read" / "failed", timestamp }
  │
  CRM updates message record and pushes to frontend via WebSocket
```

### gRPC Calls CRM Makes to Communication Gateway

| Method | When | Purpose |
|--------|------|---------|
| `GetTemplates(workspace_id, channel)` | Template picker | List approved WhatsApp templates |
| `GetChannelHealth(workspace_id)` | Settings → Channels | Channel connection status |
| `TestChannel(workspace_id, channel, config)` | Channel setup | Test channel connectivity |

---

## 5. NATS Event Bus

### Subject Naming Convention

```
{service}.{entity}.{action}

Examples:
  crm.conversation.created
  crm.opportunity.stage_changed
  comm.message.received
  comm.message.status
  accounts.person.updated
  elauth.user.deactivated
```

### Events Published by CRM

| Subject | Payload (key fields) | Consumers |
|---------|---------------------|-----------|
| `crm.contact_handle.linked` | workspace_id, person_id, handle_type, handle_value | Comm GW |
| `crm.conversation.created` | workspace_id, conversation_id, person_id, channel, source | Comm GW, Ops |
| `crm.conversation.assigned` | workspace_id, conversation_id, agent_id, method | Notification Hub |
| `crm.conversation.stage_changed` | workspace_id, conversation_id, old_stage, new_stage | Workflow (internal) |
| `crm.conversation.closed` | workspace_id, conversation_id, reason, disposition | Analytics |
| `crm.opportunity.created` | workspace_id, opportunity_id, person_id, pipeline_id | Commerce |
| `crm.opportunity.stage_changed` | workspace_id, opportunity_id, old_stage, new_stage | Workflow (internal) |
| `crm.opportunity.won` | workspace_id, opportunity_id, won_value | Commerce |

### Events Consumed by CRM

| Subject | Publisher | CRM Action |
|---------|-----------|------------|
| `comm.message.received` | Comm GW | Resolve contact, create/update conversation, store message |
| `comm.message.status` | Comm GW | Update message delivery status |
| `comm.call.incoming` | Comm GW | Notify agent of incoming call |
| `comm.call.ended` | Comm GW | Log call activity, prompt disposition |
| `accounts.person.updated` | accounts-api | Invalidate person cache in Redis |
| `accounts.entity.merged` | accounts-api | Merge related conversations |
| `elauth.user.deactivated` | elauth | Reassign conversations/opportunities |
| `commerce.order.created` | Commerce | Update linked opportunity (future) |

### Transactional Outbox Pattern

```
CRM needs to update DB AND publish event atomically:

1. Within same DB transaction:
   UPDATE conversations SET stage_id = 'qualified' WHERE id = ?;
   INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
     VALUES ('conversation', 'conv_123', 'stage_changed', '{"old":"new","new":"qualified"}');
   COMMIT;

2. Outbox poller (goroutine, runs every 100ms):
   SELECT * FROM outbox WHERE published_at IS NULL ORDER BY created_at LIMIT 100;
   For each: publish to NATS → UPDATE outbox SET published_at = now() WHERE id = ?;

3. Guarantees at-least-once delivery. Consumers must be idempotent.
```

---

## 6. Notification Hub

CRM publishes notification requests; Notification Hub delivers them.

```
CRM → NATS event: notification.send
Payload: {
  workspace_id, recipient_id, channels: ["email", "push"],
  template: "sla_breach",
  data: { contact_name: "Rahul", conversation_id: "...", frt_minutes: 12 }
}

Notification Hub:
  → Resolves recipient email from elauth
  → Renders email template with data
  → Sends via SES
  → Sends push via FCM (if push token registered)
```

---

## 7. File Service (S3)

```
Agent attaches file in composer:
  1. Frontend → CRM API: GET /uploads/presigned-url?filename=quote.pdf&type=application/pdf
  2. CRM → File Service: get presigned S3 upload URL
  3. Frontend uploads directly to S3 via presigned URL
  4. Frontend sends message with media_url = S3 URL
  5. CRM stores URL in conversation_messages.content_json
  6. Communication Gateway fetches file from S3 when sending to channel
```

---

## 8. Sequence Diagram: Inbound WhatsApp Message (Full Flow)

```
Customer    WhatsApp    Comm GW      NATS       CRM          accounts-api    Redis    PgSQL    Agent Browser
   │           │           │          │          │               │             │        │           │
   │──message─▶│           │          │          │               │             │        │           │
   │           │──webhook─▶│          │          │               │             │        │           │
   │           │           │──publish─▶│         │               │             │        │           │
   │           │           │  comm.message.received              │             │        │           │
   │           │           │          │──consume─▶│              │             │        │           │
   │           │           │          │          │──lookup──────▶│             │        │           │
   │           │           │          │          │  contact_handles            │        │           │
   │           │           │          │          │◀─person_id───│             │        │           │
   │           │           │          │          │               │             │        │           │
   │           │           │          │          │──get person────────────────▶│        │           │
   │           │           │          │          │  (cache miss)  │             │        │           │
   │           │           │          │          │◀─person data──────────────│        │           │
   │           │           │          │          │──cache─────────────────────▶│        │           │
   │           │           │          │          │               │             │        │           │
   │           │           │          │          │──store message─────────────────────▶│           │
   │           │           │          │          │──find/create conversation──────────▶│           │
   │           │           │          │          │──run assignment rules──────────────▶│           │
   │           │           │          │          │──insert outbox event───────────────▶│           │
   │           │           │          │          │               │             │        │           │
   │           │           │          │          │──WebSocket push────────────────────────────────▶│
   │           │           │          │          │               │             │        │    (new msg)│
   │           │           │          │          │               │             │        │           │
```

---

## 9. Sequence Diagram: Agent Sends Reply

```
Agent Browser    CRM           PgSQL      NATS       Comm GW      WhatsApp    Customer
     │            │              │          │           │             │           │
     │──send msg─▶│              │          │           │             │           │
     │            │──store msg──▶│          │           │             │           │
     │            │  (status:queued)        │           │             │           │
     │            │──publish────────────────▶│          │             │           │
     │            │  comm.message.send      │           │             │           │
     │◀─optimistic│              │          │──consume─▶│             │           │
     │  (sending) │              │          │           │──API call──▶│           │
     │            │              │          │           │             │──deliver─▶│
     │            │              │          │           │◀─accepted──│           │
     │            │              │          │◀─publish──│             │           │
     │            │              │  comm.message.status (sent)       │           │
     │            │◀─consume─────│          │           │             │           │
     │            │──update msg─▶│          │           │             │           │
     │            │  (status:sent)          │           │             │           │
     │◀─WS push──│              │          │           │             │           │
     │  (✓ sent)  │              │          │           │             │           │
     │            │              │          │           │             │           │
     │            │              │          │           │◀─delivery──│           │
     │            │              │          │◀─publish──│  webhook    │           │
     │            │◀─consume─────│  comm.message.status (delivered)  │           │
     │            │──update msg─▶│          │           │             │           │
     │◀─WS push──│              │          │           │             │           │
     │  (✓✓ dlvd) │              │          │           │             │           │
```
