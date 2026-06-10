# Focus Agent Output Schema

**Version:** 2.0.0  
**Last Updated:** 2026-06-06

---

## Schema Definition

The Focus Agent MUST return **ONLY** valid JSON conforming to this exact schema.

**Critical rules:**
- NO markdown code blocks (no ``` backticks)
- NO preamble, explanation, or text outside JSON
- ONLY valid JSON
- ALL required fields must be present
- ALL enum values must match exactly

---

## JSON Schema

```json
{
  "plan": {
    "summary": "String (1-2 sentences, max 200 chars, no bullet points)",
    "time_blocks": [
      {
        "start": "String (HH:MM format, 24-hour)",
        "end": "String (HH:MM format, 24-hour)",
        "activity": "String (clear action verb + object)",
        "priority": "String (enum: 'high' | 'medium' | 'low')",
        "type": "String (enum: 'deep_work' | 'meeting' | 'break' | 'admin')"
      }
    ],
    "top_priorities": [
      "String (actionable priority, start with verb)"
    ],
    "energy_pattern": "String (optional: 'morning_peak' | 'afternoon_peak' | 'evening_peak' | 'steady')",
    "notes": "String (optional: any important context or constraints)"
  }
}
```

---

## Field Specifications

### Root: `plan` (Object, Required)

Container for the entire focus plan.

---

### `plan.summary` (String, Required)

**Purpose:** High-level overview of the day's focus in 1-2 sentences

**Constraints:**
- **Max length:** 200 characters
- **Format:** 1-2 complete sentences
- **Tense:** Present tense
- **Prohibited:** Bullet points, emoji, markdown formatting

**Requirements:**
- Mention the main theme or focus area
- Reference the top priority
- Readable in <10 seconds

**Good examples:**
```json
"summary": "Today's focus is finalizing the Q2 report. Priority is completing Section 3 analysis, followed by stakeholder review."
```

```json
"summary": "Deep work day with protected focus blocks. Priority is shipping the authentication feature."
```

**Bad examples:**
```json
"summary": "Today you will: \n- Finish report\n- Review PRs"  // Uses bullets
```

```json
"summary": "Work on various tasks and attend meetings"  // Too vague
```

---

### `plan.time_blocks` (Array, Required)

**Purpose:** Chronological breakdown of time-allocated activities

**Constraints:**
- **Min items:** 1
- **Max items:** 8
- **Order:** Chronological (sorted by start time)
- **Overlap:** NONE — blocks must not overlap
- **Coverage:** Should cover majority of work hours

**Each item must include:**

#### `time_blocks[].start` (String, Required)

**Format:** `HH:MM` (24-hour time)

**Constraints:**
- Must be ≥ current time (if same day)
- Must be < `end` time
- Must not overlap with other blocks

**Examples:**
```json
"start": "09:00"  // ✅ Valid
"start": "09:30"  // ✅ Valid
"start": "9:00"   // ❌ Invalid (missing leading zero)
"start": "9am"    // ❌ Invalid (not 24-hour format)
```

---

#### `time_blocks[].end` (String, Required)

**Format:** `HH:MM` (24-hour time)

**Constraints:**
- Must be > `start` time
- Must not overlap with next block's start

**Examples:**
```json
"end": "11:00"    // ✅ Valid
"end": "11:30"    // ✅ Valid
"end": "11am"     // ❌ Invalid (not 24-hour format)
```

---

#### `time_blocks[].activity` (String, Required)

**Purpose:** Clear description of what to do during this block

**Constraints:**
- Must start with action verb
- Must be specific (reference actual tasks/events)
- Max 100 characters recommended

**Requirements:**
- Use action verbs: "Complete", "Review", "Prepare", "Attend"
- Include object: "Q2 report", "PR #123", "client meeting"
- Be specific, not generic

**Good examples:**
```json
"activity": "Complete Q2 report Section 3 data analysis"
"activity": "Review and approve 3 pending pull requests"
"activity": "Attend team standup meeting"
"activity": "Prepare slides for 2pm client presentation"
```

**Bad examples:**
```json
"activity": "Work on stuff"           // Too vague
"activity": "Q2 report"               // Missing verb
"activity": "Do some coding tasks"    // Not specific
"activity": "Meeting"                 // Which meeting?
```

---

#### `time_blocks[].priority` (Enum, Required)

**Purpose:** Importance level of this activity

**Allowed values:**
- `"high"` — Critical, time-sensitive, high impact
- `"medium"` — Important but not urgent
- `"low"` — Nice-to-have, can be deferred

**Assignment criteria:**
- **High:** External deadlines, blocks other work, high-impact deliverables
- **Medium:** Internal deadlines, important strategic work, regular responsibilities
- **Low:** Optional tasks, learning/exploration, low-impact work

**Examples:**
```json
"priority": "high"      // ✅ Valid
"priority": "medium"    // ✅ Valid
"priority": "low"       // ✅ Valid
"priority": "urgent"    // ❌ Invalid (not in enum)
"priority": "critical"  // ❌ Invalid (use "high")
```

---

#### `time_blocks[].type` (Enum, Required)

**Purpose:** Category of activity for time management

**Allowed values:**
- `"deep_work"` — Focused, uninterrupted work requiring high cognitive load
- `"meeting"` — Scheduled meetings from calendar
- `"break"` — Rest, lunch, mental breaks
- `"admin"` — Email, Slack, quick reviews, logistical tasks

**Assignment criteria:**
- **deep_work:** Complex tasks (coding, writing, analysis), 90-120 min blocks
- **meeting:** Calendar events with other attendees
- **break:** Recovery time, 15-30 min
- **admin:** Quick tasks, context-switching safe, <60 min

**Examples:**
```json
"type": "deep_work"     // ✅ Valid
"type": "meeting"       // ✅ Valid
"type": "break"         // ✅ Valid
"type": "admin"         // ✅ Valid
"type": "focus"         // ❌ Invalid (use "deep_work")
"type": "call"          // ❌ Invalid (use "meeting")
```

---

### `plan.top_priorities` (Array, Required)

**Purpose:** 3-5 most important items to accomplish today

**Constraints:**
- **Min items:** 3
- **Max items:** 5
- **Order:** Most important first

**Requirements:**
- Start with action verb
- Be specific and actionable
- Should map to time blocks
- Reflect actual tasks from tools

**Good examples:**
```json
"top_priorities": [
  "Complete Q2 financial report and submit by 5pm",
  "Review and approve 3 pending pull requests",
  "Prepare presentation slides for Friday's client meeting"
]
```

**Bad examples:**
```json
"top_priorities": [
  "Work on project",              // Too vague
  "Meetings",                     // Not actionable
  "Catch up on emails",           // Usually not a top priority
  "Be more productive"            // Not specific
]
```

---

### `plan.energy_pattern` (Enum, Optional)

**Purpose:** Insight into user's energy levels throughout the day

**Allowed values:**
- `"morning_peak"` — Highest energy 8am-12pm
- `"afternoon_peak"` — Highest energy 1pm-5pm
- `"evening_peak"` — Highest energy 5pm-9pm
- `"steady"` — Consistent energy throughout day

**When to include:**
- If user preferences provide energy data
- If calendar pattern suggests consistent schedule
- If useful for explaining time block allocation

**When to omit:**
- No clear pattern
- Not relevant to the plan
- No user preference data

**Examples:**
```json
"energy_pattern": "morning_peak"     // ✅ Valid
"energy_pattern": "afternoon_peak"   // ✅ Valid
"energy_pattern": "high"             // ❌ Invalid (not in enum)
```

---

### `plan.notes` (String, Optional)

**Purpose:** Additional context, constraints, or explanations

**Constraints:**
- Max 300 characters
- Plain text (no markdown)
- Provide actionable insights or important caveats

**When to include:**
- Tool failures or missing data
- Conflicting priorities (explain resolution)
- Important assumptions made
- Special constraints (deadlines, dependencies)

**When to omit:**
- No special circumstances
- Plan is self-explanatory
- Would just repeat information from summary

**Examples:**
```json
"notes": "Unable to fetch task data. Plan based on calendar only."
```

```json
"notes": "Prioritized client report over internal review due to external deadline."
```

```json
"notes": "No meetings scheduled. Allocated longer deep work blocks."
```

---

## Complete Example

```json
{
  "plan": {
    "summary": "Today's focus is completing the Q2 financial report. Priority is finishing data analysis, followed by stakeholder review.",
    "time_blocks": [
      {
        "start": "09:00",
        "end": "11:30",
        "activity": "Complete Q2 report Section 3 data analysis",
        "priority": "high",
        "type": "deep_work"
      },
      {
        "start": "11:30",
        "end": "11:45",
        "activity": "Break and coffee",
        "priority": "low",
        "type": "break"
      },
      {
        "start": "11:45",
        "end": "12:00",
        "activity": "Review and respond to urgent emails",
        "priority": "medium",
        "type": "admin"
      },
      {
        "start": "13:00",
        "end": "14:00",
        "activity": "Attend weekly team standup meeting",
        "priority": "medium",
        "type": "meeting"
      },
      {
        "start": "14:00",
        "end": "16:00",
        "activity": "Review 3 pending pull requests and provide feedback",
        "priority": "high",
        "type": "deep_work"
      },
      {
        "start": "16:00",
        "end": "17:00",
        "activity": "Prepare presentation slides for client meeting",
        "priority": "medium",
        "type": "deep_work"
      }
    ],
    "top_priorities": [
      "Complete Q2 financial report Section 3 by end of day",
      "Review and approve 3 pending pull requests",
      "Prepare client presentation slides for Friday"
    ],
    "energy_pattern": "morning_peak",
    "notes": "Q2 report has external deadline. Allocated morning peak energy for most critical analysis work."
  }
}
```

---

## Validation Rules

### Structural Validation

1. **Valid JSON syntax**
   - No trailing commas
   - Proper quote marks
   - Balanced braces/brackets

2. **All required fields present**
   - `plan.summary`
   - `plan.time_blocks` (array with ≥1 item)
   - Each time block has: `start`, `end`, `activity`, `priority`, `type`
   - `plan.top_priorities` (array with 3-5 items)

3. **No extra fields**
   - Only fields defined in schema
   - No custom/invented fields

---

### Semantic Validation

4. **Time logic**
   - All `start` and `end` in HH:MM format
   - `end` > `start` for each block
   - No overlapping blocks
   - Blocks in chronological order

5. **Enum values**
   - `priority`: only "high", "medium", "low"
   - `type`: only "deep_work", "meeting", "break", "admin"
   - `energy_pattern`: only "morning_peak", "afternoon_peak", "evening_peak", "steady"

6. **String constraints**
   - `summary` ≤ 200 characters
   - `notes` ≤ 300 characters (if present)
   - `top_priorities` has 3-5 items

7. **Content quality**
   - Activities start with action verbs
   - No generic activities ("work on stuff")
   - Priorities map to time blocks
   - Plan is realistic for one day

---

## Error Handling

### Invalid JSON Syntax
**Error:** `SyntaxError: Unexpected token`  
**Fix:** Check for trailing commas, missing quotes, unbalanced brackets

### Missing Required Field
**Error:** `ValidationError: Missing required field 'summary'`  
**Fix:** Ensure all required fields present

### Invalid Enum Value
**Error:** `ValidationError: Invalid priority 'critical'. Must be: high, medium, low`  
**Fix:** Use exact enum values from schema

### Overlapping Time Blocks
**Error:** `ValidationError: Time blocks overlap at 14:00`  
**Fix:** Adjust end/start times to eliminate overlap

---

## Output Format Specification

**CRITICAL:** Return ONLY the JSON object. No markdown, no explanation, no wrapper.

### ✅ Correct Output Format

```json
{
  "plan": {
    "summary": "Today's focus is...",
    "time_blocks": [ ... ],
    "top_priorities": [ ... ]
  }
}
```

### ❌ Incorrect Output Formats

**With markdown wrapper:**
```
Here's your plan:
```json
{ "plan": { ... } }
```
```

**With explanation:**
```
Based on your calendar and tasks, I've created this plan:
{ "plan": { ... } }
```

**With preamble:**
```
I analyzed your schedule and here's what I recommend:
{ "plan": { ... } }
```

**All invalid.** Return ONLY pure JSON.

---

*Output Schema Document — Version 2.0.0 — 2026-06-06*
