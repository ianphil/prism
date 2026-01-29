---
name: autopilot
description: This skill should be used when the user asks to "build this feature", "autopilot", "run the full workflow", "implement everything", or wants fully autonomous execution from plan to completion without manual orchestration.
---

# Autopilot

Fully autonomous workflow execution from quick plan to completed feature.

## User Input

INPUT = $ARGUMENTS

Accept one of:
- Quick plan filename: `"20260127-foundation-agent-framework-ollama"`
- Quick plan slug: `"foundation-agent-framework-ollama"`
- Feature number (if already planned): `"001"`
- `"all"` - Process all open quick plans sequentially
- `"next"` - Pick the highest priority open quick plan

## Decision Policies (Autonomous Defaults)

These defaults eliminate human intervention:

| Decision Point | Default Policy |
|----------------|----------------|
| Extensive mocking detected | Defer to integration test, continue |
| Incomplete tasks at close | Close anyway (log incomplete items) |
| Clarifying questions during planning | Make reasonable assumptions, document in plan |
| Test failures during implement | Retry once, then log and continue to next task |
| Lint failures | Auto-fix with `uv run ruff check --fix .`, then continue |
| Git conflicts | Abort current feature, report, move to next |

## Execution Flow

```
INPUT
  │
  ▼
┌─────────────────────────────┐
│  1. RESOLVE INPUT           │
│  - Find quick plan or       │
│    existing feature         │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  2. PLANNING (if needed)    │
│  - Skip if feature exists   │
│  - Run /planner workflow    │
│  - Creates NNN-slug/        │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  3. ANALYZE WORK PLAN       │
│  - Parse tasks.md           │
│  - Build phase dependency   │
│    graph                    │
│  - Identify parallel waves  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  4. EXECUTE PHASES          │
│  - Sequential: dependent    │
│  - Parallel: independent    │
│  - Commit after each phase  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  5. VERIFY & CLOSE          │
│  - Run all tests            │
│  - Run /closer              │
│  - Push to remote           │
└─────────────────────────────┘
```

## Step 1: Resolve Input

```python
# Pseudo-logic for input resolution

if INPUT == "all":
    plans = glob("backlog/plans/2*.md")  # All quick plans
    sort by priority (critical > high > medium > low)
    process each sequentially

elif INPUT == "next":
    plans = glob("backlog/plans/2*.md")
    pick highest priority plan

elif INPUT matches /^\d{3}/:
    # Feature number - already planned
    feature_path = find_feature(INPUT)
    skip to Step 3

else:
    # Quick plan name/slug
    plan_file = find_quick_plan(INPUT)
```

### Finding Quick Plans

```bash
# List available quick plans with their priorities
for f in backlog/plans/2*.md; do
  priority=$(grep -oP 'priority:\s*\K\w+' "$f" 2>/dev/null || echo "medium")
  echo "$priority $f"
done | sort -k1
```

## Step 2: Planning Phase

If starting from a quick plan (not an existing feature):

```
1. Read the quick plan file
2. Extract: title, motivation, goals, design hints

3. Run /planner workflow:
   - Determine next feature ID (NNN)
   - Create branch: feature/{NNN}-{slug}
   - Create folder: backlog/plans/{NNN}-{slug}/
   - Generate all planning artifacts:
     - analysis.md (analyze existing code patterns)
     - spec.md (derive from quick plan goals)
     - research.md (if external APIs involved)
     - plan.md (implementation design)
     - data-model.md (if data structures needed)
     - tasks.md (TDD task breakdown)
   - Create spec tests: specs/tests/{NNN}-{slug}.md
   - Delete the quick plan file (superseded)

4. Commit planning artifacts:
   git add backlog/plans/{NNN}-{slug}/ specs/tests/
   git commit -m "feat: planning for {NNN}-{slug}"
```

**Assumption Handling**: When planning would normally require clarification:
- Check if quick plan already answers the question
- Make the most common/reasonable assumption
- Document assumption in the relevant artifact with `<!-- ASSUMPTION: ... -->`

## Step 3: Analyze Work Plan

Parse `tasks.md` to understand execution order:

```
1. Read {feature-path}/tasks.md

2. Extract phases:
   - Phase number, name
   - Task list (T001, T002, ...)
   - Task types: [TEST], [IMPL], [SPEC]
   - Completion status

3. Build dependency graph from "## Dependencies" section

4. Compute execution waves:
   Wave 1: Phases with no dependencies (can run parallel)
   Wave 2: Phases depending only on Wave 1
   Wave 3: etc.

5. Output execution plan:
   {
     "feature": "001-foundation-agent",
     "total_phases": 5,
     "total_tasks": 34,
     "waves": [
       {"wave": 1, "phases": ["Phase 1"], "parallel": false},
       {"wave": 2, "phases": ["Phase 2", "Phase 3"], "parallel": true},
       {"wave": 3, "phases": ["Phase 4"], "parallel": false},
       {"wave": 4, "phases": ["Phase 5"], "parallel": false}
     ]
   }
```

## Step 4: Execute Phases

For each wave in order:

### Sequential Execution (single phase or dependencies)

