import Link from "next/link";

const posts = [
  {
    slug: "example-post",
    title: "Example Blog Post",
    excerpt: "This is a placeholder. Blog content is not specified in UI docs.",
  },
  {
    slug: "another-post",
    title: "Another Post",
    excerpt: "Selecting an article should open its detailed page.",
  },
];

export default function BlogHomePage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Blog</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        A small set of sample posts for local development.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2">
        {posts.map((p) => (
          <Link
            key={p.slug}
            href={`/blog/${p.slug}`}
            className="rounded-xl border bg-card p-6 hover:bg-muted/30"
          >
            <div className="text-lg font-semibold">{p.title}</div>
            <p className="mt-2 text-sm text-muted-foreground">{p.excerpt}</p>
            <div className="mt-4 text-sm underline">Read</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
