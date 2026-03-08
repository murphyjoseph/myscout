/** Row shapes matching the SQL queries in route handlers. */

export interface CanonicalJob {
  id: number;
  company: string;
  title: string;
  location: string | null;
  remote_type: string | null;
  description_clean: string | null;
  apply_url_best: string | null;
  comp_min: number | null;
  comp_max: number | null;
  comp_currency: string | null;
  fingerprint: string;
  first_seen: string;
  last_seen: string;
  is_active: boolean;
}

export interface JobWithScore extends CanonicalJob {
  score_total: number | null;
  score_breakdown_json: Record<string, number> | null;
  status: string | null;
  notes: string | null;
  tech_tags: string[] | null;
  seniority: string | null;
}

export interface JobVariantRow {
  id: number;
  source: string;
  external_id: string;
  url: string | null;
  date_seen: string;
}

export interface JobDetail extends JobWithScore {
  variants: JobVariantRow[];
}

export type JobStatus = "NEW" | "SAVED" | "APPLIED" | "SKIPPED" | "INTERVIEWING";

export interface TechPreferences {
  must_have: string[];
  strong_plus: string[];
  avoid: string[];
}
