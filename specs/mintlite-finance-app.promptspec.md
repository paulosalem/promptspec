# MintLite — Personal Finance Tracker

@refine programming/base-spec-author.promptspec.md
@refine programming/stack-typescript-nextjs-prisma.promptspec.md
@refine programming/type-saas-webapp.promptspec.md
@refine programming/module-auth.promptspec.md
@refine programming/module-rest-api.promptspec.md
@refine programming/model-finance.promptspec.md
@refine programming/module-dashboard.promptspec.md
@refine programming/module-notifications.promptspec.md
@refine programming/module-ai-features.promptspec.md

@audience "senior full-stack developer implementing from this spec"
@style "precise, implementation-ready, no hand-waving"

## Product Vision

MintLite is a **personal finance tracker** that helps individuals understand and
control their spending. It is NOT a banking app — it does not move money. Users
manually enter transactions or import CSV bank statements.

## Core Features

### Transaction Entry
- Quick-add form: amount, description, category (autocomplete), date, account.
- The amount field MUST accept natural input: "$42.50", "42.5", "4250 cents".
- After submission, show undo toast for 5 seconds.
- Duplicate detection: warn if a transaction with the same amount, date, and
  description already exists on the same account.

### CSV Import
- Accept CSV files from major banks (Chase, BofA, Wells Fargo, Citi).
- Auto-detect column mapping via header heuristics; let user confirm/adjust.
- Preview first 10 rows before committing.
- On import, run AI auto-categorization on uncategorized transactions.

### Budget Tracking
- Users set monthly budgets per category.
- Dashboard widget shows progress bars: green (<80%), yellow (80-100%), red (>100%).
- Alert when reaching 80% and 100% of a budget.

### Spending Insights
@if include_ai
  - Weekly AI digest: "You spent 23% more on dining this week vs your 4-week average."
  - Anomaly detection: flag unusually large transactions.
  - Natural language query: "What's my biggest expense category this quarter?"

@match report_depth
  "summary" ==>
    - Monthly summary: total income, total expenses, net savings, top 3 categories.
    - Trend sparklines on the dashboard for each account balance.

  "detailed" ==>
    - Monthly summary: total income, total expenses, net savings, top 3 categories.
    - Trend sparklines on the dashboard for each account balance.
    - Category-level drilldown: click a category to see all transactions.
    - Year-over-year comparison charts.
    - Cash flow forecast: project next 3 months based on recurring transactions.
    - Exportable PDF report with charts and tables.

### Recurring Transactions
- Users define rules: amount, category, frequency (daily/weekly/biweekly/monthly/yearly),
  start date, optional end date.
- System auto-generates transactions on schedule via background job.
- Editable: changing the rule does NOT modify past generated transactions.

## Non-Functional Requirements

@compress target: tokens budget: 300
  - Page load: < 2 seconds on 3G connection (Lighthouse performance > 80).
  - API response: p95 < 200ms for list endpoints, < 100ms for single-resource.
  - Data export: user can download all their data as JSON within 30 seconds.
  - Accessibility: WCAG 2.1 AA compliance. All interactive elements keyboard-navigable.
  - Mobile: fully responsive, usable on 375px-wide screens.
  - Security: OWASP Top 10 mitigations. CSP headers. No inline scripts.
  - Privacy: GDPR-ready. User can request full data deletion within 30 days.

@assert "The specification must include complete data model schemas"
@assert "Every API endpoint must specify request/response schemas and error codes"
@assert "No feature is described without acceptance criteria or testable behavior"

@output_format "markdown"
  Structure the output as a single, complete specification document with these sections:
  1. Overview & Architecture
  2. Data Models (with full schemas)
  3. API Endpoints (grouped by resource)
  4. Frontend Pages & Components
  5. Background Jobs
  6. Testing Strategy
  7. Deployment & Infrastructure
