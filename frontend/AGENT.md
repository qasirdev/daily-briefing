# Frontend AGENT.md — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Scope

This file governs all development within the Next.js 16 (React 19) frontend application. The frontend is responsible for rendering the daily briefing UI, handling user interactions, managing consent flows, and displaying observability metrics.

---

## Technology Stack

| Technology | Version | Purpose |
|---|---|---|
| Next.js | 16.x | React framework with App Router |
| React | 19.x | UI library with Server Components (use, useTransition, useOptimistic, useActionState) |
| TypeScript | 5.6+ | Type safety |
| Tailwind CSS | 4.x | Utility-first styling |
| Zod | 3.23+ | Runtime schema validation |
| DOMPurify | 3.2+ | XSS protection |

---

## Architecture

```
frontend/
├── AGENT.md                    # This file
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Home page (briefing dashboard)
│   ├── api/
│   │   └── auth/
│   │       └── callback/
│   │           └── google/
│   │               └── route.ts  # OAuth callback handler
│   ├── settings/
│   │   └── page.tsx            # User preferences, consent management
│   └── globals.css             # Global styles
├── components/
│   ├── BriefingDashboard.tsx   # Primary briefing view
│   ├── ObservabilityBadge.tsx  # Execution metrics display
│   ├── ConsentPromptModal.tsx  # JIT consent modal
│   ├── TaskList.tsx            # Task rendering component
│   └── ui/                     # Shared UI primitives
├── hooks/
│   ├── useBriefing.ts          # Briefing data fetching
│   ├── useConsents.ts          # Consent management
│   └── useObservability.ts     # Metrics tracking
├── lib/
│   ├── api.ts                  # API client
│   ├── sanitize.ts             # HTML sanitization utilities
│   └── schemas.ts              # Zod schemas for API responses
└── __tests__/                  # Vitest test files
```

---

## Workflow Rules

| Rule | Behaviour |
|---|---|
| Server Components First | Use Server Components by default; Client Components only for interactivity |
| React 19 Hooks | Extensively use `use`, `useTransition`, `useOptimistic`, and `useActionState` for seamless state and data fetching handling |
| Type Safety | All API responses must be validated with Zod before use |
| Sanitization | All markdown/HTML from API must pass through DOMPurify before rendering |
| Accessibility | All interactive elements must have ARIA labels and keyboard support |
| Error Boundaries | Wrap major sections in error boundaries for graceful degradation |
| Loading States | Every async operation must have a loading state |

---

## Component Specifications

### BriefingDashboard.tsx

**Purpose:** Primary view for displaying the generated daily briefing.

**Props:**
```typescript
interface BriefingDashboardProps {
  briefing: string;          // Sanitized HTML content
  status: 'success' | 'degraded' | 'failure';
  metadata: ExecutionMetadata;
  onRetry?: () => void;      // Retry handler for degraded state
}
```

**Security Requirements:**
- MUST use `sanitizeHtml()` before rendering any content from API
- MUST display warning badge for degraded state
- MUST NOT render raw markdown without sanitization

**Example:**
```typescript
import { sanitizeHtml } from '@/lib/sanitize';

export function BriefingDashboard({ briefing, status, metadata, onRetry }: BriefingDashboardProps) {
  const sanitizedContent = sanitizeHtml(briefing);
  
  return (
    <article role="article" aria-label="Daily Briefing">
      {status === 'degraded' && (
        <Alert variant="warning" role="alert">
          Some components failed to load.
          <Button onClick={onRetry}>Retry</Button>
        </Alert>
      )}
      
      <div 
        dangerouslySetInnerHTML={{ __html: sanitizedContent }}
        className="prose prose-lg"
      />
      
      <ObservabilityBadge data={metadata} />
    </article>
  );
}
```

### ObservabilityBadge.tsx

**Purpose:** Displays execution metrics for transparency.

**Props:**
```typescript
interface ObservabilityBadgeProps {
  data: {
    executionMs: number;
    tokensUsed: number;
    modelUsed: string;
    status: 'success' | 'degraded' | 'failure';
    agentBreakdown?: AgentMetric[];
  };
}
```

**Requirements:**
- Display-only component, no user input handling
- Expandable to show per-agent breakdown
- Accessible tooltip for each metric

### ConsentPromptModal.tsx

**Purpose:** Handles JIT (Just-In-Time) authorization for external services.

**Props:**
```typescript
interface ConsentPromptModalProps {
  request: ConsentRequest;
  onGrant: (ttlHours: number) => void;
  onDeny: () => void;
  isLoading?: boolean;
}
```

**Security Requirements:**
- MUST clearly display requested permissions
- MUST allow user to select consent duration
- MUST NOT cache tokens client-side
- MUST handle loading state during OAuth flow

---

## Data Fetching Patterns

### Server Components (Preferred)

