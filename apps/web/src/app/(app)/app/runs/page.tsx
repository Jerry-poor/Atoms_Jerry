"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppTopNav } from "@/components/top-nav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/lib/projects";
import { useCreateRun, useRunsFiltered } from "@/lib/runs";

const TEAM_ROLES = [
  "team_lead",
  "seo_expert",
  "product_manager",
  "architect",
  "engineer",
  "data_analyst",
  "deep_researcher",
] as const;

export default function RunsPage() {
  const projects = useProjects();
  const [activeProjectId, setActiveProjectId] = useState<string | null>(() => {
    try {
      return window.localStorage.getItem("atoms.activeProjectId");
    } catch {
      return null;
    }
  });
  const runs = useRunsFiltered({ projectId: activeProjectId });
  const create = useCreateRun();
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"engineer" | "team">("team");
  const [userRulesText, setUserRulesText] = useState("");

  useEffect(() => {
    const value = new URLSearchParams(window.location.search).get("prompt");
    if (value) setInput(value);
  }, []);

  return (
    <div>
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/app" className="text-lg font-semibold tracking-tight">
            Atoms
          </Link>
          <AppTopNav />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Runs</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Minimal protected area to satisfy mandatory LangGraph workflow
              requirements.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-xl border bg-card p-6">
          <div className="text-sm font-medium">Create run</div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">Project:</span>
            <select
              value={activeProjectId ?? ""}
              onChange={(e) => {
                const v = e.target.value || null;
                setActiveProjectId(v);
                try {
                  if (v) window.localStorage.setItem("atoms.activeProjectId", v);
                  else window.localStorage.removeItem("atoms.activeProjectId");
                } catch {
                  // ignore
                }
              }}
              className="h-9 rounded-xl border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-foreground/20"
            >
              <option value="">All projects</option>
              {(projects.data?.projects ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setMode("engineer")}
              className={
                mode === "engineer"
                  ? "rounded-full bg-foreground px-3 py-1 text-xs font-medium text-background"
                  : "rounded-full border px-3 py-1 text-xs font-medium hover:bg-muted"
              }
            >
              Engineer
            </button>
            <button
              type="button"
              onClick={() => setMode("team")}
              className={
                mode === "team"
                  ? "rounded-full bg-foreground px-3 py-1 text-xs font-medium text-background"
                  : "rounded-full border px-3 py-1 text-xs font-medium hover:bg-muted"
              }
            >
              Team
            </button>
          </div>

          <div className="mt-3 flex flex-col gap-3 md:flex-row">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe the task to run..."
            />
            <Button
              onClick={async () => {
                const user_rules = userRulesText
                  .split("\n")
                  .map((x) => x.trim())
                  .filter(Boolean);
                const r = await create.mutateAsync({
                  input,
                  mode,
                  roles: mode === "team" ? [...TEAM_ROLES] : null,
                  project_id: activeProjectId,
                  user_rules: user_rules.length ? user_rules : null,
                });
                setInput("");
                window.location.href = `/app/runs/${r.id}`;
              }}
              disabled={create.isPending || input.trim().length === 0}
            >
              Run
            </Button>
          </div>

          <details className="mt-3 rounded-lg border bg-muted/10 p-3">
            <summary className="cursor-pointer text-sm font-medium">
              规则（可选）
              <span className="ml-2 text-xs text-muted-foreground">
                每行一条；模块规则用{" "}
                <code className="rounded bg-background px-1">module:web:</code>
              </span>
            </summary>
            <div className="mt-3">
              <textarea
                className="min-h-24 w-full resize-y rounded-lg border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                placeholder={
                  "例如：\n禁止引入新依赖\nmodule:web: 必须使用 shadcn 组件\nmodule:api: 不允许修改数据库结构"
                }
                value={userRulesText}
                onChange={(e) => setUserRulesText(e.target.value)}
              />
            </div>
          </details>
        </div>

        <div className="mt-8">
          <h2 className="text-sm font-semibold text-muted-foreground">Recent</h2>
          <div className="mt-3 space-y-3">
            {runs.isLoading ? (
              <>
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </>
            ) : null}

            {runs.data?.runs.map((r) => (
              <Link
                key={r.id}
                href={`/app/runs/${r.id}`}
                className="block rounded-xl border bg-card p-5 hover:bg-muted/30"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium">{r.input}</div>
                  <div className="text-xs text-muted-foreground">
                    {r.status}
                  </div>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">{r.id}</div>
              </Link>
            ))}

            {runs.data && runs.data.runs.length === 0 ? (
              <div className="text-sm text-muted-foreground">No runs yet.</div>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}
