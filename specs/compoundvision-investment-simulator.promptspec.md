# CompoundVision — Interactive Compound Interest & Investment Simulator

@refine programming/base-spec-author.promptspec.md
@refine programming/stack-typescript-nextjs-prisma.promptspec.md
@refine programming/module-auth.promptspec.md
@refine programming/module-dashboard.promptspec.md

@audience "senior frontend/full-stack developer implementing from this spec"
@style "precise, mathematically rigorous, visualization-focused"

## Product Vision

CompoundVision is a **sophisticated compound interest simulator and investment
planning tool** that makes the power (and risks) of compounding viscerally
visible. It goes far beyond "plug in a rate and see a curve" — it models
real-world conditions: market volatility, inflation erosion, tax drag, fee
compounding, dollar-cost averaging, and Monte Carlo scenarios. The goal is to
help users build intuition about how small changes in rate, fees, or
contribution timing create enormous differences over decades.

## Core Calculation Engine

### Fundamental Formula
All calculations are based on discrete compounding with configurable frequency:

```
FV = PV × (1 + r/n)^(n×t) + PMT × [((1 + r/n)^(n×t) - 1) / (r/n)]
```
Where: PV = present value, r = annual rate, n = compounding periods/year,
t = years, PMT = periodic contribution.

Engine MUST support:
- **Compounding frequencies**: daily (365), monthly (12), quarterly (4),
  semi-annual (2), annual (1), continuous (limit).
- **Contribution timing**: beginning of period (annuity due) or end (ordinary annuity).
- **Variable rates**: different rates per year/period (for scenario modeling).
- **All arithmetic in arbitrary precision** (use decimal.js or similar) —
  never floating point for financial math.

### Mark-to-Market Simulation

The real magic: show what compounding looks like under **actual market conditions**.

@match simulation_mode
  "deterministic" ==>
    #### Deterministic Scenarios
    - User inputs a fixed annual return (e.g., 7%).
    - Optional: model a single drawdown event (e.g., -40% in year 5, recover over 3 years).
    - Show the compounding curve with and without the drawdown overlaid.
    - Table view: year-by-year breakdown with columns:
      `Year | Start Balance | Contributions | Growth | End Balance | Total Contributed | Total Growth`

  "historical" ==>
    #### Historical Backtesting
    - User selects an asset class or index: S&P 500, NASDAQ, Total Bond Market,
      60/40 Portfolio, Gold, Real Estate (REIT index), Bitcoin.
    - System uses actual historical annual returns (stored in DB, 1928–present for S&P 500).
    - User picks a start year → system runs the simulation using real returns from that year forward.
    - **Sliding window**: show what happens if the user started in every possible year
      (e.g., 30-year outcomes starting 1928, 1929, ..., 1994). Display as a fan chart.
    - Highlight: best case, worst case, median outcome with dollar amounts.

  "montecarlo" ==>
    #### Monte Carlo Simulation
    - User specifies: expected annual return (μ), annual volatility (σ),
      assumed return distribution (normal or log-normal).
    - Engine runs N simulations (default 10,000), each sampling returns from the distribution.
    - Output:
      - **Fan chart**: percentile bands (5th, 25th, 50th, 75th, 95th) over time.
      - **Probability table**: "Probability of reaching $X after Y years" for user-specified targets.
      - **Ruin probability**: chance of portfolio dropping below zero (relevant for withdrawal scenarios).
      - **Terminal wealth distribution**: histogram of final portfolio values.
    - Performance: 10,000 × 30-year simulations MUST complete in < 2 seconds (use Web Workers).

### Real-World Adjustments

@expand
  #### Inflation Erosion
  - Toggle: show all values in nominal dollars or real (inflation-adjusted) dollars.
  - Default inflation rate: 3% (configurable).
  - Visualization: two overlaid curves — nominal vs real — with the gap labeled
    "purchasing power lost to inflation: $X".

  #### Tax Drag
  - Model three account types: taxable, tax-deferred (401k/IRA), tax-free (Roth).
  - Taxable: annual tax on dividends + tax on realized gains at withdrawal.
  - Tax rates: configurable (federal + state). Default: 22% income, 15% LTCG.
  - Show: pre-tax vs post-tax terminal value. The difference is the "tax drag."
  - Comparison mode: same investment across all 3 account types side-by-side.

  #### Fee Erosion
  - Expense ratio: annual percentage (e.g., 0.03% for index fund, 1.0% for active fund).
  - Advisory fee: separate annual percentage.
  - Applied daily: `daily_fee = annual_fee / 365`, deducted from portfolio each day.
  - **Fee impact visualizer**: show the dollar cost of fees over the full horizon.
    "A 1% annual fee costs you $X over 30 years on a $500/mo investment."
  - Comparison: same investment at 0.03% vs 0.50% vs 1.00% fees side-by-side.

  #### Dollar-Cost Averaging vs Lump Sum
  - Scenario A: invest $X as a lump sum today.
  - Scenario B: invest $X/12 monthly over one year, remainder grows at cash rate.
  - Historical comparison: run both strategies on every possible 12-month window.
  - Show: "Lump sum beats DCA X% of the time historically" with distribution chart.

