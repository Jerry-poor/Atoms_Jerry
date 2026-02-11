import Link from "next/link";
import { notFound } from "next/navigation";

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

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = posts.find((p) => p.slug === params.slug);
  if (!post) notFound();

  return (
    <article className="mx-auto max-w-3xl px-4 py-12">
      <Link href="/blog" className="text-sm underline">
        Back to Blog
      </Link>

      <h1 className="mt-4 text-3xl font-semibold tracking-tight">
        {post.title}
      </h1>
      <p className="mt-3 text-sm text-muted-foreground">{post.excerpt}</p>

      <div className="prose prose-neutral mt-8 max-w-none">
        <p>This is a sample post used for local development.</p>
      </div>
    </article>
  );
}
