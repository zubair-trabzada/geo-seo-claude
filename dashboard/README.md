# GEO Dashboard

A full-stack platform for tracking Generative Engine Optimization (GEO) — the practice of making your website more likely to be cited by AI systems like ChatGPT, Perplexity, Google AI Overviews, and Bing Copilot.

---

## Overview

The GEO Dashboard provides:

- **Admin portal** — manage multiple client accounts, monitor GEO scores, view alerts, and trigger audits
- **Client portal** — a clean single-page dashboard showing score gauge, progress chart, competitor comparison, category breakdown, milestones, and action items
- **Audit pipeline integration** — the frontend triggers audits via the Python FastAPI backend, which runs the existing GEO audit scripts and stores results in SQLite
- **Real-time recommendations** — a Kanban-style board (Pending / In Progress / Done) surfacing actionable GEO improvements per audit

---

## Architecture

```
geo-seo-claude/
├── dashboard/
│   ├── backend/                  # FastAPI audit service
│   │   ├── main.py               # POST /audit/run endpoint
│   │   └── requirements.txt
│   └── frontend/                 # Next.js 14 App Router
│       ├── app/
│       │   ├── (admin)/          # Admin route group
│       │   │   ├── layout.tsx    # Sidebar + topbar layout
│       │   │   ├── page.tsx      # Client overview table
│       │   │   ├── alerts/       # Alert management
│       │   │   └── clients/
│       │   │       ├── new/      # Add client form
│       │   │       └── [id]/     # Single client view
│       │   ├── (auth)/
│       │   │   └── login/        # Login page
│       │   ├── (client)/         # Client route group
│       │   │   ├── layout.tsx    # Top nav layout
│       │   │   ├── page.tsx      # Main client dashboard
│       │   │   └── history/      # Full audit timeline
│       │   ├── api/
│       │   │   ├── auth/         # NextAuth handler
│       │   │   ├── audits/       # GET+POST audits
│       │   │   ├── clients/      # GET+POST clients
│       │   │   ├── alerts/[id]/  # PATCH alert read status
│       │   │   └── recommendations/[id]/  # PATCH rec status
│       │   └── page.tsx          # Root redirect
│       ├── components/           # Reusable React components
│       │   ├── ScoreGauge.tsx
│       │   ├── ProgressChart.tsx
│       │   ├── CompetitorBar.tsx
│       │   ├── CategoryBreakdown.tsx
│       │   ├── RecommendationBoard.tsx
│       │   ├── MilestoneFeed.tsx
│       │   ├── CitationExamples.tsx
│       │   ├── SignOutButton.tsx
│       │   ├── RunAuditButton.tsx
│       │   ├── AlertActions.tsx
│       │   ├── AdminClientTabs.tsx
│       │   └── RecommendationSection.tsx
│       ├── lib/
│       │   ├── auth.ts           # NextAuth options + session helpers
│       │   ├── db.ts             # Prisma singleton
│       │   └── types.ts          # Shared TypeScript types
│       └── prisma/
│           ├── schema.prisma     # SQLite data model
│           └── seed.ts           # Demo data seeder
└── geo/                          # Existing Python GEO audit scripts
```

**Data flow:**

```
Browser → Next.js API route → FastAPI (Python) → GEO audit scripts
                           ↓
                     Prisma → SQLite
                           ↓
              Next.js Server Components (read)
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18+ |
| npm | 9+ |
| Python | 3.10+ |
| pip | 23+ |

---

## Setup Instructions

### 1. Backend (FastAPI audit service)

```bash
cd dashboard/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

The backend exposes:
- `POST /audit/run` — triggers a GEO audit for a client and writes results to the database

### 2. Frontend (Next.js dashboard)

```bash
cd dashboard/frontend

# Install dependencies
npm install

# Set up the database (creates geo_dashboard.db)
npm run db:push

# Generate Prisma client
npm run db:generate

# Seed with demo admin + client data
npm run db:seed

# Start the development server
npm run dev
```

The dashboard is available at **http://localhost:3000**

---

## Environment Variables

The frontend reads from `dashboard/frontend/.env.local`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `file:../geo_dashboard.db` | SQLite database path (relative to frontend dir) |
| `NEXTAUTH_URL` | `http://localhost:3000` | Public URL of the Next.js app |
| `NEXTAUTH_SECRET` | *(change this)* | JWT signing secret — use a random 32+ character string in production |
| `FASTAPI_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

For production, generate a secure secret:
```bash
openssl rand -base64 32
```

---

## Usage

### Logging in as Admin

After seeding, navigate to **http://localhost:3000** and sign in with:
- Email: `admin@geodashboard.local`
- Password: `admin123`

You will be redirected to `/admin` — the client overview table.

### Logging in as Client (demo)

- Email: `baraband@geodashboard.local`
- Password: `client123`

You will be redirected to `/client` — the GEO performance dashboard.

### Adding a New Client (as Admin)

1. From the admin dashboard, click **Add Client**
2. Fill in: Client Name, Website URL, and up to 3 competitor URLs
3. Create a login email and password for the client's portal access
4. Click **Create Client** — this creates the DB record, user account, and triggers a baseline audit via the FastAPI backend

### Running an Audit

From any client detail page (`/admin/clients/[id]`), click **Run Audit Now**. This calls `POST /api/audits` which triggers the FastAPI backend to run the audit pipeline and store results.

### Viewing Client Dashboard

Clients log in and are automatically routed to their personalized dashboard at `/client`, showing:
- Animated score gauge with baseline delta
- GEO score trend line chart
- Competitor comparison bar chart
- Per-category score breakdown (AI Citability, Brand Authority, E-E-A-T, Technical, Schema, Platform)
- Achievement milestone timeline
- Recommendation Kanban board (drag items from Pending → In Progress → Done)
- Top audit findings with citation impact explanations

---

## How the Audit Pipeline Works

1. Admin triggers audit → Next.js `POST /api/audits` route calls `FASTAPI_URL/audit/run`
2. FastAPI backend invokes the Python GEO audit scripts from `geo/` directory
3. Audit results (score, category breakdown, findings, recommendations) are posted back to Next.js `POST /api/audits` as a callback
4. Prisma stores the `Audit` record with serialized JSON for `scores`, `rawData`, and `competitors`
5. Related `Recommendation` rows are created in the same transaction
6. If the score dropped more than 5 points vs the previous audit, an `Alert` record is created automatically
7. Server components re-fetch fresh data on next page load

---

## Development Notes

- **Server vs Client components:** Data fetching happens in server components (no `'use client'`). Interactive elements (buttons, forms, charts) are in client components.
- **Auth:** NextAuth v4 with JWT strategy. Session contains `id`, `email`, `role`, and `clientId`. Route groups `(admin)` and `(client)` each have their own layout that checks the session role.
- **Database:** SQLite via Prisma. JSON fields (`scores`, `rawData`, `competitors`) are stored as serialized strings and parsed at read time.
- **Tailwind:** Dark theme using `slate-950/900/800` scale. Custom design tokens defined in `tailwind.config.js` and CSS custom properties in `globals.css`.
- **Recharts:** Used for the ProgressChart line chart. All other visualizations (ScoreGauge, CategoryBreakdown, CompetitorBar) use custom SVG or CSS animations.

### Useful Commands

```bash
# Open Prisma Studio (visual DB browser)
npm run db:studio

# Re-generate Prisma client after schema changes
npm run db:generate

# Push schema changes to the database
npm run db:push

# Lint
npm run lint

# Build for production
npm run build
```
