"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchJobDetail, fetchTechPreferences, updateJobAction } from "@/lib/api/jobs";
import { presentJobDetail } from "./presenter";
import { JobDetailView } from "./view";
import type { JobStatus } from "@/lib/types";

interface JobDetailProps {
  jobId: number;
}

export function JobDetail({ jobId }: JobDetailProps) {
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

  const contract = presentJobDetail(data, isLoading, error, techPrefs);

  const notesValue = notes ?? contract.display.notes;

  return (
    <JobDetailView
      contract={contract}
      notesValue={notesValue}
      onNotesChange={setNotes}
      onStatusChange={(status: JobStatus) => mutation.mutate({ status })}
      onSaveNotes={() => mutation.mutate({ notes: notesValue })}
      isMutating={mutation.isPending}
    />
  );
}
