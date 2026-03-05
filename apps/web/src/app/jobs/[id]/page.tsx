"use client";

import { use } from "react";
import { JobDetail } from "@/features/job-detail/job-detail";

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <JobDetail jobId={parseInt(id, 10)} />;
}
