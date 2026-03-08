"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchJobs, fetchTechPreferences, updateJobAction } from "@/lib/api/jobs";
import { presentJobsList } from "./presenter";
import type { JobsListContract } from "./types";
import type { JobStatus } from "@/lib/api/types";

export function useJobsListController(): JobsListContract {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [minScore, setMinScore] = useState("");
  const [remoteFilter, setRemoteFilter] = useState("");

  const apiFilters: Record<string, string> = {};
  if (statusFilter) apiFilters.status = statusFilter;
  if (minScore) apiFilters.min_score = minScore;
  if (remoteFilter) apiFilters.remote_type = remoteFilter;

  const { data, isLoading, error } = useQuery({
    queryKey: ["jobs", apiFilters],
    queryFn: async () => {
      const result = await fetchJobs(apiFilters);
      if (!result.success) throw new Error(result.error);
      return result.data;
    },
  });

  const { data: techPrefs } = useQuery({
    queryKey: ["techPreferences"],
    queryFn: async () => {
      const result = await fetchTechPreferences();
      if (!result.success) return { must_have: [], strong_plus: [], avoid: [] };
      return result.data;
    },
    staleTime: 5 * 60 * 1000,
  });

  const saveMutation = useMutation({
    mutationFn: (payload: { id: number; status: string }) =>
      updateJobAction(payload.id, { status: payload.status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const dataContract = presentJobsList(data, isLoading, error, techPrefs);

  const handleFilterChange = (key: string, value: string) => {
    switch (key) {
      case "status": setStatusFilter(value); break;
      case "minScore": setMinScore(value); break;
      case "remote": setRemoteFilter(value); break;
    }
  };

  const handleQuickSave = (jobId: number, currentStatus: JobStatus) => {
    const newStatus = currentStatus === "SAVED" ? "NEW" : "SAVED";
    saveMutation.mutate({ id: jobId, status: newStatus });
  };

  return {
    ...dataContract,
    display: {
      ...dataContract.display,
      filters: { status: statusFilter, minScore, remote: remoteFilter },
    },
    effects: {
      onFilterChange: handleFilterChange,
      onQuickSave: handleQuickSave,
    },
  };
}
