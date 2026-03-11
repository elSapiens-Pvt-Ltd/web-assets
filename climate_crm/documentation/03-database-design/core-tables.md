# Core Tables — Accounts, Contacts, Handles, Addresses

> Module: `climate/database/core`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [temp_tbl_accounts](#temp_tbl_accounts)
3. [temp_tbl_contacts](#temp_tbl_contacts)
4. [temp_tbl_contact_handles](#temp_tbl_contact_handles)
5. [temp_tbl_accounts_address](#temp_tbl_accounts_address)
6. [Table Lifecycle](#table-lifecycle)
7. [Cross-References](#cross-references)

---

## Overview

The core tables store the fundamental entities of the CRM: accounts (companies/individuals), contacts (people), contact handles (phone numbers, emails), and addresses (billing/shipping). These tables use the `temp_tbl_` prefix from a migration that restructured the original `tbl_whatsapp_contacts` and `tbl_accounts` tables into a normalized profile model. Despite the prefix, they are the canonical active tables.

---

## temp_tbl_accounts

Stores company or individual customer accounts with business details, order statistics, and agent ownership.

**Created by**: `20251224000057_create_new_customer_structure.php`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `account_id` | BIGINT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `account_name` | VARCHAR(100) | Yes | NULL | Company or individual name |
| `account_type` | ENUM('Business','Individual') | No | `'Individual'` | Account classification |
| `total_orders` | DECIMAL(10,2) | No | `0.00` | Total order value |
| `completed_orders` | DECIMAL(10,2) | No | `0.00` | Completed order value |
| `pending_orders` | DECIMAL(10,2) | No | `0.00` | Pending order value |
| `total_revenue` | DECIMAL(10,2) | No | `0.00` | Total revenue from account |
| `total_paid` | DECIMAL(10,2) | No | `0.00` | Total amount paid |
| `order_value` | DECIMAL(10,2) | No | `0.00` | Current order pipeline value |
| `order_count` | INT | No | `0` | Number of orders placed |
| `first_order_date` | DATE | Yes | NULL | Date of first order |
| `last_order_date` | DATE | Yes | NULL | Date of most recent order |
| `region` | VARCHAR(20) | Yes | NULL | Geographic region |
| `residence_type` | VARCHAR(20) | Yes | NULL | Residential classification |
| `distribution_type` | ENUM('retailer','wholesaler','review_pending') | No | `'retailer'` | Distribution channel |
| `business_type` | VARCHAR(50) | Yes | NULL | Type of business |
| `bussiness_category` | VARCHAR(50) | Yes | NULL | Business category (note: legacy typo) |
| `closed_at` | DATETIME | Yes | NULL | When the account was closed |
| `account_owner_id` | VARCHAR(50) | Yes | NULL | FK to `tbl_users.user_id` — the responsible agent |
| `status` | ENUM('active','inactive','closed') | No | `'active'` | Account status |
| `account_score` | INT | No | `0` | Engagement score |
| `account_fssai_number` | VARCHAR(25) | Yes | NULL | FSSAI food license number |
| `is_export` | TINYINT(1) | No | `0` | Whether account is for export business |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |
| `updated_on` | DATETIME | No | CURRENT_TIMESTAMP ON UPDATE | Last update time |

**Business Rules**:
- `account_owner_id` determines Priority 1 in the agent assignment system — all new conversations for contacts under this account go to this agent
- Order statistics (`total_orders`, `completed_orders`, `pending_orders`, etc.) are maintained by the order lifecycle
- The `distribution_type` value `'review_pending'` is used for new accounts awaiting classification

---

## temp_tbl_contacts

Stores individual contacts belonging to accounts. Each account can have multiple contacts, with one designated as primary.

**Created by**: `20251224000057_create_new_customer_structure.php`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `contact_id` | BIGINT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `account_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_accounts` |
| `contact_name` | VARCHAR(150) | Yes | NULL | Full name |
| `designation` | VARCHAR(50) | Yes | NULL | Job title / designation |
| `is_primary_contact` | TINYINT(1) | No | `0` | Whether this is the account's primary contact |
| `status` | ENUM('active','inactive','deleted') | No | `'active'` | Contact status (soft delete) |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |
| `updated_on` | DATETIME | No | CURRENT_TIMESTAMP ON UPDATE | Last update time |

**Indexes**: `account_id`

**Business Rules**:
- Only one contact per account should have `is_primary_contact = 1`
- Contacts are soft-deleted by setting `status = 'deleted'`, not by removing the row
- When an account is created, a default primary contact is created in the same transaction

---

## temp_tbl_contact_handles

Stores communication handles (phone numbers, email addresses, social IDs) for contacts. Handles are the primary mechanism for routing inbound messages to the correct contact and conversation.

**Created by**: `20251224000057_create_new_customer_structure.php`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `handle_id` | BIGINT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `account_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_accounts` |
| `contact_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_contacts` |
| `label` | VARCHAR(50) | Yes | NULL | Handle label (e.g., "Work", "Personal") |
| `handle_type` | VARCHAR(50) | Yes | NULL | Type: `phone`, `email`, `instagram`, `telegram`, etc. |
| `handle_value` | VARCHAR(255) | Yes | NULL | The actual phone number, email address, etc. |
| `country_code` | VARCHAR(10) | Yes | NULL | Phone country code (e.g., `+91`) |
| `is_primary` | TINYINT(1) | No | `0` | Whether this is the primary handle of its type |
| `is_verified` | TINYINT(1) | No | `0` | Whether the handle has been verified |
| `is_whatsapp` | TINYINT(1) | No | `0` | Whether WhatsApp is available on this number |
| `status` | ENUM('active','inactive','deleted') | No | `'active'` | Handle status |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |
| `updated_on` | DATETIME | No | CURRENT_TIMESTAMP ON UPDATE | Last update time |

**Indexes**: `account_id`, `contact_id`

**Notes**:
- `handle_type` is VARCHAR(50), not an ENUM — this allows adding new handle types without a migration
- `is_whatsapp` is set automatically when a WhatsApp message is received from that phone number
- Phone handles are normalized to 10-digit Indian format (stripping `+91`, `91`, leading `0`) by `phone_number_helper.php` before lookup
- Handle uniqueness is enforced at the application level — no two active contacts should share the same phone number or email

---

## temp_tbl_accounts_address

Stores billing and shipping addresses for accounts. Each account can have multiple addresses of each type.

**Created by**: `20251224000057_create_new_customer_structure.php`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `address_id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `account_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_accounts` |
| `gst_number` | VARCHAR(15) | Yes | NULL | GST registration number for this address |
| `address_type` | ENUM('billing','shipping','billing & shipping') | Yes | NULL | Address usage type |
| `contact_name` | VARCHAR(255) | Yes | NULL | Contact person at this address |
| `contact_number` | VARCHAR(30) | Yes | NULL | Contact phone at this address |
| `line_1` | VARCHAR(100) | Yes | NULL | Address line 1 |
| `line_2` | VARCHAR(100) | Yes | NULL | Address line 2 |
| `city` | VARCHAR(100) | Yes | NULL | City |
| `state` | VARCHAR(100) | Yes | NULL | State name |
| `state_id` | INT UNSIGNED | Yes | NULL | FK to `tbl_states` |
| `country` | VARCHAR(100) | Yes | NULL | Country name |
| `country_id` | INT UNSIGNED | Yes | NULL | FK to `tbl_countries` |
| `pincode` | VARCHAR(10) | Yes | NULL | Postal code |
| `latitude` | DECIMAL(10,8) | Yes | NULL | GPS latitude |
| `longitude` | DECIMAL(11,8) | Yes | NULL | GPS longitude |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |
| `updated_on` | DATETIME | No | CURRENT_TIMESTAMP ON UPDATE | Last update time |

**Indexes**: `account_id`

**Business Rules**:
- The `state_id` of the billing address determines tax calculation: same state as the company → CGST + SGST; different state → IGST
- GST number is stored per address (not per account) because a business can have different GST registrations at different locations
- The `contact_name` and `contact_number` on the address may differ from the account's primary contact — they represent the person at that specific location

---

## Table Lifecycle

The `temp_tbl_*` tables were created during the December 2024 migration restructuring. The lifecycle was:

1. **Creation**: New `temp_tbl_*` tables created with the normalized schema
2. **Population**: Data migrated from legacy `tbl_whatsapp_contacts` and `tbl_accounts` tables via backfill migrations
3. **Validation**: Data integrity verified, duplicates resolved
4. **Cutover**: All controllers and models updated to use `temp_tbl_*` tables
5. **Legacy**: Original tables retained for reference but no longer written to

The models reference these tables directly:
- `ProfileAccountsModel` → `temp_tbl_accounts`
- `ProfileContactsModel` → `temp_tbl_contacts`
- `ProfileContactHandlesModel` → `temp_tbl_contact_handles`
- `ProfileAddressModel` → `temp_tbl_accounts_address`

---

## Cross-References

| Document | Path |
|----------|------|
| Schema Overview | `03-database-design/schema-overview.md` |
| CRM Tables | `03-database-design/crm-tables.md` |
| Order Tables | `03-database-design/order-tables.md` |
| Configuration Tables | `03-database-design/configuration-tables.md` |
| Accounts API | `05-api-documentation/accounts-api.md` |
| Contact Handles Module | `04-core-modules/contacts-handles.md` |
