import type { TechPreferences } from "./api/types";

/* ─── Shared types ────────────────────────────────────── */

export type TechTagCategory = "must_have" | "strong_plus" | "avoid" | "neutral";

export interface TagStyle {
  bg: string;
  color: string;
  borderColor: string;
  fontWeight: string;
}

export interface CategorizedTag {
  label: string;
  category: TechTagCategory;
  style: TagStyle;
}

/* ─── Token-based style maps ──────────────────────────── */

export const STATUS_COLORS: Record<string, string> = {
  NEW: "status.new",
  SAVED: "status.saved",
  APPLIED: "status.applied",
  SKIPPED: "status.skipped",
  INTERVIEWING: "status.interviewing",
};

const TAG_STYLES: Record<TechTagCategory, TagStyle> = {
  must_have: { bg: "accent.subtle", color: "accent.fg", borderColor: "accent.muted", fontWeight: "600" },
  strong_plus: { bg: "tag.strongPlus.bg", color: "tag.strongPlus.fg", borderColor: "tag.strongPlus.border", fontWeight: "normal" },
  avoid: { bg: "tag.avoid.bg", color: "tag.avoid.fg", borderColor: "tag.avoid.border", fontWeight: "normal" },
  neutral: { bg: "transparent", color: "fg.dim", borderColor: "border.muted", fontWeight: "normal" },
};

/* ─── Pure formatting functions ───────────────────────── */

export function scoreColor(score: number | null): string {
  if (score === null) return "fg.dim";
  if (score >= 50) return "score.high";
  if (score >= 30) return "score.good";
  if (score >= 10) return "score.mid";
  if (score >= 0) return "score.low";
  return "score.negative";
}

export function formatSalary(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null;
  const fmt = (n: number) => `$${Math.round(n / 1000)}k`;
  if (min != null && max != null && min !== max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt(min ?? max!);
}

export function categorizeTags(tags: string[], prefs: TechPreferences): CategorizedTag[] {
  const mustSet = new Set(prefs.must_have.map((t) => t.toLowerCase()));
  const strongSet = new Set(prefs.strong_plus.map((t) => t.toLowerCase()));
  const avoidSet = new Set(prefs.avoid.map((t) => t.toLowerCase()));

  const ORDER: Record<TechTagCategory, number> = { must_have: 0, strong_plus: 1, neutral: 2, avoid: 3 };

  return tags
    .map((tag) => {
      const lower = tag.toLowerCase();
      let category: TechTagCategory = "neutral";
      if (mustSet.has(lower)) category = "must_have";
      else if (strongSet.has(lower)) category = "strong_plus";
      else if (avoidSet.has(lower)) category = "avoid";
      return { label: tag, category, style: TAG_STYLES[category] };
    })
    .sort((a, b) => ORDER[a.category] - ORDER[b.category]);
}
