import { describe, expect, it } from "vitest";

import { sanitizeHtml } from "@/lib/sanitize";

describe("sanitizeHtml", () => {
  it("strips script tags", () => {
    const clean = sanitizeHtml("<script>alert('xss')</script><p>Safe content</p>");
    expect(clean).not.toContain("<script");
    expect(clean).toContain("Safe content");
  });

  it("allows safe markdown-like tags", () => {
    const clean = sanitizeHtml("<p><strong>Hello</strong></p>");
    expect(clean).toContain("<strong>Hello</strong>");
  });

  it("returns empty string for whitespace-only input", () => {
    expect(sanitizeHtml("   ")).toBe("");
  });
});
