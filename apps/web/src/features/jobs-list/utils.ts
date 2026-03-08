import type { ScoreHighlight } from "./types";

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return "Today";
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  return d.toLocaleDateString();
}

function decodeEntities(str: string): string {
  return str
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ");
}

function stripHtml(html: string): string {
  const decoded = decodeEntities(html);
  const stripped = decoded.replace(/<[^>]*>/g, " ");
  return stripped.replace(/\s+/g, " ").trim();
}

export function makeSnippet(description: string | null, maxLen: number = 140): string {
  if (!description) return "";
  const plain = stripHtml(description);
  if (plain.length <= maxLen) return plain;
  return plain.slice(0, maxLen).replace(/\s+\S*$/, "") + "...";
}

const BREAKDOWN_LABELS: Record<string, string> = {
  must_have_match: "Must-have",
  strong_plus_match: "Strong+",
  penalty_avoid_tech: "Avoid",
  penalty_exclude_phrase: "Excluded",
  recency_bonus: "Recent",
  semantic_similarity: "Similarity",
};

export function extractScoreHighlights(
  breakdown: Record<string, number> | null,
): ScoreHighlight[] {
  if (!breakdown) return [];

  const highlights: ScoreHighlight[] = [];

  for (const [key, value] of Object.entries(breakdown)) {
    if (key === "total" || value === 0) continue;
    const label = BREAKDOWN_LABELS[key];
    if (!label) continue;

    let color: string;
    let prefix: string;
    if (value > 0) {
      color = "green";
      prefix = "+";
    } else {
      color = "red";
      prefix = "";
    }

    highlights.push({ label, value: `${prefix}${value}`, color });
  }

  highlights.sort((a, b) => {
    const aVal = parseFloat(a.value);
    const bVal = parseFloat(b.value);
    return Math.abs(bVal) - Math.abs(aVal);
  });

  return highlights.slice(0, 3);
}
