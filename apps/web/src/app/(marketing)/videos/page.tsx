import Link from "next/link";

const videos = [
  { id: "v1", title: "Intro Video (placeholder)" },
  { id: "v2", title: "Building a site (placeholder)" },
];

export default function VideosPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Videos</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Watch tutorials and product walkthroughs.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2">
        {videos.map((v) => (
          <Link
            key={v.id}
            href="/app"
            className="rounded-xl border bg-card p-6 hover:bg-muted/30"
          >
            <div className="text-lg font-semibold">{v.title}</div>
            <p className="mt-2 text-sm text-muted-foreground">
              Click leads to app area if login is required; otherwise would open
              the video.
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
