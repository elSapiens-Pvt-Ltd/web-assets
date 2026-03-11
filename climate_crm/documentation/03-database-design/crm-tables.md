# CRM Tables — Conversations, Messages, Assignments

> Module: `climate/database/crm`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [tbl_open_conversations](#tbl_open_conversations)
3. [tbl_whatsapp_messages](#tbl_whatsapp_messages)
4. [tbl_contact_assignment_history](#tbl_contact_assignment_history)
5. [tbl_contact_sources](#tbl_contact_sources)
6. [Legacy Tables](#legacy-tables)
7. [Cross-References](#cross-references)

---

## Overview

The CRM tables power the conversation pipeline — from initial lead capture through qualification to conversion. `tbl_open_conversations` tracks conversation state, `tbl_whatsapp_messages` stores all messages (despite its name, it handles notes, system events, and call logs too), and `tbl_contact_assignment_history` provides a complete audit trail of agent assignments.

---

## tbl_open_conversations

Tracks all conversations (both open and closed) with their current stage, assigned agent, and disposition status. Originally a simple open/closed table, it was enhanced with CRM fields by migration `20251224000124_enhance_open_conversations_table.php`.

### Original Schema

```sql
CREATE TABLE tbl_open_conversations (
    id          INT NOT NULL AUTO_INCREMENT,
    contact_id  VARCHAR(15) NOT NULL,
    agent_id    INT NOT NULL DEFAULT 0,
    status      ENUM('open','closed') NOT NULL DEFAULT 'open',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_contact_id (contact_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Enhanced Columns (added by migration)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `conversation_id` | BIGINT UNSIGNED | No | AUTO_INCREMENT | New primary key (replaces `id`) |
| `account_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_accounts` |
| `source_id` | INT UNSIGNED | Yes | NULL | FK to `tbl_contact_sources` |
| `conversation_type` | ENUM('lead','opportunity','customer') | No | `'lead'` | Classification |
| `conversation_stage` | ENUM('new','attempted','contacted','nurturing','qualified','unqualified') | No | `'new'` | Lifecycle stage |
| `disposition_status` | ENUM (see below) | Yes | NULL | Reason for closing as unqualified |
| `priority` | ENUM('hot','warm','cold') | No | `'cold'` | Lead priority |
| `call_attempts` | TINYINT UNSIGNED | No | `0` | Number of call attempts |
| `opened_at` | DATETIME | Yes | NULL | When conversation was opened |
| `closed_at` | DATETIME | Yes | NULL | When conversation was closed |
| `last_activity_at` | DATETIME | Yes | NULL | Last message or action timestamp |

**Indexes**: `account_id`, `source_id`, `conversation_type`, `conversation_stage`, `priority`, `last_activity_at`

### Disposition Status Values

When a conversation is closed as `'unqualified'`, one of these reasons must be selected:

| Value | Category | Description |
|-------|----------|-------------|
| `rnr1` | No Response | Ring no reply — first attempt |
| `rnr2` | No Response | Ring no reply — second attempt |
| `rnr3` | No Response | Ring no reply — third attempt |
| `not_interested` | Customer Decision | Customer explicitly declined |
| `price_too_high` | Pricing | Price objection |
| `wrong_timing` | Timing | Not the right time for purchase |
| `need_approval` | Decision Process | Needs internal approval |
| `competitor_chosen` | Competition | Chose a competitor |
| `budget_issues` | Financial | Budget constraints |
| `decision_maker_unavailable` | Decision Process | Can't reach decision maker |
| `need_discount` | Pricing | Requires discount beyond threshold |
| `credit_needed` | Financial | Needs credit terms |
| `need_more_time` | Timing | Needs more time to decide |
| `non_contact` | Invalid | Not a valid contact |
| `invalid` | Invalid | Invalid lead data |
| `other` | Other | Free-text reason |

### Stage Transitions

**Triggers** (5 triggers — see [Triggers & Functions](triggers-and-functions.md#conversation-triggers)):
- `trg_conversation_before_insert` — Sets `had_account_at_start` flag
- `trg_calculate_attempt_time` — Calculates working-hours FRT using `fn_calculate_working_seconds`
- `trg_conversation_before_update` — Sets `first_reached_*_at` timestamps, auto-closes unqualified
- `trg_conversation_after_insert` — Populates `crm_conversation_cohort_summary`, `crm_conversation_activity_summary`, `crm_conversation_stage_summary`
- `trg_conversation_after_update` — Updates stage/activity/cohort summaries, writes `crm_unqualified_summary`

Two transitions are automatic; the rest are manual:

| Transition | Trigger | Type |
|------------|---------|------|
| `new` → `attempted` | Agent sends first message | Automatic |
| `attempted` → `contacted` | Customer replies | Automatic |
| `contacted` → `nurturing` | Agent marks as nurturing | Manual |
| Any → `qualified` | Agent qualifies the lead | Manual |
| Any → `unqualified` | Agent closes with disposition | Manual |
| Any → `converted` | Order is created from conversation | Automatic |

---

## tbl_whatsapp_messages

Stores all messages associated with conversations. Despite its name, this table handles not just WhatsApp messages but also agent notes, system events (order created, transfer occurred), and call status logs.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `message_id` | BIGINT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `conversation_id` | INT | Yes | NULL | FK to `tbl_open_conversations` (added via ALTER) |
| `contact_id` | VARCHAR(15) | Yes | NULL | Legacy contact identifier |
| `agent_id` | INT | Yes | NULL | Agent who sent/received the message |
| `type` | VARCHAR(50) | Yes | NULL | Message type: `text`, `image`, `video`, `audio`, `document`, `note`, `system`, `order` |
| `message` | TEXT | Yes | NULL | Message content or media URL |
| `message_source` | ENUM | Yes | NULL | Source: `whatsapp`, `note`, `system`, `call`, etc. |
| `sender` | ENUM('agent','customer','system') | Yes | NULL | Who sent the message |
| `wa_message_id` | VARCHAR(255) | Yes | NULL | WhatsApp message ID for status tracking |
| `status` | VARCHAR(20) | Yes | NULL | Delivery status: `sent`, `delivered`, `read`, `failed` |
| `media_url` | TEXT | Yes | NULL | S3/CloudFront URL for media attachments |
| `media_type` | VARCHAR(50) | Yes | NULL | MIME type of attached media |
| `is_deleted` | TINYINT(1) | No | `0` | Soft delete flag |
| `created_at` | DATETIME | No | CURRENT_TIMESTAMP | Message timestamp |

**Indexes**: `conversation_id`, `contact_id`, `agent_id`, `wa_message_id`, `created_at`

**Notes**:
- The `conversation_id` column was added retroactively via ALTER TABLE — its type is INT (not BIGINT), which is a known inconsistency with the BIGINT `conversation_id` primary key in `tbl_open_conversations`
- Message delivery status (`sent` → `delivered` → `read` → `failed`) is updated in real-time via WhatsApp status webhooks
- Media files are stored in AWS S3 and served via CloudFront CDN
- **Trigger**: `trg_agent_activity_message_insert` — on outbound messages (`sender = 'admin'`), increments `crm_agent_activity_summary.messages_sent`. See [Triggers & Functions](triggers-and-functions.md#whatsapp-message-triggers)

---

## tbl_contact_assignment_history

Provides a complete timeline of all agent assignment events for every contact — initial assignments, transfers, reassignments, round-robin rotations, and account merges. Each event is a separate row, enabling full audit trail reconstruction.

**Created by**: `20260311160023_create_contact_assignment_history.php`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | BIGINT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `contact_id` | BIGINT UNSIGNED | **No** | — | FK to `temp_tbl_contacts` |
| `account_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_accounts` |
| `conversation_id` | BIGINT UNSIGNED | Yes | NULL | FK to `tbl_open_conversations` |
| `assigned_to_user_id` | INT UNSIGNED | **No** | — | The agent receiving the assignment |
| `assigned_by_user_id` | INT UNSIGNED | Yes | NULL | The agent/system who made the assignment |
| `previous_user_id` | INT UNSIGNED | Yes | NULL | The previously assigned agent |
| `merged_from_contact_id` | BIGINT UNSIGNED | Yes | NULL | Source contact ID in merge operations |
| `assignment_type` | ENUM | **No** | `'initial'` | See assignment types below |
| `assignment_method` | ENUM | **No** | `'system'` | See assignment methods below |
| `transfer_reason` | VARCHAR(255) | Yes | NULL | Reason for transfer |
| `transfer_notes` | TEXT | Yes | NULL | Additional transfer notes |
| `lifecycle_reason` | VARCHAR(255) | Yes | NULL | Reason for lifecycle event |
| `source_system` | ENUM | **No** | — | Origin of the record |
| `source_record_id` | VARCHAR(50) | Yes | NULL | ID in the source system |
| `assigned_at` | DATETIME | **No** | — | When the assignment occurred |
| `created_at` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | DATETIME | No | CURRENT_TIMESTAMP ON UPDATE | Last update time |
| `is_backfilled` | TINYINT(1) | No | `0` | Whether this was created by data migration |
| `backfill_confidence` | ENUM('high','medium','low') | Yes | NULL | Confidence level for backfilled records |

### Assignment Type Values

| Value | Description |
|-------|-------------|
| `initial` | First-time assignment to an agent |
| `transfer` | Manual transfer between agents |
| `reassignment` | System-initiated reassignment |
| `round_robin` | Assigned via round-robin rotation |
| `contact_merged` | Assignment inherited from a merged contact |
| `contact_discarded` | Contact was discarded/deactivated |
| `contact_reactivated` | Contact was reactivated after being discarded |

### Assignment Method Values

| Value | Description |
|-------|-------------|
| `manual` | Agent or admin manually assigned |
| `automatic` | System auto-assigned (account owner, previous agent) |
| `round_robin` | Assigned via round-robin with availability checking |
| `system` | System-generated event (merge, migration) |

### Source System Values

| Value | Description |
|-------|-------------|
| `open_conversations` | Created from conversation assignment |
| `legacy_whatsapp` | Backfilled from legacy WhatsApp contact data |
| `legacy_transfer_log` | Backfilled from old transfer logs |
| `unified_transfer_log` | From unified transfer log records |
| `manual_backfill` | Manually backfilled by admin |
| `migration_contact_merge` | Created during contact merge migration |
| `migration_contact_discard` | Created during contact discard migration |

**Indexes**: `contact_id`, `account_id`, `conversation_id`, `assigned_to_user_id`, `assigned_by_user_id`, `assigned_at`, composite `(contact_id, assigned_at)`, composite `(is_backfilled, source_system)`

---

## tbl_contact_sources

Tracks the original source through which a contact/lead was acquired. Used for funnel analysis and source attribution reporting.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `contact_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_contacts` |
| `source` | VARCHAR(50) | Yes | NULL | Lead source identifier |
| `source_details` | TEXT | Yes | NULL | Additional source metadata |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |

**Common Source Values**: `whatsapp`, `justdial`, `indiamart`, `facebook`, `website`, `walk_in`, `referral`, `phone_call`

---

## Legacy Tables

These tables predate the normalized profile structure. They are retained for reference and some are still read for backward compatibility:

| Table | Status | Replaced By |
|-------|--------|-------------|
| `tbl_whatsapp_contacts` | Read-only | `temp_tbl_contacts` + `temp_tbl_contact_handles` |
| `tbl_transfer_chat_log` | Read-only | `tbl_contact_assignment_history` |
| `tbl_unified_transfer_log` | Active | Still used for transfer records alongside assignment history |

---

## Cross-References

| Document | Path |
|----------|------|
| Schema Overview | `03-database-design/schema-overview.md` |
| Core Tables | `03-database-design/core-tables.md` |
| Order Tables | `03-database-design/order-tables.md` |
| Conversation Lifecycle | `06-data-flow/conversation-lifecycle.md` |
| Assignment Flow | `06-data-flow/assignment-flow.md` |
| Message Flow | `06-data-flow/message-flow.md` |
| Triggers & Functions | `03-database-design/triggers-and-functions.md` |
| Conversations API | `05-api-documentation/conversations-api.md` |