## Investment Planning Tools

### Goal Planner
- User defines a goal: "I want $1,000,000 by age 60."
- Inputs: current age, current savings, expected annual contribution.
- Engine solves for: required rate of return, OR required monthly contribution,
  OR years needed (user picks which variable to solve for).
- Sensitivity table: "If your return is 1% lower, you need $Y more per month."

### Withdrawal Simulator (Retirement)
- User specifies: starting portfolio, annual withdrawal amount (or % rule),
  expected return, inflation rate, time horizon.
- 4% rule analysis: show probability of portfolio survival over 20/25/30/35/40 years.
- Dynamic withdrawal strategies:
  - Fixed dollar (inflation-adjusted).
  - Fixed percentage of current balance.
  - Guardrails (Guyton-Klinger): cut spending 10% if portfolio drops 20%,
    raise 10% if portfolio rises 20% above initial.
- Monte Carlo overlay: probability of ruin for each strategy.

### Portfolio Comparison Tool
- Compare up to 4 portfolio allocations side-by-side.
- Each portfolio: list of assets with allocation percentages.
- Run historical or Monte Carlo simulation on each.
- Metrics per portfolio: CAGR, max drawdown, Sharpe ratio, Sortino ratio,
  terminal value at 25th/50th/75th percentile.
- Visualization: overlaid growth curves with a shared time axis.

## Visualizations (Critical)

All charts MUST be **interactive** — hover for exact values, click to drill down,
pinch-to-zoom on mobile.

### Required Charts
1. **Growth Curve**: primary visualization. Log scale toggle. Annotations for
   contributions vs growth (stacked area). Milestone markers ("First $100K here").
2. **Fan Chart**: for Monte Carlo and historical sliding window. Gradient fill
   for percentile bands. Hover shows exact percentile values.
3. **Comparison Overlay**: up to 4 scenarios on one chart with legend toggle.
4. **Waterfall Chart**: for a single year — show starting balance, contribution,
   growth, fees, taxes, inflation → ending balance as a waterfall.
5. **Sensitivity Heatmap**: 2D grid (e.g., return rate × years) colored by outcome.
   Hover shows exact dollar amount. User picks the two axes.
6. **Distribution Histogram**: terminal wealth distribution from Monte Carlo.
   Overlay normal curve. Mark user's target with a vertical line.
7. **Fee Impact Bar**: dramatic horizontal bar showing total dollars lost to
   fees at different expense ratios.

### Shareable Results
- "Share this simulation" button generates a unique URL with all parameters encoded.
- URL contains no PII — only simulation parameters.
- Shared page: read-only interactive view with all charts.
- Export: PNG of any chart, CSV of any table, PDF report of full simulation.

## Data Model

### Historical Returns Table
| Field | Type | Constraints |
|-------|------|-------------|
| id | SERIAL | PK |
| asset_class | VARCHAR(50) | NOT NULL, indexed |
| year | INT | NOT NULL |
| annual_return_pct | DECIMAL(8,4) | NOT NULL (e.g., 7.5000 = 7.5%) |
| dividend_yield_pct | DECIMAL(8,4) | NULL |
| inflation_pct | DECIMAL(8,4) | NULL (CPI for that year) |

**Unique**: `(asset_class, year)`. Pre-seeded with S&P 500 (1928–present),
10-Year Treasury, CPI, Gold, NASDAQ (1971–), REIT (1972–).

### Saved Simulation
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NULL for anonymous |
| title | VARCHAR(200) | NOT NULL |
| parameters | JSONB | NOT NULL (all simulation inputs) |
| share_token | VARCHAR(32) | UNIQUE, NULL (set when shared) |
| created_at | TIMESTAMP | NOT NULL |

@assert "All financial calculations must use arbitrary-precision arithmetic, never IEEE 754 floats"
@assert "Monte Carlo simulations must specify the random number generator and distribution parameters"
@assert "Every chart type must specify its data inputs, axes, interactions, and accessibility features"
@assert "The spec must include exact formulas for every calculation (compound interest, tax drag, fee erosion)"

@output_format "markdown"
  Structure the output as:
  1. Architecture Overview
  2. Calculation Engine (all formulas, precision requirements, performance targets)
  3. Data Models (full schemas)
  4. API Endpoints (simulation runs, historical data, saved simulations, sharing)
  5. Frontend Pages & Components (with chart specifications)
  6. Performance Requirements (Web Workers, caching strategy)
  7. Testing Strategy (property-based tests for financial math, visual regression for charts)
