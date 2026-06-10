import DOMPurify from "dompurify";

const DOMPURIFY_CONFIG = {
  ALLOWED_TAGS: [
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "code",
    "pre",
    "blockquote",
    "hr",
    "br",
    "a",
  ],
  ALLOWED_ATTR: ["href", "title"],
  ALLOW_DATA_ATTR: false,
};

export function sanitizeHtml(dirty: string): string {
  if (!dirty.trim()) {
    return "";
  }
  return DOMPurify.sanitize(dirty, DOMPURIFY_CONFIG);
}
