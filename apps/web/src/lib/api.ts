import { z } from "zod";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export async function apiFetch(path: string, init?: RequestInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has("content-type") && init?.body) {
    headers.set("content-type", "application/json");
  }
  // Always call relative `/api/...` and rely on Next.js rewrites to proxy to FastAPI.
  return fetch(path, { ...init, headers, credentials: "include" });
}

export async function apiJson<T>(
  res: Response,
  schema: z.ZodType<T>,
): Promise<T> {
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new ApiError("API request failed", res.status, data);
  }
  return schema.parse(data);
}
