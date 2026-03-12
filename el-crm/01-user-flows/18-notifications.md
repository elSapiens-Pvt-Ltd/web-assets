# Notifications

> Role: All
> Trigger: System events that require user attention
> Delivery: In-app, browser push, email (per user preference)

---

## Flow Summary

Notifications keep agents and managers informed of events requiring attention. Users configure which notifications they receive and through which channels.

---

## Notification Types

### Agent Notifications

| Event | Default Channel | Priority |
|-------|----------------|----------|
| New conversation assigned to you | In-app + Push | High |
| New message in assigned conversation | In-app + Push | High |
| Conversation transferred to you | In-app + Push | High |
| Follow-up due | In-app + Push | Normal |
| Follow-up overdue | In-app + Push + Email | High |
| SLA warning (approaching breach) | In-app | Normal |
| SLA breach | In-app + Push | High |
| Mention by another agent (future) | In-app + Push | Normal |
| Conversation reopened | In-app | Normal |
| Message delivery failed | In-app | Normal |

### Manager Notifications

| Event | Default Channel | Priority |
|-------|----------------|----------|
| Team SLA breach | In-app + Email | High |
| High-value opportunity created (> threshold) | In-app | Normal |
| Opportunity won | In-app | Normal |
| Opportunity lost | In-app | Normal |
| Agent follow-up overdue (escalated) | In-app + Email | High |
| Daily team activity summary | Email | Low |
| Weekly pipeline report | Email | Low |

### Admin Notifications

| Event | Default Channel | Priority |
|-------|----------------|----------|
| Channel disconnected | In-app + Email + Push | Critical |
| Channel error rate spike | In-app + Email | High |
| Workflow rule execution failure | In-app | Normal |
| New user joined workspace | In-app | Low |

---

## In-App Notification Center

```
Header bar has notification bell icon with unread count badge.

Click bell → notification panel slides in from right:

┌──────────────────────────────────────┐
│ Notifications              [Mark all]│
│ ┌──────────────────────────────────┐ │
│ │ ● New message from Rahul Verma  │ │
│ │   "Can you share the quote?"    │ │
│ │   2 minutes ago                  │ │
│ └──────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │
│ │ ● Follow-up due: Ankit Shah     │ │
│ │   "Send revised pricing"        │ │
│ │   Due: 10:00 AM (15 min ago)    │ │
│ └──────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │
│ │ ○ Conversation transferred      │ │
│ │   Meera → You: TechParts inquiry│ │
│ │   1 hour ago                     │ │
│ └──────────────────────────────────┘ │
│                                      │
│ [View all notifications →]           │
└──────────────────────────────────────┘

● = Unread    ○ = Read
Click notification → navigate to relevant screen (conversation, follow-up, etc.)
```

---

## Real-Time Delivery

```
In-app notifications delivered via WebSocket:
  → CRM backend publishes notification event
  → WebSocket server pushes to user's connected clients
  → Frontend updates notification bell badge count
  → If user is on the relevant screen (e.g., inbox with that conversation open):
      → Notification still logged but may not pop up (avoid distraction)

Browser push notifications (Web Push API):
  → User grants permission on first visit
  → Service worker registered
  → Push sent when user has CRM tab in background or closed
  → Click push → opens CRM at relevant screen

Email notifications:
  → Queued via Notification Hub service
  → Sent via SES
  → Batched for low-priority: daily digest instead of individual emails
```

---

## Notification Preferences

```
User menu → Notification Preferences

┌─────────────────────────────────────────────────────────────────┐
│ Notification Preferences                                        │
├─────────────────────────────────────────────────────────────────┤
│                              In-App    Push     Email           │
│ ─────────────────────────────────────────────────────────────── │
│ New message received          ✓         ✓        ○             │
│ Conversation assigned         ✓         ✓        ○             │
│ Conversation transferred      ✓         ✓        ○             │
│ Follow-up due                 ✓         ✓        ○             │
│ Follow-up overdue             ✓         ✓        ✓             │
│ SLA warning                   ✓         ○        ○             │
│ SLA breach                    ✓         ✓        ○             │
│ Message delivery failed       ✓         ○        ○             │
│ Daily activity summary        ○         ○        ✓             │
│ Weekly pipeline report        ○         ○        ✓             │
│                                                                 │
│ ✓ = Enabled    ○ = Disabled                                    │
│                                                                 │
│ Quiet Hours: 9:00 PM - 8:00 AM (no push/email, in-app only)  │
│ [Save Preferences]                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Sound & Desktop Alerts

```
In-app settings:
  - Notification sound: On/Off (with sound selector)
  - Desktop notification popup: On/Off
  - Sound for new messages: On/Off (separate from notifications)
  - Conversation-specific mute: right-click conversation → Mute
```

---

## Notification Data Model

```
notifications:
  id: UUID
  workspace_id: UUID
  recipient_id: UUID (person_id from elauth)
  type: VARCHAR (new_message, conversation_assigned, followup_due, ...)
  title: VARCHAR
  body: TEXT
  priority: enum (low, normal, high, critical)
  data: JSONB (contextual payload: conversation_id, person_id, etc.)
  channels_sent: VARCHAR[] (in_app, push, email)
  is_read: BOOLEAN
  read_at: TIMESTAMP
  created_at: TIMESTAMP

notification_preferences:
  workspace_id: UUID
  person_id: UUID
  preferences: JSONB
    {
      "new_message": { "in_app": true, "push": true, "email": false },
      "followup_due": { "in_app": true, "push": true, "email": false },
      ...
      "quiet_hours": { "start": "21:00", "end": "08:00" }
    }
```

---

## Integration

| System | Role |
|--------|------|
| WebSocket server | Real-time in-app delivery |
| Web Push API | Browser push when CRM not in foreground |
| Notification Hub | Email delivery via SES |
| Workflow Engine | Triggers notification actions from rules |
| elauth | Resolves recipient person_id and email |
