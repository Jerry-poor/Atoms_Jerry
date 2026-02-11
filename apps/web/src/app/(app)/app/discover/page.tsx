import Link from "next/link";

import { AppTopNav } from "@/components/top-nav";

export default function DiscoverPage() {
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
        <h1 className="text-2xl font-semibold tracking-tight">发现</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          这里是占位页面。后续可以放模板市场、示例项目、热门工作流等内容。
        </p>
      </main>
    </div>
  );
}

