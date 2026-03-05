import DOMPurify from "isomorphic-dompurify";
import type { JobDetail, JobStatus, TechPreferences } from "@/lib/types";

export type TechTagCategory = "must_have" | "strong_plus" | "avoid" | "neutral";

export interface CategorizedTag {
  label: string;
  category: TechTagCategory;
}

export interface ScoreRow {
  label: string;
  value: string;
  color: string;
  isPositive: boolean;
  isNegative: boolean;
}

export interface VariantRow {
  id: number;
  source: string;
  url: string | null;
  urlDisplay: string;
  dateSeen: string;
}

export interface JobDetailContract {
  renderAs: "loading" | "error" | "content";
  display: {
    title: string;
    company: string;
    location: string;
    salary: string | null;
    score: string | null;
    scoreColor: string;
    status: JobStatus;
    statusColor: string;
    remoteBadge: string | null;
    seniorityBadge: string | null;
    techTags: CategorizedTag[];
    scoreRows: ScoreRow[];
    variants: VariantRow[];
    descriptionHtml: string;
    applyUrl: string | null;
    notes: string;
  };
  instructions: {
    showError: boolean;
    hasScore: boolean;
    hasTechTags: boolean;
    hasVariants: boolean;
    hasDescription: boolean;
  };
}

const STATUS_COLORS: Record<string, string> = {
  NEW: "blue",
  SAVED: "purple",
  APPLIED: "green",
  SKIPPED: "gray",
  INTERVIEWING: "orange",
};

function formatSalary(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null;
  const fmt = (n: number) => `$${Math.round(n / 1000)}k`;
  if (min != null && max != null && min !== max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt(min ?? max!);
}

function scoreColor(score: number | null): string {
  if (score === null) return "gray";
  if (score >= 30) return "green";
  if (score >= 10) return "yellow";
  if (score >= 0) return "gray";
  return "red";
}

function formatScoreLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function categorizeTags(tags: string[], prefs: TechPreferences): CategorizedTag[] {
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
      return { label: tag, category };
    })
    .sort((a, b) => ORDER[a.category] - ORDER[b.category]);
}

export function presentJobDetail(
  job: JobDetail | undefined,
  isLoading: boolean,
  error: unknown,
  techPrefs?: TechPreferences,
): JobDetailContract {
  if (isLoading || (!job && !error)) {
    return {
      renderAs: "loading",
      display: {
        title: "", company: "", location: "", salary: null, score: null, scoreColor: "gray",
        status: "NEW", statusColor: "blue", remoteBadge: null, seniorityBadge: null,
        techTags: [], scoreRows: [], variants: [], descriptionHtml: "",
        applyUrl: null, notes: "",
      },
      instructions: {
        showError: false, hasScore: false, hasTechTags: false,
        hasVariants: false, hasDescription: false,
      },
    };
  }

  if (error || !job) {
    return {
      renderAs: "error",
      display: {
        title: "", company: "", location: "", salary: null, score: null, scoreColor: "gray",
        status: "NEW", statusColor: "blue", remoteBadge: null, seniorityBadge: null,
        techTags: [], scoreRows: [], variants: [], descriptionHtml: "",
        applyUrl: null, notes: "",
      },
      instructions: {
        showError: true, hasScore: false, hasTechTags: false,
        hasVariants: false, hasDescription: false,
      },
    };
  }

  const breakdown = job.score_breakdown_json || {};
  const scoreRows: ScoreRow[] = Object.entries(breakdown)
    .filter(([key]) => key !== "total")
    .map(([key, value]) => ({
      label: formatScoreLabel(key),
      value: value > 0 ? `+${value}` : `${value}`,
      color: value < 0 ? "red.400" : value > 0 ? "green.400" : "gray.500",
      isPositive: value > 0,
      isNegative: value < 0,
    }));

  const variants: VariantRow[] = (job.variants || []).map((v) => ({
    id: v.id,
    source: v.source,
    url: v.url,
    urlDisplay: v.url && v.url.length > 50 ? v.url.slice(0, 50) + "..." : v.url || "",
    dateSeen: new Date(v.date_seen).toLocaleDateString(),
  }));

  const status = (job.status as JobStatus) || "NEW";

  return {
    renderAs: "content",
    display: {
      title: job.title,
      company: job.company,
      location: job.location || "",
      salary: formatSalary(job.comp_min, job.comp_max),
      score: job.score_total != null ? job.score_total.toFixed(1) : null,
      scoreColor: scoreColor(job.score_total),
      status,
      statusColor: STATUS_COLORS[status] || "gray",
      remoteBadge: job.remote_type || null,
      seniorityBadge: job.seniority || null,
      techTags: categorizeTags(job.tech_tags || [], techPrefs ?? { must_have: [], strong_plus: [], avoid: [] }),
      scoreRows,
      variants,
      descriptionHtml: DOMPurify.sanitize(job.description_clean || ""),
      applyUrl: job.apply_url_best || null,
      notes: job.notes || "",
    },
    instructions: {
      showError: false,
      hasScore: job.score_total != null,
      hasTechTags: (job.tech_tags || []).length > 0,
      hasVariants: variants.length > 0,
      hasDescription: !!job.description_clean,
    },
  };
}
