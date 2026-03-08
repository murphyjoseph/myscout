"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchJobDetail, fetchTechPreferences, updateJobAction } from "@/lib/api/jobs";
import { STATUS_COLORS } from "@/lib/display-utils";
import { presentJobDetail } from "./presenter";
import type { JobDetailContract } from "./types";
import type { JobStatus } from "@/lib/types";

const STATUSES: JobStatus[] = ["NEW", "SAVED", "APPLIED", "SKIPPED", "INTERVIEWING"];

export function useJobDetailController(jobId: number): JobDetailContract {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => {
      const result = await fetchJobDetail(jobId);
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

  const mutation = useMutation({
    mutationFn: (payload: { status?: string; notes?: string }) =>
      updateJobAction(jobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const dataContract = presentJobDetail(data, isLoading, error, techPrefs);
  const resolvedNotes = notes ?? (data?.notes || "");

  return {
    ...dataContract,
    display: {
      ...dataContract.display,
      notesValue: resolvedNotes,
      statusButtons: STATUSES.map((s) => ({
        status: s,
        color: STATUS_COLORS[s] || "fg.dim",
      })),
    },
    instructions: {
      ...dataContract.instructions,
      isMutating: mutation.isPending,
    },
    effects: {
      onStatusChange: (status: JobStatus) => mutation.mutate({ status }),
      onNotesChange: setNotes,
      onSaveNotes: () => mutation.mutate({ notes: resolvedNotes }),
    },
  };
}
