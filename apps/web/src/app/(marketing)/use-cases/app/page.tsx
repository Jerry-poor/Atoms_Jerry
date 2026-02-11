import Link from "next/link";

export default function UseCasesAppPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <Link href="/use-cases" className="text-sm underline">
        Back to Use Cases
      </Link>
      <h1 className="mt-4 text-3xl font-semibold tracking-tight">
        Use Cases (APP & Deep Research)
      </h1>
      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
        A focused landing page for app builds and deeper research workflows.
      </p>
    </div>
  );
}
