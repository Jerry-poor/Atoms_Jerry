export default function HelpCenterPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Help Center</h1>
      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
        Search guides and troubleshooting tips.
      </p>

      <div className="mt-8 max-w-lg">
        <input
          className="h-11 w-full rounded-md border bg-background px-3 text-sm"
          placeholder="Search help articles..."
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-3 md:grid-cols-2">
        {["Getting started", "Billing", "Account"].map((t) => (
          <div key={t} className="rounded-xl border bg-card p-6">
            <div className="text-base font-semibold">{t}</div>
            <p className="mt-2 text-sm text-muted-foreground">
              Placeholder category card.
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
