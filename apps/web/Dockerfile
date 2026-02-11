FROM node:24-bookworm-slim

WORKDIR /repo

RUN corepack enable

# Workspace root metadata
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml /repo/

# Workspace packages needed by @atoms/web
COPY packages/shared /repo/packages/shared
COPY apps/web /repo/apps/web

# Install only the web app and its workspace deps.
RUN pnpm install --filter @atoms/web... --frozen-lockfile

WORKDIR /repo/apps/web
EXPOSE 13000

CMD ["pnpm", "exec", "next", "dev", "-p", "13000", "-H", "0.0.0.0"]
