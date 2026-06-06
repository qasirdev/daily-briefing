# JIRA Tickets JSON Directory — AI Daily Briefing Assistant

**Version:** 1.6.0 | **Last Updated:** June 2026

---

## Purpose

This directory contains JSON exports of epics and tasks that drive the implementation backlog. Cursor Development Agents use the structured data here to perform step-by-step implementation with full context of requirements, acceptance criteria, and dependencies.

---

## Directory Structure

```
docs/jira-tickets-json/
├── README.md                              # This file
├── DB-E1-mvp1-scaffold.json               # MVP 1: Project scaffold (10 tasks)
├── DB-E2-mvp2-agents.json                 # MVP 2: Core agents (10 tasks) — canonical format
├── DB-E3-mvp3-observability.json          # MVP 3: Observability (8 tasks)
├── DB-E4-mvp4-consent.json                # MVP 4: Agentic consent (8 tasks)
├── DB-E5-mvp5-security.json               # MVP 5: Security hardening (8 tasks)
├── DB-E6-mvp6-production.json             # MVP 6: Production deployment (8 tasks)
├── DB-E7-option1-hybrid.json              # Option 1: Supabase + stdio MCP (5 tasks)
├── DB-E8-gap-remediation.json             # Gap Week 1 (legacy epic+tasks shape)
├── DB-E9-gap-remediation-week2.json       # Gap Week 2
├── DB-E10-gap-remediation-week3.json      # Gap Week 3
├── DB-E11-gap-remediation-week4.json      # Gap Week 4
└── DB-E12-gap-remediation-week5.json      # Gap Week 5 — canonical format (required for new epics)
└── DB-E13-gap-remediation-week6.json      # Gap Week 6
└── DB-E14-gap-remediation-week7.json      # Gap Week 7 — canonical format
```

**Total: 62+ tasks across 12 epics**

---

## Canonical Task Format (Required for New Epics)

**All new epic and task JSON files MUST use the DB-E2 flat-array format** with a rich `Description` column. Reference: `DB-E2-mvp2-agents.json`, `DB-E12-gap-remediation-week5.json`.

```json
{
  "DB-E12": [
    {
      "Issue id": "DB-E12",
      "Summary": "Week 5: Supply Chain Security & JIT Credentials",
      "Issue Type": "Epic",
      "Description": "Epic scope...\n\nSCOPE:\n...\n\nSUCCESS CRITERIA:\n...",
      "Labels": "gap-remediation,week5",
      "Parent": ""
    },
    {
      "Issue id": "DB-121",
      "Summary": "Day 1: AI-BOM",
      "Issue Type": "Task",
      "Description": "One-line summary.\n\nIMPLEMENTATION DETAILS:\n- Bullet list of files and changes\n\nEFFORT: M (8 hours)\nPROJECT AREA: Backend\nDEPENDENCIES: DB-120\n\nTESTING CRITERIA:\n- Measurable pass conditions\n\nEDGE CASES:\n- Failure modes agents must handle",
      "Labels": "supply-chain,week5",
      "Parent": "DB-E12"
    }
  ]
}
```

### Description Field Sections (Required per Task)

| Section | Required | Purpose |
|---|---|---|
| Summary line | Yes | One-sentence task goal before sections |
| `IMPLEMENTATION DETAILS` | Yes | Files to create/modify, APIs, config |
| `EFFORT` | Yes | T-shirt size and hours (e.g. `M (8 hours)`) |
| `PROJECT AREA` | Yes | Backend, Frontend, CI/CD, Docs, etc. |
| `DEPENDENCIES` | Yes | Prior task IDs or epic prerequisites |
| `TESTING CRITERIA` | Yes | Tests and measurable acceptance checks |
| `EDGE CASES` | Yes | Fail-safe behaviour — **Coding Agent must implement all** |

Epic entries (`Issue Type: Epic`) use `SCOPE`, `REFERENCE DOCS`, and `SUCCESS CRITERIA` instead of implementation sections.

**Legacy format:** Gap weeks DB-E8–DB-E11 use `{ "epic": {...}, "tasks": [...] }`. Do not use for new weeks; migrate to DB-E2 shape when those epics are next edited.

---

