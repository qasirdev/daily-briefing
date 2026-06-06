# Focus Agent Reasoning Guide

**Version:** 2.0.0  
**Last Updated:** 2026-06-06

---

## Purpose

This document explains **how to think through** focus planning problems systematically.

Use this reasoning approach for complex scheduling decisions, conflicting priorities, and edge cases.

---

## Core Reasoning Framework

Before generating the focus plan, think through these questions **in order**:

### 1. What are the hard constraints?

**Hard constraints = non-negotiable commitments**

- Scheduled meetings with external participants
- Deadlines (today or overdue)
- Appointments with fixed times
- Time-sensitive dependencies

**Example thinking:**
```
<thinking>
Hard constraints identified:
- 9:00-9:30am: Team standup (cannot reschedule)
- 2:00-3:00pm: Client call (external, high stakes)
- 5:00pm: Q2 report submission deadline (hard stop)
= 1.5 hours committed to meetings
= Q2 report MUST be done by 5pm
</thinking>
```

---

### 2. What tasks require deep focus vs quick execution?

**Deep focus tasks:**
- Complex problem-solving (coding, writing, analysis)
- Creative work (design, strategy, planning)
- Learning new concepts
- Estimated duration >90 minutes

**Quick execution tasks:**
- Code reviews (if familiar with codebase)
- Email responses
- Admin work (timesheets, expenses)
- Status updates
- Estimated duration <30 minutes

**Example thinking:**
```
<thinking>
Task complexity analysis:
- Q2 report Section 3: DEEP FOCUS (data analysis, 3 hours estimated)
- PR reviews (3 pending): QUICK (familiar code, 15 min each = 45 min total)
- Email catch-up: QUICK (scan and respond, 20 min)
- Presentation prep: MODERATE FOCUS (slide creation, 90 min)

Deep focus tasks need uninterrupted time → morning blocks
Quick tasks can fit between meetings → afternoon slots
</thinking>
```

---

### 3. Where are natural energy peaks/troughs?

**Typical energy patterns (if no user preference):**

| Time | Energy Level | Best For |
|---|---|---|
| 8am-10am | Rising | Warm-up tasks, planning |
| 10am-12pm | Peak | Deep work, complex problems |
| 12pm-1pm | Low | Lunch break |
| 1pm-2pm | Lowest | Light admin, recovery |
| 2pm-4pm | Moderate | Meetings, collaboration |
| 4pm-6pm | Variable | Wrap-up, prepare for tomorrow |

**Example thinking:**
```
<thinking>
Energy pattern analysis (user preference: morning_peak):
- 9:30am-12:00pm: Peak energy window (post-standup)
  → Ideal for Q2 report deep work (hardest task)
- 1:00pm-2:00pm: Post-lunch dip
  → Schedule admin work (email, quick reviews)
- 2:00pm-3:00pm: Client call (externally scheduled)
  → No choice, use moderate energy
- 3:00pm-5:00pm: Declining energy
  → Finish remaining priorities, wrap up
</thinking>
```

---

### 4. How can I create contiguous focus blocks?

**Goal:** Minimize context-switching by grouping similar work

**Strategies:**
- Batch meetings together (if possible)
- Protect 90-120 minute deep work blocks
- Group admin tasks into single session
- Leave buffer time between different work types

**Example thinking:**
```
<thinking>
Focus block optimization:
- 9:30am-12:00pm: 2.5 hour uninterrupted block after standup
  → Perfect for Q2 report deep work
- 12:00pm-1:00pm: Natural break (lunch)
- 2:00pm-3:00pm: Client call (can't move)
- 3:00pm-5:00pm: 2 hour block after call
  → Split: 1 hour PR reviews + 1 hour presentation prep

Avoided: Switching between deep work and admin every 30 min
Result: 2 major focus blocks, minimal context-switching
</thinking>
```

---

### 5. What's the minimum viable progress for today?

**MVD = Minimum Viable Day**

Ask: "If I could only complete ONE thing today, what would move the needle most?"

**Prioritization heuristics:**
1. **External deadline** > Internal deadline
2. **Blocks others' work** > Independent work
3. **High impact + reasonable effort** > Low impact or excessive effort
4. **Strategic** > Operational (if no deadlines)

**Example thinking:**
```
<thinking>
Minimum viable day analysis:
- Q2 report due today (external deadline, blocks finance team)
  → MUST complete, highest priority
- PR reviews blocking 3 developers
  → High priority, but not as critical as report
- Presentation prep (meeting is Friday)
  → Can defer to tomorrow if needed

MVD = Complete Q2 report. Everything else is secondary.
If time runs out, reschedule other tasks without guilt.
</thinking>
```

---

## Decision Trees for Common Scenarios

### Scenario 1: Conflicting Deadlines

**Problem:** Multiple high-priority tasks due same day

