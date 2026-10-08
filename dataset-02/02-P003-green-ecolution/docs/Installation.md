## Quick Start

For a development setup with hot reload:

```bash
just infra-up    # Start infra (Postgres, Keycloak, Traefik, Valhalla, Streamlet)
just migrate-up  # Apply database migrations
just run-dev     # Run backend (hot reload) + frontend
```

Open [http://localhost:3000](http://localhost:3000).

To run everything in containers with a single command (infra + app + migrations), use `just run-docker` instead.

### With HTTPS (Let's Encrypt)

For valid TLS certificates (required for PWA testing on mobile), you need a domain with DNS API access on [Porkbun](https://porkbun.com). Either ask the `green-ecolution.dev` domain owner for API keys, or register your own domain on Porkbun and set `DOMAIN=your-domain.dev` in `.env`.

1. Copy `.env.example` to `.env` and add your Porkbun API keys (and optionally `DOMAIN`)
2. Create DNS records: `just dns-setup`
3. Start infra: `just infra-up`
4. Apply migrations: `just migrate-up`
5. Start dev environment: `just run-dev`

Open `https://<your-ip>.green-ecolution.dev:3443` (or your custom domain).

## Setup

### Requirements

- Rust toolchain (rustup, includes cargo)
- WASM target (`rustup target add wasm32-unknown-unknown`) — required for WASM builds used by the domain bindings
- Node.js + pnpm (`corepack enable`)
- Docker + Docker Compose
- [`just`](https://github.com/casey/just) — command runner (`cargo install just`)
- [`wasm-pack`](https://github.com/rustwasm/wasm-pack) (`cargo install wasm-pack`) — builds the domain WASM bindings, required by `just build`
- [`bacon`](https://github.com/Canop/bacon) (`cargo install bacon`) — live reload, required by `just run-dev`
- [`sqlx-cli`](https://crates.io/crates/sqlx-cli) (`cargo install sqlx-cli --no-default-features --features rustls,postgres`) for migrations and offline-cache regeneration

### Installation

```bash
just setup       # cargo fetch + pnpm install + build frontend workspace packages + domain WASM
just build       # Build frontend + backend
```

### Common Commands

| Command | Description |
|---------|-------------|
| `just run-dev` | Backend + frontend dev via Traefik (bacon live reload) |
| `just run-docker` | Full stack via Docker Compose |
| `just infra-up` | Start infrastructure only |
| `just test` | Run all tests (Rust workspace + frontend) |
| `just lint` | Lint Rust workspace + frontend |
| `just generate-sqlx` | Refresh sqlx offline query cache |
| `just migrate-up` | Apply database migrations |
| `just migrate-new <name>` | Create new migration |
| `just seed-up` | Apply seed data on top of the migrated DB |

> For a reproducible dev environment, you can also use `nix develop`.

### Services

`just infra-up` starts these services and routes them via Traefik. The Backend API is not part of the infra stack — it becomes available once you run `just run-dev` or `just run-docker`.

**Without Porkbun keys** (HTTP on port 3000):

| Service | URL |
|---------|-----|
| Backend API | <http://localhost:3000/api> (needs `run-dev` / `run-docker`) |
| Keycloak | <http://auth.localhost:3000> |
| pgAdmin | <http://pgadmin.localhost:3000> |
| Valhalla | <http://valhalla.localhost:3000> |
| Streamlet | <http://streamlet.localhost:3000> |

**With Porkbun keys** (HTTPS on port 3443, valid Let's Encrypt certs):

| Service | URL |
|---------|-----|
| Backend API | `https://<ip>.green-ecolution.dev:3443/api` (needs `run-dev` / `run-docker`) |
| Keycloak | `https://auth.<ip>.green-ecolution.dev:3443` |
| pgAdmin | `https://pgadmin.<ip>.green-ecolution.dev:3443` |
| Valhalla | `https://valhalla.<ip>.green-ecolution.dev:3443` |
| Streamlet | `https://streamlet.<ip>.green-ecolution.dev:3443` |

## Architecture

```
backend/  → Rust (axum, sqlx, tokio) - REST API, MQTT subscriber, auth
frontend/    → React (Vite, TanStack Router/Query, Zustand, Tailwind)
```

The backend is a Cargo workspace with two crates: a portable `domain` crate
(no sqlx/axum/tokio dependencies, reusable on WASM / mobile targets) and a
`server` crate that wires up the Postgres adapters, Keycloak integration,
MQTT subscriber, and the axum HTTP layer.

## PWA

The frontend is installable as a Progressive Web App with offline support via a Workbox service worker.

### HTTPS with valid certificates

PWA features like service workers require HTTPS. The project uses [Let's Encrypt](https://letsencrypt.org/) with DNS-01 challenge via [Porkbun](https://porkbun.com) to obtain valid TLS certificates for local development.

```bash
# 1. Add Porkbun API keys to .env (see .env.example)
# 2. Create DNS records pointing to your local IP
just dns-setup

# 3. Start dev environment (HTTPS on port 3443)
just run-dev
```

Your local IP is auto-detected. Access the app at `https://<ip>.green-ecolution.dev:3443`.

### Mobile testing

With HTTPS enabled, the app is accessible from any device on the local network. No certificate installation needed since Let's Encrypt certs are trusted by default.

- Frontend: `https://<ip>.green-ecolution.dev:3443`
- Auth: `https://auth.<ip>.green-ecolution.dev:3443`

### Without HTTPS

Without Porkbun API keys, the dev environment runs on plain HTTP (port 3000). PWA install and service workers won't work, but general development is unaffected.

```bash
just run-dev   # HTTP on localhost:3000
```

### Testing the service worker

The service worker is **disabled in `vite dev`** (`devOptions.enabled: false` in `vite.config.ts`) to avoid HMR conflicts with Workbox precaching. To verify PWA behavior (install prompt, update flow, offline fallback), build and serve the production bundle:

```bash
cd frontend/app && pnpm build && pnpm preview
```

…or run the full Docker stack via `just run-docker`.

## Configuration

All settings via environment variables (prefix `APP_`, separator `__`) or YAML files in `backend/config/` (`base.yaml`, `local.yaml`, `production.yaml`). The active profile is selected by `APP_ENVIRONMENT`.

Key areas: `application.*`, `database.*`, `auth.*`, `mqtt.*`, `log.*`

See the `backend` service in `compose.yaml` for examples.
