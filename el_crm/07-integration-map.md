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
              └──┬──┬──┬──┬─┘ └──────┬──────┘ └─────────────┘
                 │  │  │  │          │
     ┌───────────┘  │  │  └──────────────────────────────┐
     │ gRPC    gRPC │  │ gRPC       │ Channel APIs       │ gRPC
     ▼              ▼  ▼            ▼                    ▼
┌──────────┐ ┌──────────┐ ┌──────────────────┐  ┌───────────────┐
│ elauth   │ │accounts  │ │ WhatsApp Cloud API│  │Ecosystem Svcs │
│ Go       │ │-api      │ │ Smartflo Voice    │  │               │
│ gRPC:6000│ │NestJS    │ │ SES Email         │  │ elGeolocations│
│ HTTP:8080│ │gRPC:21001│ │ JustDial/FB/IM    │  │ elCurrency    │
│ PgSQL    │ │HTTP:11001│ └──────────────────┘  │ Workspace Svc │
└──────────┘ │MongoDB   │                       │ Goods & Svcs  │
             └──────────┘                       │ elPBX         │
                                                │ Logger        │
                                                └───────────────┘

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

## 8. Ecosystem Service Integrations

CRM leverages existing services from the elSapiens App Registry rather than rebuilding functionality.

### 8.1 elGeolocations API

> `pe8w544nvu` | https://api.elgeolocations.elsapiens.com | 2 ports

**Purpose**: Location data for contact/account profiling — country, state, city, pincode lookup, address validation, geocoding.

**CRM uses it for:**
- Lead profiling: auto-fill city/state/country from pincode when creating or importing contacts
- Account address validation for billing/shipping addresses
- Location-based assignment rules (e.g., assign leads from Mumbai to Ravi)
- Regional report breakdowns (revenue by city/state)
- Filter contacts by location

**Integration:**
```
CRM → gRPC: elGeolocations API
  GetLocationByPincode(pincode) → { city, state, country, lat, lng }
  SearchLocations(query) → [{ city, state, country }]
  ValidateAddress(address) → { normalized_address, is_valid }
  GetStates(country_code) → [{ name, code }]
  GetCities(state_code) → [{ name, pincode_prefix }]
```

**Where in CRM UI:**
- Contact create/edit form: pincode field auto-fills city/state
- Account address fields: validation and autocomplete
- Filters: "Location" filter uses city/state dropdown from this API
- Import: location enrichment during bulk contact import

---

### 8.2 elCurrency Rates API

> `auv2fkpc4h` / `de1b5ls9h5` | https://api.elcurrencyrates.elsapiens.com | 2 ports

**Purpose**: Real-time and historical currency exchange rates.

**CRM uses it for:**
- Multi-currency opportunity values (deal in USD, dashboard shows INR equivalent)
- Pipeline forecast in workspace's base currency
- Revenue reports with currency normalization
- Contact/account currency preference

**Integration:**
```
CRM → gRPC/HTTP: elCurrency Rates API
  GetRate(from, to, date?) → { rate, timestamp }
  GetRates(base, targets[], date?) → [{ currency, rate }]
  Convert(amount, from, to, date?) → { converted_amount, rate }
```

**Where in CRM UI:**
- New Opportunity form: currency selector (INR, USD, EUR, etc.), shows converted value in base currency
- Pipeline kanban/list: values shown in workspace base currency with original currency in tooltip
- Forecast view: all values normalized to base currency
- Reports: revenue aggregations use converted values
- Settings → Workspace: base currency selection

---

### 8.3 Workspace Service

> `rttfjbb1es` | https://api.workspace.elsapiens.com | 2 ports

**Purpose**: Workspace lifecycle management, workspace-level config shared across all apps.

**CRM uses it for:**
- Workspace metadata (name, logo, industry — shared across all elSapiens apps)
- Cross-app workspace settings
- Workspace feature flags / plan limits

**Integration:**
```
CRM → gRPC: Workspace Service
  GetWorkspace(workspace_id) → { name, logo_url, industry, plan, settings }
  GetWorkspaceFeatures(workspace_id) → { max_agents, max_pipelines, channels_enabled[] }
```

**Where in CRM UI:**
- TopBar: workspace name and logo from this service
- Settings → Workspace: reads and writes shared workspace profile
- Feature gating: disable features based on workspace plan

---

### 8.4 Goods & Services API

> `fq9ksbxg54` | https://api.product.climatenaturals.com | 2 ports

**Purpose**: Product/service catalog, pricing, SKUs.

**CRM uses it for:**
- Link products/services to opportunities (what is the customer buying?)
- Product-based reporting (revenue by product)
- Template variables (product name, price in WhatsApp templates)
- Auto-populate opportunity value from product pricing