**Reasoning process:**
```
<thinking>
Conflicting deadlines:
- Task A: Client deliverable due 5pm (external)
- Task B: Internal report due 5pm (manager request)

Decision criteria:
1. Stakeholder impact: Client > Internal
2. Consequences of missing: Client = relationship damage, Internal = can explain
3. Estimated effort: A = 3 hours, B = 2 hours
4. Current time: 10am (7 hours available)

Decision: Prioritize Task A (client deliverable)
- 10am-1pm: Task A (3 hours)
- 1pm-2pm: Lunch/break
- 2pm-4pm: Task B (2 hours, aim to complete)
- 4pm-5pm: Final QA on Task A before submission

Rationale: External commitments take priority. Internal report can be explained/delayed if needed.
</thinking>
```

---

### Scenario 2: No Clear Priorities

**Problem:** Many tasks, none with urgent deadlines

**Reasoning process:**
```
<thinking>
No urgent deadlines situation:
- 5 tasks in backlog, all due "this week"
- No external dependencies
- No clear priority from user

Decision criteria (Eisenhower Matrix):
1. High impact + High urgency = Do first
2. High impact + Low urgency = Schedule strategically
3. Low impact + High urgency = Delegate or quick-batch
4. Low impact + Low urgency = Defer

Analysis:
- Task 1: Refactor auth module (high impact, no urgency) → Strategic work
- Task 2: Update dependencies (medium impact, low urgency) → Background
- Task 3: Write documentation (low impact, medium urgency) → Defer
- Task 4: Fix minor UI bug (low impact, high urgency) → Quick-batch
- Task 5: Code review (high impact, medium urgency) → Do today

Decision: Focus on high-impact work
- Morning: Task 1 (refactoring) — strategic, needs focus
- Afternoon: Task 5 (code review) — collaborative, less demanding
- Fill gaps: Task 4 (quick bug fix, 30 min max)

Rationale: Use non-urgent time for high-impact strategic work that often gets deferred.
</thinking>
```

---

### Scenario 3: Back-to-Back Meetings

**Problem:** Calendar packed with meetings, little focus time

**Reasoning process:**
```
<thinking>
Meeting-heavy day:
- 9:00-10:00am: Meeting A
- 10:00-11:00am: Meeting B
- 11:00-12:00pm: Meeting C
- 2:00-3:00pm: Meeting D
- 3:30-4:30pm: Meeting E
= 5 hours of meetings, fragmented schedule

Available focus time:
- 8:00-9:00am: 1 hour before first meeting
- 12:00-2:00pm: 2 hours (lunch + gap)
- 4:30-6:00pm: 1.5 hours (end of day)

Strategy:
- 8:00-9:00am: Prepare for meetings (review agendas, gather materials)
  → Type: admin, ensures productive meetings
- 12:00-1:00pm: Lunch break (recovery)
- 1:00-2:00pm: Quick high-priority task (PR review)
  → Type: deep_work (short), use remaining energy
- 4:30-6:00pm: Wrap up action items from meetings
  → Type: admin, follow-up work

Reality check: This is NOT a deep work day. Adjust expectations.
Focus: Make meetings productive, capture action items, minimal strategic work.
Note: Consider declining/rescheduling optional meetings to create focus time.
</thinking>
```

---

### Scenario 4: Task with Unclear Duration

**Problem:** Task has no time estimate, uncertain complexity

**Reasoning process:**
```
<thinking>
Uncertain task: "Investigate performance issue"
- No time estimate provided
- Could be 1 hour (simple config) or 8 hours (deep architecture issue)
- Due: "ASAP" (vague urgency)

Strategy for uncertainty:
1. Time-box exploration: 1 hour initial investigation
2. Decision point: After 1 hour, assess complexity
3. Options after assessment:
   a) Simple fix: Complete immediately (30 min)
   b) Complex issue: Document findings, schedule deep work session
   c) Blocked: Escalate to senior engineer

Plan:
- 10:00-11:00am: Time-boxed investigation (1 hour)
- 11:00-11:30am: Decision point
  - If simple: Complete fix
  - If complex: Document and defer to tomorrow's deep work block

Rationale: Time-boxing prevents rabbit holes. Make informed decision after exploration.
</thinking>
```

---

### Scenario 5: Interrupted Focus Time

**Problem:** Meeting scheduled during typical deep work hours

**Reasoning process:**
```
<thinking>
Interrupted schedule:
- 10:00-11:00am: Natural deep work block
- 11:00-12:00pm: Unexpected meeting added to calendar
- 12:00-1:00pm: Lunch
- Result: No 2+ hour focus blocks available

Adaptation strategy:
Option A: Reschedule meeting (if possible)
  → Best outcome, but may not be feasible

Option B: Adjust task selection
  → Choose tasks that fit 60-min slots instead of 2+ hour tasks
  → Example: 3 separate 1-hour tasks instead of 1 deep work task

Option C: Split deep work task
  → Morning: Part 1 (research & planning, 1 hour)
  → Afternoon: Part 2 (implementation, 2 hours)
  → Requires task to be naturally divisible

Decision: Use Option B
- 10:00-11:00am: Task A (PR review, fits in 1 hour)
- 11:00-12:00pm: Meeting (no choice)
- 2:00-4:00pm: Task B (deep work, 2 hours)

Rationale: Accept reality of interruption. Choose tasks that match available time blocks.
</thinking>
```

---

## Reasoning Heuristics

### Time Estimation

