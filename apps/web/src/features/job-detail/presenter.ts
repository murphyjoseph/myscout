import DOMPurify from "isomorphic-dompurify";
import type { JobDetail, JobStatus, TechPreferences } from "@/lib/types";
import { scoreColor, formatSalary, categorizeTags } from "@/lib/display-utils";
import type { CategorizedTag } from "@/lib/display-utils";
import { formatScoreLabel } from "./utils";
import type { ScoreRow, VariantRow, JobDetailDataContract } from "./types";

export function presentJobDetail(
  job: JobDetail | undefined,
  isLoading: boolean,
  error: unknown,
  techPrefs?: TechPreferences,
): JobDetailDataContract {
  const emptyDisplay = {
    title: "", company: "", location: "", salary: null, score: null, scoreColor: "fg.dim",
    status: "NEW" as JobStatus, remoteBadge: null, seniorityBadge: null,
    techTags: [] as CategorizedTag[], scoreRows: [] as ScoreRow[], variants: [] as VariantRow[],
    descriptionHtml: "", applyUrl: null,
  };

  if (isLoading || (!job && !error)) {
    return {
      renderAs: "loading",
      display: emptyDisplay,
      instructions: {
        showError: false, hasScore: false, hasTechTags: false,
        hasVariants: false, hasDescription: false,
      },
    };
  }

  if (error || !job) {
    return {
      renderAs: "error",
      display: emptyDisplay,
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
      color: value < 0 ? "fg.error" : value > 0 ? "fg.success" : "fg.dim",
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
      remoteBadge: job.remote_type || null,
      seniorityBadge: job.seniority || null,
      techTags: categorizeTags(job.tech_tags || [], techPrefs ?? { must_have: [], strong_plus: [], avoid: [] }),
      scoreRows,
      variants,
      descriptionHtml: DOMPurify.sanitize(job.description_clean || ""),
      applyUrl: job.apply_url_best || null,
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
