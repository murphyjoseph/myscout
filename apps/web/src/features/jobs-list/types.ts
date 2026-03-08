import type { JobStatus } from "@/lib/types";
import type { CategorizedTag } from "@/lib/display-utils";

export interface ScoreHighlight {
  label: string;
  value: string;
  color: string;
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

export interface JobsListFilters {
  status: string;
  minScore: string;
  remote: string;
}

export interface JobsListEffects {
  onFilterChange: (key: string, value: string) => void;
  onQuickSave: (jobId: number, currentStatus: JobStatus) => void;
}

export interface JobsListContract {
  renderAs: "loading" | "empty" | "error" | "content";
  display: {
    heading: string;
    jobCount: string;
    cards: JobCard[];
    filters: JobsListFilters;
  };
  instructions: {
    showEmptyState: boolean;
    showError: boolean;
  };
  effects: JobsListEffects;
}

/** Presenter output before the controller adds effects and filters. */
export type JobsListDataContract = Omit<JobsListContract, "effects" | "display"> & {
  display: Omit<JobsListContract["display"], "filters">;
};
