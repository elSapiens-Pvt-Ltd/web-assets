# Database Triggers & Stored Functions

> Module: `climate/database/triggers`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Summary Tables (Trigger Targets)](#summary-tables-trigger-targets)
3. [Conversation Triggers](#conversation-triggers)
4. [Order Triggers](#order-triggers)
5. [Payment Triggers](#payment-triggers)
6. [Opportunity Triggers](#opportunity-triggers)
7. [Follow-up Triggers](#follow-up-triggers)
8. [Customer & Contact Triggers](#customer--contact-triggers)
9. [Call Log Triggers](#call-log-triggers)
10. [WhatsApp Message Triggers](#whatsapp-message-triggers)
11. [Produce & Inventory Triggers](#produce--inventory-triggers)
12. [Bidlot Triggers](#bidlot-triggers)
13. [Stored Functions](#stored-functions)
14. [Trigger Dependency Map](#trigger-dependency-map)
15. [Cross-References](#cross-references)

---

## Overview

The system uses **43 MySQL triggers** and **4 stored functions** to maintain real-time summary tables, enforce business rules, and calculate derived fields. Triggers follow a pattern of writing to `crm_*` summary tables for reporting, while BEFORE triggers handle data enrichment and validation.

| Category | Trigger Count | Tables Affected |
|----------|--------------|-----------------|
| Conversations | 5 | `tbl_open_conversations` |
| Orders | 4 | `tbl_orders` |
| Order Items | 3 | `tbl_order_items` |
| Payments | 3 | `tbl_payments` |
| Payment Approvals | 3 | `tbl_payments_approval` |
| Opportunities | 4 | `tbl_opportunities` |
| Follow-ups | 4 | `tbl_followup_schedules` |
| Customers | 2 | `tbl_customers` |
| Customer Contacts | 2 | `tbl_customer_contacts` |
| Call Logs | 2 | `tbl_call_logs` |
| WhatsApp Messages | 1 | `tbl_whatsapp_messages` |
| Produces | 2 | `tbl_produces` |
| Produce Grades | 3 | `tbl_produce_grades` |
| Lots | 2 | `tbl_lots` |
| Bidlots | 2 | `tbl_bidlots` |
| Bid History | 1 | `tbl_bidlot_bids_history` |
| **Total** | **43** | |

---

## Summary Tables (Trigger Targets)

These `crm_*` tables are populated exclusively by triggers. They power the CRM reporting dashboards.

| Summary Table | Purpose | Updated By Triggers On |
|---------------|---------|----------------------|
| `crm_agent_activity_summary` | Daily agent metrics (messages, calls, tasks) | `tbl_call_logs`, `tbl_followup_schedules`, `tbl_whatsapp_messages` |
| `crm_conversation_cohort_summary` | Cohort analysis by allocation date | `tbl_open_conversations` |
| `crm_conversation_activity_summary` | Daily stage transition activity | `tbl_open_conversations` |
| `crm_conversation_stage_summary` | Current stage distribution by cohort | `tbl_open_conversations` |
| `crm_outcome_agent_summary` | Agent-level opportunity/order tracking | `tbl_opportunities`, `tbl_orders` |
| `crm_outcome_summary` | Overall opportunity→order conversion | `tbl_opportunities` |
| `crm_revenue_agent_summary` | Revenue attribution by agent/source | `tbl_orders` |
| `crm_unqualified_summary` | Unqualified disposition breakdown | `tbl_open_conversations` |
| `tbl_agent_summary` | Agent new/repeat customer counts | `tbl_customers` |
| `tbl_contact_source_summary` | Lead source profiling metrics | `tbl_customers` |

---

## Conversation Triggers

### trg_conversation_before_insert

**Event**: `BEFORE INSERT ON tbl_open_conversations`

Sets `had_account_at_start` flag based on whether the contact already has an account.

```sql
BEGIN
    IF NEW.account_id IS NOT NULL AND NEW.account_id > 0 THEN
        SET NEW.had_account_at_start = 1;
    ELSE
        SET NEW.had_account_at_start = 0;
    END IF;
END
```

---

### trg_calculate_attempt_time

**Event**: `BEFORE UPDATE ON tbl_open_conversations`

Calculates working-hours time between allocation and first attempt using `fn_calculate_working_seconds`. Excludes holidays and agent leaves.

```sql
BEGIN
    IF NEW.attempted_at IS NOT NULL
       AND OLD.attempted_at IS NULL
       AND NEW.allocated_at IS NOT NULL THEN
        SET NEW.attempt_time = fn_calculate_working_seconds(
            NEW.agent_id,
            NEW.allocated_at,
            NEW.attempted_at
        );
    END IF;
END
```

---

### trg_conversation_before_update

**Event**: `BEFORE UPDATE ON tbl_open_conversations`

Tracks first-reached timestamps for each stage and auto-closes unqualified conversations.

**Stage timestamps set** (only on first transition):
- `first_reached_attempted_at`
- `first_reached_contacted_at`
- `first_reached_nurturing_at`
- `first_reached_converted_at`
- `first_reached_unqualified_at`

**Auto-close logic**: When stage becomes `unqualified`, sets `closed_at` and `unqualified_at` if not already set.

```sql
BEGIN
    IF NEW.conversation_stage = 'attempted' AND OLD.first_reached_attempted_at IS NULL THEN
        SET NEW.first_reached_attempted_at = CURDATE();
    END IF;
    IF NEW.conversation_stage = 'contacted' AND OLD.first_reached_contacted_at IS NULL THEN
        SET NEW.first_reached_contacted_at = CURDATE();
    END IF;
    IF NEW.conversation_stage = 'nurturing' AND OLD.first_reached_nurturing_at IS NULL THEN
        SET NEW.first_reached_nurturing_at = CURDATE();
    END IF;
    IF NEW.conversation_stage = 'converted' AND OLD.first_reached_converted_at IS NULL THEN
        SET NEW.first_reached_converted_at = CURDATE();
    END IF;
    IF NEW.conversation_stage = 'unqualified' AND OLD.first_reached_unqualified_at IS NULL THEN
        SET NEW.first_reached_unqualified_at = CURDATE();
    END IF;

    -- Auto-close unqualified
    IF NEW.conversation_stage = 'unqualified' THEN
        IF NEW.closed_at IS NULL THEN SET NEW.closed_at = NOW(); END IF;
        IF NEW.unqualified_at IS NULL THEN SET NEW.unqualified_at = NOW(); END IF;
    END IF;
END
```

---

### trg_conversation_after_insert

**Event**: `AFTER INSERT ON tbl_open_conversations`

Populates three summary tables when a new conversation is created:

| Summary Table | Column Updated |
|---------------|---------------|
| `crm_conversation_cohort_summary` | `total_created` +1 |
| `crm_conversation_activity_summary` | `activity_new` +1 |
| `crm_conversation_stage_summary` | `current_{stage}` +1 |

Dimensions: `cohort_date` (from `allocated_at`), `user_id`, `source_id`, `conversation_type`.

---

### trg_conversation_after_update

**Event**: `AFTER UPDATE ON tbl_open_conversations`

Fires only when `conversation_stage` changes. Performs four operations:

1. **Stage summary**: Decrements old stage count, increments new stage count in `crm_conversation_stage_summary`
2. **Activity summary**: Increments `activity_{new_stage}` in `crm_conversation_activity_summary` (uses `CURDATE()`)
3. **Cohort first-reached**: If this is the first time reaching a stage, increments `first_{stage}` in `crm_conversation_cohort_summary`
4. **Unqualified analysis**: On first unqualified, inserts into `crm_unqualified_summary` with `disposition_status`

---

## Order Triggers

### before_order_insert

**Event**: `BEFORE INSERT ON tbl_orders`

Calculates pending amount: `pending_amount = grand_total - amount_paid`

---

### trigger_before_order_update

**Event**: `BEFORE UPDATE ON tbl_orders`

Calculates `pending_amount` and derives `payment_status` and `fulfillment_status`.

**Payment status logic**:

| Condition | Status |
|-----------|--------|
| `amount_paid = 0` | `no_payment` |
| Grand total > 1000, pending ≤ 50 | `fully_paid` |
| Grand total 5–1000, pending ≤ 5 | `fully_paid` |
| Grand total ≤ 5, pending ≤ 0 | `fully_paid` |
| `amount_paid > 0` (otherwise) | `partially_paid` |

**Auto-dispatch**: When `payment_status` transitions to `fully_paid` and `fulfillment_status` is `pending` (and order not cancelled), sets `fulfillment_status = 'for_despatch'` and `ready_time = NOW()`.

```sql
-- Payment status with tolerance thresholds
IF NEW.amount_paid = 0 THEN
    SET NEW.payment_status = 'no_payment';
ELSEIF (
    (NEW.grand_total > 1000 AND NEW.pending_amount <= 50) OR
    (NEW.grand_total > 5 AND NEW.grand_total <= 1000 AND NEW.pending_amount <= 5) OR
    (NEW.grand_total <= 5 AND NEW.pending_amount <= 0)
) THEN
    SET NEW.payment_status = 'fully_paid';
    SET NEW.pending_amount = 0;
ELSEIF NEW.amount_paid > 0 THEN
    SET NEW.payment_status = 'partially_paid';
END IF;

-- Auto-dispatch on full payment
IF NEW.payment_status = 'fully_paid'
   AND OLD.payment_status != 'fully_paid'
   AND NEW.fulfillment_status = 'pending'
   AND NEW.order_status NOT IN ('cancelled', 'cancellation_pending')
THEN
    SET NEW.fulfillment_status = 'for_despatch';
    SET NEW.ready_time = NOW();
END IF;
```

---

### after_order_insert_combined

**Event**: `AFTER INSERT ON tbl_orders`

Two responsibilities:

1. **Account metrics**: Updates `temp_tbl_accounts` with `first_order_date`, `last_order_date`, `order_value`, `order_count`
2. **Revenue summary**: Inserts into `crm_revenue_agent_summary` with order amount, deriving `source_id` from the linked opportunity

---

### after_order_update_combined

**Event**: `AFTER UPDATE ON tbl_orders`

Handles three scenarios:

| Scenario | Account Update | Revenue Summary Update | Order Items |
|----------|---------------|----------------------|-------------|
| `order_value` changed | Adjusts `order_value` delta | Adjusts `order_amount` delta | — |
| Soft delete (`order_deleted` 0→1) | Decrements `order_value`, `order_count` | Decrements `orders`, `order_amount` | Cascades `order_deleted = 1` |
| Undelete (`order_deleted` 1→0) | Increments `order_value`, `order_count` | Increments `orders`, `order_amount` | Cascades `order_deleted = 0` |

---

## Payment Triggers

### trigger_payment_before_save

**Event**: `BEFORE INSERT ON tbl_payments`

Increments `tbl_orders.amount_paid` by the payment amount.

```sql
UPDATE tbl_orders SET amount_paid = amount_paid + New.payment_amount
WHERE order_id = New.order_id;
```

---

### trigger_payment_before_update

**Event**: `BEFORE UPDATE ON tbl_payments`

Fires only when `payment_status` changes:
- **→ Success**: Adds new amount, subtracts old amount from `tbl_orders.amount_paid`
- **→ Refund/Deleted**: Subtracts old amount from `tbl_orders.amount_paid`

---

### trigger_payment_before_delete

**Event**: `BEFORE DELETE ON tbl_payments`

Decrements `tbl_orders.amount_paid` by the deleted payment amount.

---

### trigger_payments_approval_before_save

**Event**: `BEFORE INSERT ON tbl_payments_approval`

Increments `tbl_orders.approval_pending` by the approval amount.

---

### trigger_payments_approval_before_update

**Event**: `BEFORE UPDATE ON tbl_payments_approval`

| Status Change | Payment Type | Action |
|--------------|--------------|--------|
| → Approved | Order | Decrements `approval_pending`, creates `tbl_payments` record |
| → Declined | Order | Decrements `approval_pending` only |
| → Approved | Deposit | Creates `tbl_customer_deposits` record |

---

### trigger_payments_approval_before_delete

**Event**: `BEFORE DELETE ON tbl_payments_approval`

If status is `Pending`, decrements `tbl_orders.approval_pending`.

---

## Opportunity Triggers

### trg_outcome_agent_opp_insert

**Event**: `AFTER INSERT ON tbl_opportunities`

When status is not `Cancelled`:
1. Derives `source_id` from linked conversation (falls back to opportunity's `source_id`, default 2)
2. Increments `crm_outcome_agent_summary` with `opportunities` +1 and `opportunity_amount`
3. If opportunity has a linked `order_id`, also increments `orders` and `order_amount`

---

### trg_outcome_opportunity_insert

**Event**: `AFTER INSERT ON tbl_opportunities`

Updates `crm_outcome_summary`:
- `cohort_opportunity` +1 (keyed by conversation's `allocated_at` date)
- `activity_opportunity` +1 (keyed by today)

---

### trg_outcome_opportunity_update

**Event**: `AFTER UPDATE ON tbl_opportunities`

Fires when `order_id` changes from NULL to a value (opportunity linked to order):
- `cohort_order` +1 in `crm_outcome_summary`
- `activity_order` +1

---

### trg_outcome_agent_opp_update

**Event**: `AFTER UPDATE ON tbl_opportunities`

Handles three scenarios:
1. **Amount change** (non-cancelled): Adjusts `opportunity_amount` delta
2. **Cancellation**: Decrements `opportunities` and `opportunity_amount`
3. **Un-cancellation**: Re-increments with current values

---

## Follow-up Triggers

### trg_followup_insert_increment_count

**Event**: `AFTER INSERT ON tbl_followup_schedules`

Increments `tbl_open_conversations.scheduled_followups_count` when a pending follow-up is created.

---

### trg_agent_activity_task_insert

**Event**: `AFTER INSERT ON tbl_followup_schedules`

Increments `crm_agent_activity_summary.followup_tasks_created` for the creating user. Resolves `user_id` from `created_by` or via `tbl_users.agent_id`.

---

### trg_followup_update_adjust_count

**Event**: `AFTER UPDATE ON tbl_followup_schedules`

Handles 7 cases for `scheduled_followups_count`:

| Case | Delta |
|------|-------|
| Soft delete (pending) | -1 |
| Restore (to pending) | +1 |
| Status pending → other | -1 |
| Status other → pending | +1 |
| Conversation assigned (null → id) | +1 on new |
| Conversation removed (id → null) | -1 on old |
| Conversation reassigned (id → different id) | -1 on old, +1 on new |

Uses `GREATEST(0, ...)` to prevent negative counts.

---

### trg_followup_delete_decrement_count

**Event**: `AFTER DELETE ON tbl_followup_schedules`

Decrements `scheduled_followups_count` for hard-deleted pending follow-ups.

---

## Customer & Contact Triggers

### trigger_generate_number_insert / trigger_generate_number_update

**Event**: `BEFORE INSERT/UPDATE ON tbl_customer_contacts`

Generates `concatenated_num` by stripping `+` and spaces from phone code + number.

```sql
SET NEW.concatenated_num = CONCAT(REPLACE(NEW.phone_code, '+', ''), NEW.phone_number);
SET NEW.concatenated_num = REPLACE(NEW.concatenated_num, ' ', '');
```

---

### CUSTOMER_CREATE_CUSTOMER_ADMIN

**Event**: `AFTER INSERT ON tbl_customers`

Auto-creates admin access record in `tbl_customer_admin_access_table` for the creating user.

---

### after_update_on_tbl_customers

**Event**: `AFTER UPDATE ON tbl_customers`

Two responsibilities:

1. **Profile tracking**: When `profiled` changes 0→1, increments `tbl_contact_source_summary.profiled_leads`
2. **Customer type tracking**:
   - First order (`first_order_date` NULL→set, equals `last_order_date`): Increments `tbl_agent_summary.new_customer`
   - Repeat order (`order_count > 1`): Increments `tbl_agent_summary.old_customer`

---

## Call Log Triggers

### trg_agent_activity_call_insert

**Event**: `AFTER INSERT ON tbl_call_logs`

Classifies calls and updates `crm_agent_activity_summary`:

| Classification | Conditions |
|---------------|------------|
| Incoming | `call_type = 'inbound'` |
| Outgoing | `call_type != 'inbound'` |
| Successful | `call_status = 'Call Ended'` AND `call_missed = 0` |
| Missed | `call_status = 'Call Missed'` OR `call_missed = 1` |
| Missed by agent | `missed_by = 'agent'` |
| Missed by customer | `missed_by = 'customer'` |
| Error | `missed_by = 'error'` OR status contains 'error'/'Failed' |

Tracks: `incoming_attempted`, `incoming_successful`, `incoming_missed`, `outgoing_attempted`, `outgoing_successful`, `outgoing_missed`, `outgoing_missed_by_agent`, `outgoing_missed_by_customer`, `outgoing_errors`, `total_call_duration_seconds`, `total_ring_duration_seconds`.

---

### trg_agent_activity_call_update

**Event**: `AFTER UPDATE ON tbl_call_logs`

Recalculates call classification when status changes. Computes delta between old and new states, only updates summary when classification or duration actually changes. Uses `GREATEST(0, ...)` to prevent negative counts.

---

## WhatsApp Message Triggers

### trg_agent_activity_message_insert

**Event**: `AFTER INSERT ON tbl_whatsapp_messages`

When `sender = 'admin'` (outbound message), increments `crm_agent_activity_summary.messages_sent`. Resolves `user_id` from the message's `user_id` field or via `tbl_users.agent_id`.

---

## Produce & Inventory Triggers

### Order Item Triggers (tbl_order_items)

#### trigger_order_items_before_save

**Event**: `BEFORE INSERT ON tbl_order_items`

For produce lots (`lot_type = 'produce'`): Increments `tbl_lots.quantity_sold` and sets lot status to `Sold Out` if fully sold.

#### trigger_order_items_before_update

**Event**: `BEFORE UPDATE ON tbl_order_items`

Handles:
- **Soft delete** (0→1): Restores lot quantity
- **Undelete** (1→0): Re-deducts lot quantity
- **Quantity change**: Adjusts delta

#### trigger_order_items_before_delete

**Event**: `BEFORE DELETE ON tbl_order_items`

Restores lot quantity on hard delete.

---

### Produce Triggers (tbl_produces)

#### trig_produce_b_in / trig_produce_b_up

**Event**: `BEFORE INSERT/UPDATE ON tbl_produces`

- Sets default display picture: `'default/default_produce.png'` if NULL
- On update: Cascades display picture changes to all grades with the old picture

---

### Produce Grade Triggers (tbl_produce_grades)

#### trigger_produce_grades_before_save

**Event**: `BEFORE INSERT ON tbl_produce_grades`

- Activates parent produce (`produce_status = 1`) when first grade is added
- Inherits `grade_dp` from parent produce if NULL

#### trigger_produce_grades_before_update

**Event**: `BEFORE UPDATE ON tbl_produce_grades`

- Deactivates parent produce when last active grade is deactivated
- Reactivates parent produce when a grade is activated
- Inherits `grade_dp` from parent produce if NULL

#### trigger_produce_grade_before_delete

**Event**: `BEFORE DELETE ON tbl_produce_grades`

Deactivates parent produce when the last grade is deleted.

---

### Lot Triggers (tbl_lots)

#### trig_lot_b_in / trig_lot_b_up

**Event**: `BEFORE INSERT/UPDATE ON tbl_lots`

Denormalizes produce metadata: copies `grade_name`, `gi_name`, `produce_name` from joined lookup tables. Sets `lot_dp` from parent produce if NULL.

---

## Bidlot Triggers

### trig_bid_lot_bf_ins / trig_bid_lots_bf_upd

**Event**: `BEFORE INSERT/UPDATE ON tbl_bidlots`

Same denormalization pattern as lot triggers — copies `grade_name`, `gi_name`, `produce_name` from produce lookup tables.

### trig_bef_ins_bidhist

**Event**: `BEFORE INSERT ON tbl_bidlot_bids_history`

Updates the bidlot's `highest_bidder`, `last_bid_amount`, and `last_bidtime` with the new bid data.

---

## Stored Functions

### fn_calculate_working_seconds

**Parameters**: `p_agent_id INT`, `p_start_time DATETIME`, `p_end_time DATETIME`
**Returns**: `INT` (seconds)

Calculates working seconds between two timestamps, excluding:
- Non-working days (configurable via `tbl_company_work_hours.working_days`, default: Mon–Sat)
- Holidays (via `fn_is_holiday`)
- Agent leaves (via `fn_get_agent_leave_type`)
- Lunch break (between `first_half_end` and `second_half_start`, default: 14:00–15:00)

Work hours default: 10:00–19:00. Used by `trg_calculate_attempt_time` for FRT calculation.

---

### fn_is_holiday

**Parameters**: `check_date DATE`
**Returns**: `TINYINT` (0 or 1)

Checks `tbl_company_holidays` for active holidays with recurrence types:

| Recurrence Type | Match Logic |
|----------------|-------------|
| `once` | Exact date match |
| `yearly_same_date` | Same day + month |
| `monthly_same_date` | Same day of month |
| `yearly_same_weekday_of_month` | Same weekday + week number + month |
| `monthly_same_weekday` | Same weekday + week number |

---

### fn_get_agent_leave_type

**Parameters**: `p_agent_id INT`, `check_date DATE`
**Returns**: `VARCHAR(20)` — `NULL`, `'full_day'`, `'first_half'`, or `'second_half'`

Checks `tbl_user_leaves` for approved leaves. Two `first_half` + `second_half` leaves on the same day are treated as `full_day`.

---

### fn_get_next_working_start

**Parameters**: `p_agent_id INT`, `p_from_time DATETIME`
**Returns**: `DATETIME`

Finds the next working-hours start time from a given timestamp. Accounts for holidays, leaves (half-day leaves shift to the available half), and non-working days. Searches up to 60 days forward.

---

## Trigger Dependency Map

```
tbl_open_conversations
  ├── BEFORE INSERT → trg_conversation_before_insert
  ├── BEFORE UPDATE → trg_calculate_attempt_time
  │                    └── calls fn_calculate_working_seconds
  │                         ├── calls fn_is_holiday
  │                         └── calls fn_get_agent_leave_type
  ├── BEFORE UPDATE → trg_conversation_before_update
  ├── AFTER INSERT  → trg_conversation_after_insert
  │                    ├── writes crm_conversation_cohort_summary
  │                    ├── writes crm_conversation_activity_summary
  │                    └── writes crm_conversation_stage_summary
  └── AFTER UPDATE  → trg_conversation_after_update
                       ├── writes crm_conversation_stage_summary
                       ├── writes crm_conversation_activity_summary
                       ├── writes crm_conversation_cohort_summary
                       └── writes crm_unqualified_summary

tbl_orders
  ├── BEFORE INSERT → before_order_insert
  ├── BEFORE UPDATE → trigger_before_order_update
  ├── AFTER INSERT  → after_order_insert_combined
  │                    ├── writes temp_tbl_accounts
  │                    └── writes crm_revenue_agent_summary
  └── AFTER UPDATE  → after_order_update_combined
                       ├── writes temp_tbl_accounts
                       ├── writes crm_revenue_agent_summary
                       └── cascades to tbl_order_items

tbl_payments → trigger_payment_* → updates tbl_orders.amount_paid
  └── triggers tbl_orders BEFORE UPDATE → recalculates payment_status

tbl_payments_approval → trigger_payments_approval_*
  ├── updates tbl_orders.approval_pending
  └── on Approved: creates tbl_payments or tbl_customer_deposits record

tbl_opportunities
  ├── AFTER INSERT → trg_outcome_agent_opp_insert → crm_outcome_agent_summary
  ├── AFTER INSERT → trg_outcome_opportunity_insert → crm_outcome_summary
  ├── AFTER UPDATE → trg_outcome_opportunity_update → crm_outcome_summary
  └── AFTER UPDATE → trg_outcome_agent_opp_update → crm_outcome_agent_summary

tbl_followup_schedules
  ├── AFTER INSERT → trg_followup_insert_increment_count → tbl_open_conversations
  ├── AFTER INSERT → trg_agent_activity_task_insert → crm_agent_activity_summary
  ├── AFTER UPDATE → trg_followup_update_adjust_count → tbl_open_conversations
  └── AFTER DELETE → trg_followup_delete_decrement_count → tbl_open_conversations

tbl_call_logs
  ├── AFTER INSERT → trg_agent_activity_call_insert → crm_agent_activity_summary
  └── AFTER UPDATE → trg_agent_activity_call_update → crm_agent_activity_summary

tbl_whatsapp_messages
  └── AFTER INSERT → trg_agent_activity_message_insert → crm_agent_activity_summary

tbl_order_items → trigger_order_items_* → updates tbl_lots.quantity_sold
tbl_customers → after_update_* → tbl_agent_summary, tbl_contact_source_summary
tbl_customer_contacts → trigger_generate_number_* → self (concatenated_num)
tbl_produce_grades → trigger_produce_grades_* → tbl_produces.produce_status
tbl_produces → trig_produce_b_* → tbl_produce_grades.grade_dp (cascade)
```

---

## Cross-References

| Document | Path |
|----------|------|
| Schema Overview | `03-database-design/schema-overview.md` |
| Core Tables | `03-database-design/core-tables.md` |
| CRM Tables | `03-database-design/crm-tables.md` |
| Order Tables | `03-database-design/order-tables.md` |
| Migration System | `03-database-design/migration-system.md` |
| Reporting Module | `04-core-modules/reporting.md` |
| Order Management | `04-core-modules/order-management.md` |
| Conversations Module | `04-core-modules/conversations.md` |
