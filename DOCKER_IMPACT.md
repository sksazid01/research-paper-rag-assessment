# How Frontend Changes Impact Docker Image

## Current Docker Setup

### Frontend Container Configuration
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: rag_frontend
  ports:
    - "3456:3456"
  environment:
    NEXT_PUBLIC_API_URL: http://localhost:8000
```

### Frontend Dockerfile Strategy
The frontend uses a **multi-stage build** with Next.js:
1. **deps stage**: Install node_modules
2. **builder stage**: Build the Next.js app (`npm run build`)
3. **runner stage**: Production-optimized image with standalone output

**Key Detail**: The Dockerfile builds a **standalone production bundle** - no source code or hot-reload.

## ⚠️ Critical Impact: Changes Are NOT Automatically Reflected

### Current Situation
```
❌ NO VOLUME MOUNT for frontend source code
❌ Changes to QueryInterface.tsx are NOT live-reloaded
❌ Container runs pre-built static assets from build time
```

Your changes to `QueryInterface.tsx` exist **only on your host machine**, not in the running container.

## How to Apply Your Changes

You have **3 options**, depending on your workflow:

---

### **Option 1: Rebuild Frontend Container** ⚡ (Recommended for Testing)

This rebuilds the entire frontend with your changes:

```bash
# Stop and rebuild only the frontend
docker compose stop frontend
docker compose build --no-cache frontend
docker compose up -d frontend

# Or in one command
docker compose up -d --build frontend
```

**Pros:**
- ✅ Production-like build
- ✅ Tests the actual deployment
- ✅ Optimized bundle

**Cons:**
- ❌ Slow (2-3 minutes per rebuild)
- ❌ No hot-reload during development

**When to use:** Before testing or final submission

---

### **Option 2: Add Volume Mount for Development** 🔥 (Best for Development)

Modify `docker-compose.yml` to mount source code:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile.dev  # Use dev dockerfile
  container_name: rag_frontend
  ports:
    - "3456:3456"
  environment:
    NEXT_PUBLIC_API_URL: http://localhost:8000
  volumes:
    - ./frontend:/app              # Mount source code
    - /app/node_modules            # Preserve node_modules
    - /app/.next                   # Preserve build cache
  command: npm run dev             # Run in dev mode
```

Then create `frontend/Dockerfile.dev`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# Don't copy source code - it's mounted via volume
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

EXPOSE 3456

CMD ["npm", "run", "dev", "--", "-p", "3456"]
```

**Usage:**
```bash
docker compose down
docker compose up -d --build
```

**Pros:**
- ✅ Hot-reload enabled (instant updates)
- ✅ No rebuild needed for changes
- ✅ Fast development workflow

**Cons:**
- ❌ Not production-like
- ❌ Larger container

**When to use:** During active development

---

### **Option 3: Run Frontend Locally** 💻 (Simplest for Quick Testing)

Skip Docker for frontend during development:

```bash
# Stop frontend container
docker compose stop frontend

# Run locally
cd frontend
npm install  # First time only
npm run dev  # Runs on http://localhost:3000

# Backend still in Docker
# Update NEXT_PUBLIC_API_URL if needed
```

**Pros:**
- ✅ Instant hot-reload
- ✅ Easy debugging with browser DevTools
- ✅ No Docker complexity
- ✅ Fastest iteration cycle

**Cons:**
- ❌ Different from production
- ❌ Need Node.js installed locally

**When to use:** Active development and debugging

---

## What Happens Inside the Docker Image?

### Build Process (Current Setup)

```
1. docker compose build frontend
   │
   ├─ Stage 1: deps
   │  └─ npm ci (install dependencies)
   │
   ├─ Stage 2: builder
   │  ├─ Copy source code (including QueryInterface.tsx)
   │  ├─ npm run build
   │  │  └─ Next.js compiles:
   │  │     - QueryInterface.tsx → JavaScript bundle
   │  │     - Optimizes images, CSS, etc.
   │  │     - Creates .next/standalone directory
   │  │
   │  └─ Result: Compiled static assets
   │
   └─ Stage 3: runner
      ├─ Copy ONLY .next/standalone + .next/static
      ├─ Original .tsx files are DISCARDED
      └─ Runs: node server.js (pre-compiled)
