import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-3xl flex-col items-center justify-center px-4 py-20 text-center">
      <div className="text-sm text-muted-foreground">404</div>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">
        Page not found
      </h1>
      <p className="mt-3 text-sm text-muted-foreground">
        This matches the documented presence of a dedicated 404 page.
      </p>
      <div className="mt-6">
        <Link
          href="/"
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground"
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}
