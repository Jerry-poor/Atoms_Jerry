"use client";

import {
  RunArtifactsSchema,
  ArtifactDetailSchema,
  RunCheckpointsSchema,
  RunDetailSchema,
  RunEventsSchema,
  RunListSchema,
  type RunArtifacts,
  type ArtifactDetail,
  type RunDetail,
  type RunCheckpoints,
  type RunEvents,
  type RunList,
} from "@atoms/shared";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiJson } from "@/lib/api";

export function useRuns() {
  return useRunsFiltered({});
}

export function useRunsFiltered({ projectId }: { projectId?: string | null }) {
  return useQuery({
    queryKey: ["runs", projectId ?? ""],
    queryFn: async (): Promise<RunList> => {
      const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
      const res = await apiFetch(`/api/runs${qs}`);
      return apiJson(res, RunListSchema);
    },
  });
}

export function useRun(runId: string) {
  return useQuery({
    queryKey: ["run", runId],
    enabled: runId.trim().length > 0,
    queryFn: async (): Promise<RunDetail> => {
      const res = await apiFetch(`/api/runs/${runId}`);
      return apiJson(res, RunDetailSchema);
    },
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status === "queued" || status === "running" || status === "paused"
        ? 1000
        : false;
    },
  });
}

export function useRunEvents(runId: string) {
  return useQuery({
    queryKey: ["run", runId, "events"],
    enabled: runId.trim().length > 0,
    queryFn: async (): Promise<RunEvents> => {
      const res = await apiFetch(`/api/runs/${runId}/events`);
      return apiJson(res, RunEventsSchema);
    },
    refetchInterval: 1000,
  });
}

export function useRunCheckpoints(runId: string) {
  return useQuery({
    queryKey: ["run", runId, "checkpoints"],
    enabled: runId.trim().length > 0,
    queryFn: async (): Promise<RunCheckpoints> => {
      const res = await apiFetch(`/api/runs/${runId}/checkpoints`);
      return apiJson(res, RunCheckpointsSchema);
    },
    refetchInterval: 1000,
  });
}

export function useRunArtifacts(runId: string, status?: string) {
  return useQuery({
    queryKey: ["run", runId, "artifacts", status ?? ""],
    enabled: runId.trim().length > 0,
    queryFn: async (): Promise<RunArtifacts> => {
      const res = await apiFetch(`/api/runs/${runId}/artifacts`);
      return apiJson(res, RunArtifactsSchema);
    },
    refetchInterval: (q) => {
      if (status === "queued" || status === "running" || status === "paused")
        return 1000;
      const n = q.state.data?.artifacts.length ?? 0;
      return n === 0 ? 1000 : false;
    },
  });
}

export function useRunArtifact(runId: string, artifactId: string) {
  return useQuery({
    queryKey: ["run", runId, "artifact", artifactId],
    enabled: runId.trim().length > 0 && artifactId.trim().length > 0,
    queryFn: async (): Promise<ArtifactDetail> => {
      const res = await apiFetch(`/api/runs/${runId}/artifacts/${artifactId}`);
      return apiJson(res, ArtifactDetailSchema);
    },
  });
}

export function useCreateRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      input: string;
      mode?: "engineer" | "team";
      roles?: string[] | null;
      project_id?: string | null;
      user_rules?: string[] | null;
    }): Promise<RunDetail> => {
      const res = await apiFetch("/api/runs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return apiJson(res, RunDetailSchema);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["runs"] });
    },
  });
}
