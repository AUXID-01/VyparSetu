-- wipe.sql — safe to re-run any time; respects FK order via CASCADE
TRUNCATE TABLE
  invoice_extraction_audit,
  invoice_packaging_adjustments,
  invoice_line_items,
  invoices,
  outbox_events,
  insight_cache,
  alerts,
  settlement_daily_rollups,
  ledger_transactions,
  distributors,
  customers,
  merchants
CASCADE;