**Integration:**
```
CRM → gRPC/HTTP: Goods & Services API
  SearchProducts(query, workspace_id) → [{ id, name, sku, price, unit }]
  GetProduct(product_id) → { id, name, sku, price, unit, description }
  GetProducts(product_ids[]) → [{ ... }]
```

**Where in CRM UI:**
- New/Edit Opportunity: "Products" field — searchable multi-select from product catalog
- Opportunity detail: linked products with quantity and line-item value
- Reports → Revenue Contribution: breakdown by product
- WhatsApp templates: `{{product_name}}`, `{{product_price}}` variables

---

### 8.5 elPBX

> `2stpu7ws4g` | https://elpbx.elsapiens.com | 3 ports

**Purpose**: Voice/telephony management — agent phone mapping, call routing, IVR configuration.

**CRM uses it for:**
- Click-to-call: CRM triggers outbound call via PBX
- Agent ↔ phone number mapping (which extension rings which agent)
- Call routing rules (IVR → CRM assignment rules)
- Call recording access

**Integration:**
```
CRM → gRPC/HTTP: elPBX
  InitiateCall(agent_id, destination_number, workspace_id) → { call_id }
  GetAgentExtension(agent_id, workspace_id) → { extension, phone_number }
  GetCallRecording(call_id) → { recording_url, duration }
```

Communication Gateway handles the actual call events (incoming/outgoing/ended). PBX is the configuration layer.

**Where in CRM UI:**
- Inbox: "Call" button on contact → triggers PBX call
- Contact detail: "Call" action button
- Settings → Channels → Voice: links to PBX for agent mapping config

---

### 8.6 Logger Service

> `oxe54hpejx` | 2 ports

**Purpose**: Centralized logging, audit trail, analytics event collection.

**CRM uses it for:**
- Audit logging: who did what, when (config changes, data access, exports)
- Error logging: structured error reporting from CRM service
- Analytics events: page views, feature usage for product analytics

**Integration:**
```
CRM → gRPC/HTTP: Logger Service
  Log(service, level, event, payload, workspace_id, person_id) → void
  LogAudit(action, resource_type, resource_id, old_value, new_value, actor_id) → void
```

**Where in CRM:**
- Every API endpoint logs request/response
- Config changes (Settings) logged with before/after values
- Data exports logged for compliance
- Errors forwarded for monitoring/alerting

---

### 8.7 Accounts (Frontend)

> `at354wg5kd` | https://accounts.elsapiens.com | 1 port

**Purpose**: The Accounts web app — user profile management, workspace switching, billing.

**CRM uses it for:**
- "Manage Account" link in user menu → redirects to Accounts app
- Workspace switching: OrgSwitcher component from elsdk (backed by this app)
- User profile editing happens in this app, not in CRM

**Integration:**
- No API calls — this is a frontend-to-frontend redirect
- CRM user menu: "My Account" → `https://accounts.elsapiens.com`
- elsdk OrgSwitcher reads workspace list from elauth but the management UI is in Accounts app

---

### 8.8 App Registry

> `rk1tqtcq7w` | https://registry.elsapiens.com | 1 port

**Purpose**: Internal app store — service discovery, app metadata.

**CRM uses it for:**
- Service discovery: CRM resolves API URLs for other services from registry
- App navigation: "All Apps" menu in TopBar links to other elSapiens apps
- Health monitoring: check if dependent services are registered and active

**Integration:**
```
CRM → HTTP: App Registry API
  GetApp(app_id) → { name, url, ports, status }
  GetApps(category?) → [{ name, url, category, tag, status }]
```

**Where in CRM UI:**
- TopBar app switcher (grid icon) → shows available apps from registry

---

### Ecosystem Integration Summary

| Service | CRM Uses It For | Integration Type |
|---------|----------------|-----------------|
| **elauth** | Auth, JWT, RBAC, workspace membership | gRPC (core) |
| **accounts-api** | Contact/Account CRUD, person resolution | gRPC (core) |
| **Workspace Service** | Workspace metadata, plan limits | gRPC |
| **Comm Gateway** | WhatsApp, Voice, Email, SMS channels | NATS + gRPC |
| **elGeolocations** | Address validation, location profiling | gRPC |
| **elCurrency Rates** | Multi-currency conversion, reports | gRPC/HTTP |
| **Goods & Services** | Product catalog for opportunities | gRPC/HTTP |
| **elPBX** | Click-to-call, agent phone mapping | gRPC/HTTP |
| **Logger** | Audit logging, error reporting | gRPC/HTTP |
| **Accounts (FE)** | User profile redirect, workspace mgmt | Redirect |
| **App Registry** | Service discovery, app navigation | HTTP |
| **Notification Hub** | Email/Push/SMS delivery | NATS |
| **File Service (S3)** | Attachments, media | Presigned URLs |

---

## 9. Sequence Diagram: Inbound WhatsApp Message (Full Flow)

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
