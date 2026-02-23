# AI Kanban — Task Board for Human-AI Collaboration

@refine programming/base-spec-author.promptspec.md
@refine programming/stack-typescript-nextjs-prisma.promptspec.md
@refine programming/type-saas-webapp.promptspec.md
@refine programming/module-auth.promptspec.md
@refine programming/module-rest-api.promptspec.md
@refine programming/module-realtime.promptspec.md
@refine programming/module-ai-features.promptspec.md

@audience "senior full-stack developer implementing from this spec"
@style "precise, implementation-ready, interaction-design-conscious"

## Product Vision

AI Kanban is a **task board designed for human-AI collaboration**. Unlike
traditional Kanban boards where humans do all the work, here the user defines
tasks for an AI agent system to execute. Cards are not passive sticky notes —
they are **live workspaces** where the AI streams progress, surfaces outputs,
and the user steers direction in real time.

The key insight: AI work is not linear. An AI might explore 3 approaches in
parallel, produce intermediate artifacts, encounter ambiguities that need human
input, and generate outputs in multiple formats simultaneously. The board must
make all of this visible and navigable.

## Board Architecture

### Columns (Default Pipeline)
- **Inbox**: user drafts tasks (plain language or structured).
- **Planning**: AI decomposes task into sub-steps, estimates complexity, identifies needed tools/data. User reviews and approves plan.
- **In Progress**: AI actively executing. Card shows live status.
- **Review**: AI finished. User reviews outputs, can request revisions.
- **Done**: accepted deliverables. Archived after 30 days.
- **Blocked**: AI encountered an issue requiring human input.

Users MAY create custom columns. Moving a card to a column triggers the
corresponding lifecycle hook (see Card Lifecycle below).

### Card Model

Each card has:
- **Header**: title, priority badge (P0–P3), assignee (AI agent name or "Unassigned").
- **Description**: markdown body with the user's intent. Supports `@mention` of other cards for dependencies.
- **AI Plan Panel**: collapsible section showing the AI's decomposition:
  sub-tasks as a checklist, each with status indicator (⏳ pending, 🔄 running, ✅ done, ❌ failed).
- **Output Surfaces** (see below).
- **Activity Stream**: chronological log of all events (AI actions, user edits, status changes).
  Filterable by: AI events, human events, errors only.
- **Context Attachments**: files, URLs, code snippets, or references to other cards
  that the AI should use as input.
- **Metadata sidebar**: created date, last updated, time in current column,
  estimated tokens used, cost estimate.

### Output Surfaces — The Core Innovation

AI outputs are NOT buried in a single text block. Instead, each card has
**multiple typed output surfaces** that display results in purpose-built views:

@match output_surface_level
  "standard" ==>
    #### Output Surface Types
    1. **Text**: rendered markdown. Default surface for prose, explanations, plans.
    2. **Code**: syntax-highlighted code blocks with language tag, copy button,
       and "Apply to file" action (if integrated with a repo).
    3. **Table**: structured data rendered as sortable/filterable table.
       AI specifies columns + rows as JSON; UI renders interactively.
    4. **Diff**: before/after comparison view (side-by-side or unified).
    5. **Image**: generated images or diagrams (AI provides URL or base64).
    6. **Status**: key-value dashboard (e.g., "Tests Passing: 47/50", "Coverage: 82%").
       Rendered as metric cards with trend arrows.

  "advanced" ==>
    #### Output Surface Types
    1. **Text**: rendered markdown with collapsible sections for long outputs.
    2. **Code**: syntax-highlighted, multi-file tabbed view. Each tab = one file.
       Supports inline comments from user. "Apply All" button pushes to repo.
    3. **Table**: structured data as interactive table. Supports column resize,
       CSV export, chart-from-table (select columns → generate chart).
    4. **Diff**: before/after with inline commenting. Approval workflow:
       user approves or rejects each hunk.
    5. **Image**: gallery view for multiple images. Click to expand. Side-by-side
       comparison mode for iterations.
    6. **Status**: real-time metric dashboard with sparklines and threshold coloring
       (green/yellow/red). Configurable layout (grid or list).
    7. **Canvas**: freeform spatial layout where AI places connected nodes
       (for mind maps, architecture diagrams, flowcharts). User can rearrange.
    8. **Terminal**: scrolling log output for long-running tasks (build, test run).
       ANSI color support. Auto-scroll with "pin to bottom" toggle.
    9. **Form**: AI-generated input form for collecting structured user decisions
       (e.g., "Which approach do you prefer?" with radio buttons and a confirm action).

