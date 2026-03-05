import { NextRequest, NextResponse } from "next/server";
import { query } from "@/lib/db";
import type { JobWithScore, JobVariantRow } from "@/lib/types";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const jobId = parseInt(id, 10);
  if (isNaN(jobId)) {
    return NextResponse.json({ error: "Invalid ID" }, { status: 400 });
  }

  const jobSql = `
    SELECT
      cj.id, cj.company, cj.title, cj.location, cj.remote_type,
      cj.description_clean, cj.apply_url_best,
      cj.comp_min, cj.comp_max, cj.comp_currency,
      cj.fingerprint, cj.first_seen, cj.last_seen, cj.is_active,
      js.score_total, js.score_breakdown_json,
      COALESCE(ja.status, 'NEW') as status, ja.notes,
      jf.tech_tags, jf.seniority
    FROM canonical_jobs cj
    LEFT JOIN LATERAL (
      SELECT score_total, score_breakdown_json
      FROM job_scores
      WHERE canonical_job_id = cj.id
      ORDER BY created_at DESC
      LIMIT 1
    ) js ON true
    LEFT JOIN job_actions ja ON ja.canonical_job_id = cj.id
    LEFT JOIN job_features jf ON jf.canonical_job_id = cj.id
    WHERE cj.id = $1
  `;

  const jobs = await query<JobWithScore>(jobSql, [jobId]);
  if (jobs.length === 0) {
    return NextResponse.json({ error: "Job not found" }, { status: 404 });
  }

  const variantsSql = `
    SELECT id, source, external_id, url, date_seen
    FROM job_variants
    WHERE canonical_job_id = $1
    ORDER BY date_seen DESC
  `;
  const variants = await query<JobVariantRow>(variantsSql, [jobId]);

  return NextResponse.json({ ...jobs[0], variants });
}
