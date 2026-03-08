import { NextRequest, NextResponse } from "next/server";
import { query } from "@/lib/server/db";
import type { JobWithScore } from "@/lib/api/types";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const status = searchParams.get("status");
  const minScore = searchParams.get("min_score");
  const remoteType = searchParams.get("remote_type");
  const source = searchParams.get("source");

  const conditions: string[] = ["cj.is_active = true"];
  const params: unknown[] = [];
  let paramIdx = 1;

  if (status) {
    conditions.push(`COALESCE(ja.status, 'NEW') = $${paramIdx++}`);
    params.push(status);
  }
  if (minScore) {
    conditions.push(`COALESCE(js.score_total, 0) >= $${paramIdx++}`);
    params.push(parseFloat(minScore));
  }
  if (remoteType) {
    conditions.push(`cj.remote_type = $${paramIdx++}`);
    params.push(remoteType);
  }
  if (source) {
    conditions.push(`EXISTS (SELECT 1 FROM job_variants jv WHERE jv.canonical_job_id = cj.id AND jv.source = $${paramIdx++})`);
    params.push(source);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  const sql = `
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
    ${whereClause}
    ORDER BY COALESCE(js.score_total, 0) DESC
  `;

  const jobs = await query<JobWithScore>(sql, params);
  return NextResponse.json(jobs);
}