## Backend Verification Gate (Required Before Task Complete)

Before marking any backend task done (including the last task of a gap week), run from the repository root:

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

- Use `uv run ruff check backend --fix` if import sort (`I001`) fails.
- Capture output in `proof/weekN/` or `logs/` when the epic success criteria require it.
- See `backend/AGENT.md` and `AGENT.md` workflow rules.

---

## JSON Schema (Legacy Reference)

### Epic Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "title", "mvp", "status", "stories"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^EPIC-\\d{3}$",
      "description": "Unique epic identifier"
    },
    "title": {
      "type": "string",
      "description": "Epic title"
    },
    "description": {
      "type": "string",
      "description": "Detailed epic description"
    },
    "mvp": {
      "type": "integer",
      "minimum": 1,
      "maximum": 6,
      "description": "MVP milestone this epic belongs to"
    },
    "status": {
      "type": "string",
      "enum": ["planned", "in_progress", "completed", "blocked"],
      "description": "Current epic status"
    },
    "acceptance_criteria": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Epic-level acceptance criteria"
    },
    "dependencies": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Other epic IDs this depends on"
    },
    "stories": {
      "type": "array",
      "items": { "$ref": "#/definitions/story" },
      "description": "User stories in this epic"
    }
  },
  "definitions": {
    "story": {
      "type": "object",
      "required": ["id", "title", "status", "tasks"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^STORY-\\d{4}$"
        },
        "title": {
          "type": "string"
        },
        "description": {
          "type": "string"
        },
        "status": {
          "type": "string",
          "enum": ["planned", "in_progress", "completed", "blocked"]
        },
        "acceptance_criteria": {
          "type": "array",
          "items": { "type": "string" }
        },
        "tasks": {
          "type": "array",
          "items": { "$ref": "#/definitions/task" }
        }
      }
    },
    "task": {
      "type": "object",
      "required": ["id", "title", "status"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^TASK-\\d{5}$"
        },
        "title": {
          "type": "string"
        },
        "description": {
          "type": "string",
          "description": "Detailed task description with edge cases"
        },
        "status": {
          "type": "string",
          "enum": ["todo", "in_progress", "review", "done", "blocked"]
        },
        "assignee": {
          "type": "string",
          "description": "Cursor agent or developer assigned"
        },
        "files_affected": {
          "type": "array",
          "items": { "type": "string" },
          "description": "File paths this task will modify"
        },
        "edge_cases": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Edge cases to handle"
        },
        "test_requirements": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Tests that must pass"
        }
      }
    }
  }
}
```

---

## Example Epic File

```json
{
  "id": "EPIC-002",
  "title": "Core Agent Implementation",
  "description": "Implement the core agents: Task, Calendar, Focus, and Critic",
  "mvp": 2,
  "status": "planned",
  "acceptance_criteria": [
    "All four agents return valid AgentResultEnvelope",
    "Agents communicate via LangGraph state",
    "MCP integrations are functional",
    "Unit tests achieve 80% coverage"
  ],
  "dependencies": ["EPIC-001"],
  "stories": [
    {
      "id": "STORY-0005",
      "title": "Implement Task Agent",
      "description": "Create the Task Agent that fetches and prioritizes tasks from PostgreSQL MCP",
      "status": "planned",
      "acceptance_criteria": [
        "Agent fetches tasks via PostgreSQL MCP query tool",
        "Tasks are sorted by priority and due date",
        "Returns AgentResultEnvelope with task list",
        "Handles MCP timeout gracefully"
      ],
      "tasks": [
        {
          "id": "TASK-00020",
          "title": "Create Task Agent node function",
          "description": "Implement the LangGraph node for Task Agent in backend/agents/task/node.py",
          "status": "todo",
          "assignee": "Coding Agent",
          "files_affected": [
            "backend/agents/task/__init__.py",
            "backend/agents/task/node.py",
            "backend/agents/task/AGENT.md"
          ],
          "edge_cases": [
            "No tasks in database - return empty list",
            "MCP timeout - escalate to orchestrator",
            "RLS violation - log and escalate",
            "Invalid task data - validate with Pydantic"
          ],
          "test_requirements": [
            "test_task_agent_success",
            "test_task_agent_empty_list",
            "test_task_agent_mcp_timeout",
            "test_task_agent_invalid_data"
          ]
        },
        {
          "id": "TASK-00021",
          "title": "Create Task Agent prompts",
          "description": "Create prompt files for Task Agent in prompts/task/",
          "status": "todo",
          "assignee": "Coding Agent",
          "files_affected": [
            "prompts/task/CONTRACT.md",
            "prompts/task/CHANGELOG.md",
            "prompts/task/system.md",
            "prompts/task/skills.md",
            "prompts/task/tools.md",
            "prompts/task/guardrails.md"
          ],
          "edge_cases": [],
          "test_requirements": [
            "test_task_agent_prompts_valid_xml",
            "test_task_agent_contract_schema"
          ]
        }
      ]
    }
  ]
}
```

---

## Workflow Rules

| Rule | Behaviour |
|---|---|
| JSON Sync | When JSON files change, update `docs/PLAN.md` to reflect changes |
| Description format | New epics use DB-E2 flat-array format with `IMPLEMENTATION DETAILS`, `TESTING CRITERIA`, `EDGE CASES` sections |
| Edge Cases | Coding Agent MUST implement all `EDGE CASES` listed in the task `Description` field |
| Test Requirements | Coding Agent MUST create tests matching `test_requirements` |
| File Tracking | Update `files_affected` when task scope changes |
| Status Updates | Update task status as work progresses |
| Dependencies | Check epic dependencies before starting implementation |

---

## Agent Usage

### Cursor Coding Agent

When assigned a task:

1. **Read the task description** including edge cases
2. **Check dependencies** - ensure prerequisite tasks are done
3. **Implement the feature** following edge case requirements
4. **Create tests** matching `test_requirements`
5. **Update task status** to `done` when complete

### Example Agent Workflow

```
1. Agent reads TASK-00020 from epic-002-mvp2-agents.json
2. Sees edge_cases: ["No tasks in database - return empty list", ...]
3. Implements node.py with handling for empty list case
4. Creates test_task_agent_empty_list() in tests/
5. Updates TASK-00020 status to "done"
6. Updates docs/tasks/todo.md with completion note
```

---

## Validation

### JSON Schema Validation

```python
import json
import jsonschema
from pathlib import Path

