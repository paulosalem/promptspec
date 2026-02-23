## Tech Stack: TypeScript + Next.js + Prisma + PostgreSQL

### Frontend
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript 5+ (strict mode, no `any`)
- **Styling**: Tailwind CSS with design tokens in `tailwind.config.ts`
- **State**: React Server Components by default; client state via Zustand where needed
- **Forms**: react-hook-form with zod validation schemas (shared with API)
- **Data fetching**: Server Actions for mutations, `fetch` in Server Components for reads

### Backend (API Routes)
- **Runtime**: Next.js API routes (Edge or Node.js depending on data needs)
- **ORM**: Prisma with PostgreSQL provider
- **Validation**: zod schemas shared between client and server
- **Authentication**: NextAuth.js v5 with JWT strategy, credentials + OAuth providers
- **Rate limiting**: upstash/ratelimit on sensitive endpoints

### Database
- **Engine**: PostgreSQL 16+
- **Migrations**: Prisma Migrate
- **Naming**: camelCase in Prisma schema, auto-mapped to snake_case in DB via `@@map`
- **Soft deletes**: `deletedAt DateTime?` field; Prisma middleware filters automatically
- **Audit fields**: `createdAt DateTime @default(now())`, `updatedAt DateTime @updatedAt`

### Testing
- **Unit**: Vitest with happy-dom for component tests
- **API**: Vitest + supertest for route handler tests
- **E2E**: Playwright for critical user flows
- **Coverage**: minimum 80% line coverage

### Deployment
- **Platform**: Vercel (or Docker for self-hosted)
- **Config**: environment variables via `env.mjs` with zod validation at build time
- **Health check**: `GET /api/health` returning `{"status": "ok", "version": "..."}`
