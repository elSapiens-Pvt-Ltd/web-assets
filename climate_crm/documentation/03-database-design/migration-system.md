# Migration System

> Module: `climate/database/migrations`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [File Naming Convention](#file-naming-convention)
3. [Class Naming Convention](#class-naming-convention)
4. [Running Migrations](#running-migrations)
5. [Migration Categories](#migration-categories)
6. [Example Migration](#example-migration)
7. [Temporary Table Lifecycle](#temporary-table-lifecycle)
8. [Best Practices](#best-practices)
9. [Cross-References](#cross-references)

---

## Overview

The Climate CRM uses CodeIgniter 3's timestamp-based migration system. Each migration is a PHP class with `up()` and `down()` methods that modify the database schema.

| Setting | Value |
|---------|-------|
| Framework | CodeIgniter 3 Migration Class |
| Type | Timestamp-based (`YYYYMMDDHHMMSS`) |
| Table | `tbl_migrations` (tracks current version) |
| Total Migrations | 326 |
| Earliest | `20241211*` (December 2024) |
| Latest | `20260311160036` |
| Directory | `application/migrations/` |
| Auto-Migrate | Enabled (migrates to latest on app startup) |

---

## File Naming Convention

Migration files follow the pattern `YYYYMMDDHHMMSS_description.php`:

| Segment | Format | Example |
|---------|--------|---------|
| Year | `YYYY` | `2026` |
| Month | `MM` | `03` |
| Day | `DD` | `11` |
| Hour | `HH` | `16` |
| Minute | `MM` | `00` |
| Second | `SS` | `36` |
| Separator | `_` | `_` |
| Description | `snake_case` | `create_contact_assignment_history` |

**Examples**:
```
20241211144520_add_message_source_to_whatsapp.php
20251224000057_create_new_customer_structure.php
20251224000124_enhance_open_conversations_table.php
20251224000321_split_order_status_fields.php
20260311160023_create_contact_assignment_history.php
20260311160036_backfill_assignment_history.php
```

---

## Class Naming Convention

The class name is `Migration_` followed by the description portion with the first letter capitalized:

```php
// File: 20260311160023_create_contact_assignment_history.php
class Migration_Create_contact_assignment_history extends CI_Migration {
    public function up() { ... }
    public function down() { ... }
}
```

| Rule | Example |
|------|---------|
| Prefix | `Migration_` |
| First word capitalized | `Create_`, `Add_`, `Modify_` |
| Remaining words | lowercase with underscores |
| Must match filename description | `create_contact_assignment_history` → `Migration_Create_contact_assignment_history` |

---

## Running Migrations

### CLI Execution

```bash
# Migrate to latest version
php /path/to/climate-api/index.php migrate

# Check current migration version
mysql -e "SELECT * FROM tbl_migrations;" climate
```

### Auto-Migration

With auto-migration enabled in `application/config/migration.php`, the application automatically runs pending migrations on startup. The `migration_version` setting in `tbl_migrations` tracks the current version.

### File Permissions

All migration files should be readable by the PHP process:

```bash
chmod 644 application/migrations/*.php
```

---

## Migration Categories

### Initial Schema Creation (December 2024)

The first wave of migrations created the foundational tables — WhatsApp messaging, conversation management, and basic CRM structure:

```
20241211144520_add_message_source_to_whatsapp.php
```

### Profile Restructuring (December 2025)

A major restructuring migrated from the legacy `tbl_whatsapp_contacts` / `tbl_accounts` tables to the normalized `temp_tbl_*` profile model:

```
20251224000057_create_new_customer_structure.php    # Create temp_tbl_accounts, contacts, handles, addresses
20251224000087_modify_tbl_contact_handles.php       # Add constraints and phone_code
20251224000121_populate_conversations_from_whatsapp_contacts.php
20251224000124_enhance_open_conversations_table.php # Add CRM fields to conversations
20251224000135_add_phone_number_to_contact_handles.php
```

### Order Status Split (December 2025)

The monolithic `order_status` ENUM was split into four independent status dimensions:

```
20251224000321_split_order_status_fields.php   # order_status, payment_status, fulfillment_status, shipping_status
20260210170000_add_confirmed_order_status.php  # Added 'confirmed' to order_status
```

### CRM Enhancements (2026)

Assignment history, ship-without-pay workflow, and reporting:

```
20250910123020_add_ship_without_pay_columns_to_orders.php
20260206000002_add_ship_without_pay_rejected_at.php
20260311160023_create_contact_assignment_history.php
20260311160036_backfill_assignment_history.php
```

---

## Example Migration

A migration that creates new tables using CodeIgniter's dbforge:

```php
<?php
// 20260101000001_create_holiday_calendar_tables.php

class Migration_Create_holiday_calendar_tables extends CI_Migration {

    public function up() {
        // Create tbl_company_holidays
        $this->dbforge->add_field(array(
            'id' => array(
                'type' => 'INT',
                'unsigned' => TRUE,
                'auto_increment' => TRUE
            ),
            'company_id' => array(
                'type' => 'INT',
                'unsigned' => TRUE,
            ),
            'holiday_date' => array(
                'type' => 'DATE',
            ),
            'holiday_name' => array(
                'type' => 'VARCHAR',
                'constraint' => 100,
            ),
            'created_on' => array(
                'type' => 'DATETIME',
                'default' => 'CURRENT_TIMESTAMP',
            ),
        ));
        $this->dbforge->add_key('id', TRUE);
        $this->dbforge->add_key('company_id');
        $this->dbforge->create_table('company_holidays', TRUE);

        // Create tbl_user_leaves
        $this->dbforge->add_field(array(
            'id' => array(
                'type' => 'INT',
                'unsigned' => TRUE,
                'auto_increment' => TRUE
            ),
            'user_id' => array(
                'type' => 'INT',
                'unsigned' => TRUE,
            ),
            'leave_date' => array(
                'type' => 'DATE',
            ),
            'leave_type' => array(
                'type' => 'ENUM',
                'constraint' => array('full_day', 'first_half', 'second_half'),
                'default' => 'full_day',
            ),
            'status' => array(
                'type' => 'ENUM',
                'constraint' => array('pending', 'approved', 'rejected'),
                'default' => 'pending',
            ),
        ));
        $this->dbforge->add_key('id', TRUE);
        $this->dbforge->add_key('user_id');
        $this->dbforge->create_table('user_leaves', TRUE);
    }

    public function down() {
        $this->dbforge->drop_table('user_leaves', TRUE);
        $this->dbforge->drop_table('company_holidays', TRUE);
    }
}
```

Many migrations also use raw SQL for ALTER TABLE operations, index additions, and data backfills:

```php
public function up() {
    // Add column via raw SQL
    $this->db->query("ALTER TABLE tbl_open_conversations
        ADD COLUMN conversation_stage ENUM('new','attempted','contacted','nurturing','qualified','unqualified')
        DEFAULT 'new' AFTER conversation_type");

    // Add index
    $this->db->query("ALTER TABLE tbl_open_conversations
        ADD INDEX idx_conversation_stage (conversation_stage)");
}
```

---

## Temporary Table Lifecycle

The `temp_tbl_*` tables followed a structured migration lifecycle:

1. **Creation**: New normalized tables created with `dbforge` (`20251224000057`)
2. **Population**: Data migrated from legacy tables via INSERT...SELECT backfill queries (`20251224000121`)
3. **Validation**: Data integrity verified — row counts, foreign key consistency, handle uniqueness
4. **Cutover**: All controllers and models updated to reference `temp_tbl_*` tables
5. **Legacy Retention**: Original `tbl_whatsapp_contacts` and `tbl_accounts` tables retained for reference but no longer written to

---

## Best Practices

### Do

- Use `$this->dbforge` for table creation (handles `tbl_` prefix if configured)
- Include `down()` method for rollback capability
- Use `IF NOT EXISTS` / `IF EXISTS` guards for idempotency
- Add indexes in the same migration that creates the column
- Use ENUM for fixed value sets; VARCHAR for extensible types
- Test migrations on a copy of production data before deploying

### Avoid

- Dropping tables or columns without a backup plan
- Changing ENUM values without considering existing data
- Running large data backfills without batching (can lock tables)
- Modifying the `system/` directory or core CI migration class

---

## Cross-References

| Document | Path |
|----------|------|
| Schema Overview | `03-database-design/schema-overview.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Migration Guide (development) | `08-development-guidelines/migration-guide.md` |
| Database Setup (deployment) | `07-deployment-guide/database-setup.md` |
