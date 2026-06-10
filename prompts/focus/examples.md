# Focus Agent Examples

**Purpose:** These examples demonstrate correct input processing, reasoning, and output generation for the Focus Agent. Use these as few-shot prompting examples to improve consistency and accuracy.

---

## Example 1: Standard Workday with Mixed Priorities

### Input Context
```xml
<calendar_events>
  <event>
    <title>Team Standup</title>
    <start>2026-06-06T09:00:00</start>
    <end>2026-06-06T09:30:00</end>
    <attendees>5 people</attendees>
  </event>
  <event>
    <title>Client Presentation</title>
    <start>2026-06-06T14:00:00</start>
    <end>2026-06-06T15:00:00</end>
    <attendees>Client: Acme Corp</attendees>
  </event>
</calendar_events>

<tasks>
  <task>
    <title>Finish Q2 Financial Report</title>
    <deadline>2026-06-06T17:00:00</deadline>
    <priority>high</priority>
    <estimated_duration>3 hours</estimated_duration>
  </task>
  <task>
    <title>Review PR #456: Authentication Fix</title>
    <priority>medium</priority>
    <estimated_duration>45 minutes</estimated_duration>
  </task>
  <task>
    <title>Respond to customer support tickets</title>
    <priority>medium</priority>
    <estimated_duration>1 hour</estimated_duration>
  </task>
</tasks>
```

### Reasoning
```
<thinking>
Calendar analysis:
- 9:00-9:30am: Team standup (30 min committed)
- 14:00-15:00pm: Client presentation (1 hour committed)
- Total committed: 1.5 hours
- Available blocks: 9:30am-2pm (4.5h), 3pm-5pm (2h) = 6.5h available

Task prioritization:
1. Q2 Financial Report: HIGH (due today 5pm, 3h needed)
2. Client Presentation prep: CRITICAL (happening today, need buffer)
3. PR review: MEDIUM (45 min, can fit in afternoon)
4. Support tickets: MEDIUM (1h, ongoing work)

Optimal schedule:
- 9:30am-1pm: Deep work on Q2 report (3.5h block for 3h task, includes buffer)
- 1pm-2pm: Prepare for client presentation (1h buffer)
- 3pm-3:45pm: Review PR #456 (after presentation, energy still good)
- 3:45pm-5pm: Support tickets and final report polish

Energy considerations:
- Morning peak (9:30-1pm) = best for complex report work
- Post-presentation (3pm+) = lower energy, suitable for shorter tasks
</thinking>
```

### Output
```json
{
  "plan": {
    "summary": "Focus on completing Q2 report before client presentation, with afternoon time for PR review and support follow-up.",
    "time_blocks": [
      {
        "start": "09:30",
        "end": "13:00",
        "activity": "Complete Q2 Financial Report (final draft)",
        "priority": "high",
        "type": "deep_work"
      },
      {
        "start": "13:00",
        "end": "14:00",
        "activity": "Prepare slides and talking points for Acme Corp presentation",
        "priority": "high",
        "type": "admin"
      },
      {
        "start": "15:00",
        "end": "15:45",
        "activity": "Review PR #456: Authentication fix and provide feedback",
        "priority": "medium",
        "type": "deep_work"
      },
      {
        "start": "15:45",
        "end": "17:00",
        "activity": "Respond to support tickets and finalize Q2 report",
        "priority": "medium",
        "type": "admin"
      }
    ],
    "top_priorities": [
      "Complete Q2 Financial Report by 5pm deadline",
      "Deliver successful client presentation to Acme Corp",
      "Review and approve PR #456"
    ],
    "energy_pattern": "morning_peak",
    "notes": "Q2 report is today's critical deadline. Allocated full morning focus block to ensure completion before presentation."
  }
}
```

---

## Example 2: Meeting-Heavy Day (Limited Focus Time)

