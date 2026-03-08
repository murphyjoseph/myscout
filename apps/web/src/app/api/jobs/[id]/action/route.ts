import { NextRequest, NextResponse } from "next/server";
import { query } from "@/lib/server/db";

// LOCAL-ONLY: No authentication or CSRF protection — this is a single-user
// local tool. In a production app, every mutation endpoint would require
// auth and CSRF tokens.
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const jobId = parseInt(id, 10);
  if (isNaN(jobId)) {
    return NextResponse.json({ error: "Invalid ID" }, { status: 400 });
  }

  const body = await request.json();
  const { status, notes } = body;

  const validStatuses = ["NEW", "SAVED", "APPLIED", "SKIPPED", "INTERVIEWING"];
  if (status && !validStatuses.includes(status)) {
    return NextResponse.json({ error: "Invalid status" }, { status: 400 });
  }
  if (notes != null && typeof notes !== "string") {
    return NextResponse.json({ error: "Notes must be a string" }, { status: 400 });
  }

  const sql = `
    INSERT INTO job_actions (canonical_job_id, status, notes, updated_at)
    VALUES ($1, $2, $3, NOW())
    ON CONFLICT (canonical_job_id) DO UPDATE
    SET status = COALESCE($2, job_actions.status),
        notes = COALESCE($3, job_actions.notes),
        updated_at = NOW()
    RETURNING *
  `;

  const result = await query(sql, [jobId, status || "NEW", notes || null]);
  return NextResponse.json(result[0]);
}
