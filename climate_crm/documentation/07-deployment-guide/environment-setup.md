> Module: climate/deployment/environment-setup
> Last updated: 2026-03-11

# Environment Setup

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
  - [System Requirements](#system-requirements)
  - [Optional Services](#optional-services)
- [Backend Environment Variables](#backend-environment-variables)
  - [Database](#database)
  - [Authentication](#authentication)
  - [AWS S3](#aws-s3)
  - [WebSocket](#websocket)
  - [Email (AWS SES)](#email-aws-ses)
  - [Redis](#redis)
- [Frontend Configuration](#frontend-configuration)
  - [Environment Files](#environment-files)
  - [Runtime Config Files](#runtime-config-files)
  - [Key URLs](#key-urls)
- [Apache Virtual Host (Backend)](#apache-virtual-host-backend)
  - [.htaccess (URL Rewriting)](#htaccess-url-rewriting)
- [Nginx Configuration (Alternative)](#nginx-configuration-alternative)
- [Hosts File (Development)](#hosts-file-development)
- [PHP Extensions Required](#php-extensions-required)
- [Timezone](#timezone)
- [CDN Configuration](#cdn-configuration)
- [Quick Start Checklist](#quick-start-checklist)
- [Cross-References](#cross-references)

---

## Overview

This guide covers prerequisites and environment configuration for the Climate CRM application.

---

## Prerequisites

### System Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Node.js | 18.x LTS+ | Angular CLI, frontend build |
| npm | 9.x+ | Package management |
| PHP | 7.4+ / 8.x | Backend runtime |
| MySQL / MariaDB | 5.7+ / 10.x+ | Database |
| Redis | 6.x+ | Queue system, caching |
| Composer | 2.x | PHP dependency management |
| Apache / Nginx | 2.4+ / 1.18+ | Web server |
| wkhtmltopdf | 0.12.6+ | PDF generation (invoices) |
| Git | 2.x+ | Version control |

### Optional Services

| Service | Purpose |
|---------|---------|
| AWS S3 | File storage (media, invoices) |
| AWS CloudFront | CDN for static assets |
| AWS SES | Transactional email |
| Firebase | Push notifications (FCM) |
| WhatsApp Business API | Messaging integration |

---

## Backend Environment Variables

The backend reads configuration from server environment variables (`$_SERVER`). Set these in your web server or `.env` file:

### Database

```bash
DBHOST=127.0.0.1
DBUSER=root
DBPASSWORD=your_password
DBNAME=climate
```

### Authentication

```bash
JWT_KEY=your_jwt_secret_key_here
```

The JWT key is used for HS512 token signing. Use a strong random string (64+ characters).

### AWS S3

```bash
S3_KEY=AKIAXXXXXXXXXXXXXXXXX
S3_TOKEN=your_secret_access_key
S3_BUCKET=your-bucket-name
```

### WebSocket

```bash
CHAT_PORT=8988
```

### Email (AWS SES)

SMTP is configured in `application/config/config.php`:
- Host: `email-smtp.ap-south-1.amazonaws.com`
- Port: 587
- Protocol: TLS

### Redis

Configured in `application/config/redis.php`:

```php
$config['redis_default']['host'] = 'localhost';
$config['redis_default']['port'] = 6379;
$config['redis_default']['password'] = '';
$config['redis_default']['queue_name'] = 'message_queue';
```

---

## Frontend Configuration

### Environment Files

Located in `climate-admin/src/environments/`:

| File | Purpose |
|------|---------|
| `environment.ts` | Development defaults |
| `environment.beta.ts` | Beta/staging config |
| `environment.prod.ts` | Production config |

### Runtime Config Files

Located in `climate-admin/src/assets/config/`:

| File | Purpose |
|------|---------|
| `config.dev.json` | Development API URLs |
| `config.beta.json` | Beta API URLs |
| `config.prod.json` | Production API URLs |

Structure:

```json
{
  "apiServer": {
    "dataServer": "http://climate.loc/index.php"
  }
}
```

The `AppConfig` singleton service loads this at application startup and makes it available as `AppConfig.settings.apiServer.dataServer`.

### Key URLs

| Environment | Frontend | API | WebSocket |
|-------------|----------|-----|-----------|
| Development | `http://localhost:4200` | `http://climate.loc/index.php` | `ws://localhost:8988` |
| Production | `https://admin.climatenaturals.com` | `https://api.climatenaturals.com/index.php` | `wss://api.climatenaturals.com/chat` |

---

## Apache Virtual Host (Backend)

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
</VirtualHost>
```

### .htaccess (URL Rewriting)

The API uses CodeIgniter's URL routing with `.htaccess`:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php/$1 [L]
```

---

## Nginx Configuration (Alternative)

```nginx
server {
    listen 80;
    server_name climate.loc;
    root /path/to/climate-api;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?/$request_uri;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;

        # Environment variables
        fastcgi_param DBHOST 127.0.0.1;
        fastcgi_param DBUSER root;
        fastcgi_param DBPASSWORD your_password;
        fastcgi_param DBNAME climate;
        fastcgi_param JWT_KEY your_jwt_secret;
        fastcgi_param S3_KEY your_s3_key;
        fastcgi_param S3_TOKEN your_s3_token;
        fastcgi_param S3_BUCKET your_bucket;
        fastcgi_param CHAT_PORT 8988;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

---

## Hosts File (Development)

Add to `/etc/hosts`:

```
127.0.0.1   climate.loc
```

---

## PHP Extensions Required

```
php-mysqli      # MySQL database driver
php-mbstring    # Multi-byte string support
php-json        # JSON encoding/decoding
php-curl        # HTTP client (WhatsApp API, external APIs)
php-gd          # Image processing
php-xml         # XML parsing
php-zip         # ZIP archive support
php-redis       # Redis extension (or use predis via Composer)
```

---

## Timezone

The application is configured for Indian Standard Time:

```php
// application/config/config.php
date_default_timezone_set('Asia/Kolkata');
```

Ensure the MySQL server timezone is also set to `Asia/Kolkata` or `+05:30` for consistent datetime handling.

---

## CDN Configuration

Static assets (media, invoices, documents) are served via AWS CloudFront:

```
CDN URL: https://d1r95e2xq05b34.cloudfront.net
Origin: S3 bucket
```

The frontend references media files using the CDN URL prefix combined with the `media_key` from the database.

---

## Quick Start Checklist

1. Install prerequisites (Node.js, PHP, MySQL, Redis, Composer)
2. Clone repositories (`climate-admin`, `climate-api`)
3. Set up database (see [database-setup.md](database-setup.md))
4. Configure backend environment variables
5. Install backend dependencies: `cd climate-api && composer install`
6. Install frontend dependencies: `cd climate-admin && npm install`
7. Configure frontend API URLs in `src/assets/config/config.dev.json`
8. Start backend: Apache/Nginx pointing to `climate-api/`
9. Start frontend: `npm start` (port 4200) or `npm run startadmin` (port 4302)
10. Start Redis: `redis-server`
11. Start WebSocket server: `php index.php chat start`

---

## Cross-References

- [System Architecture Overview](../01-system-architecture/overview.md)
- [Backend Architecture](../01-system-architecture/backend-architecture.md)
- [Frontend Architecture](../01-system-architecture/frontend-architecture.md)
- [Database Schema Overview](../03-database-design/schema-overview.md)
- [Migration System](../03-database-design/migration-system.md)
- [Database Setup](database-setup.md)
- [Backend Setup](backend-setup.md)
- [Frontend Setup](frontend-setup.md)
- [Coding Standards](../08-development-guidelines/coding-standards.md)
