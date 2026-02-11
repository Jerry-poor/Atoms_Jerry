export const links = {
  docs: process.env.NEXT_PUBLIC_DOCS_URL ?? "/docs",
  github: process.env.NEXT_PUBLIC_GITHUB_URL ?? "https://github.com",
  community: process.env.NEXT_PUBLIC_COMMUNITY_URL ?? "https://atoms.dev",
} as const;

export function isExternalHref(href: string): boolean {
  return /^https?:\/\//.test(href);
}
