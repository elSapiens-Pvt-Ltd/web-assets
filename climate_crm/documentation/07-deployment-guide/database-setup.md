> Module: climate/deployment/database-setup
> Last updated: 2026-03-11

# Database Setup

## Table of Contents

- [Overview](#overview)
- [Initial Setup](#initial-setup)
  - [1. Create Database](#1-create-database)
  - [2. Create Database User](#2-create-database-user)
  - [3. Configure Connection](#3-configure-connection)
- [Migration System](#migration-system)
  - [Configuration](#configuration)
  - [Running Migrations](#running-migrations)
  - [Migration File Location](#migration-file-location)
  - [Migration File Format](#migration-file-format)
  - [Naming Conventions](#naming-conventions)
- [Table Naming Conventions](#table-naming-conventions)
- [Core Tables Overview](#core-tables-overview)
  - [User & Auth](#user--auth)
  - [CRM Core](#crm-core)
  - [Orders](#orders)
  - [Configuration](#configuration-1)
  - [Integrations](#integrations)
- [Creating a New Migration](#creating-a-new-migration)
- [Seed Data](#seed-data)
  - [Roles](#roles)
  - [Contact Sources](#contact-sources)
  - [Default Settings](#default-settings)
- [Backup & Restore](#backup--restore)
- [Performance Considerations](#performance-considerations)
- [Cross-References](#cross-references)

---

## Overview

The Climate CRM uses MySQL/MariaDB with CodeIgniter's migration system for schema management. The database contains 300+ tables with `tbl_` and `temp_tbl_` prefixes.

---

## Initial Setup

### 1. Create Database

```sql
CREATE DATABASE climate
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### 2. Create Database User

```sql
CREATE USER 'climate_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON climate.* TO 'climate_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configure Connection

Set environment variables (or update `application/config/database.php`):

```bash
DBHOST=127.0.0.1
DBUSER=climate_user
DBPASSWORD=strong_password_here
DBNAME=climate
```

**Database config reference** (`application/config/database.php`):

```php
$db['default'] = array(
    'dsn'      => '',
    'hostname' => $_SERVER['DBHOST'] ?? '127.0.0.1',
    'username' => $_SERVER['DBUSER'] ?? 'root',
    'password' => $_SERVER['DBPASSWORD'] ?? '',
    'database' => $_SERVER['DBNAME'] ?? 'climate',
    'dbdriver' => 'mysqli',
    'char_set' => 'utf8mb4',
    'dbcollat' => 'utf8mb4_unicode_ci',
    'swap_pre' => '',
    'encrypt'  => FALSE,
    'compress' => FALSE,
    'stricton' => FALSE,
    'failover' => array(),
    'save_queries' => TRUE
);
```

---

## Migration System

### Configuration

File: `application/config/migration.php`

```php
$config['migration_enabled'] = TRUE;
$config['migration_type'] = 'timestamp';           // YYYYMMDDHHMMSS format
$config['migration_table'] = 'migrations';          // Tracks applied migrations
$config['migration_auto_latest'] = TRUE;            // Auto-migrate on load
$config['migration_version'] = 20260311160036;      // Current version
```

### Running Migrations

```bash
# Run all pending migrations
cd /path/to/climate-api
php index.php migrate

# Or via HTTP (if migration controller exists)
curl http://climate.loc/index.php/migrate
```

With `migration_auto_latest = TRUE`, migrations run automatically on the first request after deployment.

### Migration File Location

```
climate-api/application/migrations/
├── 20240101120000_initial_schema.php
├── 20240215130001_add_whatsapp_tables.php
├── 20251205130001_create_holiday_calendar_tables.php
├── ...
└── 20260311160036_backfill_conversation_type.php
```

### Migration File Format

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Migration_Create_example_table extends CI_Migration {

    public function up() {
        // Create table
        $this->dbforge->add_field([
            'id' => [
                'type' => 'BIGINT',
                'unsigned' => TRUE,
                'auto_increment' => TRUE
            ],
            'name' => [
                'type' => 'VARCHAR',
                'constraint' => 255
            ],
            'status' => [
                'type' => 'ENUM',
                'constraint' => ['active', 'inactive'],
                'default' => 'active'
            ],
            'created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
            'updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
        ]);
        $this->dbforge->add_key('id', TRUE);
        $this->dbforge->create_table('tbl_example', TRUE);

        // Add indexes
        $this->db->query('ALTER TABLE tbl_example ADD INDEX idx_status (status)');
    }

    public function down() {
        $this->dbforge->drop_table('tbl_example', TRUE);
    }
}
```

### Naming Conventions

| Pattern | Example |
|---------|---------|
| File name | `20260311120000_create_feature_table.php` |
| Class name | `Migration_Create_feature_table` |
| Timestamp | YYYYMMDDHHMMSS (Year, Month, Day, Hour, Minute, Second) |

---

## Table Naming Conventions

| Prefix | Purpose | Examples |
|--------|---------|----------|
| `tbl_` | Standard tables | `tbl_orders`, `tbl_users`, `tbl_settings` |
| `temp_tbl_` | CRM data tables (migrated from old schema) | `temp_tbl_contacts`, `temp_tbl_accounts` |

The `temp_tbl_` prefix is historical — these tables were created during a data migration from an older system and the prefix was retained for backward compatibility.

---

## Core Tables Overview

### User & Auth

```sql
tbl_users              -- System users (agents, managers, admins)
tbl_authentications    -- JWT tokens, login_hash, last_active
tbl_user_roles         -- Role assignments
tbl_roles              -- Role definitions
tbl_capability         -- Permission capabilities
tbl_role_capability    -- Role-to-capability mapping
```

### CRM Core

```sql
temp_tbl_accounts          -- Customer/company accounts
temp_tbl_contacts          -- Contact records
temp_tbl_contact_handles   -- Phone/email/social handles
temp_tbl_accounts_address  -- Billing/shipping addresses
tbl_open_conversations     -- Active conversation state machine
tbl_whatsapp_messages      -- All messages (WhatsApp, system, notes)
tbl_contact_assignment_history  -- Assignment audit trail
tbl_contact_sources        -- Lead source master list
```

### Orders

```sql
tbl_orders             -- Order header
tbl_order_items        -- Line items
tbl_order_data         -- Metadata (address snapshot, transport)
tbl_payments           -- Payment records
tbl_opportunities      -- CRM opportunities linked to orders
tbl_admin_approvals    -- Approval workflows
```

### Configuration

```sql
tbl_settings           -- System settings (key-value)
tbl_menu               -- Navigation menu items
tbl_company            -- Company master data
tbl_company_work_hours -- Working hours for round-robin
tbl_user_leaves        -- Leave calendar
tbl_holiday_calendar   -- Company holidays
```

### Integrations

```sql
tbl_whatsapp_callback      -- Raw webhook payloads (audit)
tbl_whatsapp_token         -- WhatsApp API credentials
tbl_justdial_leads         -- JustDial lead data
tbl_facebook_leads         -- Facebook lead data
tbl_indiamart_leads        -- IndiaMart lead data
tbl_api_auth               -- External API credentials
```

---

## Creating a New Migration

### Step 1: Generate timestamp

```bash
date +%Y%m%d%H%M%S
# Output: 20260311170000
```

### Step 2: Create migration file

```bash
touch application/migrations/20260311170000_add_my_feature.php
```

### Step 3: Write migration class

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Migration_Add_my_feature extends CI_Migration {

    public function up() {
        // Schema changes
        $this->dbforge->add_column('tbl_orders', [
            'new_field' => [
                'type' => 'VARCHAR',
                'constraint' => 100,
                'null' => TRUE,
                'after' => 'existing_field'
            ]
        ]);
    }

    public function down() {
        $this->dbforge->drop_column('tbl_orders', 'new_field');
    }
}
```

### Step 4: Update migration version

In `application/config/migration.php`, update:

```php
$config['migration_version'] = 20260311170000;
```

### Step 5: Run migration

```bash
php index.php migrate
```

---

## Seed Data

After initial migration, the following seed data is required:

### Roles

```sql
INSERT INTO tbl_roles (role_name, role_description) VALUES
('Super Admin', 'Full system access'),
('Admin', 'Administrative access'),
('Manager', 'Team management'),
('Agent', 'CRM agent operations');
```

### Contact Sources

```sql
INSERT INTO tbl_contact_sources (source_name, source_type) VALUES
('Whatsapp', 'direct'),
('JustDial', 'webhook'),
('IndiaMart', 'api'),
('Facebook', 'webhook'),
('Website', 'direct'),
('Referral', 'manual'),
('Walk-in', 'manual');
```

### Default Settings

```sql
INSERT INTO tbl_settings (setting_name, field_value) VALUES
('agent_allocation', '[]'),
('round_robin_enabled', '1');
```

---

## Backup & Restore

### Backup

```bash
mysqldump -u climate_user -p climate > climate_backup_$(date +%Y%m%d).sql
```

### Restore

```bash
mysql -u climate_user -p climate < climate_backup_20260311.sql
```

### Automated Backup (Cron)

```bash
0 2 * * * mysqldump -u climate_user -p'password' climate | gzip > /backups/climate_$(date +\%Y\%m\%d).sql.gz
```

---

## Performance Considerations

- **Character set**: `utf8mb4` supports full Unicode including emojis (important for WhatsApp messages)
- **Indexes**: Ensure indexes on frequently queried columns (`contact_id`, `account_id`, `handle_value`, `conversation_stage`)
- **Query logging**: `save_queries = TRUE` is useful for development; consider disabling in production for memory savings
- **Connection pooling**: Use persistent connections for high-traffic deployments

---

## Cross-References

- [System Architecture Overview](../01-system-architecture/overview.md)
- [Backend Architecture](../01-system-architecture/backend-architecture.md)
- [Database Schema Overview](../03-database-design/schema-overview.md)
- [Migration System](../03-database-design/migration-system.md)
- [Environment Setup](environment-setup.md)
- [Backend Setup](backend-setup.md)
- [Migration Guide](../08-development-guidelines/migration-guide.md)
- [Coding Standards](../08-development-guidelines/coding-standards.md)