### Input Context
```xml
<calendar_events>
  <event>
    <title>Project Kickoff</title>
    <start>2026-06-07T09:00:00</start>
    <end>2026-06-07T10:30:00</end>
  </event>
  <event>
    <title>Architecture Review</title>
    <start>2026-06-07T11:00:00</start>
    <end>2026-06-07T12:00:00</end>
  </event>
  <event>
    <title>Lunch with CEO</title>
    <start>2026-06-07T12:30:00</start>
    <end>2026-06-07T13:30:00</end>
  </event>
  <event>
    <title>Sprint Planning</title>
    <start>2026-06-07T14:00:00</start>
    <end>2026-06-07T15:30:00</end>
  </event>
  <event>
    <title>1:1 with Sarah</title>
    <start>2026-06-07T16:00:00</start>
    <end>2026-06-07T16:30:00</end>
  </event>
</calendar_events>

<tasks>
  <task>
    <title>Approve expense reports</title>
    <priority>high</priority>
    <estimated_duration>20 minutes</estimated_duration>
  </task>
  <task>
    <title>Update project roadmap</title>
    <priority>medium</priority>
    <estimated_duration>1 hour</estimated_duration>
  </task>
</tasks>
```

### Reasoning
```
<thinking>
Calendar analysis:
- 9am-10:30am: Meeting (1.5h)
- 11am-12pm: Meeting (1h)
- 12:30pm-1:30pm: Lunch (1h)
- 2pm-3:30pm: Meeting (1.5h)
- 4pm-4:30pm: Meeting (30min)
- Total committed: 5.5 hours out of 8-hour day
- Available: 10:30-11am (30min), 3:30-4pm (30min), 4:30-5pm (30min) = 1.5h total

Task prioritization:
- Expense reports: HIGH priority, 20 min (fits in 30-min slot)
- Roadmap update: MEDIUM priority, 1h (no single slot available today)

Strategy:
- Heavy meeting day = limited deep work capacity
- Fit quick high-priority task in morning gap
- Defer 1-hour roadmap work to tomorrow (no suitable block today)
- Use small gaps for meeting prep and follow-up
</thinking>
```

### Output
```json
{
  "plan": {
    "summary": "Meeting-heavy day with limited focus time. Prioritize quick administrative tasks and defer deep work to tomorrow.",
    "time_blocks": [
      {
        "start": "10:30",
        "end": "11:00",
        "activity": "Approve pending expense reports",
        "priority": "high",
        "type": "admin"
      },
      {
        "start": "15:30",
        "end": "16:00",
        "activity": "Review sprint planning notes and follow up on action items",
        "priority": "medium",
        "type": "admin"
      },
      {
        "start": "16:30",
        "end": "17:00",
        "activity": "Prepare for tomorrow's deep work: outline roadmap updates",
        "priority": "medium",
        "type": "admin"
      }
    ],
    "top_priorities": [
      "Approve expense reports before end of day",
      "Capture action items from 5 meetings",
      "Prepare roadmap outline for tomorrow's focused work"
    ],
    "notes": "Heavy meeting load today (5 meetings, 5.5 hours). Roadmap update deferred to tomorrow when longer focus block available."
  }
}
```

---

## Example 3: Empty Calendar, Task-Focused Day

### Input Context
```xml
<calendar_events>
  <!-- No events -->
</calendar_events>

<tasks>
  <task>
    <title>Refactor user authentication module</title>
    <priority>high</priority>
    <estimated_duration>4 hours</estimated_duration>
  </task>
  <task>
    <title>Write unit tests for payment service</title>
    <priority>high</priority>
    <estimated_duration>2 hours</estimated_duration>
  </task>
  <task>
    <title>Update API documentation</title>
    <priority>medium</priority>
    <estimated_duration>1 hour</estimated_duration>
  </task>
  <task>
    <title>Review security audit findings</title>
    <priority>medium</priority>
    <estimated_duration>1 hour</estimated_duration>
  </task>
</tasks>
```

