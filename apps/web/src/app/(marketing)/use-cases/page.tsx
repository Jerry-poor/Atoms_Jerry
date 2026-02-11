import Link from "next/link";

const useCases = [
  { href: "/use-cases/app", title: "APP & Deep Research" },
  { href: "/use-cases", title: "Website (placeholder)" },
  { href: "/use-cases", title: "Landing pages (placeholder)" },
];

export default function UseCasesPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Use Cases</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Explore a few common ways teams use Atoms.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        {useCases.map((u, i) => (
          <Link
            key={i}
            href={u.href}
            className="rounded-xl border bg-card p-6 hover:bg-muted/30"
          >
            <div className="text-lg font-semibold">{u.title}</div>
            <p className="mt-2 text-sm text-muted-foreground">
              Click navigates to details (if applicable).
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
