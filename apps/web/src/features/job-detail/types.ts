import type { JobStatus } from "@/lib/api/types";
import type { CategorizedTag } from "@/lib/display-utils";

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

export interface StatusButton {
  status: JobStatus;
  color: string;
}

export interface JobDetailEffects {
  onStatusChange: (status: JobStatus) => void;
  onNotesChange: (value: string) => void;
  onSaveNotes: () => void;
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
    remoteBadge: string | null;
    seniorityBadge: string | null;
    techTags: CategorizedTag[];
    scoreRows: ScoreRow[];
    variants: VariantRow[];
    descriptionHtml: string;
    applyUrl: string | null;
    notesValue: string;
    statusButtons: StatusButton[];
  };
  instructions: {
    showError: boolean;
    hasScore: boolean;
    hasTechTags: boolean;
    hasVariants: boolean;
    hasDescription: boolean;
    isMutating: boolean;
  };
  effects: JobDetailEffects;
}

/** Presenter output before the controller adds effects and mutable state. */
export type JobDetailDataContract = Omit<JobDetailContract, "effects" | "display" | "instructions"> & {
  display: Omit<JobDetailContract["display"], "notesValue" | "statusButtons">;
  instructions: Omit<JobDetailContract["instructions"], "isMutating">;
};
