"use client";

import {
  ProjectListSchema,
  ProjectPublicSchema,
  type ProjectList,
  type ProjectPublic,
} from "@atoms/shared";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, apiJson } from "@/lib/api";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: async (): Promise<ProjectList> => {
      const res = await apiFetch("/api/projects");
      return apiJson(res, ProjectListSchema);
    },
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name?: string | null }): Promise<ProjectPublic> => {
      const res = await apiFetch("/api/projects", {
        method: "POST",
        body: JSON.stringify(payload ?? {}),
      });
      return apiJson(res, ProjectPublicSchema);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

