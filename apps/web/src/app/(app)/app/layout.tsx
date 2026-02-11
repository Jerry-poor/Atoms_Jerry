import { RequireAuth } from "@/components/require-auth";

export default function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <RequireAuth>
      <div className="min-h-dvh bg-background text-foreground">
        {children}
      </div>
    </RequireAuth>
  );
}
