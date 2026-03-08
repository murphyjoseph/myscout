"use client";

import { useJobsListController } from "./use-controller";
import { JobsListView } from "./view";

export function JobsList() {
  const contract = useJobsListController();
  return <JobsListView contract={contract} />;
}
