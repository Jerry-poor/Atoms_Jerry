"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

type TemplateCategory = "All" | "Website" | "App";

type Template = {
  id: string;
  title: string;
  category: Exclude<TemplateCategory, "All">;
  prompt: string;
  description: string;
};

const templates: Template[] = [
  {
    id: "t-website-landing",
    title: "Landing Page",
    category: "Website",
    prompt:
      "Build a modern landing page for a new product, with pricing and FAQ.",
    description:
      "A clean marketing site layout with sections and calls to action.",
  },
  {
    id: "t-website-docs",
    title: "Docs Site",
    category: "Website",
    prompt:
      "Create a docs site structure with a sidebar and a few example pages.",
    description: "A lightweight documentation layout to start from.",
  },
  {
    id: "t-app-runner",
    title: "Workflow Runner",
    category: "App",
    prompt:
      "Create an app where users can submit a task and view run status, events, and artifacts.",
    description:
      "A simple app shell that matches the Runs workflow in this repo.",
  },
  {
    id: "t-app-dashboard",
    title: "Dashboard",
    category: "App",
    prompt: "Build a dashboard with auth, navigation, and a few example pages.",
    description: "A starter dashboard layout for authenticated users.",
  },
];

export function HomeClient() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [tab, setTab] = useState<TemplateCategory>("All");

  const visibleTemplates = useMemo(() => {
    if (tab === "All") return templates;
    return templates.filter((t) => t.category === tab);
  }, [tab]);

  function goToBuilder(p: string) {
    const q = p.trim();
    router.push(`/app?prompt=${encodeURIComponent(q)}`);
  }

  return (
    <div>
      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
            Build anything at the speed of thought
          </h1>
          <p className="mt-4 text-base text-muted-foreground md:text-lg">
            AI-powered web/app builder for fast prototyping and automation.
          </p>

          <div className="mt-8 flex flex-col items-stretch gap-3 sm:flex-row sm:justify-center">
            <input
              className="h-11 flex-1 rounded-md border bg-background px-3 text-sm"
              placeholder="Describe what you want to build..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <button
              type="button"
              className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60"
              disabled={prompt.trim().length === 0}
              onClick={() => goToBuilder(prompt)}
            >
              Start
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16">
        <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
          <div>
            <h2 className="text-xl font-semibold">Templates</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Pick a starter and jump into the builder.
            </p>
          </div>
          <Link href="/pricing" className="text-sm underline">
            See pricing
          </Link>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {(["All", "Website", "App"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={
                t === tab
                  ? "rounded-full bg-foreground px-3 py-1 text-xs font-medium text-background"
                  : "rounded-full border px-3 py-1 text-xs font-medium text-foreground hover:bg-muted"
              }
            >
              {t}
            </button>
          ))}
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          {visibleTemplates.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => goToBuilder(t.prompt)}
              className="text-left rounded-xl border bg-card p-5 hover:bg-muted/30"
            >
              <div className="text-xs text-muted-foreground">{t.category}</div>
              <div className="mt-2 text-base font-semibold">{t.title}</div>
              <p className="mt-1 text-sm text-muted-foreground">
                {t.description}
              </p>
              <div className="mt-4 text-sm underline">Use template</div>
            </button>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16">
        <h2 className="text-xl font-semibold">Pricing preview</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Simple plans for individuals and teams.
        </p>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          {["Free", "Pro", "Max"].map((p) => (
            <div key={p} className="rounded-xl border bg-card p-5">
              <div className="text-base font-semibold">{p}</div>
              <div className="mt-2 text-sm text-muted-foreground">
                Compare features and pick the plan that fits.
              </div>
              <div className="mt-4">
                <Link
                  href="/signup"
                  className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
                >
                  Get Started
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20">
        <h2 className="text-xl font-semibold">FAQ</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Common questions about how Atoms works.
        </p>
        <div className="mt-6 space-y-3">
          {[
            "What is Atoms?",
            "Do I need to code?",
            "How do I get started?",
          ].map((q) => (
            <details key={q} className="rounded-lg border bg-card px-4 py-3">
              <summary className="cursor-pointer text-sm font-medium">
                {q}
              </summary>
              <p className="mt-2 text-sm text-muted-foreground">
                This section is being expanded. For now, use the app to explore
                the workflow runner.
              </p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
