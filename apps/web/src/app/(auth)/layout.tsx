import Link from "next/link";

export default function AuthLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-dvh bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-6xl items-center px-4">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            Atoms
          </Link>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
