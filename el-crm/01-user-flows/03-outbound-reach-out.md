# Outbound Reach-Out

> Role: Sales Agent
> Trigger: Agent initiates contact with a customer
> Primary screen: Inbox or Contacts

---

## Flow Summary

Agent proactively reaches out to a contact — sends a WhatsApp template, makes an outbound call, or sends an email. This creates or updates a conversation and logs the activity.

---

## Scenario A: WhatsApp Template Message (Outside 24h Window)

```
Agent opens an existing contact's conversation
  → Last customer message was > 24 hours ago
  → Composer shows: "WhatsApp session expired. Use a template to restart."
  → Agent clicks "Template" button in composer
  → Template picker modal opens:
      - Search templates
      - Categories: Sales, Follow-up, Greeting, Payment, Custom
      - Each template shows: name, body preview, required variables
  → Agent selects template: "follow_up_pricing"
      Body: "Hi {{1}}, following up on your enquiry about {{2}}. Would you like to discuss further?"
  → Agent fills variables: {{1}} = "Rahul", {{2}} = "Grade A spices"
  → Preview shown
  → Agent clicks Send
  → Communication Gateway sends template via WhatsApp Cloud API
  → Message appears in thread as template message (distinct styling)
  → Status: Sent → Delivered → Read
  → 24-hour window reopens once customer replies
```

### If No Prior Conversation Exists

```
Agent navigates to Contacts
  → Finds contact "Rahul Verma"
  → Clicks "Message" button on contact card
  → Channel selector: WhatsApp | Email | SMS
  → Selects WhatsApp
  → System checks: Does this contact have a WhatsApp handle?
      → YES → open/create conversation, show template picker (no 24h window for new)
      → NO → show error: "No WhatsApp number for this contact. Add a phone number first."
  → Agent sends template
  → New conversation created with status: open, stage: first pipeline stage
  → Assignment: auto-assigned to the agent who initiated
```

---

## Scenario B: Outbound Phone Call

```
Agent clicks phone icon on contact card (or in conversation panel)
  → System initiates call via Communication Gateway
  → Browser shows call UI: dialing → ringing → connected
  → Call is recorded (if workspace has recording enabled)
  → Call ends
  → System auto-logs activity:
      Type: Outbound Call
      Duration: 4m 32s
      Recording: [link]
  → Agent prompted for disposition:
      - Interested
      - Call Back Later
      - Not Reachable
      - Wrong Number
      - Not Interested
      - Custom (workspace-configurable dispositions)
  → Agent selects disposition, adds optional notes
  → Activity saved, visible in conversation timeline
  → If "Call Back Later" → prompt to create follow-up with date/time
```

---

## Scenario C: Outbound Email

```
Agent clicks email icon on contact card
  → Rich text email composer opens:
      To: contact's email (pre-filled)
      Subject: [editable]
      Body: rich text editor (formatting, links, images)
      Attachments: drag & drop or browse
  → Agent composes email, clicks Send
  → Communication Gateway sends via SES/SMTP
  → Email appears in conversation thread (email styling, shows subject)
  → Status: Sent → Delivered (no read tracking for email unless pixel tracking enabled)
  → If contact replies → threaded into same conversation (In-Reply-To header matching)
```

---

## Scenario D: Bulk Outreach (Template Broadcast)

```
Manager or Agent with broadcast capability navigates to Contacts list
  → Filters contacts: Stage = "Qualified", Source = "Trade Show", Last contact > 7 days
  → Selects contacts (checkbox) → "Send Template" bulk action
  → Template picker opens (same as individual)
  → Selects template, fills variables (supports merge fields: {{contact_name}}, {{account_name}})
  → Preview with sample contact
  → Confirm: "Send to 47 contacts?"
  → System queues messages via Communication Gateway
  → Progress: 47/47 sent (real-time progress bar)
  → For each contact:
      - If open conversation exists → append template message
      - If no conversation → create new conversation
  → Broadcast logged as a campaign activity
```

---

## Channel Selection Logic

When agent initiates outbound from a contact with multiple handles:

```
Contact has: WhatsApp (+91...), Email (rahul@acme.com), Phone (+91...)

Agent clicks "Message" →
  → Default channel = contact's primaryChannel (workspace or contact-level preference)
  → If no preference → channel priority: WhatsApp > Email > SMS (workspace-configurable)
  → Agent can override: channel selector dropdown in composer

Agent clicks "Call" →
  → Uses phone handle directly
  → If multiple phone numbers → show selector
```

---

## Data Created Per Outbound Action

| Action | Entities Created |
|--------|-----------------|
| Send template message | conversation_message (outbound), conversation (if new) |
| Make outbound call | activity (call), conversation_message (call_event), conversation (if new) |
| Send email | conversation_message (outbound, email type), conversation (if new) |
| Bulk broadcast | conversation_message per contact, conversations as needed, campaign record |

---

## Error States

| Scenario | Behavior |
|----------|----------|
| Template not approved by Meta | Template not shown in picker (filtered server-side) |
| WhatsApp number not on WhatsApp | Message fails, show "Number not on WhatsApp", suggest email/SMS |
| Call fails to connect | Log failed call attempt, show retry option |
| Email bounce | Update delivery status to "bounced", flag contact handle |
| Bulk send partial failure | Show success/failure count, allow retry for failures |
| Rate limit hit (WhatsApp API) | Queue remaining messages, show "Sending... (queued)" |
