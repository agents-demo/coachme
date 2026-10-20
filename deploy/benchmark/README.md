# Remote / cloud deployment

This runs the benchmark UI as a multi-user service with local accounts and
tenant-scoped data roots.

## Quick start

```bash
cd deploy/benchmark
cp .env.example .env
# edit the admin password and session secret
docker compose up -d --build
```

The compose file binds to `127.0.0.1:8765`. Put a TLS reverse proxy (Caddy,
nginx, Traefik) in front for remote access. Set
`COACHME_BENCHMARK_COOKIE_SECURE=true` when the public URL is HTTPS.

## Accounts and tenants

Users are stored in `/data/.auth/users.json`; passwords are PBKDF2-hashed.
Each user belongs to one tenant and sees only `/data/tenants/<tenant>`.

Create users inside the container:

```bash
docker compose exec benchmark coachme-benchmark user-add \
  --data /data --username coach-a --role labeler --tenant default

docker compose exec benchmark coachme-benchmark user-list --data /data
```

Roles: `admin`, `operator`, `labeler`, `rater`, `adjudicator`.

## Remote without Docker

```bash
coachme-benchmark user-add --data benchmark --username admin --role admin --tenant default
COACHME_BENCHMARK_AUTH=1 coachme-benchmark ui \
  --data benchmark --host 0.0.0.0 --allow-remote --auth --port 8765
```

Remote binding is refused unless `--allow-remote` **and** auth are enabled.