### Reasoning
```
<thinking>
Calendar analysis:
- No meetings scheduled = full day available for deep work
- 8-hour workday = ~6.5h productive time (accounting for breaks)

Task prioritization:
1. Auth refactor: HIGH (4h) - complex, requires deep focus
2. Unit tests: HIGH (2h) - related to auth work, best done together
3. API docs: MEDIUM (1h) - can be done in afternoon
4. Security audit: MEDIUM (1h) - important but not urgent

Optimal schedule:
- Morning: Auth refactor (4h) - most complex work when energy highest
- Afternoon: Unit tests (2h) - related work, easier than refactoring
- Late afternoon: Documentation and security review (lighter tasks)

Energy strategy:
- Front-load complex work (morning peak)
- Related tasks together (auth + tests)
- Lighter tasks for energy trough (afternoon)
- Include breaks to maintain focus
</thinking>
```

### Output
```json
{
  "plan": {
    "summary": "Deep work day with no meetings. Focus on authentication refactor in morning, followed by testing and documentation.",
    "time_blocks": [
      {
        "start": "09:00",
        "end": "13:00",
        "activity": "Refactor user authentication module (complete core logic)",
        "priority": "high",
        "type": "deep_work"
      },
      {
        "start": "13:00",
        "end": "14:00",
        "activity": "Lunch break",
        "priority": "low",
        "type": "break"
      },
      {
        "start": "14:00",
        "end": "16:00",
        "activity": "Write comprehensive unit tests for payment service",
        "priority": "high",
        "type": "deep_work"
      },
      {
        "start": "16:00",
        "end": "17:00",
        "activity": "Update API documentation and review security audit findings",
        "priority": "medium",
        "type": "admin"
      }
    ],
    "top_priorities": [
      "Complete authentication module refactoring",
      "Write unit tests for payment service",
      "Update API documentation",
      "Review security audit findings"
    ],
    "energy_pattern": "morning_peak",
    "notes": "No meetings scheduled. Ideal day for deep technical work. Auth refactor is largest task, allocated full morning block."
  }
}
```

---

## Example 4: Urgent Deadline with Interruptions

### Input Context
```xml
<calendar_events>
  <event>
    <title>Daily Standup</title>
    <start>2026-06-08T09:15:00</start>
    <end>2026-06-08T09:30:00</end>
  </event>
  <event>
    <title>Emergency: Production Issue Discussion</title>
    <start>2026-06-08T11:00:00</start>
    <end>2026-06-08T11:30:00</end>
  </event>
</calendar_events>

<tasks>
  <task>
    <title>Launch blog post for product announcement</title>
    <deadline>2026-06-08T12:00:00</deadline>
    <priority>critical</priority>
    <estimated_duration>2 hours</estimated_duration>
  </task>
  <task>
    <title>Fix critical bug in checkout flow</title>
    <priority>high</priority>
    <estimated_duration>3 hours</estimated_duration>
  </task>
</tasks>
```

### Reasoning
```
<thinking>
URGENT SITUATION ANALYSIS:
- Blog post due at NOON (3 hours from 9am)
- Emergency meeting at 11am (will interrupt workflow)
- Only 1.5h available before meeting (9:30-11am)
- 30min available after meeting (11:30am-12pm) before deadline

Critical path:
- Blog post MUST be prioritized (external deadline, public-facing)
- 2h work needed, but only 2h total available in fragments
- Need to work efficiently in interrupted blocks
- Bug fix is HIGH but can wait until after blog launch

Schedule strategy:
- 9:30-11am: First chunk of blog work (1.5h)
- 11am-11:30am: Emergency meeting (unavoidable)
- 11:30am-12pm: Final blog review and publish (30min)
- Afternoon: Bug fix work (uninterrupted 3h needed)

Risk mitigation:
- Front-load blog work before interruption
- Leave only final polish/publish for post-meeting slot
- Alert team to focus mode (minimize additional interruptions)
</thinking>
```

