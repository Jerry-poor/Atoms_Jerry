"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Fragment, useEffect, useMemo, useRef, useState } from "react";

import type { Artifact } from "@atoms/shared";

import { AppTopNav } from "@/components/top-nav";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CodeEditor } from "@/components/code-editor";
import {
  useRun,
  useRunArtifact,
  useRunArtifacts,
  useRunCheckpoints,
  useRunEvents,
} from "@/lib/runs";

type StreamEvent = {
  seq: number;
  type: string;
  message: string;
  data?: unknown;
  created_at: string;
};

function fmtTime(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function extFromMime(mime: string) {
  const t = mime.split("/").pop() || "txt";
  if (t === "json") return "json";
  if (t.includes("javascript")) return "js";
  if (t.includes("typescript")) return "ts";
  if (t.includes("html")) return "html";
  if (t.includes("css")) return "css";
  if (t.includes("markdown")) return "md";
  return "txt";
}

function titleForNode(node: string) {
  const map: Record<string, string> = {
    init: "初始化",
    rule_node: "规则裁决",
    team_router: "路由",
    team_lead: "团队领导",
    seo_expert: "SEO 专家",
    product_manager: "产品经理",
    architect: "架构师",
    task_view: "任务视图",
    engineer: "工程师",
    engineer_solo: "工程师",
    data_analyst: "数据分析师",
    deep_researcher: "深度研究员",
    team_finalize: "汇总",
  };
  return map[node] ?? node;
}

function mimeFromPath(p: string) {
  const n = p.toLowerCase();
  if (n.endsWith(".json")) return "application/json";
  if (n.endsWith(".html")) return "text/html";
  if (n.endsWith(".css")) return "text/css";
  if (n.endsWith(".ts") || n.endsWith(".tsx") || n.endsWith(".js") || n.endsWith(".jsx")) return "text/plain";
  if (n.endsWith(".md")) return "text/markdown";
  return "text/plain";
}

function isMetaArtifact(a: Artifact) {
  return a.name === "final_output.json" || a.name === "files_manifest.json";
}

function normalizeNewlines(text: string) {
  return (text || "").replace(/\r\n/g, "\n");
}

function LineNumberedCode({ value }: { value: string }) {
  const content = useMemo(() => normalizeNewlines(value), [value]);
  const lines = useMemo(() => content.split("\n"), [content]);
  const maxLines = 5000;
  const shown = lines.length > maxLines ? lines.slice(0, maxLines) : lines;
  const numbers = useMemo(
    () => shown.map((_, i) => String(i + 1)).join("\n"),
    [shown],
  );
  const body = useMemo(() => shown.join("\n"), [shown]);

  return (
    <div className="relative h-full overflow-auto rounded-xl border bg-muted/10">
      <div className="flex min-w-max font-mono text-[12px] leading-5">
        <pre className="select-none border-r bg-muted/20 px-4 py-3 text-right text-muted-foreground">
          {numbers}
        </pre>
        <pre className="px-4 py-3 text-foreground">{body || "\n"}</pre>
      </div>
      {lines.length > maxLines ? (
        <div className="sticky bottom-0 border-t bg-background/90 px-4 py-2 text-xs text-muted-foreground backdrop-blur">
          文件过大，仅展示前 {maxLines} 行（共 {lines.length} 行）。
        </div>
      ) : null}
    </div>
  );
}

type FileTreeDir = {
  kind: "dir";
  name: string;
  path: string;
  children: Array<FileTreeDir | FileTreeFile>;
};

type FileTreeFile = {
  kind: "file";
  name: string;
  path: string;
  artifact: Artifact;
};

function buildFileTree(artifacts: Artifact[]) {
  type MutableDir = {
    name: string;
    path: string;
    dirs: Map<string, MutableDir>;
    files: Map<string, FileTreeFile>;
  };

  const root: MutableDir = {
    name: "",
    path: "",
    dirs: new Map(),
    files: new Map(),
  };

  for (const a of artifacts) {
    const parts = String(a.name || "")
      .replaceAll("\\", "/")
      .split("/")
      .filter(Boolean);
    if (parts.length === 0) continue;

    let cur = root;
    for (let i = 0; i < parts.length; i += 1) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      const nextPath = cur.path ? `${cur.path}/${part}` : part;
      if (isLast) {
        cur.files.set(nextPath.toLowerCase(), {
          kind: "file",
          name: part,
          path: nextPath,
          artifact: a,
        });
      } else {
        const key = nextPath.toLowerCase();
        const next = cur.dirs.get(key) ?? {
          name: part,
          path: nextPath,
          dirs: new Map(),
          files: new Map(),
        };
        cur.dirs.set(key, next);
        cur = next;
      }
    }
  }

  function toDir(d: MutableDir): FileTreeDir {
    const children: Array<FileTreeDir | FileTreeFile> = [];
    const dirs = [...d.dirs.values()].sort((a, b) => a.name.localeCompare(b.name));
    const files = [...d.files.values()].sort((a, b) => a.name.localeCompare(b.name));
    for (const x of dirs) children.push(toDir(x));
    for (const x of files) children.push(x);
    return { kind: "dir", name: d.name, path: d.path, children };
  }

  return toDir(root);
}

