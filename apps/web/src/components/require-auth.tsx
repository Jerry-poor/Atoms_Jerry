"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useMe } from "@/lib/auth";
import { Skeleton } from "@/components/ui/skeleton";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const path = usePathname();
  const me = useMe();

  useEffect(() => {
    if (me.isLoading) return;
    if (me.data) return;
    const returnTo = encodeURIComponent(path || "/app");
    router.replace(`/login?returnTo=${returnTo}`);
  }, [me.isLoading, me.data, router, path]);

  if (me.isLoading) {
    return (
      <div className="p-6">
        <div className="space-y-3">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-5 w-96" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (!me.data) return null;
  return <>{children}</>;
}
