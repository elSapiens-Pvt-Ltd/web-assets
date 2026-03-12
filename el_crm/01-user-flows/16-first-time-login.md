# First-Time Login

> Role: All
> Trigger: User accesses el-CRM for the first time
> Primary screen: Login → Workspace Select → Inbox/Dashboard

---

## Flow Summary

Authentication is handled entirely by **elauth**. The CRM frontend uses elsdk's AuthGuard and AuthProvider to manage the login flow. Users don't create a separate CRM account — they log in once and access all elSapiens services.

---

## Flow: New User (Invited by Admin)

```
1. User receives invite email:
   "You've been invited to {Workspace Name} on elSapiens CRM"
   → [Accept Invitation] button → links to elauth

2. elauth registration page:
   → Email pre-filled (from invite)
   → Set password (strength requirements)
   → [Create Account]

3. MFA Setup (if workspace requires it):
   → "Your organization requires two-factor authentication"
   → Options: Authenticator App (TOTP) | Security Key (WebAuthn)
   → Setup flow → verify → complete

4. Redirect to CRM:
   → elauth issues JWT (access + refresh tokens)
   → Redirect to CRM app URL
   → elsdk SDKProvider initializes:
       AuthProvider → stores JWT, sets up auto-refresh
       OrganizationProvider → loads workspace context
   → elsdk AuthGuard validates JWT → pass

5. Workspace Selection (if user has multiple workspaces):
   → OrgSwitcher component (from elsdk) shows:
     ┌────────────────────────┐
     │ Select Workspace       │
     │ ┌────────────────────┐ │
     │ │ Climate Naturals   │ │
     │ │ Role: Agent        │ │
     │ └────────────────────┘ │
     │ ┌────────────────────┐ │
     │ │ Acme Trading       │ │
     │ │ Role: Manager      │ │
     │ └────────────────────┘ │
     └────────────────────────┘
   → User selects workspace → workspace_id set in context

6. CRM Landing:
   → Agent role → Inbox (home screen)
   → Manager role → Dashboard
   → Admin role → Dashboard (or Settings if first-time setup needed)
```

---

## Flow: Returning User

```
User opens CRM URL
  → elsdk AuthGuard checks localStorage for JWT
  → JWT found and valid → load workspace context → show Inbox/Dashboard
  → JWT found but expired:
      → AuthProvider attempts refresh using refresh token
      → Refresh succeeds → new access token → proceed
      → Refresh fails (refresh token also expired) → redirect to elauth login
  → No JWT → redirect to elauth login page
  → After login → redirect back to CRM at the originally requested URL
```

---

## Flow: Switch Workspace

```
User is in "Climate Naturals" workspace
  → Clicks workspace name in header/sidebar
  → OrgSwitcher dropdown shows available workspaces
  → Selects "Acme Trading"
  → System:
      - Updates workspace_id in context
      - Clears CRM-specific cached data (conversations, pipeline, etc.)
      - Reloads CRM with new workspace data
      - Role may differ (Agent in one, Manager in another)
      - UI adapts to role capabilities
```

---

## Session Management

| Aspect | Behavior |
|--------|----------|
| Access token expiry | 24 hours (from elauth config) |
| Refresh token expiry | 7-30 days (workspace-configurable in elauth) |
| Concurrent sessions | Allowed (user can be logged in on multiple devices) |
| Session invalidation | Admin can force-logout via elauth |
| Idle timeout | Configurable per workspace (default: none — relies on token expiry) |
| Tab/window behavior | Shared auth state via localStorage — login in one tab logs in all |

---

## Error States

| Scenario | Behavior |
|----------|----------|
| Invalid invite link | "This invitation has expired or is invalid. Contact your admin." |
| Email already registered | "An account with this email already exists. Log in instead." |
| MFA device lost | "Can't access your authenticator? Contact your admin for recovery." |
| Workspace suspended | "This workspace is currently inactive. Contact support." |
| No CRM access in workspace | "You don't have CRM access in this workspace. Contact your admin." |
