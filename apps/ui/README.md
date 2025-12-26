# PLK_KB UI

Next.js app that surfaces pipeline status, search, authority, and audit views.

## Environment

Create `apps/ui/.env.local` (not committed) to configure client-visible settings:

```
NEXT_PUBLIC_PLK_INGESTION_ROOT=/mnt/d/TestData
```

- `NEXT_PUBLIC_PLK_INGESTION_ROOT` sets the default folder for ingestion. Must be accessible from the browser/Next.js
  client context (Windows mount example: `D:\TestData` → `/mnt/d/TestData`).

Server-side environment (read from process env, not exposed to the client):

- `PLK_PYTHON`: Path to the Python executable (defaults to `/home/jim/PLK_KB/.venv/bin/python`).
- `PLK_ROOT`: Repository root for spawned Python processes (defaults to `/home/jim/PLK_KB`).

## Development

```bash
npm install
npm run dev
```

Then open http://localhost:3000.