```
For PHASE in wave.phases:
  1. Log: "Starting {PHASE}"

  2. Run /implement "{PHASE}":
     - Execute [SPEC] entry test (expect fail)
     - For each [TEST] task: write test, run, expect fail
     - For each [IMPL] task: implement, run test, expect pass
     - Execute [SPEC] exit test (expect pass)
     - Mark tasks complete in tasks.md

  3. Handle failures:
     - Test failure: retry once, then mark task with ⚠️ and continue
     - Lint failure: run `uv run ruff check --fix .`, retry
     - Build failure: log error, ask for help (break autonomy)

  4. Commit phase:
     git add -A
     git commit -m "feat({NNN}): complete {PHASE}"

  5. Push incrementally:
     git push -u origin feature/{NNN}-{slug}
```

### Parallel Execution (independent phases)

```
For wave with multiple independent phases:
  1. Spawn agents using /implement-agents:
     Task(
       subagent_type: "general-purpose",
       description: "Implement {PHASE_A}",
       prompt: "Run /implement '{PHASE_A}'",
       run_in_background: true
     )
     Task(
       subagent_type: "general-purpose",
       description: "Implement {PHASE_B}",
       prompt: "Run /implement '{PHASE_B}'",
       run_in_background: true
     )

  2. Monitor progress via output files

  3. Wait for all agents to complete

  4. Check for conflicts:
     git status
     If conflicts: resolve or abort

  5. Commit combined progress:
     git add -A
     git commit -m "feat({NNN}): complete {PHASE_A}, {PHASE_B}"
```

## Step 5: Verify & Close

After all phases complete:

```
1. Final verification:
   uv run pytest                    # All tests pass
   uv run ruff check .              # No lint errors
   uv run black --check .           # Formatting OK

2. Check tasks.md:
   - Count completed vs total
   - List any incomplete tasks

3. If all tasks complete:
   Run /closer "{NNN}":
   - Move to backlog/plans/_completed/
   - Update documentation references
   - Commit closure

4. If incomplete tasks:
   Log incomplete items
   Still run /closer (per decision policy)
   Mark feature as "partial" in commit

5. Final push:
   git push origin feature/{NNN}-{slug}

6. Output summary:
   ✅ Feature {NNN}-{slug} complete
   - Phases: 5/5
   - Tasks: 32/34 (2 deferred to integration)
   - Commits: 7
   - Branch: feature/{NNN}-{slug}

   Remaining:
   - Create PR: gh pr create
   - Manual testing items: [list from tasks.md]
```

## Error Recovery

### Recoverable Errors (continue automatically)

| Error | Recovery |
|-------|----------|
| Single test failure | Mark task ⚠️, continue |
| Lint error | Auto-fix, retry |
| Network timeout (git push) | Retry with backoff (4 attempts) |
| Missing optional file | Skip, document |

### Non-Recoverable Errors (stop and report)

| Error | Action |
|-------|--------|
| Build completely broken | Stop, output diagnostics |
| Git conflict in critical file | Stop, list conflicts |
| All tests in phase failing | Stop, likely design issue |
| Missing required dependency | Stop, report what's needed |

### Recovery Log

All errors logged to `.ai/autopilot/{NNN}-{slug}.log`:

```
[2026-01-29T10:15:32] START autopilot "foundation-agent-framework-ollama"
[2026-01-29T10:15:45] PLANNING created 001-foundation-agent
[2026-01-29T10:23:12] PHASE_START Phase 1: Core Framework
[2026-01-29T10:28:45] TASK_COMPLETE T001
[2026-01-29T10:31:22] TASK_WARN T002 - test flaky, passed on retry
[2026-01-29T10:45:00] PHASE_COMPLETE Phase 1
[2026-01-29T10:45:05] COMMIT abc123 "feat(001): complete Phase 1"
...
[2026-01-29T12:30:00] COMPLETE 001-foundation-agent (32/34 tasks)
```

## Batch Mode: "all"

When INPUT = "all":

```
1. List all quick plans in backlog/plans/
2. Sort by priority (from frontmatter)
3. For each plan:
   a. Run full autopilot workflow
   b. On success: continue to next
   c. On failure: log, skip to next
4. Output batch summary:

   Autopilot Batch Complete
   ========================
   ✅ 001-foundation-agent (34 tasks)
   ✅ 002-data-pipeline (28 tasks)
   ⚠️ 003-rag-feed (stopped: build error)
   ✅ 004-observability (19 tasks)

   Total: 3/4 features complete
   See: .ai/autopilot/batch-2026-01-29.log
```

## Usage Examples

```bash
# Single feature from quick plan
/autopilot "foundation-agent-framework-ollama"

# Continue existing feature
/autopilot "001"

# Process next highest priority
/autopilot "next"

# Process all open plans
/autopilot "all"
```

## Monitoring Progress

While autopilot runs, progress visible via:

1. **Todo list** - Updated in real-time
2. **Git log** - Commits after each phase
3. **Log file** - `.ai/autopilot/{feature}.log`
4. **tasks.md** - Checkboxes updated as tasks complete

## Integration with Existing Skills

Autopilot orchestrates these skills internally:

```
/autopilot
    ├── /planner (Step 2)
    ├── /work-plan (Step 3 - analysis only)
    ├── /implement (Step 4 - sequential)
    ├── /implement-agents (Step 4 - parallel)
    ├── /commit (after each phase)
    └── /closer (Step 5)
```

Does NOT call:
- `/prime` - Context loaded directly
- `/prime-feat` - Context loaded directly
- `/quick-plan` - Input, not generated
- `/share-transcript` - Optional, user-initiated
- `/work-plan` - Output only, not needed during execution
