import Link from "next/link";

import { isExternalHref, links } from "@/lib/links";

const footer = {
  product: [
    { href: "/", label: "Templates" }, // Templates are on the home page per UI docs
    { href: "/pricing", label: "Pricing" },
    { href: links.docs, label: "Docs" },
  ],
  resources: [
    { href: "/blog", label: "Blog" },
    { href: "/use-cases", label: "Use Cases" },
    { href: "/videos", label: "Videos" },
    { href: links.github, label: "GitHub" },
  ],
  about: [
    { href: "/terms", label: "Terms" },
    { href: "/privacy", label: "Privacy" },
  ],
  community: [
    { href: "/affiliate", label: "Affiliates" },
    { href: "/explorer-program", label: "Explorer Program" },
    { href: "/help-center", label: "Help Center" },
  ],
};

export function SiteFooter() {
  return (
    <footer className="border-t bg-background">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 px-4 py-10 md:grid-cols-5">
        <div className="col-span-2 md:col-span-1">
          <div className="text-sm font-semibold">Atoms</div>
          <p className="mt-2 text-sm text-muted-foreground">
            Footer link structure derived from UI docs.
          </p>
        </div>

        <div>
          <div className="text-xs font-semibold text-muted-foreground">
            Product
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {footer.product.map((l) => (
              <li key={l.label}>
                {isExternalHref(l.href) ? (
                  <a
                    className="hover:underline"
                    href={l.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {l.label}
                  </a>
                ) : (
                  <Link className="hover:underline" href={l.href}>
                    {l.label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="text-xs font-semibold text-muted-foreground">
            Resources
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {footer.resources.map((l) => (
              <li key={l.label}>
                {isExternalHref(l.href) ? (
                  <a
                    className="hover:underline"
                    href={l.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {l.label}
                  </a>
                ) : (
                  <Link className="hover:underline" href={l.href}>
                    {l.label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="text-xs font-semibold text-muted-foreground">
            About
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {footer.about.map((l) => (
              <li key={l.label}>
                {isExternalHref(l.href) ? (
                  <a
                    className="hover:underline"
                    href={l.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {l.label}
                  </a>
                ) : (
                  <Link className="hover:underline" href={l.href}>
                    {l.label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="text-xs font-semibold text-muted-foreground">
            Community
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {footer.community.map((l) => (
              <li key={l.label}>
                {isExternalHref(l.href) ? (
                  <a
                    className="hover:underline"
                    href={l.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {l.label}
                  </a>
                ) : (
                  <Link className="hover:underline" href={l.href}>
                    {l.label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="border-t py-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between">
          <div>© {new Date().getFullYear()} Atoms</div>
          <div>Language: English</div>
        </div>
      </div>
    </footer>
  );
}
