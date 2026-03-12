# Inbound Message Handling

> Role: Sales Agent (primary), System (auto-processing)
> Trigger: Customer sends message via any channel
> Primary screen: Inbox

---

## Flow Summary

When a customer sends a message (WhatsApp, email, voice call, lead form), the system processes it through the Communication Gateway, resolves the contact, creates or updates a conversation, assigns an agent, and notifies them in real-time.

---

## System Processing Pipeline (Before Agent Sees Anything)

```
1. WEBHOOK RECEIVED
   Communication Gateway receives webhook from channel provider
   → Adapter validates signature/authenticity
   → Adapter parses channel-specific payload
   → Adapter normalizes to UnifiedMessage format

2. HANDLE RESOLUTION
   CRM receives comm.message.received event
   → Extract handle_value (phone: +919876543210, email: john@acme.com)
   → Query contact_handles table: WHERE workspace_id = ? AND handle_value = ?
   → FOUND → get person_id → proceed to step 3
   → NOT FOUND → create new:
       a. Call accounts-api gRPC: CreatePerson(name from message metadata if available)
       b. Create contact_handle record linking person_id + handle
       c. Proceed to step 3

3. CONVERSATION RESOLUTION
   → Query conversations: WHERE workspace_id = ? AND person_id = ? AND status IN ('open', 'pending')
   → FOUND (open conversation exists) → append message to existing conversation
   → NOT FOUND → create new conversation:
       - status: open
       - stage: first stage in default pipeline (workspace-configured)
       - channel: source channel
       - created_at: now
       - Proceed to step 4 (assignment)

4. ASSIGNMENT (new conversations only)
   → Load workspace assignment_rules ordered by priority
   → Evaluate rules:
       Rule 1: Source-based → "If source = JustDial, assign to Agent X"
       Rule 2: Round-robin → distribute evenly among available agents
       Rule 3: Load-balanced → assign to agent with fewest open conversations
       Rule 4: Manual queue → leave unassigned for manager to pick
   → First matching rule wins → assign agent
   → Log assignment in assignment_history

5. NOTIFICATION
   → WebSocket push to assigned agent's browser (real-time)
   → If agent is offline → queue for push notification / email (per preference)
   → Update conversation list ordering (new message = top of list)

6. MESSAGE STORED
   → Insert into conversation_messages:
       conversation_id, channel, direction: inbound, content_type, content_text,
       content_json (media/template/interactive), delivery_status: received
```

---

## Agent Interaction Flow

### Scenario A: Existing Conversation, Agent Online

```
Agent has Inbox open
  → Conversation item blinks/moves to top with unread badge (1)
  → Agent clicks conversation
  → New message appears at bottom of chat thread
  → Agent reads message
  → Types reply in composer
  → Clicks Send (or Ctrl+Enter)
  → Message appears in thread with "Sending..." status
  → Communication Gateway sends via channel
  → Status updates: Sending → Sent → Delivered → Read
```

### Scenario B: New Contact, First Message Ever

```
Unknown number sends WhatsApp message "Hi, I want to enquire about pricing"
  → System creates: Person (accounts-api) + Contact Handle + Conversation
  → Assignment engine assigns to Agent Priya (round-robin)
  → Priya's Inbox shows new conversation:
      Contact name: "+919876543210" (no name yet)
      Last message: "Hi, I want to enquire about pricing"
      Channel: WhatsApp icon
      Stage: "New"
      Badge: NEW + unread (1)
  → Priya clicks → reads message
  → Opens Contact Details panel → edits contact name ("Rahul Verma")
      → accounts-api gRPC: UpdatePerson(name: "Rahul Verma")
  → Replies: "Hello Rahul! Thank you for reaching out. What products are you interested in?"
  → Conversation name updates to "Rahul Verma" across all panels
```

### Scenario C: Message on Closed Conversation

```
Customer sends new message on previously closed conversation
  → System finds closed conversation for this person
  → Decision (workspace-configurable):
      Option A: Reopen the same conversation → status back to "open"
      Option B: Create new conversation → fresh pipeline stage
  → If reopened → re-assign to original agent (if available) or run assignment rules
  → Agent notified as per standard flow
```

### Scenario D: Multi-Channel — Same Contact, Different Channel

```
Customer previously messaged on WhatsApp (conversation exists)
  → Same customer now sends an email
  → Handle resolution: email handle → same person_id
  → Conversation resolution: existing open conversation found
  → Message appended to SAME conversation thread
  → Message shows email icon in thread (different from WhatsApp messages above)
  → Agent can reply on either channel (composer shows channel selector)
  → Conversation's activeChannels updated: [whatsapp, email]
```

---

## Channel-Specific Behaviors

### WhatsApp
- **24-hour window**: After last customer message, business can send free-form messages for 24h. After that, must use approved templates.
- **Media support**: Images, videos, documents, audio, location, contacts
- **Interactive**: Buttons (up to 3), list messages (up to 10 sections)
- **Status tracking**: Sent → Delivered → Read (blue ticks)
- **Template messages**: Pre-approved by Meta, with variable substitution

### Voice (Phone Call)
- **Inbound call**: Ring notification in browser → Agent answers → call recorded
- **Call ends**: Auto-log call activity (duration, recording URL)
- **Missed call**: Create/update conversation, log "missed call" activity, trigger follow-up
- **No message in thread**: Call events shown as activity cards in the chat timeline

### Email
- **Threading**: Match by In-Reply-To header or subject+sender
- **Rich content**: HTML body rendered in chat thread, attachments listed
- **Compose**: Rich text editor for email replies (not just plain text)
- **CC/BCC**: Visible in message metadata

### Lead Capture (JustDial, Facebook, IndiaMart, Web Forms)
- **Auto-create**: Contact + conversation created from lead data
- **Pre-filled fields**: Name, phone, email, enquiry text extracted from lead payload
- **Source tagged**: conversation.source_id set to the lead source
- **Lead message**: Displayed as a structured card in the chat thread (not plain text)

---

## Assignment Rules Detail

Rules are evaluated in priority order. First match wins.

| Priority | Rule Type | Example Config | Behavior |
|----------|-----------|---------------|----------|
| 1 | Source-based | `source = "JustDial" → agent_id = 5` | Specific leads to specific agents |
| 2 | Channel-based | `channel = "email" → team = "inside_sales"` | Route by channel |
| 3 | Time-based | `after_hours = true → agent_id = null` | Queue for next business day |
| 4 | Round-robin | `team = "sales" → strategy = round_robin` | Even distribution |
| 5 | Load-balanced | `team = "sales" → strategy = load_balanced` | Least active agent |
| 6 | Fallback | `default → unassigned queue` | Manager picks manually |

**Agent availability**: Assignment skips agents who are:
- Offline (no active session in last X minutes — workspace-configurable)
- On leave (integrated with el-tracker if configured)
- At capacity (max open conversations limit — workspace-configurable)

---

## Data Created Per Inbound Message

| Entity | Created/Updated | Storage |
|--------|----------------|---------|
| Person | Created if new handle | accounts-api (MongoDB) |
| Contact Handle | Created if new | CRM (PostgreSQL) |
| Conversation | Created if no open conversation exists | CRM (PostgreSQL) |
| Conversation Message | Always created | CRM (PostgreSQL) |
| Assignment History | Created if new conversation assigned | CRM (PostgreSQL) |
| Activity | Created for calls, lead captures | CRM (PostgreSQL) |

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Webhook → message visible to agent | < 2 seconds |
| Handle resolution | < 50ms |
| Conversation resolution | < 50ms |
| Assignment rule evaluation | < 100ms |
| WebSocket push latency | < 200ms |
