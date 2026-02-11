"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRequestPasswordReset } from "@/lib/auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);

  const requestReset = useRequestPasswordReset();

  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Forgot password</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Enter your email address and we will send you a password reset link.
        (Email delivery is not implemented in this MVP; in dev/test we return a
        reset token to complete the flow.)
      </p>

      <div className="mt-6 space-y-3">
        <Input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          type="email"
        />
        <Button
          className="w-full"
          disabled={requestReset.isPending || email.trim().length === 0}
          onClick={async () => {
            try {
              const res = await requestReset.mutateAsync({
                email: email.trim(),
              });
              setResetToken(res.reset_token ?? null);
              setSubmitted(true);
            } catch {
              // handled via requestReset.isError
            }
          }}
        >
          {requestReset.isPending ? "Sending..." : "Send reset link"}
        </Button>
        {requestReset.isError ? (
          <div className="text-sm text-destructive">
            Could not request a reset link. Try again later.
          </div>
        ) : null}
        {submitted ? (
          <div className="space-y-2 text-sm text-muted-foreground">
            <div>
              If an account exists for {email || "that email"}, you will receive
              a reset email.
            </div>
            {resetToken ? (
              <div className="rounded-md border bg-card p-3">
                <div className="text-xs font-medium text-foreground">
                  Reset token (dev/test only)
                </div>
                <div className="mt-1 break-all font-mono text-xs text-muted-foreground">
                  {resetToken}
                </div>
                <div className="mt-2">
                  <Link
                    className="text-xs underline"
                    href={`/reset-password?token=${encodeURIComponent(resetToken)}`}
                  >
                    Continue to reset password
                  </Link>
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
