import type { JobWithScore, JobStatus, TechPreferences } from "@/lib/types";
import { scoreColor, formatSalary, categorizeTags, STATUS_COLORS } from "@/lib/display-utils";
import { formatDate, makeSnippet, extractScoreHighlights } from "./utils";
import type { JobCard, JobsListDataContract } from "./types";

const MAX_VISIBLE_TAGS = 4;

export function presentJobsList(
  jobs: JobWithScore[] | undefined,
  isLoading: boolean,
  error: unknown,
  techPrefs?: TechPreferences,
): JobsListDataContract {
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
    const allCategorized = categorizeTags(job.tech_tags || [], prefs);
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
      statusColor: STATUS_COLORS[status] || "fg.dim",
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