```

### What's Actually in the Container

```
/app/
├── server.js              # Pre-compiled Next.js server
├── .next/
│   └── static/            # Compiled JS bundles
│       └── chunks/
│           └── app-xyz123.js  # Your QueryInterface.tsx compiled here
├── node_modules/          # Production dependencies only
└── package.json

❌ NO frontend/components/QueryInterface.tsx source file
❌ NO TypeScript files
❌ NO development dependencies
```

### Why Changes Don't Appear

```
Your Host Machine              Docker Container
─────────────────              ────────────────
frontend/
├── components/
│   └── QueryInterface.tsx    ≠    Pre-compiled JS bundle
│       (NEW CHANGES)               (OLD CODE from build time)
```

The container has **zero knowledge** of your file system changes until you rebuild.

---

## Verification After Changes

After applying changes (any option above), verify:

### 1. Check Frontend Logs
```bash
docker logs rag_frontend -f
```

Look for:
```
✓ Ready on http://0.0.0.0:3456
○ Compiling / ...
✓ Compiled / in 234ms
```

### 2. Test in Browser
```bash
# Open browser
open http://localhost:3456

# Or curl
curl -I http://localhost:3456
```

Expected: HTTP 200, new UI visible

### 3. Verify API Connectivity
Open browser console (F12) and check:
- Network tab shows `/api/query/stream` requests
- No CORS errors
- Streaming works

### 4. Check Changed Features
Test the new improvements:
- ✅ Progress bar appears during query
- ✅ Timeout handling (try complex query)
- ✅ Professional gradient UI
- ✅ Enhanced citations with badges
- ✅ Custom slider styling

---

## Current Status: What You Need to Do

### Your Changes Are:
- ✅ Saved on host: `/home/sk-sazid/Desktop/research-paper-rag-assessment/frontend/components/QueryInterface.tsx`
- ❌ **NOT** in Docker container yet

### To See Changes:

**Quick Test (Option 3):**
```bash
# Stop Docker frontend
docker compose stop frontend

# Run locally
cd frontend
npm run dev
# Open http://localhost:3000
```

**Production Test (Option 1):**
```bash
# Rebuild and restart
docker compose up -d --build frontend

# Wait 2-3 minutes for build
# Open http://localhost:3456
```

**Development Setup (Option 2):**
```bash
# See "Option 2" section above for docker-compose.yml changes
# Then:
docker compose down
docker compose up -d --build
```

---

## Recommended Workflow

### For This Assessment Submission:

1. **Test locally first** (Option 3)
   ```bash
   cd frontend && npm run dev
   ```
   - Verify all features work
   - Test with backend running
   - Check browser console

2. **Then build production image** (Option 1)
   ```bash
   docker compose up -d --build frontend
   ```
   - Test at http://localhost:3456
   - Verify in production-like environment
   - Take screenshots if needed

3. **Commit and push**
   ```bash
   git add frontend/components/QueryInterface.tsx
   git add IMPROVEMENTS.md QUERY_FIX_SUMMARY.md
   git commit -m "feat: enhance query performance and professional UI"
   git push origin submission/YOUR_NAME
   ```

---

## Common Issues & Solutions

### Issue 1: "Changes not visible after rebuild"
```bash
# Solution: Clear Docker build cache
docker compose build --no-cache frontend
docker compose up -d frontend
```

### Issue 2: "Port 3456 already in use"
```bash
# Check what's using the port
lsof -i :3456

# Kill the process or stop container
docker compose stop frontend
```

### Issue 3: "API calls failing from container"
```bash
# Check if API is accessible
docker exec rag_frontend wget -O- http://localhost:8000/health

# If fails, check API container
docker logs rag_api
```

### Issue 4: "npm run build fails"
```bash
# Check for TypeScript errors
cd frontend
npm run build

# Fix errors, then rebuild Docker
docker compose build frontend
```

---

## Summary

### Key Takeaway
🔑 **Docker containers are isolated** - your file changes on the host don't automatically appear inside unless you:
1. **Rebuild** the image (for production builds)
2. **Mount volumes** (for development hot-reload)
3. **Run locally** (bypass Docker for frontend)

### Best Practice for This Assessment
- Develop locally: `npm run dev` 
- Test frequently with hot-reload
- Final verification: `docker compose up --build`
- Submit with working Docker setup

### Current Action Required
```bash
# Choose one:

# A. Quick local test
cd frontend && npm run dev

# B. Production Docker test  
docker compose up -d --build frontend
```

Your enhanced UI with performance fixes will then be visible! 🎉