```typescript
// app/page.tsx
import { getBriefing } from '@/lib/api';

export default async function HomePage() {
  const briefing = await getBriefing();
  
  return <BriefingDashboard {...briefing} />;
}
```

### Client Components (When Needed)

```typescript
// components/InteractiveBriefing.tsx
'use client';

import { useBriefing } from '@/hooks/useBriefing';

export function InteractiveBriefing() {
  const { data, isLoading, error, refetch } = useBriefing();
  
  if (isLoading) return <BriefingSkeleton />;
  if (error) return <ErrorState onRetry={refetch} />;
  
  return <BriefingDashboard {...data} onRetry={refetch} />;
}
```

---

## Schema Validation

All API responses must be validated with Zod:

```typescript
// lib/schemas.ts
import { z } from 'zod';

export const executionMetadataSchema = z.object({
  executionMs: z.number().int().nonnegative(),
  tokensUsed: z.number().int().nonnegative(),
  modelUsed: z.string().min(1),
  traceId: z.string().min(32),
  dataClassification: z.enum(['public', 'internal', 'confidential', 'confidential_pii']),
});

export const briefingResponseSchema = z.object({
  status: z.enum(['success', 'failure', 'degraded']),
  briefing: z.string(),
  metadata: executionMetadataSchema,
  escalation: z.object({
    reason: z.string(),
    context: z.string().optional(),
  }).optional(),
});

export type BriefingResponse = z.infer<typeof briefingResponseSchema>;
```

---

## Sanitization

```typescript
// lib/sanitize.ts
import DOMPurify from 'dompurify';

const DOMPURIFY_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre',
    'blockquote', 'hr', 'br', 'a',
  ],
  ALLOWED_ATTR: ['href', 'title'],
  ALLOW_DATA_ATTR: false,
};

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, DOMPURIFY_CONFIG);
}
```

---

## Error Handling

### Error Boundary Pattern

```typescript
// components/BriefingErrorBoundary.tsx
'use client';

import { ErrorBoundary } from 'react-error-boundary';

function BriefingFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert" className="p-4 bg-red-50 rounded-lg">
      <h2 className="text-lg font-semibold text-red-800">
        Something went wrong
      </h2>
      <p className="text-sm text-red-600">{error.message}</p>
      <Button onClick={resetErrorBoundary}>Try again</Button>
    </div>
  );
}

export function BriefingErrorBoundary({ children }) {
  return (
    <ErrorBoundary FallbackComponent={BriefingFallback}>
      {children}
    </ErrorBoundary>
  );
}
```

---

## Styling Guidelines

### Tailwind CSS Configuration (v4 — CSS-first)

Tailwind 4 uses `@import "tailwindcss"` and `@theme` in `app/globals.css` instead of `tailwind.config.ts`:

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --color-briefing-primary: #2563eb;
  --color-briefing-success: #16a34a;
  --color-briefing-warning: #d97706;
  --color-briefing-error: #dc2626;
}
```

### Component Styling Pattern

```typescript
// Use semantic color tokens
<div className="bg-briefing-primary text-white">
  Primary action
</div>

// Use prose for markdown content
<div className="prose prose-lg prose-slate">
  {/* Sanitized HTML content */}
</div>
```

---

## Testing Requirements

### Component Tests (Vitest)

```typescript
// __tests__/components/BriefingDashboard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BriefingDashboard } from '@/components/BriefingDashboard';

describe('BriefingDashboard', () => {
  it('renders briefing content with proper accessibility', () => {
    render(
      <BriefingDashboard 
        briefing="<p>Test content</p>" 
        status="success"
        metadata={mockMetadata}
      />
    );
    
    expect(screen.getByRole('article')).toBeInTheDocument();
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('shows degraded state with retry option', () => {
    const onRetry = vi.fn();
    
    render(
      <BriefingDashboard 
        briefing="" 
        status="degraded"
        metadata={mockMetadata}
        onRetry={onRetry}
      />
    );
    
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('sanitizes HTML content before rendering', () => {
    render(
      <BriefingDashboard 
        briefing="<script>alert('xss')</script><p>Safe content</p>" 
        status="success"
        metadata={mockMetadata}
      />
    );
    
    expect(screen.queryByText("alert('xss')")).not.toBeInTheDocument();
    expect(screen.getByText('Safe content')).toBeInTheDocument();
  });
});
```

---

## Accessibility Requirements

| Requirement | Implementation |
|---|---|
| Keyboard Navigation | All interactive elements focusable via Tab |
| Screen Reader Support | Semantic HTML + ARIA labels |
| Color Contrast | WCAG 2.1 AA minimum (4.5:1 for text) |
| Focus Indicators | Visible focus rings on all focusables |
| Error Announcements | `role="alert"` for error messages |

---

*Frontend AGENT.md — Version 1.5.0 — May 2026*
