"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AuthResponseSchema,
  PasswordResetConfirmResponseSchema,
  PasswordResetRequestResponseSchema,
  type UserPublic,
} from "@atoms/shared";
import { apiFetch, apiJson, ApiError } from "@/lib/api";

async function fetchMe(): Promise<UserPublic | null> {
  const res = await apiFetch("/api/auth/me");
  if (res.status === 401) return null;
  const data = await apiJson(res, AuthResponseSchema);
  return data.user;
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
    retry: (count, err) => {
      if (err instanceof ApiError && err.status === 401) return false;
      return count < 1;
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiFetch("/api/auth/logout", { method: "POST" });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useLoginWithPassword() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const res = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const data = await apiJson(res, AuthResponseSchema);
      return data.user;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useSignupWithPassword() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      username: string;
      email: string;
      password: string;
    }) => {
      const res = await apiFetch("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const data = await apiJson(res, AuthResponseSchema);
      return data.user;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: async (payload: { email: string }) => {
      const res = await apiFetch("/api/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return apiJson(res, PasswordResetRequestResponseSchema);
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (payload: { token: string; new_password: string }) => {
      const res = await apiFetch("/api/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return apiJson(res, PasswordResetConfirmResponseSchema);
    },
  });
}
