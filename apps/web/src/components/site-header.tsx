"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { isExternalHref, links } from "@/lib/links";

const resources = [
  { href: "/blog", label: "Blog" },
  { href: "/use-cases", label: "Use Cases" },
  { href: "/videos", label: "Videos" },
  { href: "/affiliate", label: "Affiliates" },
  { href: "/explorer-program", label: "Explorer Program" },
  { href: "/help-center", label: "Help Center" },
  { href: links.community, label: "Community" },
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link
          href="/"
          className="text-lg font-semibold tracking-tight text-foreground"
        >
          Atoms
        </Link>

        <nav className="flex items-center gap-2">
          <Link href="/pricing" className="px-3 py-2 text-sm text-foreground">
            Pricing
          </Link>

          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <button className="px-3 py-2 text-sm text-foreground">
                Resources
              </button>
            </DialogTrigger>
            <DialogContent className="h-[90vh] max-w-4xl p-0">
              <DialogHeader className="p-6 pb-0">
                <DialogTitle>Resources</DialogTitle>
              </DialogHeader>

              <div className="grid h-full grid-cols-1 gap-0 p-6 pt-4 md:grid-cols-2">
                <div className="space-y-2">
                  {resources.map((r) =>
                    isExternalHref(r.href) ? (
                      <a
                        key={r.href}
                        href={r.href}
                        className="block rounded-md px-3 py-2 text-sm hover:bg-muted"
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => setOpen(false)}
                      >
                        {r.label}
                      </a>
                    ) : (
                      <Link
                        key={r.href}
                        href={r.href}
                        className="block rounded-md px-3 py-2 text-sm hover:bg-muted"
                        onClick={() => setOpen(false)}
                      >
                        {r.label}
                      </Link>
                    ),
                  )}
                </div>

                <div className="mt-6 md:mt-0 md:pl-6">
                  <Separator className="mb-6 md:hidden" />
                  <div className="rounded-xl border bg-card p-5">
                    <div className="text-xs text-muted-foreground">
                      Highlighted article preview (from UI docs)
                    </div>
                    <div className="mt-2 text-base font-semibold">
                      Building with Atoms
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      A quick walkthrough of how Atoms turns a prompt into a
                      runnable workflow.
                    </p>
                    <div className="mt-4">
                      <Button asChild>
                        <Link href="/blog/example-post">Read Article</Link>
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <Link href="/login" className="px-3 py-2 text-sm text-foreground">
            Log in
          </Link>
          <Button asChild>
            <Link href="/signup">Sign up</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