export default function RunDetailPage() {
  const params = useParams<{ id: string | string[] }>();
  const runId = Array.isArray(params?.id) ? params.id[0] : params?.id || "";
  const run = useRun(runId);
  const arts = useRunArtifacts(runId, run.data?.status);

  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [done, setDone] = useState<string | null>(null);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string>("");
  const [openTabs, setOpenTabs] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);
  const nodeListRef = useRef<HTMLDivElement | null>(null);
  const [openNode, setOpenNode] = useState<string>("");
  const [autoFollow, setAutoFollow] = useState(true);
  const [showMeta, setShowMeta] = useState(false);
  const [fileQuery, setFileQuery] = useState("");
  const [openDirs, setOpenDirs] = useState<Record<string, boolean>>({});

  const polledEvents = useRunEvents(runId);
  const checkpoints = useRunCheckpoints(runId);
  const [ctlPending, setCtlPending] = useState(false);

  useEffect(() => {
    if (!runId) return;
    setStreamEvents([]);
    setDone(null);
    setOpenNode("");
    setSelectedLivePath("");

    const es = new EventSource(`/api/runs/${runId}/stream`);
    es.addEventListener("run_event", (evt) => {
      try {
        const data = JSON.parse((evt as MessageEvent).data) as StreamEvent;
        setStreamEvents((prev) => {
          if (prev.some((e) => e.seq === data.seq)) return prev;
          return [...prev, data].sort((a, b) => a.seq - b.seq);
        });
      } catch {
        // ignore
      }
    });
    es.addEventListener("done", (evt) => {
      try {
        const data = JSON.parse((evt as MessageEvent).data) as { status?: string };
        setDone(data.status || "done");
      } catch {
        setDone("done");
      } finally {
        es.close();
      }
    });
    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [runId]);

  useEffect(() => {
    const el = nodeListRef.current;
    if (!el) return;
    if (!autoFollow) return;
    el.scrollTop = el.scrollHeight;
  }, [autoFollow, streamEvents.length, checkpoints.data?.checkpoints.length]);

  const allArtifacts = useMemo(() => arts.data?.artifacts ?? [], [arts.data?.artifacts]);
  const codeArtifacts = useMemo(() => {
    const q = fileQuery.trim().toLowerCase();
    const list = allArtifacts.filter((a) => !isMetaArtifact(a));
    const filtered = q ? list.filter((a) => a.name.toLowerCase().includes(q)) : list;

    function rank(a: Artifact) {
      const n = a.name.toLowerCase();
      if (n === "index.html") return 0;
      if (n === "app.js") return 1;
      if (n === "style.css") return 2;
      return 10;
    }

    return [...filtered].sort((a, b) => {
      const ra = rank(a);
      const rb = rank(b);
      if (ra !== rb) return ra - rb;
      return a.name.localeCompare(b.name);
    });
  }, [allArtifacts, fileQuery]);

  const metaArtifacts = useMemo(() => {
    const q = fileQuery.trim().toLowerCase();
    const list = allArtifacts.filter(isMetaArtifact);
    const filtered = q ? list.filter((a) => a.name.toLowerCase().includes(q)) : list;
    return [...filtered].sort((a, b) => a.name.localeCompare(b.name));
  }, [allArtifacts, fileQuery]);

  useEffect(() => {
    if (selectedArtifactId) return;
    if (codeArtifacts.length > 0) {
      setSelectedArtifactId(codeArtifacts[0].id);
      return;
    }
    if (metaArtifacts.length > 0) setSelectedArtifactId(metaArtifacts[0].id);
  }, [codeArtifacts, metaArtifacts, selectedArtifactId]);

  useEffect(() => {
    if (!selectedArtifactId) return;
    setOpenTabs((prev) => (prev.includes(selectedArtifactId) ? prev : [...prev, selectedArtifactId]));
  }, [selectedArtifactId]);

  const selected = useMemo(() => {
    return allArtifacts.find((a) => a.id === selectedArtifactId) ?? null;
  }, [allArtifacts, selectedArtifactId]);

  const artifactDetail = useRunArtifact(runId, selectedArtifactId);

  const visibleEvents: StreamEvent[] = useMemo(() => {
    if (streamEvents.length > 0) return streamEvents;
    return (
      polledEvents.data?.events.map((e) => ({
        seq: e.seq,
        type: e.type,
        message: e.message,
        data: e.data,
        created_at: e.created_at,
      })) ?? []
    );
  }, [polledEvents.data?.events, streamEvents]);

  const checkpointList = useMemo(
    () => checkpoints.data?.checkpoints ?? [],
    [checkpoints.data?.checkpoints],
  );

  const liveFiles = useMemo(() => {
    for (let i = checkpointList.length - 1; i >= 0; i -= 1) {
      const st = checkpointList[i]?.state as unknown;
      if (!st || typeof st !== "object") continue;
      const files = (st as { files?: unknown }).files;
      if (!Array.isArray(files) || files.length === 0) continue;
      const out: Array<{ path: string; content: string }> = [];
      for (const f of files) {
        if (!f || typeof f !== "object") continue;
        const path = String((f as { path?: unknown }).path ?? "").trim();
        const content = String((f as { content?: unknown }).content ?? "");
        if (!path) continue;
        out.push({ path, content });
      }
      if (out.length > 0) return out;
    }
    return [];
  }, [checkpointList]);

  const [selectedLivePath, setSelectedLivePath] = useState<string>("");

  useEffect(() => {
    if (selectedArtifactId) return;
    if (liveFiles.length > 0 && !selectedLivePath) {
      setSelectedLivePath(liveFiles[0].path);
    }
  }, [liveFiles, selectedArtifactId, selectedLivePath]);

  const nodes = useMemo(() => {
    const order: string[] = [];
    const seen = new Set<string>();
    for (const cp of checkpointList) {
      if (!seen.has(cp.node)) {
        seen.add(cp.node);
        order.push(cp.node);
      }
    }
    return order;
  }, [checkpointList]);

  const currentNode = useMemo(() => {
    const last = checkpointList.length > 0 ? checkpointList[checkpointList.length - 1] : null;
    return last?.node ?? "";
  }, [checkpointList]);

  useEffect(() => {
    if (!currentNode) return;
    setOpenNode((prev) => prev || currentNode);
  }, [currentNode]);

  const completedNodes = useMemo(() => {
    const s = new Set<string>();
    for (const e of visibleEvents) {
      if (e.type !== "node.completed") continue;
      const n =
        e.data && typeof e.data === "object" && "node" in e.data
          ? String((e.data as { node?: unknown }).node ?? "")
          : "";
      if (n) s.add(n);
    }
    return s;
  }, [visibleEvents]);

  const outputsByRole = useMemo(() => {
    const out = new Map<string, string[]>();
    for (const e of visibleEvents) {
      if (e.type !== "agent.output") continue;
      const role =
        e.data && typeof e.data === "object" && "role" in e.data
          ? String((e.data as { role?: unknown }).role ?? "")
          : e.message;
      const text =
        e.data && typeof e.data === "object" && "text" in e.data
          ? String((e.data as { text?: unknown }).text ?? "")
          : "";
      if (!role || !text) continue;
      const arr = out.get(role) ?? [];
      arr.push(text);
      out.set(role, arr);
    }
    return out;
  }, [visibleEvents]);

  const deltasByRole = useMemo(() => {
    const out = new Map<string, string>();
    for (const e of visibleEvents) {
      if (e.type !== "agent.delta") continue;
      const role =
        e.data && typeof e.data === "object" && "role" in e.data
          ? String((e.data as { role?: unknown }).role ?? "")
          : e.message;
      const delta =
        e.data && typeof e.data === "object" && "delta" in e.data
          ? String((e.data as { delta?: unknown }).delta ?? "")
          : "";
      if (!role || !delta) continue;
      out.set(role, (out.get(role) ?? "") + delta);
    }
    return out;
  }, [visibleEvents]);

  function outputsForNode(node: string) {
    if (outputsByRole.has(node)) return outputsByRole.get(node) ?? [];
    if (node === "engineer_solo") return outputsByRole.get("engineer") ?? [];
    // When no finalized output is available yet, show live deltas (streaming tokens).
    const role = node === "engineer_solo" ? "engineer" : node;
    const delta = deltasByRole.get(role) ?? "";
    if (delta) return [delta];
    return [];
  }

  function latestCheckpointForNode(node: string) {
    for (let i = checkpointList.length - 1; i >= 0; i -= 1) {
      const cp = checkpointList[i];
      if (cp.node === node) return cp;
    }
    return null;
  }

  async function rerunFromNode(node: string) {
    setCtlPending(true);
    try {
      const res = await fetch(`/api/runs/${runId}/rerun?node=${encodeURIComponent(node)}&goto=${encodeURIComponent(node)}`, {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) return;
      const data = (await res.json()) as { id?: string };
      if (data?.id) window.location.href = `/app/runs/${data.id}`;
    } finally {
      setCtlPending(false);
    }
  }

  const tree = useMemo(() => buildFileTree(codeArtifacts), [codeArtifacts]);

  function toggleDir(path: string) {
    setOpenDirs((prev) => ({ ...prev, [path]: !prev[path] }));
  }

  function isDirOpen(path: string) {
    return openDirs[path] ?? path.split("/").length <= 1;
  }

  const openArtifacts: Artifact[] = useMemo(() => {
    const byId = new Map(allArtifacts.map((a) => [a.id, a] as const));
    const out: Artifact[] = [];
    for (const id of openTabs) {
      const a = byId.get(id);
      if (a) out.push(a);
    }
    return out;
  }, [allArtifacts, openTabs]);

  function renderTreeNode(node: FileTreeDir | FileTreeFile, depth: number) {
    if (node.kind === "file") {
      const active = node.artifact.id === selectedArtifactId;
      return (
        <button
          key={node.path}
          type="button"
          onClick={() => setSelectedArtifactId(node.artifact.id)}
          className={
            active
              ? "flex w-full items-center gap-2 rounded-lg bg-foreground px-2 py-1.5 text-left text-xs text-background"
              : "flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs hover:bg-muted/40"
          }
          style={{ paddingLeft: 8 + depth * 14 }}
          title={node.path}
        >
          <span className="truncate">{node.name}</span>
          <span className="ml-auto text-[10px] opacity-70">
            {node.artifact.mime_type.split("/").pop()}
          </span>
        </button>
      );
    }

    const open = isDirOpen(node.path);
    return (
      <Fragment key={node.path || "__root"}>
        {node.name ? (
          <button
            type="button"
            onClick={() => toggleDir(node.path)}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs hover:bg-muted/40"
            style={{ paddingLeft: 8 + depth * 14 }}
            title={node.path}
          >
            <span className="inline-flex w-4 select-none justify-center text-muted-foreground">
              {open ? "▾" : "▸"}
            </span>
            <span className="truncate font-medium">{node.name}</span>
          </button>
        ) : null}
        {open
          ? node.children.map((c) => renderTreeNode(c, depth + (node.name ? 1 : 0)))
          : null}
      </Fragment>
    );
  }

  return (
    <div>
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-[1480px] items-center justify-between px-4">
          <Link href="/app" className="text-lg font-semibold tracking-tight">
            Atoms
          </Link>
          <AppTopNav />
        </div>
      </header>

      <main className="mx-auto max-w-[1480px] px-4 py-6">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <Link href="/app/runs" className="text-sm underline">
              Back to Runs
            </Link>
            <div className="mt-3">
              {run.isLoading ? (
                <Skeleton className="h-10 w-96" />
              ) : (
                <h1 className="text-2xl font-semibold tracking-tight">{run.data?.input}</h1>
              )}
              <div className="mt-2 text-sm text-muted-foreground">
                Status: {run.data?.status || "…"}
                {done ? <span className="ml-2">({done})</span> : null}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              disabled={ctlPending || run.isLoading}
              onClick={() => {
                const q = encodeURIComponent(run.data?.input ?? "");
                if (!q) return;
                window.location.href = `/app?prompt=${q}`;
              }}
            >
              Re-run
            </Button>
            {run.data?.status === "running" ? (
              <Button
                variant="secondary"
                disabled={ctlPending}
                onClick={async () => {
                  setCtlPending(true);
                  try {
                    await fetch(`/api/runs/${runId}/pause`, { method: "POST", credentials: "include" });
                  } finally {
                    setCtlPending(false);
                  }
                }}
              >
                Pause
              </Button>
            ) : null}
            {run.data?.status === "paused" ? (
              <Button
                variant="secondary"
                disabled={ctlPending}
                onClick={async () => {
                  setCtlPending(true);
                  try {
                    await fetch(`/api/runs/${runId}/resume`, { method: "POST", credentials: "include" });
                  } finally {
                    setCtlPending(false);
                  }
                }}
              >
                Resume
              </Button>
            ) : null}
            {run.data?.status === "queued" || run.data?.status === "running" || run.data?.status === "paused" ? (
              <Button
                variant="destructive"
                disabled={ctlPending}
                onClick={async () => {
                  setCtlPending(true);
                  try {
                    await fetch(`/api/runs/${runId}/cancel`, { method: "POST", credentials: "include" });
                  } finally {
                    setCtlPending(false);
                  }
                }}
              >
                Cancel
              </Button>
            ) : null}
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[440px_1fr] lg:items-stretch">
          <section className="flex min-h-[640px] flex-col overflow-hidden rounded-2xl border bg-card">
            <div className="border-b bg-muted/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                  <div className="text-sm font-semibold">跟随智能体的屏幕</div>
                  <div className="rounded-full border bg-background px-2 py-0.5 text-[10px] text-muted-foreground">
                    {streamEvents.length > 0 ? "SSE" : "Polling"}
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <button
                    type="button"
                    onClick={() => setAutoFollow((v) => !v)}
                    className={
                      autoFollow
                        ? "rounded-full bg-foreground px-2 py-1 text-[10px] font-medium text-background"
                        : "rounded-full border bg-background px-2 py-1 text-[10px] font-medium"
                    }
                  >
                    {autoFollow ? "Auto-follow: ON" : "Auto-follow: OFF"}
                  </button>
                </div>
              </div>

              <div className="mt-3 rounded-xl border bg-background p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground">已处理 {completedNodes.size} 步</div>
                  <div className="text-xs text-muted-foreground">
                    当前节点：{currentNode ? titleForNode(currentNode) : "—"}
                  </div>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-foreground transition-all"
                    style={{
                      width:
                        nodes.length > 0
                          ? `${Math.min(100, Math.round((completedNodes.size / nodes.length) * 100))}%`
                          : "0%",
                    }}
                  />
                </div>
              </div>
            </div>

            <div ref={nodeListRef} className="flex-1 overflow-auto bg-muted/5 p-4">
              <div className="mb-4 rounded-2xl border bg-background p-4">
                <div className="text-xs font-semibold text-muted-foreground">用户提问</div>
                <div className="mt-2 whitespace-pre-wrap break-words text-sm">{run.data?.input || "—"}</div>
              </div>

              {polledEvents.isLoading && streamEvents.length === 0 ? (
                <div className="space-y-3">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ) : null}

              <Accordion type="single" collapsible value={openNode} onValueChange={(v) => setOpenNode(v)}>
                {nodes.map((n, idx) => {
                  const completed = completedNodes.has(n);
                  const running = !completed && n === currentNode && run.data?.status === "running";
                  const outputs = outputsForNode(n);
                  const cp = latestCheckpointForNode(n);
                  const preview = outputs.length > 0 ? (outputs[outputs.length - 1] || "").trim() : "";
                  const previewLine = preview ? preview.split("\n")[0].slice(0, 140) : "";
                  const isOpen = openNode === n;
                  return (
                    <AccordionItem
                      key={n}
                      value={n}
                      className="mb-4 border-0 bg-transparent px-0"
                    >
                      <AccordionTrigger className="px-0 py-0 hover:no-underline">
                        <div className="flex w-full items-start gap-3">
                          <div className="mt-1 shrink-0">
                            <span
                              className={
                                running
                                  ? "inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"
                                  : completed
                                    ? "inline-flex h-2.5 w-2.5 rounded-full bg-foreground"
                                    : "inline-flex h-2.5 w-2.5 rounded-full bg-muted-foreground/40"
                              }
                            />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div
                              className={
                                isOpen
                                  ? "rounded-2xl border bg-background px-4 py-3 shadow-sm"
                                  : "rounded-2xl border bg-background/70 px-4 py-3"
                              }
                            >
                              <div className="flex items-center justify-between gap-3">
                                <div className="min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="rounded-full border bg-muted/10 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                                      第 {idx + 1} 步
                                    </span>
                                    <span className="truncate text-sm font-semibold">{titleForNode(n)}</span>
                                    {running ? (
                                      <span className="rounded-full bg-foreground px-2 py-0.5 text-[10px] font-medium text-background">
                                        running
                                      </span>
                                    ) : completed ? (
                                      <span className="rounded-full border bg-background px-2 py-0.5 text-[10px] font-medium">
                                        done
                                      </span>
                                    ) : (
                                      <span className="rounded-full border bg-muted/30 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                                        pending
                                      </span>
                                    )}
                                  </div>
                                  {!isOpen ? (
                                    <div className="mt-1 whitespace-normal break-words text-xs text-muted-foreground">
                                      {previewLine
                                        ? previewLine
                                        : cp
                                          ? `checkpoint #${cp.seq} · ${fmtTime(cp.created_at)}`
                                          : "waiting…"}
                                    </div>
                                  ) : null}
                                </div>
                                <div className="shrink-0 text-xs text-muted-foreground">
                                  {cp ? fmtTime(cp.created_at) : ""}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </AccordionTrigger>

                      <AccordionContent className="px-0 pb-0">
                        <div className="ml-[22px] mt-3 space-y-3">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="secondary"
                              className="h-8 px-3 text-xs"
                              disabled={ctlPending}
                              onClick={() => rerunFromNode(n)}
                            >
                              Re-run from this node
                            </Button>
                          </div>

                          <div className="rounded-2xl border bg-muted/10 p-4">
                            <div className="flex items-center justify-between gap-3">
                              <div className="text-xs font-semibold text-muted-foreground">
                                {titleForNode(n)} 输出
                              </div>
                              {cp ? (
                                <div className="text-[10px] text-muted-foreground">
                                  checkpoint #{cp.seq}
                                </div>
                              ) : null}
                            </div>
                            <div className="mt-3 whitespace-pre-wrap break-words text-sm leading-6">
                              {outputs.length > 0 ? outputs[outputs.length - 1] : "暂无输出。"}
                            </div>
                          </div>

                          {outputs.length > 1 ? (
                            <details className="rounded-2xl border bg-background p-4">
                              <summary className="cursor-pointer text-xs font-semibold text-muted-foreground">
                                查看历史输出（{outputs.length - 1} 条）
                              </summary>
                              <div className="mt-3 space-y-3">
                                {outputs.slice(0, -1).map((t, outIdx) => (
                                  <div key={`${n}-out-${outIdx}`} className="rounded-2xl border bg-muted/10 p-4">
                                    <div className="text-[10px] text-muted-foreground">output {outIdx + 1}</div>
                                    <div className="mt-2 whitespace-pre-wrap break-words text-sm leading-6">{t}</div>
                                  </div>
                                ))}
                              </div>
                            </details>
                          ) : null}

                          {cp ? (
                            <details className="rounded-2xl border bg-background p-4">
                              <summary className="cursor-pointer text-xs font-semibold text-muted-foreground">
                                查看节点详情（state JSON）
                              </summary>
                              <div className="mt-3 h-56">
                                <LineNumberedCode value={JSON.stringify(cp.state, null, 2)} />
                              </div>
                            </details>
                          ) : null}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>

              {nodes.length === 0 ? (
                <div className="rounded-2xl border bg-background p-4 text-sm text-muted-foreground">等待节点开始…</div>
              ) : null}
            </div>

            <div className="border-t bg-background p-4">
              <div className="text-xs font-semibold text-muted-foreground">最终输出</div>
              <div className="mt-2 whitespace-pre-wrap break-words text-sm text-muted-foreground">
                {run.data?.output_text || "No output yet."}
              </div>
              {run.data?.error ? <div className="mt-3 text-sm text-destructive">{run.data.error}</div> : null}
            </div>
          </section>

          <section className="flex min-h-[640px] flex-col overflow-hidden rounded-2xl border border-sky-200 bg-card shadow-[0_0_0_3px_rgba(56,189,248,0.15)]">
            <div className="border-b bg-muted/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-semibold">代码工作区</div>
                  <div className="mt-1 truncate text-xs text-muted-foreground">
                    {selected
                      ? selected.name
                      : selectedLivePath
                        ? selectedLivePath
                        : liveFiles.length > 0
                          ? "Live files…"
                          : "Waiting for artifacts…"}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    className="h-8 px-3 text-xs"
                    disabled={!artifactDetail.data && !selectedLivePath}
                    onClick={async () => {
                      const live = liveFiles.find((f) => f.path === selectedLivePath) ?? null;
                      const txt = live
                        ? live.content
                        : artifactDetail.data?.content_text
                          ? artifactDetail.data.content_text
                          : artifactDetail.data?.content_json
                            ? JSON.stringify(artifactDetail.data.content_json, null, 2)
                            : "";
                      try {
                        await navigator.clipboard.writeText(txt);
                        setCopied(true);
                        window.setTimeout(() => setCopied(false), 900);
                      } catch {
                        // ignore
                      }
                    }}
                  >
                    {copied ? "Copied" : "Copy"}
                  </Button>
                  <Button
                    variant="secondary"
                    className="h-8 px-3 text-xs"
                    disabled={!selectedArtifactId}
                    onClick={async () => {
                      if (!selectedArtifactId) return;
                      const res = await fetch(`/api/runs/${runId}/artifacts/${selectedArtifactId}/download`, {
                        credentials: "include",
                      });
                      if (!res.ok) return;
                      const blob = await res.blob();
                      const a = allArtifacts.find((x) => x.id === selectedArtifactId);
                      const name = a?.name || `artifact.${extFromMime(a?.mime_type || "text/plain")}`;
                      const url = URL.createObjectURL(blob);
                      const link = document.createElement("a");
                      link.href = url;
                      link.download = name;
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    Download
                  </Button>
                  <Button
                    variant="secondary"
                    className="h-8 px-3 text-xs"
                    onClick={() => {
                      window.location.href = `/api/runs/${runId}/workspace.zip`;
                    }}
                  >
                    Export ZIP
                  </Button>
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2">
                  <input
                    value={fileQuery}
                    onChange={(e) => setFileQuery(e.target.value)}
                    placeholder="搜索文件…"
                    className="h-9 w-64 rounded-xl border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-foreground/20"
                  />
                  <button
                    type="button"
                    onClick={() => setShowMeta((v) => !v)}
                    className={
                      showMeta
                        ? "rounded-full bg-foreground px-3 py-1 text-xs font-medium text-background"
                        : "rounded-full border bg-background px-3 py-1 text-xs font-medium"
                    }
                  >
                    {showMeta ? "隐藏元文件" : "显示元文件"}
                  </button>
                </div>
                <div className="text-xs text-muted-foreground">{arts.isLoading ? "Loading…" : ""}</div>
              </div>
            </div>

            <div className="grid flex-1 grid-cols-1 overflow-hidden md:grid-cols-[280px_1fr]">
              <aside className="overflow-auto border-r bg-background p-3">
                {arts.isLoading ? <Skeleton className="h-6 w-full" /> : null}

                <div className="rounded-xl border bg-muted/10 p-2 text-xs text-muted-foreground">文件</div>
                <div className="mt-2 space-y-1">
                  {codeArtifacts.length > 0 ? (
                    tree.children.map((n) => renderTreeNode(n, 0))
                  ) : liveFiles.length > 0 ? (
                    liveFiles
                      .filter((f) => (fileQuery.trim() ? f.path.toLowerCase().includes(fileQuery.trim().toLowerCase()) : true))
                      .map((f) => {
                        const active = f.path === selectedLivePath;
                        return (
                          <button
                            key={f.path}
                            type="button"
                            onClick={() => setSelectedLivePath(f.path)}
                            className={
                              active
                                ? "flex w-full items-center justify-between rounded-lg bg-foreground px-2 py-1.5 text-left text-xs text-background"
                                : "flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-xs hover:bg-muted/40"
                            }
                            title={f.path}
                          >
                            <span className="truncate">{f.path}</span>
                            <span className="ml-2 text-[10px] opacity-70">{mimeFromPath(f.path).split("/").pop()}</span>
                          </button>
                        );
                      })
                  ) : null}

                  {arts.data && codeArtifacts.length === 0 ? (
                    <div className="px-2 py-2 text-xs text-muted-foreground">Waiting for artifacts…</div>
                  ) : null}
                </div>

                {showMeta && metaArtifacts.length > 0 ? (
                  <div className="mt-4">
                    <div className="rounded-xl border bg-muted/10 p-2 text-xs text-muted-foreground">元文件</div>
                    <div className="mt-2 space-y-1">
                      {metaArtifacts.map((a) => (
                        <button
                          key={a.id}
                          type="button"
                          onClick={() => setSelectedArtifactId(a.id)}
                          className={
                            a.id === selectedArtifactId
                              ? "flex w-full items-center justify-between rounded-lg bg-foreground px-2 py-1.5 text-left text-xs text-background"
                              : "flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-xs hover:bg-muted/40"
                          }
                          title={a.name}
                        >
                          <span className="truncate">{a.name}</span>
                          <span className="ml-2 text-[10px] opacity-70">{a.mime_type.split("/").pop()}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </aside>

              <div className="flex min-w-0 flex-col overflow-hidden bg-background p-3">
                {codeArtifacts.length > 0 || metaArtifacts.length > 0 ? (
                  <Tabs value={selectedArtifactId} onValueChange={setSelectedArtifactId}>
                    <div className="flex items-center justify-between gap-3">
                      <TabsList variant="line" className="max-w-full overflow-auto">
                        {openArtifacts.map((a) => (
                          <TabsTrigger key={a.id} value={a.id} className="text-xs">
                            {a.name}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                    </div>

                    {openTabs.map((id) => (
                      <TabsContent key={id} value={id} className="mt-3 h-full">
                        {id === selectedArtifactId && artifactDetail.isLoading ? (
                          <Skeleton className="h-20 w-full" />
                        ) : null}
                        {id === selectedArtifactId && artifactDetail.data ? (
                          <CodeEditor
                            path={selected?.name || ""}
                            value={
                              artifactDetail.data.content_text
                                ? artifactDetail.data.content_text
                                : artifactDetail.data.content_json
                                  ? JSON.stringify(artifactDetail.data.content_json, null, 2)
                                  : ""
                            }
                            readOnly
                            height={560}
                          />
                        ) : null}
                      </TabsContent>
                    ))}
                  </Tabs>
                ) : liveFiles.length > 0 ? (
                  <div className="h-full">
                    <div className="rounded-xl border bg-muted/10 px-3 py-2 text-xs text-muted-foreground">
                      Live rendering from checkpoints (artifacts will appear when run finishes).
                    </div>
                    <div className="mt-3">
                      <CodeEditor
                        path={selectedLivePath || "live.txt"}
                        value={liveFiles.find((f) => f.path === selectedLivePath)?.content ?? ""}
                        readOnly
                        height={560}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border bg-muted/10 p-4 text-sm text-muted-foreground">
                    Waiting for artifacts…
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
