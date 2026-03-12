# Contact & Account Management

> Role: Sales Agent, Manager
> Trigger: Agent needs to view, edit, or organize customer data
> Primary screen: Contacts, Accounts, Inbox (Contact Details panel)

---

## Flow Summary

Contacts (people) and Accounts (companies) are managed via **accounts-api** — CRM does not own this data. The CRM enriches it with CRM-specific information (stage, source, custom fields, conversations) and provides the UI for agents to manage everything in one place.

---

## Data Ownership

```
accounts-api (MongoDB, via gRPC):
  - Person: name, email, phone, designation
  - Entity: company name, address, industry
  - Membership: person ↔ entity relationship
  - Contact handles: phone numbers, emails (base data)

CRM (PostgreSQL):
  - contact_handles: workspace-scoped handle → person mapping
  - conversations, opportunities, activities: linked by person_id
  - custom_field_values: CRM-specific fields on contacts/accounts
  - Lifecycle stage, source, assigned agent (CRM context)
```

---

## Flow: View Contact List

```
Agent navigates to Contacts (sidebar)
  → CRM backend:
      1. Query CRM data: person_ids with conversations/opportunities in this workspace
      2. Batch call accounts-api gRPC: GetPersons(person_ids, workspace_id)
      3. Merge: accounts-api person data + CRM enrichment (stage, source, agent, custom fields)
      4. Return unified contact list

  Contact List page:
  ┌────────────────────────────────────────────────────────────────┐
  │ Contacts (342)        [🔍 Search] [⬇ Import] [⬆ Export]      │
  │ [Lifecycle▾] [Source▾] [Agent▾] [Account▾] [+ More Filters]  │
  ├────────────────────────────────────────────────────────────────┤
  │ □ Name          Phone            Account        Stage    Agent │
  │ □ Rahul Verma   +91 98765 43210  Acme Corp      Lead     Priya│
  │ □ Ankit Shah    +91 87654 32109  TechParts      Customer Ravi │
  │ □ Meera Joshi   +91 76543 21098  —              Lead     Ankit│
  │ ...                                                            │
  │                              Page 1 of 14  [< 1 2 3 ... 14 >]│
  └────────────────────────────────────────────────────────────────┘

  Agent role: sees only contacts assigned to them
  Manager role: sees all, can filter by agent
```

---

## Flow: View Contact Detail

```
Agent clicks on "Rahul Verma" in list (or from Inbox Contact Details → "View Full Profile")
  → Contact Detail page (/contacts/:personId)

  ┌────────────────────────────────────────────────────────────┐
  │ ← Back to Contacts                                         │
  │                                                            │
  │ ┌────────────────────────────────────────────────────────┐ │
  │ │ Rahul Verma                           [✏ Edit] [⋮]   │ │
  │ │ Procurement Manager at Acme Corp Pvt Ltd               │ │
  │ │ 📞 +91 98765 43210  📧 rahul@acme.com                │ │
  │ │ 📍 Mumbai, Maharashtra                                 │ │
  │ │                                                        │ │
  │ │ Lifecycle: Lead    Source: JustDial    Agent: Priya    │ │
  │ │ Created: Mar 1, 2026    Last Activity: Mar 12, 2026   │ │
  │ │                                                        │ │
  │ │ [💬 Message] [📞 Call] [📧 Email]                     │ │
  │ │ [+ Opportunity] [+ Follow-up] [📝 Note]               │ │
  │ └────────────────────────────────────────────────────────┘ │
  │                                                            │
  │ [Conversations] [Opportunities] [Activities] [Custom Fields]│
  │                                                            │
  │ ┌────────────────────────────────────────────────────────┐ │
  │ │ Tab content (e.g., Conversations):                     │ │
  │ │                                                        │ │
  │ │ ● Active: "Pricing inquiry" — WhatsApp — Qualified    │ │
  │ │   Last message: 2 hours ago                            │ │
  │ │   [Open in Inbox →]                                    │ │
  │ │                                                        │ │
  │ │ ○ Closed: "Initial inquiry" — JustDial — Won          │ │
  │ │   Closed: Feb 15, 2026                                 │ │
  │ │   [View History →]                                     │ │
  │ └────────────────────────────────────────────────────────┘ │
  └────────────────────────────────────────────────────────────┘
```

---

## Flow: Edit Contact

```
Agent clicks [✏ Edit] on contact detail
  → Inline edit mode or slide-over form:
      Name: [Rahul Verma]
      Designation: [Procurement Manager]
      Lifecycle Stage: [Lead ▾]        ← CRM-owned
      Source: [JustDial ▾]             ← CRM-owned

  → On save:
      Name, designation → CRM backend → gRPC to accounts-api: UpdatePerson()
      Stage, source → CRM backend → update CRM tables directly
      Custom fields → CRM backend → update custom_field_values table

  → Contact detail page refreshes with updated data
```

---

## Flow: Add Contact Handle

