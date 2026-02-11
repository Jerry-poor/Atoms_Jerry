"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useResetPassword } from "@/lib/auth";

function ResetPasswordPageContent() {
  const router = useRouter();
  const token = useMemo(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("token") || "";
  }, []);

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);

  const reset = useResetPassword();

  const mismatch = confirm.length > 0 && confirm !== password;
  const missingToken = token.trim().length === 0;

  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Reset password</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Enter a new password to complete the reset.
      </p>

      {missingToken ? (
        <div className="mt-6 rounded-md border bg-card p-4 text-sm text-muted-foreground">
          Missing reset token. Return to{" "}
          <Link href="/forgot-password" className="underline">
            Forgot password
          </Link>
          .
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              New password
            </label>
            <Input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              placeholder="New password"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              Confirm password
            </label>
            <Input
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              type="password"
              placeholder="Confirm password"
            />
            {mismatch ? (
              <div className="mt-1 text-xs text-destructive">
                Passwords do not match.
              </div>
            ) : null}
          </div>

          <Button
            className="w-full"
            disabled={reset.isPending || mismatch || password.length < 8}
            onClick={async () => {
              try {
                await reset.mutateAsync({
                  token,
                  new_password: password,
                });
                setDone(true);
                router.replace("/login");
              } catch {
                // handled via reset.isError
              }
            }}
          >
            {reset.isPending ? "Resetting..." : "Reset password"}
          </Button>

          {reset.isError ? (
            <div className="text-sm text-destructive">
              Reset failed. The token may be invalid or expired.
            </div>
          ) : null}

          {done ? (
            <div className="text-sm text-muted-foreground">
              Password reset successful. Redirecting to login...
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  return <ResetPasswordPageContent />;
}
