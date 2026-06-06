# Focus Agent Quality Checklist

**Version:** 2.0.0  
**Last Updated:** 2026-06-06

---

## Purpose

Before returning your focus plan output, verify **ALL** criteria in this checklist.

**Rule:** If ANY check fails, revise the plan. Do NOT return invalid or low-quality output.

---

## JSON Validation

### ✅ Syntax Validation

- [ ] Valid JSON syntax (parseable by standard JSON parser)
- [ ] No trailing commas (last item in array/object)
- [ ] Proper quote marks (double quotes for strings, not single)
- [ ] Balanced braces `{}` and brackets `[]`
- [ ] All strings properly escaped (e.g., `\"` for quotes inside strings)
- [ ] No comments (JSON doesn't support `//` or `/* */`)

**Test:** Copy output and run through `JSON.parse()` or `jq` — must not error

**Common errors:**
```json
// ❌ Trailing comma
{
  "plan": {
    "summary": "...",
    "time_blocks": [...],  // <- Remove this comma
  }
}

// ❌ Single quotes
{
  'plan': {  // <- Use "plan"
    'summary': '...'  // <- Use "summary" and "..."
  }
}

// ❌ Unescaped quote
{
  "summary": "Today's focus is..."  // <- Should be "Today\'s focus is..."
}
```

---

### ✅ Schema Compliance

- [ ] Root object is `{"plan": {...}}`
- [ ] All required fields present:
  - `plan.summary` (string)
  - `plan.time_blocks` (array)
  - `plan.top_priorities` (array)
- [ ] Each time block has required fields:
  - `start` (string)
  - `end` (string)
  - `activity` (string)
  - `priority` (enum)
  - `type` (enum)
- [ ] No extra fields beyond schema
- [ ] Optional fields only used when appropriate:
  - `plan.energy_pattern` (enum, optional)
  - `plan.notes` (string, optional)

**Test:** Compare output structure to schema in `output-schema.md`

---

### ✅ Enum Validation

- [ ] `priority` only uses: `"high"`, `"medium"`, `"low"` (exact match, lowercase)
- [ ] `type` only uses: `"deep_work"`, `"meeting"`, `"break"`, `"admin"` (exact match, lowercase with underscore)
- [ ] `energy_pattern` (if present) only uses: `"morning_peak"`, `"afternoon_peak"`, `"evening_peak"`, `"steady"` (exact match)

**Common errors:**
```json
// ❌ Invalid enum values
"priority": "critical"  // Use "high"
"priority": "High"      // Use "high" (lowercase)
"type": "focus"         // Use "deep_work"
"type": "call"          // Use "meeting"
"energy_pattern": "morning"  // Use "morning_peak"
```

---

### ✅ Array Constraints

- [ ] `time_blocks` has between 1-8 items (min=1, max=8)
- [ ] `top_priorities` has between 3-5 items (min=3, max=5)
- [ ] All array items are non-empty
- [ ] All array items are strings (for `top_priorities`)
- [ ] All array items are objects with required fields (for `time_blocks`)

---

## Logical Consistency

### ✅ Time Format Validation

- [ ] All `start` and `end` times in `HH:MM` format (24-hour)
- [ ] Leading zeros present (e.g., `"09:00"` not `"9:00"`)
- [ ] Valid hours: 00-23
- [ ] Valid minutes: 00-59
- [ ] No 12-hour format (no "9am" or "2pm")
- [ ] No timezone indicators

**Examples:**
```json
// ✅ Valid
"start": "09:00"
"end": "17:30"

// ❌ Invalid
"start": "9:00"      // Missing leading zero
"start": "9am"       // 12-hour format
"start": "09:00:00"  // Includes seconds
"start": "09:00 EST" // Includes timezone
```

---

### ✅ Time Logic Validation

- [ ] All `end` > `start` for every time block (duration > 0)
- [ ] No time blocks extend past midnight (start/end on same day)
- [ ] All start times ≥ current time (if planning for today)
- [ ] Time blocks are chronological (sorted by start time)
- [ ] Time blocks fit within reasonable work hours (e.g., 07:00-22:00)

**Test cases:**
```json
// ❌ Invalid: end before start
{"start": "14:00", "end": "13:00"}

// ❌ Invalid: same time (zero duration)
{"start": "10:00", "end": "10:00"}

// ❌ Invalid: crosses midnight
{"start": "22:00", "end": "02:00"}

// ✅ Valid
{"start": "09:00", "end": "11:00"}
```

---

### ✅ Overlap Detection

- [ ] No overlapping time blocks (each minute assigned to ≤1 block)
- [ ] Gap between blocks allowed (not required to be continuous)
- [ ] Blocks in chronological order

**Test algorithm:**
```
For each block B1:
  For each subsequent block B2:
    Assert: B2.start >= B1.end
```

**Example:**
```json
// ❌ Invalid: overlap at 11:00
[
  {"start": "09:00", "end": "11:30"},
  {"start": "11:00", "end": "12:00"}  // Overlaps with previous
]

// ✅ Valid: no overlap
[
  {"start": "09:00", "end": "11:00"},
  {"start": "11:00", "end": "12:00"}  // Starts exactly when previous ends
]

// ✅ Valid: gap allowed
[
  {"start": "09:00", "end": "11:00"},
  {"start": "11:15", "end": "12:00"}  // 15 min gap is fine
]
```

---

### ✅ Calendar Consistency

- [ ] No focus time blocks scheduled during calendar meetings
- [ ] Meeting blocks match calendar events (start/end times)
- [ ] All calendar commitments accounted for
- [ ] If tool call failed, noted in `notes` field

**Test:** Cross-reference time blocks with `get_calendar_events` results

---

## Content Quality

### ✅ Summary Quality

- [ ] Summary is 1-2 complete sentences
- [ ] Summary length ≤ 200 characters
- [ ] No bullet points or lists (prose format)
- [ ] No markdown formatting (no `**bold**`, `_italic_`, etc.)
- [ ] No emoji or special characters (unless user-provided)
- [ ] Present tense used
- [ ] Mentions main theme or top priority
- [ ] Readable in <10 seconds

**Good examples:**
```json
"summary": "Today's focus is completing the Q2 financial report. Priority is finishing data analysis, followed by stakeholder review."

"summary": "Deep work day with protected focus blocks. Priority is shipping the authentication feature."
```

**Bad examples:**
```json
"summary": "Today you should: \n- Finish report\n- Review PRs"  // Bullets, wrong format

"summary": "Work on various tasks and attend some meetings"  // Too vague

"summary": "🚀 Super productive day ahead! Let's crush these goals! 💪"  // Emoji, unprofessional
```

---

### ✅ Activity Quality

- [ ] All activities start with action verb
- [ ] Activities are specific (not generic)
- [ ] Activities reference actual tasks/events from tools
- [ ] No vague descriptions ("work on stuff")
- [ ] Max ~100 characters per activity (concise)
- [ ] No invented tasks (only from tool results)

**Action verb examples:** Complete, Review, Attend, Prepare, Analyze, Write, Fix, Test, Deploy, Meet, Discuss, Plan

**Quality comparison:**
```json
// ❌ Bad activities
"activity": "Work on project"              // No verb, too vague
"activity": "Coding"                       // No object, what code?
"activity": "Meeting"                      // No context, which meeting?
"activity": "Do some tasks"                // Meaningless

// ✅ Good activities
"activity": "Complete Q2 report Section 3 data analysis"
"activity": "Review and approve 3 pending pull requests"
"activity": "Attend weekly team standup meeting"
"activity": "Prepare slides for client presentation"
```

---

### ✅ Priority Quality

- [ ] Priorities reflect both urgency AND importance
- [ ] External deadlines prioritized over internal
- [ ] Blocking work prioritized appropriately
- [ ] At least ONE high-priority item per day
- [ ] High-priority items scheduled during peak energy
- [ ] Priority distribution reasonable (not all "high")

**Priority guidelines:**
- **high:** <40% of time blocks
- **medium:** 40-60% of time blocks
- **low:** <20% of time blocks (breaks, optional tasks)

---

### ✅ Top Priorities Quality

- [ ] 3-5 items (not 2, not 6)
- [ ] All items are actionable
- [ ] All items start with action verbs
- [ ] Items are specific (not "work on X")
- [ ] Items map to time blocks
- [ ] Items are achievable in one day
- [ ] Ordered by importance (most critical first)

**Mapping test:** Each top priority should correspond to a time block

**Example verification:**
```json
"top_priorities": [
  "Complete Q2 financial report by 5pm",  // ✓ Maps to 09:00-12:00 block
  "Review 3 pending pull requests",       // ✓ Maps to 14:00-15:00 block
  "Prepare client presentation slides"    // ✓ Maps to 16:00-17:00 block
]
```

---

### ✅ Notes Quality (if present)

- [ ] Notes ≤ 300 characters
- [ ] Provides useful context or explanation
- [ ] Mentions tool failures (if any)
- [ ] Explains non-obvious decisions
- [ ] No redundant information (already in summary)

**When to include notes:**
- Tool call failed: "Unable to fetch calendar data"
- Conflict resolved: "Prioritized X over Y due to external deadline"
- Missing data: "No tasks found, plan based on calendar only"
- Important assumption: "Assumed 2-hour duration for task A"

**When to omit notes:**
- Everything is straightforward
- No special circumstances
- Would just repeat summary

---

## Evidence-Based Validation

### ✅ Calendar Alignment

- [ ] All calendar events accounted for
- [ ] Meeting times match calendar exactly
- [ ] No invented meetings
- [ ] Calendar gaps correctly identified as focus time

**Test:** Compare time blocks of type `"meeting"` with `get_calendar_events` results

---

### ✅ Task Alignment

- [ ] All high-priority tasks from tools included
- [ ] Tasks with today's deadline addressed
- [ ] No invented tasks (only from `get_tasks`)
- [ ] Task effort estimates considered

**Test:** Cross-reference activities with `get_tasks` results

---

### ✅ Assumption Transparency

- [ ] Any assumptions clearly noted
- [ ] Missing data acknowledged (in `notes`)
- [ ] User preferences applied (if available)
- [ ] Defaults used when no data available

---

## Realism Check

### ✅ Time Allocation Realism

- [ ] Total planned work ≤ 6-7 hours (not 8-10 hours)
- [ ] Includes breaks and buffer time
- [ ] Deep work blocks ≤ 3 hours each
- [ ] Admin tasks ≤ 1 hour total
- [ ] Meetings duration = calendar events
- [ ] 80% rule followed (don't over-schedule)

**Formula:** 
```
Realistic workday = (Work hours × 0.8) - Meeting hours
Example: (8 hours × 0.8) - 2 hours meetings = 4.4 hours focus time
```

---

### ✅ Task Effort Realism

- [ ] Task durations include 25% buffer
- [ ] Complex tasks allocated sufficient time
- [ ] No 30-minute slots for 2-hour tasks
- [ ] Context-switching costs considered

**Buffer formula:**
```
Allocated time = Estimated time × 1.25
Example: Task estimated 2 hours → Allocate 2.5 hours
```

---

### ✅ Energy Alignment

- [ ] Hardest tasks during peak energy
- [ ] Light tasks during low energy
- [ ] Breaks after 90-120 min focus
- [ ] No deep work during typical slump times (1-2pm)

---

## Output Format Validation

### ✅ Pure JSON Output

- [ ] NO markdown code blocks (no ``` backticks)
- [ ] NO preamble or explanation text
- [ ] NO comments outside JSON
- [ ] ONLY the JSON object
- [ ] Starts with `{` and ends with `}`

**Correct format:**
```json
{
  "plan": {
    ...
  }
}
```

**Incorrect formats:**
```
Here's your plan:
```json
{ "plan": { ... } }
```  ← Has markdown wrapper, WRONG

Based on analysis:
{ "plan": { ... } }  ← Has preamble, WRONG
```

---

## Final Self-Check Questions

Before submitting, answer these questions:

1. **Would I be confident executing this plan if I were the user?**
   - [ ] Yes (clear, actionable, realistic)
   - [ ] No (revise unclear or unrealistic parts)

2. **Can the user understand this plan in <30 seconds?**
   - [ ] Yes (concise, scannable)
   - [ ] No (simplify summary or reduce complexity)

3. **Is every time block based on actual data (not assumptions)?**
   - [ ] Yes (evidence-based)
   - [ ] No (document assumptions in `notes`)

4. **Would this plan survive unexpected interruptions?**
   - [ ] Yes (includes buffers, realistic)
   - [ ] No (too optimistic, add slack)

5. **Does the JSON output parse without errors?**
   - [ ] Yes (tested with parser)
   - [ ] No (fix syntax errors)

---

## Revision Protocol

**If ANY check fails:**

1. **Identify the issue**
   - Which checklist item failed?
   - What is the specific problem?

2. **Fix the issue**
   - Correct the JSON, logic, or content
   - Re-run affected checklist items

3. **Re-validate**
   - Check that fix didn't break other items
   - Ensure no new issues introduced

4. **Repeat until all checks pass**

**DO NOT:**
- ❌ Skip checks to save time
- ❌ Return output with known issues
- ❌ Assume "good enough" quality
- ❌ Leave validation to downstream systems

---

## Quick Reference: Common Failures

| Issue | Check Failed | Fix |
|---|---|---|
| Invalid JSON syntax | JSON Validation > Syntax | Use JSON validator, fix commas/quotes |
| Wrong enum value | JSON Validation > Enum | Use exact values: `"high"`, `"deep_work"`, etc. |
| Overlapping blocks | Logical Consistency > Overlap | Adjust end/start times to eliminate overlap |
| Generic activity | Content Quality > Activity | Add action verb + specific object |
| Too many priorities | Content Quality > Top Priorities | Limit to 3-5 items |
| Vague summary | Content Quality > Summary | Make specific, mention key theme |
| Over-scheduled day | Realism Check > Time Allocation | Apply 80% rule, add buffers |
| Markdown wrapper | Output Format > Pure JSON | Remove backticks, return ONLY JSON |

---

## Automated Validation (Optional)

If implementing automated checks, use this checklist as specification:

```python
def validate_focus_plan(output):
    """Validate focus plan against quality checklist."""
    
    # JSON Validation
    assert is_valid_json(output)
    assert has_required_fields(output)
    assert all_enums_valid(output)
    assert array_sizes_correct(output)
    
    # Logical Consistency
    assert all_times_valid_format(output)
    assert all_end_after_start(output)
    assert no_overlapping_blocks(output)
    assert chronological_order(output)
    
    # Content Quality
    assert summary_length_ok(output)
    assert activities_have_verbs(output)
    assert priorities_reasonable(output)
    
    # Evidence-Based
    assert calendar_alignment(output, calendar_data)
    assert task_alignment(output, task_data)
    
    # Realism
    assert total_hours_realistic(output)
    assert energy_alignment(output)
    
    # Output Format
    assert is_pure_json(output)
    
    return True
```

---

*Quality Checklist — Version 2.0.0 — 2026-06-06*
