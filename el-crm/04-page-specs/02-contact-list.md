# Page Spec: Contact List

> URL: `/contacts`
> Role: All

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Contacts (342)              [🔍 Search] [⬇ Import] [⬆ Export]  │
│ [Lifecycle▾] [Source▾] [Agent▾] [Account▾] [+ More Filters]    │
├──────────────────────────────────────────────────────────────────┤
│ □ Name           Phone           Email          Account    Stage │
│ □ Rahul Verma    +91 98765 432   rahul@acme..   Acme Corp  Lead │
│ □ Ankit Shah     +91 87654 321   ankit@tech..   TechParts  Cust │
│ ...                                                              │
│                                  Page 1 of 14 [< 1 2 3 ... >]  │
└──────────────────────────────────────────────────────────────────┘
```

- Table with sortable columns, configurable visible columns via [Columns ▾]
- Checkbox for bulk actions: Assign To, Change Stage, Export Selected, Delete
- Click row → navigate to `/contacts/:personId`
- Agent sees own contacts only; Manager sees all with Agent filter
- Data: CRM calls backend → backend batch-fetches from accounts-api + enriches with CRM data
- Pagination: server-side, 25 per page
- Search: debounced, searches name + phone + email via accounts-api