```
Agent discovers Rahul also has a personal email
  → Contact Detail → Handles section → [+ Add Handle]
  → Type: Email
  → Value: rahul.personal@gmail.com
  → Is Primary: No
  → Save

  → CRM checks: does this handle already exist for another person in this workspace?
      YES → "This email belongs to Ankit Shah. Merge contacts?" → Merge flow
      NO → Create handle:
          1. CRM creates contact_handle record (workspace_id, person_id, handle_type, handle_value)
          2. accounts-api may also store the handle on the person record

  → New handle appears in contact detail
  → Future messages from this email will route to Rahul's conversations
```

---

## Flow: Link Contact to Account

```
Contact "Rahul Verma" has no account linked
  → Contact Detail → Account section shows "No account"
  → Agent clicks [Link to Account]
  → Search modal:
      🔍 "Acme"
      Results:
        Acme Corp Pvt Ltd (3 contacts)
        Acme Trading Co (1 contact)
      [+ Create New Account]

  → Agent selects "Acme Corp Pvt Ltd"
  → CRM backend → gRPC to accounts-api: CreateMembership(person_id, entity_id)
  → Contact now shows account link
  → Account detail now shows Rahul in its contacts list
```

---

## Flow: Merge Duplicate Contacts

```
Agent discovers two records for the same person:
  "Rahul Verma" (person_id: A, phone: +919876543210)
  "Rahul V" (person_id: B, email: rahul@acme.com)

  → Contact Detail for "Rahul Verma" → [⋮ More] → "Merge with another contact"
  → Search for target: "Rahul V"
  → Merge preview:

  ┌────────────────────────────────────────────────────────────┐
  │ Merge Contacts                                             │
  │                                                            │
  │ Keep (Primary):          Merge Into:                       │
  │ Rahul Verma              Rahul V                           │
  │ +91 98765 43210          rahul@acme.com                    │
  │ Acme Corp                —                                 │
  │ 3 conversations          1 conversation                    │
  │ 2 opportunities          0 opportunities                   │
  │                                                            │
  │ Result after merge:                                        │
  │ ✓ Name: Rahul Verma (from primary)                        │
  │ ✓ Handles: +91 98765 43210, rahul@acme.com (combined)     │
  │ ✓ Account: Acme Corp (from primary)                        │
  │ ✓ Conversations: 4 (all reassigned to primary)             │
  │ ✓ Opportunities: 2 (kept on primary)                       │
  │ ✓ Activities: combined timeline                            │
  │                                                            │
  │ ⚠ This action cannot be undone.                           │
  │                                                            │
  │ [Cancel]                              [Confirm Merge]      │
  └────────────────────────────────────────────────────────────┘

  → On confirm:
      1. accounts-api gRPC: MergePersons(primary_id: A, secondary_id: B)
      2. CRM: reassign all conversations from person B → person A
      3. CRM: reassign all opportunities from person B → person A
      4. CRM: merge contact_handles (combine all handles under person A)
      5. CRM: merge activities (combined timeline)
      6. CRM: delete person B references
      7. Log merge activity for audit trail
```

---

## Flow: Account Management

### View Account Detail

```
/accounts/:entityId

  ┌────────────────────────────────────────────────────────────┐
  │ Acme Corp Pvt Ltd                         [✏ Edit] [⋮]   │
  │ Industry: Manufacturing    Location: Mumbai                │
  │ Contacts: 5    Active Opportunities: 3    Total: ₹4,50,000│
  │                                                            │
  │ [Contacts] [Opportunities] [Activities]                    │
  │                                                            │
  │ Contacts (5):                                              │
  │   Rahul Verma — Procurement — Lead — Priya                │
  │   Suresh K — Director — Customer — Ravi                    │
  │   Anita M — Accounts — Customer — Priya                   │
  │   ...                                                      │
  │   [+ Add Contact to Account]                               │
  └────────────────────────────────────────────────────────────┘
```

### Create Account

```
Contacts or Accounts page → [+ New Account]
  → Form: Company Name, Industry, Address, Phone, Email, Website
  → Save → CRM backend → gRPC accounts-api: CreateEntity()
  → Redirect to new account detail page
  → Optionally link existing contacts to this account
```

---

## Custom Fields During Contact/Account Management

Custom fields appear in the Contact Detail and Account Detail pages. They are configured per workspace in Settings.

```
Contact Detail → Custom Fields tab:
  Business Type: [Trader ▾]               ← dropdown
  Monthly Volume: [500 kg]                ← text
  Product Interest: [Grade A Turmeric ✕]  ← multi-select
  Payment Terms: [30 days ▾]              ← dropdown
  GST Number: [29AABCT1234Z1]            ← text

  All editable inline. Save updates custom_field_values in CRM PostgreSQL.
```

---

## Error States

| Scenario | Behavior |
|----------|----------|
| accounts-api unreachable | Show cached data with "Data may be outdated" banner, retry |
| Duplicate handle on different person | Merge suggestion dialog |
| Merge fails midway | Rollback CRM changes, show error, ask to retry |
| Contact not found (deleted in accounts-api) | "Contact no longer exists" with option to clean up CRM references |
| Import CSV with invalid data | Show validation errors per row, allow fix and retry |
