"use client";

import { useJobDetailController } from "./use-controller";
import { JobDetailView } from "./view";

interface JobDetailProps {
  jobId: number;
}

export function JobDetail({ jobId }: JobDetailProps) {
  const contract = useJobDetailController(jobId);
  return <JobDetailView contract={contract} />;
}
