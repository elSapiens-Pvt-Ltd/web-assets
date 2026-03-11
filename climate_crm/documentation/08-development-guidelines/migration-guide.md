> Module: climate/guidelines/migration-guide
> Last updated: 2026-03-11

# Migration Guide

## Table of Contents

- [Overview](#overview)
- [Migration System Configuration](#migration-system-configuration)
- [Creating a Migration](#creating-a-migration)
  - [Step 1: Generate Timestamp](#step-1-generate-timestamp)
  - [Step 2: Create File](#step-2-create-file)
  - [Naming Convention](#naming-convention)
  - [Step 3: Write Migration Class](#step-3-write-migration-class)
- [Common Migration Patterns](#common-migration-patterns)
  - [Create Table](#create-table)
  - [Add Columns](#add-columns)
  - [Modify Column](#modify-column)
  - [Add Index](#add-index)
  - [Insert Seed Data](#insert-seed-data)
  - [Data Backfill](#data-backfill)
- [Running Migrations](#running-migrations)
  - [Automatic (Default)](#automatic-default)
  - [Manual via CLI](#manual-via-cli)
  - [Manual via HTTP](#manual-via-http)
- [Update Migration Version](#update-migration-version)
- [Migration Categories](#migration-categories)
- [Temp Table Convention](#temp-table-convention)
- [Best Practices](#best-practices)
  - [Do](#do)
  - [Don't](#dont)
  - [Transaction Safety](#transaction-safety)
- [Troubleshooting](#troubleshooting)
- [Cross-References](#cross-references)

---

## Overview

The Climate CRM uses CodeIgniter 3's timestamp-based migration system to manage database schema changes. This guide covers creating, running, and managing migrations.

---

## Migration System Configuration

File: `application/config/migration.php`

```php
$config['migration_enabled'] = TRUE;
$config['migration_type'] = 'timestamp';            // YYYYMMDDHHMMSS format
$config['migration_table'] = 'migrations';           // Tracking table
$config['migration_auto_latest'] = TRUE;             // Auto-run on first request
$config['migration_version'] = 20260311160036;       // Current version
```

With `migration_auto_latest = TRUE`, pending migrations run automatically on the next HTTP request after deployment.

---

## Creating a Migration

### Step 1: Generate Timestamp

```bash
date +%Y%m%d%H%M%S
# Example: 20260312100000
```

### Step 2: Create File

```bash
touch application/migrations/20260312100000_description_of_change.php
```

### Naming Convention

| Part | Format | Example |
|------|--------|---------|
| Timestamp | YYYYMMDDHHMMSS | `20260312100000` |
| Separator | `_` | `_` |
| Description | snake_case | `add_tracking_to_orders` |
| Extension | `.php` | `.php` |
| Class name | `Migration_` + capitalize first letter | `Migration_Add_tracking_to_orders` |

### Step 3: Write Migration Class

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Migration_Add_tracking_to_orders extends CI_Migration {

    public function up() {
        // Forward migration — apply changes
    }

    public function down() {
        // Reverse migration — undo changes
    }
}
```

---

## Common Migration Patterns

### Create Table

```php
public function up() {
    $this->dbforge->add_field([
        'id' => [
            'type' => 'BIGINT',
            'unsigned' => TRUE,
            'auto_increment' => TRUE
        ],
        'name' => [
            'type' => 'VARCHAR',
            'constraint' => 255,
            'null' => FALSE
        ],
        'description' => [
            'type' => 'TEXT',
            'null' => TRUE
        ],
        'status' => [
            'type' => 'ENUM',
            'constraint' => ['active', 'inactive', 'deleted'],
            'default' => 'active'
        ],
        'amount' => [
            'type' => 'DECIMAL',
            'constraint' => '12,2',
            'default' => '0.00'
        ],
        'created_by' => [
            'type' => 'BIGINT',
            'unsigned' => TRUE,
            'null' => TRUE
        ],
        'created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
        'updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
    ]);

    $this->dbforge->add_key('id', TRUE);
    $this->dbforge->create_table('tbl_my_table', TRUE);

    // Add indexes
    $this->db->query('ALTER TABLE tbl_my_table ADD INDEX idx_status (status)');
    $this->db->query('ALTER TABLE tbl_my_table ADD INDEX idx_created_by (created_by)');
}

public function down() {
    $this->dbforge->drop_table('tbl_my_table', TRUE);
}
```

### Add Columns

```php
public function up() {
    $this->dbforge->add_column('tbl_orders', [
        'tracking_number' => [
            'type' => 'VARCHAR',
            'constraint' => 100,
            'null' => TRUE,
            'after' => 'courier_id'
        ],
        'shipped_at' => [
            'type' => 'DATETIME',
            'null' => TRUE,
            'after' => 'tracking_number'
        ]
    ]);
}

public function down() {
    $this->dbforge->drop_column('tbl_orders', 'tracking_number');
    $this->dbforge->drop_column('tbl_orders', 'shipped_at');
}
```

### Modify Column

```php
public function up() {
    $this->dbforge->modify_column('tbl_orders', [
        'status' => [
            'type' => 'ENUM',
            'constraint' => ['draft', 'confirmed', 'final', 'despatched', 'delivered', 'cancelled', 'returned'],
            'default' => 'draft'
        ]
    ]);
}
```

### Add Index

```php
public function up() {
    $this->db->query('ALTER TABLE tbl_whatsapp_messages ADD INDEX idx_conversation_id (conversation_id)');
    $this->db->query('ALTER TABLE tbl_whatsapp_messages ADD INDEX idx_handle_value (handle_value)');
}

public function down() {
    $this->db->query('ALTER TABLE tbl_whatsapp_messages DROP INDEX idx_conversation_id');
    $this->db->query('ALTER TABLE tbl_whatsapp_messages DROP INDEX idx_handle_value');
}
```

### Insert Seed Data

```php
public function up() {
    // Add capabilities
    $capabilities = [
        ['module' => 'shipping', 'cap' => 'shipping.view', 'title' => 'View Shipping'],
        ['module' => 'shipping', 'cap' => 'shipping.manage', 'title' => 'Manage Shipping'],
    ];

    foreach ($capabilities as $c) {
        $this->db->insert('tbl_capability', [
            'module_name' => $c['module'],
            'capability' => $c['cap'],
            'capability_title' => $c['title'],
            'capability_description' => $c['title'],
            'menu_id' => 0,
            'sort_order' => 100
        ]);
    }
}

public function down() {
    $this->db->where('module_name', 'shipping')->delete('tbl_capability');
}
```

### Data Backfill

```php
public function up() {
    // Backfill a computed column from existing data
    $this->db->query("
        UPDATE tbl_open_conversations oc
        INNER JOIN temp_tbl_contacts c ON c.contact_id = oc.contact_id
        SET oc.account_id = c.account_id
        WHERE oc.account_id IS NULL
        AND c.account_id IS NOT NULL
    ");
}

public function down() {
    // Backfills are typically not reversible
}
```

---

## Running Migrations

### Automatic (Default)

With `migration_auto_latest = TRUE`, migrations run on the next request after deployment. No manual action needed.

### Manual via CLI

```bash
cd /path/to/climate-api
php index.php migrate
```

### Manual via HTTP

If a migration controller exists:

```bash
curl http://climate.loc/index.php/migrate
```

---

## Update Migration Version

After creating a new migration, update `application/config/migration.php`:

```php
$config['migration_version'] = 20260312100000;  // Your new timestamp
```

This tells CodeIgniter what the latest migration version should be.

---

## Migration Categories

| Category | Description | Example |
|----------|-------------|---------|
| Schema creation | New tables | `create_holiday_calendar_tables` |
| Schema alteration | Add/modify columns | `add_tracking_to_orders` |
| Index management | Add/remove indexes | `add_index_on_handle_value` |
| Data backfill | Populate computed fields | `backfill_assignment_history` |
| Seed data | Insert reference data | `add_shipping_capabilities` |
| Cleanup | Remove deprecated tables/columns | `drop_legacy_lead_tables` |

---

## Temp Table Convention

The project uses `temp_tbl_` prefix for tables that were migrated from an older schema:

```
temp_tbl_contacts         -- Migrated contact records
temp_tbl_contact_handles  -- Migrated handle records
temp_tbl_accounts         -- Migrated account records
temp_tbl_accounts_address -- Migrated address records
```

These tables function identically to `tbl_` tables — the prefix is historical and retained for backward compatibility with existing queries.

---

## Best Practices

### Do

- Always write both `up()` and `down()` methods
- Use transactions for complex migrations
- Add indexes on frequently queried columns
- Test migrations on a copy of production data before deploying
- Use `IF NOT EXISTS` / `IF EXISTS` guards for safety
- Keep migrations small and focused — one logical change per file

### Don't

- Never modify an existing migration that has been applied
- Never delete migration files — create new ones to reverse changes
- Don't put business logic in migrations
- Don't use `$this->load->model()` in migrations — use raw SQL
- Don't change the timestamp of an existing migration

### Transaction Safety

For complex migrations with multiple operations:

```php
public function up() {
    $this->db->trans_begin();

    try {
        $this->dbforge->create_table('tbl_new_table', TRUE);
        $this->db->query("ALTER TABLE tbl_existing ADD COLUMN new_col VARCHAR(100)");
        $this->db->query("UPDATE tbl_existing SET new_col = 'default' WHERE new_col IS NULL");

        if ($this->db->trans_status() === FALSE) {
            throw new Exception('Transaction failed');
        }

        $this->db->trans_commit();
    } catch (Exception $e) {
        $this->db->trans_rollback();
        log_message('error', 'Migration failed: ' . $e->getMessage());
        throw $e;
    }
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Migration not running | Check `migration_version` in config matches your file timestamp |
| "Migration file not found" | Verify file name format: `{timestamp}_{description}.php` |
| "Class name mismatch" | Class must be `Migration_` + description with first letter capitalized |
| Migration partially applied | Check `migrations` table, fix data manually, update version |
| Duplicate timestamp | Ensure each migration has a unique timestamp |

---

## Cross-References

- [Backend Architecture](../01-system-architecture/backend-architecture.md) — How CodeIgniter hooks and the request lifecycle relate to migration auto-run
- [Frontend Architecture](../01-system-architecture/frontend-architecture.md) — Frontend has no direct role in migrations, but schema changes affect API responses consumed here
- [Folder Structure Overview](../02-folder-structure/overview.md) — Location of the `application/migrations/` and `application/config/migration.php` files
- [Migration System (Database Design)](../03-database-design/migration-system.md) — Database-level design decisions and table conventions that inform migration structure
- [Adding New Modules](./adding-modules.md) — Step 3 of the module guide shows a full migration example for a new feature table
- [Adding New APIs](./adding-apis.md) — Step 3 covers registering capabilities via migration when adding new endpoints
- [Deployment Guide](../07-deployment-guide/) — How migrations are triggered during the deployment process
