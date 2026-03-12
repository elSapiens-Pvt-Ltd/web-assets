# Page Spec: Account List

> URL: `/accounts`
> Role: All

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Accounts (87)                        [🔍 Search] [+ New Account]│
│ [Industry▾] [Agent▾] [+ More Filters]                          │
├──────────────────────────────────────────────────────────────────┤
│ Name              Contacts  Opportunities  Total Value  Created  │
│ Acme Corp         5         3              ₹4,50,000   Mar 1    │
│ TechParts Ltd     3         2              ₹2,80,000   Feb 15   │
│ FreshMart         2         1              ₹80,000     Jan 20   │
│ ...                                                              │
│                                  Page 1 of 4  [< 1 2 3 4 >]    │
└──────────────────────────────────────────────────────────────────┘
```

- Table: entity data from accounts-api + CRM aggregations (contact count, opportunity count, total value)
- Click row → `/accounts/:entityId`
- [+ New Account] → create form (→ accounts-api)
- Search: entity name via accounts-api
