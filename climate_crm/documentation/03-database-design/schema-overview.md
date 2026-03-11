# Database Schema — Overview

> Module: `climate/database`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Database Configuration](#database-configuration)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Table Summary](#table-summary)
4. [Key Relationships](#key-relationships)
5. [Naming Conventions](#naming-conventions)
6. [Migration System](#migration-system)
7. [Cross-References](#cross-references)

---

## Database Configuration

The Climate CRM uses MySQL/MariaDB with the `utf8mb4` character set to support emoji characters in WhatsApp messages. The connection is configured in `application/config/database.php`:

```php
$db['default'] = array(
    'hostname' => $_SERVER['DBHOST'] ?? '127.0.0.1',
    'username' => $_SERVER['DBUSER'] ?? 'root',
    'password' => $_SERVER['DBPASSWORD'] ?? '',
    'database' => $_SERVER['DBNAME'] ?? 'climate',
    'dbdriver' => 'mysqli',
    'char_set' => 'utf8mb4',
    'dbcollat' => 'utf8mb4_unicode_ci',
    'db_debug' => (ENVIRONMENT !== 'production'),
    'pconnect' => FALSE,
);
```

| Setting | Value |
|---------|-------|
| Engine | InnoDB |
| Character Set | `utf8mb4` |
| Collation | `utf8mb4_unicode_ci` |
| Timezone | `+5:30` (Asia/Kolkata) — set via `SET time_zone='+5:30'` on every authenticated request |
| Driver | MySQLi |
| Persistent Connections | Disabled |

---

## Entity Relationship Diagram

```
                            ┌──────────────────────┐
                            │    tbl_companies      │
                            │    company_id (PK)    │
                            └──────────┬───────────┘
                                       │ 1:N
                                       ▼
┌───────────────────┐         ┌──────────────────────┐         ┌───────────────────┐
│   tbl_roles       │         │     tbl_users         │         │ tbl_login         │
│   role_id (PK)    │◄────────│     user_id (PK)      │───────►│ login_id (PK)     │
│   role_name       │  1:N    │     role_id (FK)      │  1:N   │ user_id (FK)      │
└───────┬───────────┘         │     company_id (FK)   │        │ login_hash        │
        │ N:M                 │     user_status       │        └───────────────────┘
        ▼                     │     is_super          │
┌───────────────────┐         └──────────┬───────────┘
│tbl_role_capability│                    │ owns (account_owner_id)
│ role_id (FK)      │                    ▼
│ capability_id(FK) │         ┌──────────────────────────┐
└───────┬───────────┘         │   temp_tbl_accounts      │
        ▼                     │   account_id (PK)        │
┌───────────────────┐         │   account_owner_id (FK)  │
│  tbl_capability   │         │   account_type           │
│  id (PK)          │         └──────────┬───────────────┘
│  module_name      │                    │
│  capability       │         ┌──────────┼──────────────────┐
└───────────────────┘         │ 1:N      │ 1:N              │ 1:N
                              ▼          ▼                  ▼
               ┌──────────────────┐ ┌────────────────┐ ┌─────────────────────────┐
               │ temp_tbl_contacts│ │temp_tbl_accounts│ │ temp_tbl_contact_handles│
               │ contact_id (PK) │ │   _address      │ │ handle_id (PK)         │
               │ account_id (FK) │ │ address_id (PK) │ │ contact_id (FK)        │
               │ contact_name    │ │ account_id (FK) │ │ handle_type            │
               │ is_primary      │ │ address_type    │ │ handle_value           │
               └────────┬────────┘ │ gst_number      │ │ is_whatsapp            │
                        │          └─────────────────┘ └───────────┬────────────┘
                        │ 1:N                                      │ lookup
                        ▼                                          │
               ┌────────────────────────────┐                     │
               │  tbl_open_conversations    │◄────────────────────┘
               │  conversation_id (PK)      │
               │  contact_id (FK)           │
               │  account_id (FK)           │
               │  agent_id (FK)             │
               │  conversation_stage        │
               │  disposition_status        │
               └──────────┬─────────────────┘
                          │
               ┌──────────┼──────────────────┐
               │ 1:N      │ 1:1              │ 1:N
               ▼          ▼                  ▼
    ┌──────────────┐ ┌────────────────┐ ┌──────────────────────────────┐
    │tbl_whatsapp  │ │tbl_orders      │ │tbl_contact_assignment_history│
    │  _messages   │ │ order_id (PK)  │ │ id (PK)                     │
    │ message_id   │ │ account_id(FK) │ │ contact_id (FK)             │
    │ conversation │ │ order_status   │ │ assigned_to_user_id (FK)    │
    │   _id (FK)   │ │ payment_status │ │ assignment_type              │
    │ type         │ │ fulfillment    │ │ assignment_method            │
    │ message      │ │   _status      │ │ assigned_at                  │
    └──────────────┘ └───────┬────────┘ └──────────────────────────────┘
                             │
                    ┌────────┼────────┐
                    │ 1:N    │ 1:N    │ 1:N
                    ▼        ▼        ▼
         ┌───────────┐ ┌────────┐ ┌──────────────┐
         │tbl_order  │ │tbl_    │ │tbl_order     │
         │  _items   │ │payments│ │  _status_logs│
         │ item_id   │ │ id(PK) │ │ id (PK)      │
         │ order_id  │ │order_id│ │ order_id(FK) │
         │ product_id│ │ amount │ │ status       │
         │ quantity  │ │ mode   │ │ changed_by   │
         └───────────┘ └────────┘ └──────────────┘
```

---

## Table Summary

### Profile & Account Tables (`temp_tbl_*`)

These tables use the `temp_tbl_` prefix — a result of a migration restructuring from the original `tbl_whatsapp_contacts` / `tbl_accounts` structure to the new normalized profile model. Despite the prefix, these are the active canonical tables for all account and contact data.

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `temp_tbl_accounts` | Company/individual accounts with business details | `account_id` (BIGINT) |
| `temp_tbl_contacts` | Contacts belonging to accounts | `contact_id` (BIGINT) |
| `temp_tbl_contact_handles` | Phone numbers, emails, social IDs per contact | `handle_id` (BIGINT) |
| `temp_tbl_accounts_address` | Billing and shipping addresses per account | `address_id` (INT) |

### CRM & Conversation Tables

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `tbl_open_conversations` | Active and closed conversations with stage tracking | `conversation_id` (BIGINT) |
| `tbl_whatsapp_messages` | All messages (WhatsApp, notes, system events) | `message_id` (BIGINT) |
| `tbl_contact_assignment_history` | Complete agent assignment audit trail | `id` (BIGINT) |
| `tbl_contact_sources` | Lead source attribution per contact | `id` (INT) |
| `tbl_call_logs` | Phone call records | `id` (INT) |
| `tbl_unified_transfer_log` | Conversation transfer records | `id` (INT) |

### Order & Finance Tables

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `tbl_orders` | Order header with 4 independent status fields | `order_id` (INT) |
| `tbl_order_items` | Line items with per-item tax calculation | `item_id` (INT) |
| `tbl_order_data` | JSON storage for billing/shipping address snapshots | `id` (INT) |
| `tbl_payments` | Payment records with mode and amount tracking | `id` (INT) |
| `tbl_order_status_logs` | Status transition audit trail | `id` (INT) |
| `tbl_opportunities` | Sales opportunities linked to conversations | `opportunity_id` (INT) |
| `tbl_admin_approvals` | Approval requests (discounts, ship-without-pay) | `id` (INT) |

### User & Auth Tables

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `tbl_users` | System users with role and company assignment | `user_id` (INT) |
| `tbl_roles` | Role definitions | `role_id` (INT) |
| `tbl_capability` | Individual capability definitions (`module.action`) | `id` (INT) |
| `tbl_role_capability` | Role-to-capability mapping (N:M) | Composite |
| `tbl_login` | Active sessions with `login_hash` for single-device enforcement | `login_id` (INT) |
| `tbl_user_last_request_log` | Last API request timestamp for inactivity tracking | `id` (INT) |

### Configuration & Reference Tables

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `tbl_companies` | Multi-company configuration | `company_id` (INT) |
| `tbl_settings` | Key-value system settings | `setting_id` (INT) |
| `tbl_countries` | Country reference data | `country_id` (INT) |
| `tbl_states` | State/region reference data | `state_id` (INT) |
| `tbl_couriers` | Shipping courier definitions | `courier_id` (INT) |
| `tbl_godowns` | Warehouse/godown locations | `godown_id` (INT) |
| `tbl_company_holidays` | Holiday calendar | `id` (INT) |
| `tbl_user_leaves` | Employee leave records | `id` (INT) |
| `tbl_company_work_hours` | Working hours per day-of-week | `id` (INT) |

### CRM Summary Tables (Trigger-Populated)

These tables are populated exclusively by MySQL triggers and cron jobs. They power the reporting dashboards. See [Triggers & Functions](triggers-and-functions.md) for the complete trigger inventory.

| Table | Purpose | Populated By Triggers On |
|-------|---------|------------------------|
| `crm_agent_activity_summary` | Daily agent metrics | `tbl_call_logs`, `tbl_followup_schedules`, `tbl_whatsapp_messages` |
| `crm_conversation_cohort_summary` | Cohort analysis | `tbl_open_conversations` |
| `crm_conversation_activity_summary` | Daily stage transitions | `tbl_open_conversations` |
| `crm_conversation_stage_summary` | Stage distribution | `tbl_open_conversations` |
| `crm_outcome_agent_summary` | Agent opportunity/order tracking | `tbl_opportunities`, `tbl_orders` |
| `crm_outcome_summary` | Opportunity→order conversion | `tbl_opportunities` |
| `crm_revenue_agent_summary` | Revenue by agent/source | `tbl_orders` |
| `crm_unqualified_summary` | Disposition breakdown | `tbl_open_conversations` |
| `crm_agent_frt_daily_summary` | First response time | Cron job (`calculateAgentFRTSummary`) |
| `crm_conversation_aging_snapshot` | Aging snapshots | Cron job (`calculateAgingSnapshot`) |

### Integration & Audit Tables

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `tbl_whatsapp_callback` | Raw WhatsApp webhook payloads (audit trail) | `id` (INT) |
| `tbl_justdial_leads` | Raw JustDial lead data | `id` (INT) |
| `tbl_justdial_credentials` | API key storage for external integrations | `id` (INT) |
| `tbl_facebook_leads` | Raw Facebook Lead Ads data | `id` (INT) |
| `tbl_firebase_tokens` | FCM device tokens per user | `id` (INT) |
| `tbl_notifications` | System notification records | `id` (INT) |

---

## Key Relationships

| Relationship | Type | Description |
|-------------|------|-------------|
| Account → Contacts | 1:N | Each account has multiple contacts; one marked `is_primary_contact` |
| Account → Addresses | 1:N | Multiple billing/shipping addresses per account |
| Contact → Handles | 1:N | Each contact has multiple phone/email/social handles |
| Handle → Conversation | Lookup | Inbound messages matched to conversations via `handle_value` lookup |
| Conversation → Messages | 1:N | All messages in `tbl_whatsapp_messages` keyed by `conversation_id` |
| Conversation → Agent | N:1 | Each conversation assigned to one agent (`agent_id` → `tbl_users`) |
| Account → Owner | N:1 | `account_owner_id` designates the primary responsible agent |
| Order → Account | N:1 | Orders belong to an account |
| Order → Items | 1:N | Line items in `tbl_order_items` |
| Order → Payments | 1:N | Payment records in `tbl_payments` |
| User → Role | N:1 | Each user has one role |
| Role → Capabilities | N:M | Via `tbl_role_capability` junction table |
| User → Login Sessions | 1:N | `tbl_login` records per user; only latest `login_hash` is valid |

---

## Naming Conventions

| Convention | Pattern | Example |
|------------|---------|---------|
| Table prefix | `tbl_` (standard), `temp_tbl_` (profile/account) | `tbl_orders`, `temp_tbl_accounts` |
| Primary key | `{entity}_id` or `id` | `order_id`, `account_id`, `id` |
| Foreign key | `{related_entity}_id` | `account_id`, `agent_id`, `role_id` |
| Timestamps | `created_on`/`updated_on` or `created_at`/`updated_at` | Varies by table vintage |
| Status fields | ENUM with lowercase values | `'active'`, `'draft'`, `'open'` |
| Boolean flags | TINYINT(1) or ENUM('Yes','No') | `is_primary`, `is_super`, `is_deleted` |
| Soft delete | `status` includes `'deleted'` or `is_deleted` column | Varies by table |

---

## Migration System

Migrations use CodeIgniter 3's timestamp-based system (`YYYYMMDDHHMMSS` prefix). Each migration contains `up()` and `down()` methods.

| Setting | Value |
|---------|-------|
| Type | Timestamp |
| Total | 326 |
| Earliest | December 2024 (`20241211*`) |
| Latest | `20260311160036` |
| Auto-Migrate | Enabled |
| Directory | `application/migrations/` |

See [Migration System](migration-system.md) for detailed conventions and examples.

---

## Cross-References

| Document | Path |
|----------|------|
| Core Tables | `03-database-design/core-tables.md` |
| CRM Tables | `03-database-design/crm-tables.md` |
| Order Tables | `03-database-design/order-tables.md` |
| Configuration Tables | `03-database-design/configuration-tables.md` |
| Triggers & Functions | `03-database-design/triggers-and-functions.md` |
| Migration System | `03-database-design/migration-system.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Migration Guide | `08-development-guidelines/migration-guide.md` |