### Output
```json
{
  "plan": {
    "summary": "URGENT: Blog post due at noon with emergency meeting interruption. Complete draft before 11am meeting, finalize immediately after.",
    "time_blocks": [
      {
        "start": "09:30",
        "end": "11:00",
        "activity": "Write and edit blog post for product announcement (draft completion)",
        "priority": "high",
        "type": "deep_work"
      },
      {
        "start": "11:30",
        "end": "12:00",
        "activity": "Final review, polish, and publish blog post",
        "priority": "high",
        "type": "admin"
      },
      {
        "start": "12:00",
        "end": "15:00",
        "activity": "Investigate and fix critical bug in checkout flow",
        "priority": "high",
        "type": "deep_work"
      },
      {
        "start": "15:00",
        "end": "17:00",
        "activity": "Test checkout fix, deploy, and monitor",
        "priority": "high",
        "type": "admin"
      }
    ],
    "top_priorities": [
      "Publish blog post by noon deadline (CRITICAL)",
      "Fix critical checkout bug",
      "Attend emergency production issue meeting"
    ],
    "notes": "Blog post has external deadline at noon. Emergency meeting will interrupt workflow at 11am. Draft must be complete by 11am to allow time for final review and publishing after meeting."
  }
}
```

---

## Example 5: Empty Calendar AND Empty Tasks

### Input Context
```xml
<calendar_events>
  <!-- No events -->
</calendar_events>

<tasks>
  <!-- No tasks -->
</tasks>
```

### Reasoning
```
<thinking>
No scheduled work detected.

Options:
1. Strategic planning (long-term thinking)
2. Professional development (learning, skill building)
3. Process improvement (optimize workflows)
4. Proactive outreach (networking, relationship building)

Since this is unusual, should suggest productive use of open time rather than leaving it unstructured. Focus on activities that are always valuable but often deprioritized.
</thinking>
```

### Output
```json
{
  "plan": {
    "summary": "No scheduled meetings or tasks. Ideal day for strategic planning, professional development, and proactive work.",
    "time_blocks": [
      {
        "start": "09:00",
        "end": "11:00",
        "activity": "Review quarterly goals and plan next 30 days",
        "priority": "medium",
        "type": "deep_work"
      },
      {
        "start": "11:00",
        "end": "13:00",
        "activity": "Professional development: learn new technology or complete online course",
        "priority": "medium",
        "type": "deep_work"
      },
      {
        "start": "14:00",
        "end": "16:00",
        "activity": "Process improvement: document workflows, update team playbooks",
        "priority": "medium",
        "type": "admin"
      },
      {
        "start": "16:00",
        "end": "17:00",
        "activity": "Proactive outreach: connect with colleagues, network, or mentor",
        "priority": "low",
        "type": "admin"
      }
    ],
    "top_priorities": [
      "Review and update quarterly goals",
      "Invest in professional development",
      "Improve team processes and documentation"
    ],
    "notes": "No meetings or tasks scheduled. Use this open time for strategic work that's important but not urgent."
  }
}
```

---

## Usage Guidelines

When using these examples for few-shot prompting:

1. **Select 2-3 relevant examples** based on the input pattern (don't include all 5)
2. **Wrap in XML tags** to distinguish from instructions:
   ```xml
   <examples>
     <example index="1">
       <!-- Example content -->
     </example>
   </examples>
   ```
3. **Match example complexity** to the task (simple day → Example 1-2, complex → Example 4-5)
4. **Emphasize reasoning** by including the `<thinking>` blocks when you want more transparent decision-making
5. **Update examples quarterly** based on real-world usage patterns and edge cases

---

## Anti-Patterns to Avoid

These are **bad** examples that violate best practices:

### ❌ Bad Example 1: Generic Activities
```json
{
  "time_blocks": [
    {
      "activity": "Work on stuff",  // Too vague
      "activity": "Do tasks",       // No specificity
      "activity": "Meeting prep"    // No context
    }
  ]
}
```

### ❌ Bad Example 2: Overlapping Time Blocks
```json
{
  "time_blocks": [
    {"start": "09:00", "end": "11:00", ...},
    {"start": "10:30", "end": "12:00", ...}  // Overlaps with previous
  ]
}
```

### ❌ Bad Example 3: Ignoring Calendar Events
```json
{
  // User has meeting 2pm-3pm, but plan includes:
  "time_blocks": [
    {"start": "14:00", "end": "16:00", "activity": "Deep work"}  // Conflicts with meeting!
  ]
}
```

### ❌ Bad Example 4: Invalid Enum Values
```json
{
  "priority": "urgent",       // Should be: high, medium, or low
  "type": "focus_time"        // Should be: deep_work, meeting, break, or admin
}
```
