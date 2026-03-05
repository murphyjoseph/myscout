import type { JobWithScore, JobStatus, TechPreferences } from "@/lib/types";

export interface ScoreHighlight {
  label: string;
  value: string;
  color: string;
}

export type TechTagCategory = "must_have" | "strong_plus" | "avoid" | "neutral";

export interface CategorizedTag {
  label: string;
  category: TechTagCategory;
}

export interface JobCard {
  id: number;
  title: string;
  company: string;
  companyInitial: string;
  location: string;
  remoteBadge: string | null;
  seniorityBadge: string | null;
  salary: string | null;
  score: string | null;
  scoreColor: string;
  scored: boolean;
  scoreHighlights: ScoreHighlight[];
  status: JobStatus;
  statusColor: string;
  isSaved: boolean;
  techTags: CategorizedTag[];
  extraTagCount: number;
  snippet: string;
  lastSeen: string;
}

export interface JobsListContract {
  renderAs: "loading" | "empty" | "error" | "content";
  display: {
    heading: string;
    jobCount: string;
    cards: JobCard[];
  };
  instructions: {
    showEmptyState: boolean;
    showError: boolean;
  };
}

const STATUS_COLORS: Record<string, string> = {
  NEW: "blue",
  SAVED: "purple",
  APPLIED: "green",
  SKIPPED: "gray",
  INTERVIEWING: "orange",
};

function scoreColor(score: number | null): string {
  if (score === null) return "gray";
  if (score >= 30) return "green";
  if (score >= 10) return "yellow";
  if (score >= 0) return "gray";
  return "red";
}

function formatDate(dateStr: string): string {
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
  // Decode entities first so encoded tags like &lt;div&gt; become real tags,
  // then strip all tags, then decode any remaining entities in text content.
  const decoded = decodeEntities(html);
  const stripped = decoded.replace(/<[^>]*>/g, " ");
  return stripped.replace(/\s+/g, " ").trim();
}

function makeSnippet(description: string | null, maxLen: number = 140): string {
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

function extractScoreHighlights(
  breakdown: Record<string, number> | null
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

    highlights.push({
      label,
      value: `${prefix}${value}`,
      color,
    });
  }

  // Sort: biggest positive first, then biggest negative
  highlights.sort((a, b) => {
    const aVal = parseFloat(a.value);
    const bVal = parseFloat(b.value);
    return Math.abs(bVal) - Math.abs(aVal);
  });

  return highlights.slice(0, 3);
}

function formatSalary(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null;
  const fmt = (n: number) => `$${Math.round(n / 1000)}k`;
  if (min != null && max != null && min !== max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt(min ?? max!);
}

const MAX_VISIBLE_TAGS = 4;

function categorizeTags(tags: string[], prefs: TechPreferences): CategorizedTag[] {
  const mustSet = new Set(prefs.must_have.map((t) => t.toLowerCase()));
  const strongSet = new Set(prefs.strong_plus.map((t) => t.toLowerCase()));
  const avoidSet = new Set(prefs.avoid.map((t) => t.toLowerCase()));

  return tags.map((tag) => {
    const lower = tag.toLowerCase();
    let category: TechTagCategory = "neutral";
    if (mustSet.has(lower)) category = "must_have";
    else if (strongSet.has(lower)) category = "strong_plus";
    else if (avoidSet.has(lower)) category = "avoid";
    return { label: tag, category };
  });
}

export function presentJobsList(
  jobs: JobWithScore[] | undefined,
  isLoading: boolean,
  error: unknown,
  techPrefs?: TechPreferences,
): JobsListContract {
  if (isLoading) {
    return {
      renderAs: "loading",
      display: { heading: "MyScout", jobCount: "", cards: [] },
      instructions: { showEmptyState: false, showError: false },
    };
  }

  if (error || !jobs) {
    return {
      renderAs: "error",
      display: { heading: "MyScout", jobCount: "", cards: [] },
      instructions: { showEmptyState: false, showError: true },
    };
  }

  if (jobs.length === 0) {
    return {
      renderAs: "empty",
      display: { heading: "MyScout", jobCount: "0 jobs", cards: [] },
      instructions: { showEmptyState: true, showError: false },
    };
  }

  const prefs = techPrefs ?? { must_have: [], strong_plus: [], avoid: [] };

  const cards: JobCard[] = jobs.map((job) => {
    const rawTags = job.tech_tags || [];
    const allCategorized = categorizeTags(rawTags, prefs);

    // Sort: must_have first, then strong_plus, then neutral, avoid last
    const ORDER: Record<TechTagCategory, number> = { must_have: 0, strong_plus: 1, neutral: 2, avoid: 3 };
    allCategorized.sort((a, b) => ORDER[a.category] - ORDER[b.category]);

    const status = (job.status as JobStatus) || "NEW";
    return {
      id: job.id,
      title: job.title,
      company: job.company,
      companyInitial: (job.company || "?")[0].toUpperCase(),
      location: job.location || "",
      remoteBadge: job.remote_type || null,
      seniorityBadge: job.seniority || null,
      salary: formatSalary(job.comp_min, job.comp_max),
      score: job.score_total != null ? job.score_total.toFixed(1) : null,
      scoreColor: scoreColor(job.score_total),
      scored: job.score_total != null,
      scoreHighlights: extractScoreHighlights(job.score_breakdown_json),
      status,
      statusColor: STATUS_COLORS[status] || "gray",
      isSaved: status === "SAVED" || status === "APPLIED" || status === "INTERVIEWING",
      techTags: allCategorized.slice(0, MAX_VISIBLE_TAGS),
      extraTagCount: Math.max(0, allCategorized.length - MAX_VISIBLE_TAGS),
      snippet: makeSnippet(job.description_clean),
      lastSeen: job.last_seen ? formatDate(job.last_seen) : "",
    };
  });

  return {
    renderAs: "content",
    display: {
      heading: "MyScout",
      jobCount: `${jobs.length} ${jobs.length === 1 ? "job" : "jobs"}`,
      cards,
    },
    instructions: { showEmptyState: false, showError: false },
  };
}