def validate_epic_file(file_path: Path):
    """Validate epic JSON against schema."""
    with open(file_path) as f:
        epic = json.load(f)
    
    with open("docs/jira-tickets-json/schema.json") as f:
        schema = json.load(f)
    
    jsonschema.validate(epic, schema)
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

for file in docs/jira-tickets-json/*.json; do
    if [[ "$file" != *"README"* ]] && [[ "$file" != *"schema"* ]]; then
        python -c "
import json
import jsonschema
with open('$file') as f: epic = json.load(f)
with open('docs/jira-tickets-json/schema.json') as f: schema = json.load(f)
jsonschema.validate(epic, schema)
print('Valid: $file')
"
    fi
done
```

---

## Sync with docs/PLAN.md

When epic/story/task files are updated, `docs/PLAN.md` should be regenerated:

```python
def generate_plan_md(epics_dir: Path) -> str:
    """Generate PLAN.md from epic JSON files."""
    plan = ["# Implementation Plan\n"]
    
    for epic_file in sorted(epics_dir.glob("epic-*.json")):
        with open(epic_file) as f:
            epic = json.load(f)
        
        status_emoji = {"planned": "⬜", "in_progress": "🔄", "completed": "✅", "blocked": "🚫"}
        
        plan.append(f"\n## {epic['id']}: {epic['title']} {status_emoji[epic['status']]}\n")
        plan.append(f"**MVP {epic['mvp']}**\n")
        
        for story in epic["stories"]:
            plan.append(f"\n### {story['id']}: {story['title']} {status_emoji[story['status']]}\n")
            
            for task in story["tasks"]:
                task_status = {"todo": "[ ]", "in_progress": "[~]", "review": "[R]", "done": "[x]", "blocked": "[!]"}
                plan.append(f"- {task_status[task['status']]} {task['id']}: {task['title']}\n")
    
    return "".join(plan)
```

---

*JIRA Tickets JSON README — Version 1.6.0 — June 2026*
