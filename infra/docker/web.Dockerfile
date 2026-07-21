# Build from the repo root:
#   docker build -f infra/docker/web.Dockerfile .
# NOTE: requires web/ (Workflow D). Placeholder until it lands.

FROM node:20-slim AS deps
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci

FROM node:20-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY web/ .
RUN npm run build

FROM node:20-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN useradd --create-home appuser
COPY --from=build --chown=appuser /app ./
USER appuser
EXPOSE 3000
CMD ["npm", "run", "start"]
