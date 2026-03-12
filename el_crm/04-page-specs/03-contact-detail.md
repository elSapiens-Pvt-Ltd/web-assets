# Page Spec: Contact Detail

> URL: `/contacts/:personId`
> Role: All

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Back to Contacts                                               │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Rahul Verma                                   [✏ Edit] [⋮] ││
│ │ Procurement Manager at Acme Corp Pvt Ltd                     ││
│ │ 📞 +91 98765 43210  📧 rahul@acme.com  📍 Mumbai           ││
│ │ Stage: Lead  |  Source: JustDial  |  Agent: Priya           ││
│ │ [💬 Message] [📞 Call] [📧 Email] [+ Opportunity] [+ F-up] ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ [Conversations] [Opportunities] [Activities] [Custom Fields]     │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ (Tab content — e.g., Conversations list with open/closed)    ││
│ └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

- Header: person data from accounts-api + CRM enrichment (stage, source, agent)
- Quick actions: Message/Call/Email open composer or initiate call
- Tabs:
  - **Conversations**: all conversations (open + closed) for this person
  - **Opportunities**: linked opportunities with pipeline, stage, value
  - **Activities**: chronological timeline of all activities
  - **Custom Fields**: workspace-configured fields, editable inline
- Edit delegates to accounts-api via CRM backend gRPC
- [⋮] menu: Add Handle, Link to Account, Merge, View in Inbox
