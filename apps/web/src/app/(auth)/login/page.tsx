"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLoginWithPassword } from "@/lib/auth";

function LoginPageContent() {
  const router = useRouter();
  const sp = useSearchParams();
  const returnTo = sp.get("returnTo") || "/app";
  const oauthGoogle = "/api/auth/oauth/google/start";
  const oauthGithub = "/api/auth/oauth/github/start";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const login = useLoginWithPassword();

  return (
    <div className="mx-auto grid max-w-6xl grid-cols-1 gap-0 px-4 py-10 md:grid-cols-2 md:gap-6">
      <section className="rounded-2xl border bg-card p-8">
        <h1 className="text-2xl font-semibold tracking-tight">Login</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Login form per UI docs: Google OAuth + email/password.
        </p>

        <div className="mt-6 space-y-2">
          <Button asChild className="w-full">
            <a href={oauthGoogle}>Log in with Google</a>
          </Button>
          <Button asChild variant="secondary" className="w-full">
            <a href={oauthGithub}>Log in with GitHub</a>
          </Button>
        </div>

        <div className="mt-6 space-y-3">
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              Email
            </label>
            <Input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              type="email"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              Password
            </label>
            <Input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              type="password"
            />
          </div>

          <Button
            className="w-full"
            disabled={login.isPending}
            onClick={async () => {
              const u = await login.mutateAsync({ email, password });
              if (u) router.push(returnTo);
            }}
          >
            Log in
          </Button>

          {login.isError ? (
            <div className="text-sm text-destructive">
              Login failed. Check your credentials.
            </div>
          ) : null}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
          <Link href="/signup" className="underline">
            Create your account
          </Link>
          <Link href="/forgot-password" className="underline">
            Forgot password?
          </Link>
        </div>
      </section>

      <aside className="mt-6 rounded-2xl border bg-gradient-to-br from-muted to-background p-8 md:mt-0">
        <div className="text-xs text-muted-foreground">Right panel</div>
        <h2 className="mt-2 text-xl font-semibold">
          Promotional graphic (placeholder)
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          UI docs show a split page with a promotional graphic and tagline. The
          exact content may vary by release.
        </p>
      </aside>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-xl px-4 py-12 text-sm text-muted-foreground">Loading...</div>}>
      <LoginPageContent />
    </Suspense>
  );
}
