"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppTopNav } from "@/components/top-nav";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useMe } from "@/lib/auth";
import { useProjects, useCreateProject } from "@/lib/projects";
import { useCreateRun, useRunsFiltered } from "@/lib/runs";

function initials(s: string) {
  const t = s.trim();
  if (!t) return "U";
  return t.slice(0, 1).toUpperCase();
}

const TEAM_ROLES = [
  {
    id: "team_lead",
    name: "团队领导",
    desc: "拆解任务，分配角色，汇总输出",
    color: "bg-blue-500/15 text-blue-700",
  },
  {
    id: "product_manager",
    name: "产品经理",
    desc: "澄清需求，确定 MVP 与范围",
    color: "bg-emerald-500/15 text-emerald-700",
  },
  {
    id: "architect",
    name: "架构师",
    desc: "系统设计，接口与模块划分",
    color: "bg-violet-500/15 text-violet-700",
  },
  {
    id: "engineer",
    name: "工程师",
    desc: "实现步骤与关键代码落地",
    color: "bg-zinc-500/15 text-zinc-800",
  },
  {
    id: "seo_expert",
    name: "SEO 专家",
    desc: "关键词与站内优化建议",
    color: "bg-amber-500/15 text-amber-800",
  },
  {
    id: "data_analyst",
    name: "数据分析师",
    desc: "指标体系与验证方案",
    color: "bg-sky-500/15 text-sky-800",
  },
  {
    id: "deep_researcher",
    name: "深度研究员",
    desc: "风险点与研究路径",
    color: "bg-rose-500/15 text-rose-700",
  },
] as const;

type TeamRoleId = (typeof TEAM_ROLES)[number]["id"];

function defaultTeamSelection(): TeamRoleId[] {
  return TEAM_ROLES.map((r) => r.id);
}

function roleById(id: TeamRoleId) {
  return TEAM_ROLES.find((r) => r.id === id) ?? TEAM_ROLES[0];
}

