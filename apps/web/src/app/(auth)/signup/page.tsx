"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSignupWithPassword } from "@/lib/auth";
import { ApiError } from "@/lib/api";

function getSignupErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return "Sign up failed. Please try again.";

  if (error.status === 422) {
    const body = error.body as { detail?: Array<{ loc?: Array<string | number>; msg?: string }> };
    const first = body?.detail?.[0];
    if (!first) return "Invalid form fields. Please check your inputs.";

    const path = Array.isArray(first.loc) ? first.loc.join(".") : "field";
    return `Validation failed (${path}): ${first.msg ?? "invalid value"}.`;
  }

  if (error.status === 400) {
    const body = error.body as { detail?: string };
    return body?.detail ?? "Sign up failed. Please check your email/username.";
  }

  return "Sign up failed. Please try again.";
}

export default function SignupPage() {
  const router = useRouter();
  const oauthGoogle = "/api/auth/oauth/google/start";
  const oauthGithub = "/api/auth/oauth/github/start";

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const signup = useSignupWithPassword();

  const mismatch = confirm.length > 0 && confirm !== password;
  const passwordTooShort = password.length > 0 && password.length < 8;
  const invalidUsername = username.trim().length === 0;
  const invalidEmail = email.trim().length === 0;
  const invalidForm = mismatch || passwordTooShort || invalidUsername || invalidEmail;

  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Sign Up</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Registration form per UI docs: username/email/password/confirm + Google
        OAuth.
      </p>

      <div className="mt-6 space-y-2">
        <Button asChild className="w-full">
          <a href={oauthGoogle}>Sign up with Google</a>
        </Button>
        <Button asChild variant="secondary" className="w-full">
          <a href={oauthGithub}>Sign up with GitHub</a>
        </Button>
      </div>

      <div className="mt-6 space-y-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            Username
          </label>
          <Input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="jerry"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            Email address
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
          {passwordTooShort ? (
            <div className="mt-1 text-xs text-destructive">
              Password must be at least 8 characters.
            </div>
          ) : null}
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            Confirm password
          </label>
          <Input
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Confirm password"
            type="password"
          />
          {mismatch ? (
            <div className="mt-1 text-xs text-destructive">
              Passwords do not match.
            </div>
          ) : null}
        </div>

        <Button
          className="w-full"
          disabled={signup.isPending || invalidForm}
          onClick={async () => {
            const u = await signup.mutateAsync({ username, email, password });
            if (u) router.push("/app");
          }}
        >
          Create account
        </Button>

        <div className="text-xs text-muted-foreground">
          By creating an account, you agree to the{" "}
          <Link href="/terms" className="underline">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="underline">
            Privacy Policy
          </Link>
          .
        </div>

        {signup.isError ? (
          <div className="text-sm text-destructive">
            {getSignupErrorMessage(signup.error)}
          </div>
        ) : null}
      </div>

      <div className="mt-6 text-sm">
        Already have an account?{" "}
        <Link href="/login" className="underline">
          Log in now
        </Link>
      </div>
    </div>
  );
}
