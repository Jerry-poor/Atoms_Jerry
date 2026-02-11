"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { useLogout } from "@/lib/auth";

export function AppTopNav() {
  const router = useRouter();
  const logout = useLogout();

  return (
    <nav className="flex items-center gap-2">
      <Link href="/app/runs" className="px-3 py-2 text-sm">
        Runs
      </Link>
      <Button
        variant="secondary"
        onClick={async () => {
          await logout.mutateAsync();
          router.push("/");
        }}
        disabled={logout.isPending}
      >
        Logout
      </Button>
    </nav>
  );
}