export default function WorkspacePage() {
  const router = useRouter();

  const me = useMe();
  const projects = useProjects();
  const createProject = useCreateProject();
  const [activeProjectId, setActiveProjectId] = useState<string | null>(() => {
    try {
      return window.localStorage.getItem("atoms.activeProjectId");
    } catch {
      return null;
    }
  });
  const runs = useRunsFiltered({ projectId: activeProjectId });
  const createRun = useCreateRun();

  const [prompt, setPrompt] = useState("");
  const [userRulesText, setUserRulesText] = useState("");
  const [newProjectOpen, setNewProjectOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [mode, setMode] = useState<"engineer" | "team">("team");
  const [teamRoles, setTeamRoles] = useState<TeamRoleId[]>(() =>
    defaultTeamSelection(),
  );

  useEffect(() => {
    // When landing from marketing `/app?prompt=...`, keep URL clean after we hydrate the input.
    const value = new URLSearchParams(window.location.search).get("prompt");
    if (value) {
      setPrompt(value);
      router.replace("/app");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    try {
      if (activeProjectId) window.localStorage.setItem("atoms.activeProjectId", activeProjectId);
      else window.localStorage.removeItem("atoms.activeProjectId");
    } catch {
      // ignore
    }
  }, [activeProjectId]);

  const activeProject = useMemo(() => {
    if (!activeProjectId) return null;
    return projects.data?.projects.find((p) => p.id === activeProjectId) ?? null;
  }, [activeProjectId, projects.data?.projects]);

  const recentRuns = useMemo(() => {
    return runs.data?.runs.slice(0, 3) ?? [];
  }, [runs.data?.runs]);

  const displayName =
    me.data?.username || me.data?.email || (me.data ? "User" : "");
  const avatar = initials(displayName);

  const selectedTeamRoles = useMemo(() => {
    return teamRoles
      .map((id) => roleById(id))
      .filter(Boolean)
      .slice(0, TEAM_ROLES.length);
  }, [teamRoles]);

  return (
    <div className="flex min-h-dvh">
      <aside className="hidden w-72 shrink-0 border-r bg-muted/10 md:flex md:flex-col">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="text-base font-semibold tracking-tight">Atoms</div>
            <div className="h-8 w-8 rounded-md border bg-background" />
          </div>
        </div>

        <div className="px-3">
          <Dialog open={newProjectOpen} onOpenChange={setNewProjectOpen}>
            <DialogTrigger asChild>
              <button
                type="button"
                className="flex w-full items-center justify-center gap-2 rounded-md bg-muted px-3 py-2 text-sm font-medium hover:bg-muted/70"
                onClick={() => {
                  const ts = new Date().toLocaleString([], {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  });
                  setNewProjectName(`新项目 ${ts}`);
                }}
                disabled={createProject.isPending}
              >
                <span className="text-lg leading-none">+</span>
                新项目
              </button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>创建新项目</DialogTitle>
              </DialogHeader>
              <div className="space-y-3">
                <div className="text-sm text-muted-foreground">
                  你可以自定义项目名称（会显示在左侧列表，并用于筛选 Runs）。
                </div>
                <Input
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="例如：股票溢价监控工具"
                />
                <div className="flex justify-end gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => setNewProjectOpen(false)}
                    disabled={createProject.isPending}
                  >
                    取消
                  </Button>
                  <Button
                    onClick={async () => {
                      const name = newProjectName.trim();
                      const p = await createProject.mutateAsync({
                        name: name.length > 0 ? name : null,
                      });
                      setActiveProjectId(p.id);
                      setPrompt("");
                      setNewProjectOpen(false);
                    }}
                    disabled={createProject.isPending}
                  >
                    创建
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <nav className="mt-4 px-3 text-sm">
          <Link
            href="/app/discover"
            className="flex items-center gap-2 rounded-md px-3 py-2 hover:bg-muted/60"
          >
            <span className="h-4 w-4 rounded-full border" />
            发现
          </Link>
        </nav>

        <div className="mt-4 px-3">
          <div className="text-xs font-semibold text-muted-foreground">
            我的项目
          </div>
          <div className="mt-2 space-y-1">
            {projects.isLoading ? (
              <>
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </>
            ) : null}
            {projects.data?.projects.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setActiveProjectId(p.id)}
                className={
                  p.id === activeProjectId
                    ? "flex w-full items-center justify-between rounded-md bg-foreground px-3 py-2 text-left text-sm text-background"
                    : "flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-muted/60"
                }
              >
                <span className="truncate">{p.name}</span>
                <span className="ml-2 text-xs opacity-70">&gt;</span>
              </button>
            ))}
            {projects.data && projects.data.projects.length === 0 ? (
              <div className="rounded-md border bg-card px-3 py-2 text-xs text-muted-foreground">
                还没有项目，点击 “新项目” 创建一个。
              </div>
            ) : null}
          </div>
        </div>

        <div className="mt-4 px-3">
          <div className="text-xs font-semibold text-muted-foreground">最近</div>
          <div className="mt-2 space-y-1">
            {runs.isLoading ? <Skeleton className="h-8 w-full" /> : null}
            {recentRuns.map((r) => (
              <Link
                key={r.id}
                href={`/app/runs/${r.id}`}
                className="block truncate rounded-md px-3 py-2 text-sm hover:bg-muted/60"
                title={r.input}
              >
                {r.input}
              </Link>
            ))}
            {runs.data && runs.data.runs.length === 0 ? (
              <div className="rounded-md border bg-card px-3 py-2 text-xs text-muted-foreground">
                暂无运行记录。
              </div>
            ) : null}
          </div>
        </div>

        <div className="mt-auto p-3">
          <div className="rounded-xl border bg-card p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-sm font-semibold">
                {avatar}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">
                  {displayName || "…"}
                </div>
                <div className="text-xs text-muted-foreground">Free</div>
              </div>
            </div>
            <div className="mt-4">
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div className="h-2 w-[35%] bg-primary" />
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                <span>剩余积分</span>
                <span>14.28 剩余</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b px-4 py-3 md:px-6">
          <div className="md:hidden">
            <Link href="/" className="text-base font-semibold tracking-tight">
              Atoms
            </Link>
          </div>
          <div className="flex items-center gap-3">
            {activeProject ? (
              <div className="hidden text-sm text-muted-foreground md:block">
                当前项目: <span className="text-foreground">{activeProject.name}</span>
              </div>
            ) : null}
            <AppTopNav />
          </div>
        </header>

        <main className="flex-1 px-4 pb-12 pt-10 md:px-10">
          <div className="mx-auto max-w-3xl">
            <div className="flex items-center justify-center gap-2">
              {[
                "bg-orange-300",
                "bg-zinc-200",
                "bg-pink-300",
                "bg-slate-300",
                "bg-sky-300",
                "bg-emerald-300",
                "bg-violet-300",
              ].map((cls) => (
                <div
                  key={cls}
                  className={`h-10 w-10 rounded-full border ${cls}`}
                />
              ))}
            </div>

            <h1 className="mt-8 text-center text-4xl font-semibold tracking-tight md:text-6xl">
              把想法变成可销售的 <span className="text-blue-600">产品</span>
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-center text-sm text-muted-foreground md:text-base">
              AI 员工用于验证想法、构建产品并获取客户。几分钟内完成。无需编码。
            </p>

            <div className="mt-10 rounded-2xl border bg-card p-4 md:p-6">
              <div className="text-xs text-muted-foreground">
                竞争模式大大改善首次生成效果。
              </div>

              <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setMode("engineer")}
                    className={
                      mode === "engineer"
                        ? "rounded-full bg-foreground px-3 py-1 text-xs font-medium text-background"
                        : "rounded-full border px-3 py-1 text-xs font-medium hover:bg-muted"
                    }
                  >
                    工程师
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
                    团队
                  </button>
                </div>

                {mode === "team" ? (
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <div className="flex -space-x-2">
                        {selectedTeamRoles.slice(0, 5).map((r) => (
                          <div
                            key={r.id}
                            title={`${r.name} (${r.id})`}
                            className={`flex h-8 w-8 items-center justify-center rounded-full border bg-background text-[10px] font-semibold ${r.color}`}
                          >
                            {r.name.slice(0, 1)}
                          </div>
                        ))}
                        {selectedTeamRoles.length > 5 ? (
                          <div className="flex h-8 w-8 items-center justify-center rounded-full border bg-background text-[10px] font-semibold text-muted-foreground">
                            +{selectedTeamRoles.length - 5}
                          </div>
                        ) : null}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        已选择 {teamRoles.length}/{TEAM_ROLES.length}
                      </div>
                    </div>

                    <Dialog>
                      <DialogTrigger asChild>
                        <button
                          type="button"
                          className="rounded-full border bg-background px-3 py-1 text-xs font-medium hover:bg-muted"
                        >
                          配置团队
                        </button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>团队成员</DialogTitle>
                        </DialogHeader>

                        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                          <div className="text-xs text-muted-foreground">
                            选择参与本次生成的角色。团队领导建议保留。
                          </div>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <button
                              type="button"
                              className="underline"
                              onClick={() => setTeamRoles(defaultTeamSelection())}
                            >
                              全选
                            </button>
                            <button
                              type="button"
                              className="underline"
                              onClick={() =>
                                setTeamRoles([
                                  "team_lead",
                                  "product_manager",
                                  "architect",
                                  "engineer",
                                ])
                              }
                            >
                              仅核心
                            </button>
                          </div>
                        </div>

                        <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-2">
                          {TEAM_ROLES.map((r) => {
                            const enabled = teamRoles.includes(r.id);
                            return (
                              <div
                                key={r.id}
                                className={
                                  enabled
                                    ? "flex items-center justify-between gap-3 rounded-xl border bg-background p-3"
                                    : "flex items-center justify-between gap-3 rounded-xl border bg-muted/20 p-3 opacity-75"
                                }
                              >
                                <div className="min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${r.color}`}
                                    >
                                      {r.name}
                                    </span>
                                    <span
                                      className="truncate text-xs text-muted-foreground"
                                      title={r.id}
                                    >
                                      {r.id}
                                    </span>
                                  </div>
                                  <div className="mt-1 truncate text-xs text-muted-foreground">
                                    {r.desc}
                                  </div>
                                </div>
                                <div className="shrink-0">
                                  <Switch
                                    checked={enabled}
                                    onCheckedChange={(v) => {
                                      setTeamRoles((prev) => {
                                        if (v) {
                                          const next = prev.includes(r.id)
                                            ? prev
                                            : [...prev, r.id];
                                          return next.includes("team_lead")
                                            ? [
                                                "team_lead",
                                                ...next.filter((x) => x !== "team_lead"),
                                              ]
                                            : next;
                                        }
                                        const next = prev.filter((x) => x !== r.id);
                                        return next.length > 0 ? next : prev;
                                      });
                                    }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                ) : null}
              </div>

              <div className="mt-4 flex gap-3">
                <button
                  type="button"
                  className="flex h-10 w-10 items-center justify-center rounded-lg border bg-background hover:bg-muted"
                  title="Add"
                  onClick={() => setPrompt((p) => (p ? `${p}\n` : ""))}
                >
                  +
                </button>

                <textarea
                  className="min-h-28 w-full resize-none rounded-lg border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                  placeholder="输入你的想法，例如：做一个可以生成贪吃蛇小游戏代码的网站…"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                />

                <Button
                  className="h-10 w-10 shrink-0 rounded-lg p-0"
                  onClick={async () => {
                    const input = prompt.trim();
                    if (!input) return;
                    if (mode === "team" && teamRoles.length === 0) return;
                    const user_rules = userRulesText
                      .split("\n")
                      .map((x) => x.trim())
                      .filter(Boolean);
                    const r = await createRun.mutateAsync({
                      input,
                      mode,
                      roles: mode === "team" ? [...teamRoles] : null,
                      project_id: activeProjectId,
                      user_rules: user_rules.length ? user_rules : null,
                    });
                    setPrompt("");
                    router.push(`/app/runs/${r.id}`);
                  }}
                  disabled={
                    createRun.isPending ||
                    prompt.trim().length === 0 ||
                    (mode === "team" && teamRoles.length === 0)
                  }
                  title="Run"
                >
                  Run
                </Button>
              </div>

              <details className="mt-3 rounded-xl border bg-muted/10 p-3">
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

            <div className="mt-8 text-center text-xs text-muted-foreground">
              提示: 你也可以直接去 <Link className="underline" href="/app/runs">Runs</Link> 查看所有运行记录。
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
