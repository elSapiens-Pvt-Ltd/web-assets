> Module: climate/deployment/frontend-setup
> Last updated: 2026-03-11

# Frontend Setup

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
  - [1. Install Dependencies](#1-install-dependencies)
  - [2. Angular CLI](#2-angular-cli)
- [Configuration](#configuration)
  - [Runtime API Config](#runtime-api-config)
  - [Environment Files](#environment-files)
  - [WebSocket URL](#websocket-url)
  - [CDN URL](#cdn-url)
- [Development Server](#development-server)
  - [Standard Dev Server](#standard-dev-server)
  - [Alternate Port](#alternate-port)
  - [Watch Mode](#watch-mode)
- [Build](#build)
  - [Production Build](#production-build)
  - [Beta Build](#beta-build)
  - [Build Configuration (angular.json)](#build-configuration-angularjson)
- [TypeScript Configuration](#typescript-configuration)
- [Deployment](#deployment)
  - [Static File Deployment](#static-file-deployment)
  - [Web Server Configuration](#web-server-configuration)
- [PWA / Service Worker](#pwa--service-worker)
- [Firebase Configuration](#firebase-configuration)
- [Module Architecture](#module-architecture)
- [Common Issues](#common-issues)
- [Cross-References](#cross-references)

---

## Overview

The Angular 17 frontend (`climate-admin`) serves as the CRM admin panel. This guide covers installation, configuration, building, and deployment.

---

## Installation

### 1. Install Dependencies

```bash
cd climate-admin
npm install
```

Key dependencies installed:
- Angular 17.0.5 + Angular Material 17.0.2
- RxJS 7.8.0
- Tailwind CSS 3.4.17
- Firebase (@angular/fire 17.0.0)
- ngx-translate (i18n)
- TinyMCE editor
- ngx-echarts (charts)
- moment, date-fns, chart.js

### 2. Angular CLI

```bash
# Install globally (if not already)
npm install -g @angular/cli@17
```

---

## Configuration

### Runtime API Config

Edit `src/assets/config/config.dev.json`:

```json
{
  "apiServer": {
    "dataServer": "http://climate.loc/index.php"
  }
}
```

| Environment | File | API URL |
|-------------|------|---------|
| Development | `config.dev.json` | `http://climate.loc/index.php` |
| Beta | `config.beta.json` | Beta server URL |
| Production | `config.prod.json` | `https://api.climatenaturals.com/index.php` |

### Environment Files

Located in `src/environments/`:

```typescript
// environment.ts (development)
export const environment = {
  production: false,
  // ... environment-specific flags
};

// environment.prod.ts (production)
export const environment = {
  production: true,
  // ...
};
```

### WebSocket URL

Configured in the WebSocket service:
- Development: `ws://localhost:8988`
- Production: `wss://api.climatenaturals.com/chat`

### CDN URL

Media files served from CloudFront:

```
https://d1r95e2xq05b34.cloudfront.net/{media_key}
```

---

## Development Server

### Standard Dev Server

```bash
npm start
# or
ng serve
```

Runs on `http://localhost:4200` with hot module replacement.

### Alternate Port

```bash
npm run startadmin
```

Runs on `http://localhost:4302`.

### Watch Mode

```bash
npm run watch
```

Builds and watches for changes without serving.

---

## Build

### Production Build

```bash
ng build --configuration production --build-optimizer
```

Output: `dist/` directory

### Beta Build

```bash
ng build --configuration beta --build-optimizer
```

### Build Configuration (angular.json)

Key production settings:
- **Optimization**: enabled (minification, tree-shaking)
- **Source maps**: disabled
- **Vendor chunk**: disabled (single bundle)
- **Service Worker**: enabled (`ngsw-worker.js`)
- **Budget warnings**: 5MB max bundle size, 50KB per style

```json
{
  "budgets": [
    {
      "type": "initial",
      "maximumWarning": "5mb",
      "maximumError": "10mb"
    },
    {
      "type": "anyComponentStyle",
      "maximumWarning": "50kb",
      "maximumError": "100kb"
    }
  ]
}
```

---

## TypeScript Configuration

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "strict": true,
    "noImplicitAny": false,
    "strictPropertyInitialization": false,
    "strictTemplates": false,
    "downlevelIteration": true,
    "experimentalDecorators": true
  }
}
```

Note: `noImplicitAny` and `strictPropertyInitialization` are disabled for development flexibility.

---

## Deployment

### Static File Deployment

After building, deploy the `dist/` directory to your web server:

```bash
# Build
ng build --configuration production --build-optimizer

# Deploy to server
rsync -avz dist/ user@server:/var/www/climate-admin/
```

### Web Server Configuration

The Angular app requires all routes to fall back to `index.html`:

**Nginx:**

```nginx
server {
    listen 80;
    server_name admin.climatenaturals.com;
    root /var/www/climate-admin;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # No cache for index.html (to pick up new deployments)
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

**Apache (.htaccess):**

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /index.html [L]
```

---

## PWA / Service Worker

The app includes a Service Worker for PWA capabilities:

- Configuration: `ngsw-config.json`
- Worker file: `ngsw-worker.js` (Angular built-in)
- Enabled in production builds

Features:
- Offline caching of static assets
- Background sync for API calls
- Push notification handling (FCM)

---

## Firebase Configuration

Firebase is used for push notifications (FCM):

1. Place `firebase-messaging-sw.js` in `src/` (service worker for background messages)
2. Configure Firebase credentials in the environment files
3. The `@angular/fire` module handles FCM token registration

---

## Module Architecture

The app uses lazy loading for all 48+ feature modules:

```typescript
// app-routing.module.ts
{
  path: 'dashboard',
  loadChildren: () => import('./views/dashboard/dashboard.module').then(m => m.DashboardModule),
  canActivate: [AuthGuard]
}
```

Each module follows the pattern:

```
src/app/views/{feature}/
├── {feature}.module.ts
├── {feature}-routing.module.ts
├── components/
│   └── {component}/
│       ├── {component}.component.ts
│       ├── {component}.component.html
│       └── {component}.component.scss
└── services/
    └── {feature}.service.ts
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| `ng serve` fails with memory error | Increase Node memory: `export NODE_OPTIONS=--max-old-space-size=4096` |
| CORS errors in development | Ensure backend has CORS headers configured (handled by CI3 hooks) |
| WebSocket connection fails | Check WebSocket server is running and port matches config |
| Styles not loading | Run `npm run build` to compile Tailwind CSS |
| Service Worker issues in dev | Service Workers only work in production builds; use `ng serve` without SW |

---

## Cross-References

- [System Architecture Overview](../01-system-architecture/overview.md)
- [Frontend Architecture](../01-system-architecture/frontend-architecture.md)
- [Environment Setup](environment-setup.md)
- [Backend Setup](backend-setup.md)
- [Adding Modules](../08-development-guidelines/adding-modules.md)
- [Coding Standards](../08-development-guidelines/coding-standards.md)
- [Adding APIs](../08-development-guidelines/adding-apis.md)