**Rule of thumb:** Add 25% buffer to all estimates

```
<thinking>
Task: "Update API documentation"
Initial estimate: 2 hours
Realistic estimate: 2 hours × 1.25 = 2.5 hours

Why? Accounts for:
- Unexpected complexity
- Interruptions (Slack, email)
- Context switching costs
- Review/QA time
</thinking>
```

---

### Priority Scoring

**Formula:** `Priority = (Impact × Urgency) / Effort`

```
<thinking>
Task prioritization:
- Task A: Impact=9, Urgency=8, Effort=3 → Score = (9×8)/3 = 24
- Task B: Impact=7, Urgency=9, Effort=6 → Score = (7×9)/6 = 10.5
- Task C: Impact=8, Urgency=6, Effort=2 → Score = (8×6)/2 = 24

Ranking: Task A = Task C > Task B
Tiebreaker: Higher urgency wins → Task A first
</thinking>
```

---

### Energy Allocation

**Match task complexity to energy level:**

- **Peak energy** (90-100%) → Hardest, most important tasks
- **Good energy** (70-90%) → Moderate complexity, collaborative work
- **Low energy** (50-70%) → Admin, routine tasks, meetings
- **Recovery** (<50%) → Breaks, light reading, planning

```
<thinking>
Energy-task matching:
- 10am: Peak (95%) → Q2 report data analysis (hardest task)
- 1pm: Low (60%) → Email responses (routine)
- 3pm: Good (75%) → Client call (collaborative)
- 5pm: Recovery (50%) → Tomorrow's planning (light)
</thinking>
```

---

## When to Override Defaults

### Override Priority if:

1. **Strategic importance** > Tactical urgency
   - Example: No deadline, but critical for Q3 OKRs
   
2. **Dependency chains** affect others
   - Example: Blocking 3 team members > personal deadline

3. **Risk of escalation**
   - Example: Minor issue now, major crisis if ignored

```
<thinking>
Override example:
- Task: "Update team documentation" (no deadline, low priority)
- Context: New team member starts Monday, needs docs
- Impact: Without docs, onboarding delayed 1 week
- Decision: Elevate to HIGH priority today

Rationale: Prevents future pain, enables team member success.
</thinking>
```

---

## Common Reasoning Mistakes

### ❌ Mistake 1: Underestimating Context-Switching Costs

**Wrong thinking:**
```
- 9:00-9:30am: Task A
- 9:30-10:00am: Task B
- 10:00-10:30am: Task C
= "I can do 3 tasks in 90 minutes"
```

**Correct thinking:**
```
- Switching cost: ~10-15 min per switch
- Real time: 30 min - 10 min switching = 20 min actual work
- 3 tasks × 20 min = 60 min productive time (not 90 min)
- Better: Focus on 1-2 tasks, batch similar work
```

---

### ❌ Mistake 2: Ignoring Energy Patterns

**Wrong thinking:**
```
- 2:00-5:00pm: Deep work on complex algorithm problem
= "I have 3 hours, that's enough time"
```

**Correct thinking:**
```
- 2pm = post-lunch energy dip
- Complex problem needs peak energy
- Better: Schedule for morning (10am-1pm)
- Afternoon: Meetings or admin work
```

---

### ❌ Mistake 3: Over-Optimistic Scheduling

**Wrong thinking:**
```
- 9:00am-5:00pm: Deep work (8 hours)
= "I'll be super productive all day"
```

**Correct thinking:**
```
- Realistic focused work: 4-6 hours per day
- Need: Breaks, lunch, context switches, interruptions
- Better: Plan 5-6 hours productive work, expect interruptions
```

---

## Templates for `<thinking>` Tags

### Template 1: Standard Day
```
<thinking>
## Input Analysis
- Calendar: [X meetings, Y hours committed]
- Tasks: [Z tasks, priorities: A high, B medium, C low]
- Available time: [N hours for focus work]

## Constraints
- Hard deadlines: [list]
- Meetings: [list with times]
- Energy pattern: [morning/afternoon/evening peak]

## Priority Ranking
1. [Task A]: [reason] → [time allocation]
2. [Task B]: [reason] → [time allocation]
3. [Task C]: [reason] → [time allocation]

## Time Allocation Strategy
- [Time block 1]: [activity] (rationale: [why])
- [Time block 2]: [activity] (rationale: [why])
- [Time block 3]: [activity] (rationale: [why])

## Reality Check
- Total planned work: [X hours]
- Available time: [Y hours]
- Buffer: [Z%]
- Realistic? [Yes/No, adjust if needed]
</thinking>
```

---

### Template 2: Conflict Resolution
```
<thinking>
## Conflict Identified
- Option A: [task/time] — [pros] — [cons]
- Option B: [task/time] — [pros] — [cons]

## Decision Criteria
1. [Criterion 1]: A scores [X], B scores [Y]
2. [Criterion 2]: A scores [X], B scores [Y]

## Decision
Choose [Option A/B] because [rationale]

## Mitigation
- Deferred item: [what was postponed]
- Plan for deferment: [when/how to address later]
</thinking>
```

---

*Reasoning Guide — Version 2.0.0 — 2026-06-06*
