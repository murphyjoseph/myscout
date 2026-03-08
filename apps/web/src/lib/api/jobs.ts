import type { JobWithScore, JobDetail, TechPreferences } from "@/lib/api/types";

type Result<T> =
  | { success: true; data: T }
  | { success: false; error: string };

export async function fetchJobs(
  filters: Record<string, string>
): Promise<Result<JobWithScore[]>> {
  try {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value) params.set(key, value);
    }
    const res = await fetch(`/api/jobs?${params}`);
    if (!res.ok) return { success: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { success: true, data };
  } catch {
    return { success: false, error: "Network error" };
  }
}

export async function fetchJobDetail(
  id: number
): Promise<Result<JobDetail>> {
  try {
    const res = await fetch(`/api/jobs/${id}`);
    if (!res.ok) return { success: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { success: true, data };
  } catch {
    return { success: false, error: "Network error" };
  }
}

export async function fetchTechPreferences(): Promise<Result<TechPreferences>> {
  try {
    const res = await fetch("/api/profile");
    if (!res.ok) return { success: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { success: true, data };
  } catch {
    return { success: false, error: "Network error" };
  }
}

export async function updateJobAction(
  id: number,
  data: { status?: string; notes?: string }
): Promise<Result<unknown>> {
  try {
    const res = await fetch(`/api/jobs/${id}/action`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) return { success: false, error: `HTTP ${res.status}` };
    const result = await res.json();
    return { success: true, data: result };
  } catch {
    return { success: false, error: "Network error" };
  }
}