Each card can have multiple surfaces. Surfaces are ordered by the AI (most
important first) but the user can reorder, pin, minimize, or pop out into a
floating window.

### Board-Level Dashboards

Beyond individual cards, the board itself has **aggregate views**:

- **Progress Dashboard**: total cards by column (bar chart), throughput over time
  (cards completed per day), average time-in-column, cost tracker.
- **Surface Aggregator**: a single view that collects all Status surfaces across
  all In Progress cards into one unified dashboard. Filters by tag or agent.
- **Dependency Graph**: visual DAG of card dependencies (from `@mention` links).
  Highlights critical path and blocked chains.
- **Agent Activity**: which AI agents are working on what, their queue depth,
  recent errors, and token usage per agent.

## Card Lifecycle & AI Integration

### Lifecycle Hooks
When a card moves to a column, the system fires a hook:

| Column | Hook | AI Behavior |
|--------|------|-------------|
| Inbox | — | No AI action. User drafts. |
| Planning | `on_plan` | AI reads description + attachments, generates sub-task plan, estimates complexity. Creates AI Plan Panel. |
| In Progress | `on_start` | AI begins executing plan. Opens WebSocket channel for live updates. Creates output surfaces as needed. |
| Review | `on_review` | AI generates summary of what was done. Highlights decisions it made and any deviations from the plan. |
| Blocked | `on_block` | AI posts a Form surface with the specific question/decision it needs from the user. |
| Done | `on_complete` | AI archives intermediate artifacts. Final outputs pinned. |

### Real-Time Updates (WebSocket)
- While a card is In Progress, the AI streams events via WebSocket:
  - `surface_update`: new content for an output surface (append or replace).
  - `subtask_status`: a sub-task changed status.
  - `attention_needed`: AI needs user input (auto-moves card to Blocked if no response in 5 min).
  - `progress`: percentage completion estimate.
- All events are also persisted to the Activity Stream.
- Client renders updates immediately — no polling.

### Parallel Execution
- A single card MAY have multiple sub-tasks running in parallel.
- Each sub-task gets its own output surface.
- The card's Status surface shows aggregate progress.
- If sub-tasks conflict (e.g., two approaches to the same problem), AI creates a
  Form surface asking the user to choose.

## AI Agent Protocol

### Agent Interface
- Agents connect via API: `POST /api/v1/cards/{id}/events` with event payloads.
- Authentication: per-agent API keys with scoped permissions (read card, write surfaces, move columns).
- Rate limit: 100 events/minute per card.

### Agent Types
@if multi_agent
  - **Planner**: decomposes tasks, no execution.
  - **Coder**: writes and modifies code. Outputs Code + Diff surfaces.
  - **Researcher**: searches web/docs, summarizes findings. Outputs Text + Table.
  - **Reviewer**: reviews outputs from other agents. Outputs Diff with comments.
  - **Orchestrator**: meta-agent that assigns sub-tasks to other agents and monitors progress.
  Agent assignment rules configurable per board (e.g., "all coding tasks go to Coder agent").

## Keyboard & Power User Features

- `N`: new card in Inbox.
- `E`: edit current card description.
- `→` / `←`: move card to next/previous column.
- `/`: command palette (fuzzy search cards, actions, agents).
- `Ctrl+Shift+S`: toggle Surface Aggregator.
- Drag cards between columns. Drag to reorder within column.
- Card quick-filter: type to filter visible cards by title (instant, no submit).

@assert "Every output surface type must specify its data schema and rendering behavior"
@assert "The WebSocket protocol must define all event types with payload schemas"
@assert "Card lifecycle hooks must specify exactly what the AI does at each stage"

@output_format "markdown"
  Structure the output as:
  1. Architecture Overview (system components, data flow)
  2. Data Models (cards, surfaces, agents, events — full schemas)
  3. API Endpoints (card CRUD, surface management, agent events, board queries)
  4. WebSocket Protocol (all event types with JSON schemas)
  5. Frontend Pages (board view, card detail, dashboards — component breakdown)
  6. Agent Integration (protocol, authentication, lifecycle)
  7. Testing Strategy
