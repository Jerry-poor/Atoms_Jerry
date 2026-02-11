import Link from "next/link";

export default function ExplorerProgramPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">
        Explorer Program
      </h1>
      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
        UI docs note an Apply button that leads to an application flow which may
        require login.
      </p>

      <div className="mt-8">
        <Link
          href="/app"
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground"
        >
          Apply
        </Link>
      </div>
    </div>
  );
}
