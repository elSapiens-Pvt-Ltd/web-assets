> Module: climate/deployment/backend-setup
> Last updated: 2026-03-11

# Backend Setup

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
  - [1. Install PHP Dependencies](#1-install-php-dependencies)
  - [2. Verify PHP Extensions](#2-verify-php-extensions)
  - [3. Set File Permissions](#3-set-file-permissions)
- [Web Server Configuration](#web-server-configuration)
  - [Apache](#apache)
  - [URL Rewriting (.htaccess)](#url-rewriting-htaccess)
- [CodeIgniter Configuration](#codeigniter-configuration)
  - [Main Config](#main-config-applicationconfigconfigphp)
  - [Routing](#routing-applicationconfigroutesuphp)
- [Authentication System](#authentication-system)
  - [JWT Configuration](#jwt-configuration)
  - [Hooks](#hooks-applicationconfighooksphp)
- [Redis Setup](#redis-setup)
  - [Start Redis Server](#start-redis-server)
  - [Redis Config](#redis-config)
  - [Usage in Application](#usage-in-application)
- [WebSocket Server](#websocket-server)
  - [Start WebSocket Server](#start-websocket-server)
  - [Production (Background Process)](#production-background-process)
- [Cron Jobs](#cron-jobs)
  - [Required Cron Jobs](#required-cron-jobs)
- [PDF Generation (wkhtmltopdf)](#pdf-generation-wkhtmltopdf)
- [AWS Services Configuration](#aws-services-configuration)
  - [S3 (File Storage)](#s3-file-storage)
  - [SES (Email)](#ses-email)
  - [CloudFront (CDN)](#cloudfront-cdn)
- [Logging](#logging)
  - [Application Logs](#application-logs)
  - [Log Format](#log-format)
  - [Log Rotation](#log-rotation)
- [Health Check](#health-check)
- [Troubleshooting](#troubleshooting)
- [Cross-References](#cross-references)

---

## Overview

The PHP backend (`climate-api`) runs on CodeIgniter 3 with Apache/Nginx. This guide covers installation, configuration, and service setup.

---

## Installation

### 1. Install PHP Dependencies

```bash
cd climate-api
composer install
```

Key packages:
- `firebase/php-jwt` — JWT token generation/validation
- `predis/predis` — Redis client
- `knplabs/knp-snappy` — PDF generation via wkhtmltopdf
- `aws/aws-sdk-php` — AWS S3, SES, CloudFront
- `takielias/codeigniter-websocket` — WebSocket server

### 2. Verify PHP Extensions

```bash
php -m | grep -E "mysqli|mbstring|json|curl|gd|xml|zip|redis"
```

Required extensions: `mysqli`, `mbstring`, `json`, `curl`, `gd`, `xml`, `zip`

Optional: `redis` (native extension, or use `predis` Composer package)

### 3. Set File Permissions

```bash
# Writable directories
chmod -R 775 application/cache/
chmod -R 775 application/logs/

# Secure config files
chmod 644 application/config/config.php
chmod 644 application/config/database.php
```

---

## Web Server Configuration

### Apache

Ensure `mod_rewrite` is enabled:

```bash
sudo a2enmod rewrite
sudo systemctl restart apache2
```

Virtual host:

```apache
<VirtualHost *:80>
    ServerName climate.loc
    DocumentRoot /path/to/climate-api

    <Directory /path/to/climate-api>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # PHP settings
    php_value upload_max_filesize 50M
    php_value post_max_size 50M
    php_value max_execution_time 300
    php_value memory_limit 256M

    # Pass environment variables
    SetEnv DBHOST 127.0.0.1
    SetEnv DBUSER climate_user
    SetEnv DBPASSWORD strong_password
    SetEnv DBNAME climate
    SetEnv JWT_KEY your_jwt_secret
    SetEnv S3_KEY your_s3_key
    SetEnv S3_TOKEN your_s3_token
    SetEnv S3_BUCKET your_bucket
    SetEnv CHAT_PORT 8988
</VirtualHost>
```

### URL Rewriting (.htaccess)

Already included in the project root:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php/$1 [L]
```

---

## CodeIgniter Configuration

### Main Config (`application/config/config.php`)

Key settings:

```php
$config['base_url'] = '';                    // Auto-detect
$config['index_page'] = 'index.php';         // URI segment
$config['uri_protocol'] = 'REQUEST_URI';
$config['log_threshold'] = 1;                // 0=off, 1=errors, 2=debug, 3=info, 4=all
$config['sess_expiration'] = 7200;           // Session timeout (2 hours)
$config['composer_autoload'] = TRUE;         // Composer packages
```

### Routing (`application/config/routes.php`)

```php
$route['default_controller'] = 'home';
$route['404_override'] = '';
$route['translate_uri_dashes'] = FALSE;
```

API endpoints follow the pattern: `/{Controller}/{method}`

Example: `/orders/save` → `Orders::save()`

---

## Authentication System

### JWT Configuration

```php
// In config.php
$config['jwt_key'] = $_SERVER['JWT_KEY'];
$config['jwt_algorithm'] = 'HS512';
$config['token_timeout'] = 48 * 60;  // 48 hours in minutes
```

### Hooks (`application/config/hooks.php`)

Two critical hooks handle authentication and CORS:

```php
$hook['pre_system'][] = array(
    'class'    => '',
    'function' => 'cors_headers',
    'filename' => 'cors.php',
    'filepath' => 'hooks'
);

$hook['post_controller_constructor'][] = array(
    'class'    => 'AuthHook',
    'function' => 'authenticate',
    'filename' => 'AuthHook.php',
    'filepath' => 'hooks'
);
```

**CORS Hook** (`pre_system`): Sets Access-Control headers before any processing.

**Auth Hook** (`post_controller_constructor`): Validates JWT token, enforces capabilities via `@capability` DocBlock annotations on controller methods.

---

## Redis Setup

### Start Redis Server

```bash
# Install
sudo apt install redis-server

# Start
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping
# → PONG
```

### Redis Config

File: `application/config/redis.php`

```php
$config['redis_default']['host'] = 'localhost';
$config['redis_default']['port'] = 6379;
$config['redis_default']['password'] = '';
$config['redis_default']['queue_name'] = 'message_queue';
```

### Usage in Application

Redis is used for:
- **Real-time queue**: Message delivery notifications to WebSocket clients
- **Caching**: Work hours, agent allocation data
- **Pub/Sub**: Broadcasting events (conversation updates, transfers)

---

## WebSocket Server

### Start WebSocket Server

```bash
cd /path/to/climate-api
php index.php chat start
```

The WebSocket server runs on the port defined by `CHAT_PORT` (default: 8988).

### Production (Background Process)

Use `systemd` or `supervisor` to keep the WebSocket server running:

**Supervisor config:**

```ini
[program:climate-websocket]
command=php /path/to/climate-api/index.php chat start
directory=/path/to/climate-api
autostart=true
autorestart=true
stderr_logfile=/var/log/climate-websocket.err.log
stdout_logfile=/var/log/climate-websocket.out.log
user=www-data
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start climate-websocket
```

---

## Cron Jobs

The application uses cron jobs for scheduled tasks:

```bash
# Edit crontab
crontab -e
```

### Required Cron Jobs

```bash
# Process scheduled follow-ups (every 5 minutes)
*/5 * * * * php /path/to/climate-api/index.php cron processScheduledFollowups >> /var/log/climate-cron.log 2>&1

# Sync IndiaMart leads (every 15 minutes)
*/15 * * * * php /path/to/climate-api/index.php cron indiaMartLeads >> /var/log/climate-cron.log 2>&1

# Send pending order confirmation emails (every 10 minutes)
*/10 * * * * php /path/to/climate-api/index.php cron sendOrderConfirmedMail >> /var/log/climate-cron.log 2>&1

# Update exchange rates (daily at midnight)
0 0 * * * php /path/to/climate-api/index.php cron getExchangeRates >> /var/log/climate-cron.log 2>&1

# Calculate agent FRT summary (daily at 00:30)
30 0 * * * php /path/to/climate-api/index.php cron calculateAgentFRTSummary >> /var/log/climate-cron.log 2>&1

# Calculate conversation aging snapshot (daily at 06:00)
0 6 * * * php /path/to/climate-api/index.php cron calculateAgingSnapshot >> /var/log/climate-cron.log 2>&1
```

---

## PDF Generation (wkhtmltopdf)

Required for invoice generation:

```bash
# Install wkhtmltopdf
sudo apt install wkhtmltopdf

# Or download specific version
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
sudo dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb
```

The `knp-snappy` library wraps wkhtmltopdf for PDF generation from HTML templates.

---

## AWS Services Configuration

### S3 (File Storage)

Environment variables:

```bash
S3_KEY=AKIAXXXXXXXXXXXXXXXXX
S3_TOKEN=your_secret_access_key
S3_BUCKET=climate-files
```

Used for:
- WhatsApp media storage (images, documents, audio, video)
- Invoice PDFs
- Profile photos
- Document uploads

### SES (Email)

Configured in `config.php`:

```php
$config['smtp_host'] = 'email-smtp.ap-south-1.amazonaws.com';
$config['smtp_port'] = 587;
$config['smtp_crypto'] = 'tls';
```

### CloudFront (CDN)

All S3 files are served via CloudFront:

```
URL: https://d1r95e2xq05b34.cloudfront.net/{media_key}
```

---

## Logging

### Application Logs

Location: `application/logs/`

Log levels configured in `config.php`:

```php
$config['log_threshold'] = 1;  // 1 = error only, 4 = all
```

### Log Format

```
ERROR - 2026-03-11 10:30:00 --> Failed to send WhatsApp message: API error 131047
```

### Log Rotation

Set up logrotate for production:

```
/path/to/climate-api/application/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
}
```

---

## Health Check

Verify the backend is running:

```bash
# Test API endpoint
curl http://climate.loc/index.php/home
# Should return JSON response

# Test Redis
redis-cli ping
# → PONG

# Test WebSocket
wscat -c ws://localhost:8988
# Should connect

# Test database
php index.php migrate
# Should complete without errors
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 500 Internal Server Error | Check `application/logs/` for PHP errors |
| Database connection failed | Verify DBHOST/DBUSER/DBPASSWORD env vars |
| JWT token invalid | Verify JWT_KEY matches between API and token |
| Redis connection refused | Ensure `redis-server` is running on port 6379 |
| WebSocket not connecting | Check CHAT_PORT env var and firewall rules |
| File upload fails | Verify S3 credentials and bucket permissions |
| PDF generation fails | Ensure wkhtmltopdf is installed and in PATH |
| CORS errors | Check hooks are loading correctly in hooks.php |

---

## Cross-References

- [System Architecture Overview](../01-system-architecture/overview.md)
- [Backend Architecture](../01-system-architecture/backend-architecture.md)
- [Database Schema Overview](../03-database-design/schema-overview.md)
- [Migration System](../03-database-design/migration-system.md)
- [Environment Setup](environment-setup.md)
- [Database Setup](database-setup.md)
- [Adding APIs](../08-development-guidelines/adding-apis.md)
- [Coding Standards](../08-development-guidelines/coding-standards.md)
- [Migration Guide](../08-development-guidelines/migration-guide.md)
