# Local Development Guide

**Application:** Data Lineage Visualizer Frontend
**Last Updated:** 2025-10-26

---

## Table of Contents

1. [Overview](#overview)
2. [Running in VSCode Devcontainer](#running-in-vscode-devcontainer)
3. [Standalone Development](#standalone-development)
4. [Development Workflow](#development-workflow)
5. [Loading Production Data](#loading-production-data)
6. [Hot Module Replacement](#hot-module-replacement)
7. [Debugging](#debugging)
8. [Common Tasks](#common-tasks)

---

## Overview

The frontend can be run in **two modes**:

1. **Integrated Mode** (Recommended): Run frontend + Python backend together in the same VSCode devcontainer
2. **Standalone Mode**: Run frontend only from the `frontend/` subfolder

Both modes serve the same React application on `http://localhost:3000`.

---

## Running in VSCode Devcontainer

### Prerequisites

✅ Already installed in your devcontainer:
- Node.js 18.x or 20.x
- npm 9.x or 10.x
- Python 3.12.3 (for backend)

### Method 1: Quick Start (Recommended)

```bash
# From workspace root
cd /workspaces/ws-psidwh/frontend

# Install dependencies (first time only)
# Dependencies already installed in devcontainer

# Start development server
npm run dev
```

**Output:**
```
  VITE v6.2.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://172.17.0.2:3000/
  ➜  press h + enter to show help
```

**Access the app:**
- In devcontainer: Click the link in terminal (VS Code will forward port automatically)
- Or open browser to: `http://localhost:3000`

### Method 2: Running Both Frontend + Backend

**Terminal 1 (Backend):**
```bash
cd /workspaces/ws-psidwh

# Generate lineage data
python lineage_v3/main.py run --parquet parquet_snapshots/
```

**Terminal 2 (Frontend):**
```bash
cd /workspaces/ws-psidwh/frontend

# Start dev server
npm run dev
```

**Workflow:**
1. Backend generates `lineage_output/frontend_lineage.json`
2. Frontend loads this file via the Import Data modal
3. Visualize and explore the lineage graph

---

## Standalone Development

### From the `frontend/` Subfolder

If you want to work only on the frontend:

```bash
# Navigate to frontend folder
cd frontend/

# Install dependencies
# Dependencies already installed in devcontainer

# Start dev server
npm run dev
```

**Note:** The app will use sample data by default. To load production data, see [Loading Production Data](#loading-production-data).

### Available npm Scripts

```bash
# Development server (hot reload)
npm run dev

# Production build
npm run build

# Preview production build locally
npm run preview
```

---

## Development Workflow

### 1. Install Dependencies

**First time setup:**
```bash
cd /workspaces/ws-psidwh/frontend
# Dependencies already installed in devcontainer
```

**Dependencies installed:**
- React 19.2.0
- ReactFlow 11.11.4
- Vite 6.2.0
- TypeScript 5.8.2
- Dagre, Graphology
- Type definitions

### 2. Start Dev Server

```bash
npm run dev
```

**Features:**
- ⚡ Lightning-fast HMR (Hot Module Replacement)
- 🔍 TypeScript type checking
- 🎨 Instant style updates
- 📦 Optimized dependency pre-bundling

### 3. Make Changes

Edit any file in `frontend/`:
- `*.tsx` - React components
- `*.ts` - TypeScript utilities/hooks
- `index.html` - HTML template
- `vite.config.ts` - Build configuration

**Changes auto-reload in browser!**

### 4. Build for Production

```bash
npm run build
```

**Output:** `dist/` folder with optimized files:
```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js    # Minified, tree-shaken
│   └── index-[hash].css   # Purged Tailwind
└── ...
```

### 5. Preview Production Build

```bash
npm run preview
```

Serves the `dist/` folder on `http://localhost:4173` (or next available port).

---

## Loading Production Data

### Option 1: Import via UI (Recommended)

1. Generate lineage JSON from Python backend:
   ```bash
   cd /workspaces/ws-psidwh
   python lineage_v3/main.py run --parquet parquet_snapshots/
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. In the app:
   - Click **Import Data** button (upload icon in toolbar)
   - Click **Upload File**
   - Select `../lineage_output/frontend_lineage.json`
   - Click **Apply Changes**

### Option 2: Replace Sample Data (Permanent)

**Edit:** `frontend/utils/data.ts`

```typescript
import productionData from '../../lineage_output/frontend_lineage.json';

export const generateSampleData = (): DataNode[] => {
  // Return production data instead of sample
  return productionData as DataNode[];
};
```

**Then rebuild:**
```bash
npm run dev  # Will use production data on load
```

### Option 3: Load from Public URL

If you host the JSON file somewhere:

```typescript
// In App.tsx, replace generateSampleData() with:
useEffect(() => {
  fetch('https://your-server.com/frontend_lineage.json')
    .then(res => res.json())
    .then(data => setAllData(data));
}, []);
```

---

## Hot Module Replacement (HMR)

Vite provides instant HMR for fast development:

### What Updates Instantly

✅ **React Components** - State preserved
✅ **CSS/Tailwind** - Styles update without reload
✅ **TypeScript** - Type errors shown in browser overlay
✅ **Constants/Utils** - Most changes apply immediately

### When Full Reload Happens

⚠️ **These require full page reload:**
- Changes to `index.html`
- Changes to `vite.config.ts`
- Adding new dependencies (restart dev server)

### Keyboard Shortcuts in Dev Server

- `h` + Enter: Show help
- `r` + Enter: Restart server
- `u` + Enter: Show server URL
- `o` + Enter: Open in browser
- `c` + Enter: Clear console
- `q` + Enter: Quit server

---

## Debugging

### Browser DevTools

**Open DevTools:** F12 or Right-click → Inspect

**React DevTools:**
1. Install [React DevTools extension](https://react.dev/learn/react-developer-tools)
2. View component tree, props, state
3. Profile performance

### TypeScript Errors

**In VS Code:**
- Errors show inline with red squiggles
- Hover for details
- Cmd/Ctrl + Click to jump to definition

**In Terminal:**
```bash
# Run type checker manually
npx tsc --noEmit
```

### Vite Dev Server Logs

**View in terminal where `npm run dev` is running:**
- Green: Successful HMR updates
- Yellow: Warnings
- Red: Errors

**Common errors:**
```
[vite] Internal server error: Transform failed
→ Syntax error in TSX/JSX
→ Check the file mentioned in error
```

### Source Maps

Vite generates source maps by default:
- Set breakpoints in original TypeScript files
- Step through code in DevTools
- Inspect variables in original source

### Performance Profiling

**React DevTools Profiler:**
1. Open React DevTools → Profiler tab
2. Click Record (●)
3. Interact with app
4. Stop recording
5. Analyze component render times

**Chrome DevTools Performance:**
1. F12 → Performance tab
2. Record while interacting
3. Analyze flame graph

---

## Common Tasks

### Add a New Component

```bash
# Create component file
touch frontend/components/MyNewComponent.tsx
```

```typescript
// MyNewComponent.tsx
import React from 'react';

export const MyNewComponent = () => {
  return <div>Hello World</div>;
};
```

```typescript
// Import in App.tsx
import { MyNewComponent } from './components/MyNewComponent';
```

### Add a New npm Package

```bash
cd frontend

# Install production dependency
# Dependencies already installed in devcontainer <package-name>

# Install dev dependency
# Dependencies already installed in devcontainer --save-dev <package-name>
```

**Example:**
```bash
# Dependencies already installed in devcontainer lodash
# Dependencies already installed in devcontainer --save-dev @types/lodash
```

### Update Dependencies

```bash
# Check for outdated packages
npm outdated

# Update all to latest (within version ranges)
npm update

# Update to latest major versions (breaking changes)
# Dependencies already installed in devcontainer react@latest react-dom@latest
```

### Clear Build Cache

```bash
# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
# Dependencies already installed in devcontainer

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Change Dev Server Port

**Edit:** `frontend/vite.config.ts`

```typescript
export default defineConfig({
  server: {
    port: 5000,  // Change from 3000 to 5000
    host: '0.0.0.0',
  },
  // ...
});
```

### Enable HTTPS in Development

```bash
# Install mkcert (one-time setup)
# Dependencies already installed in devcontainer -D @vitejs/plugin-basic-ssl

# Update vite.config.ts
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
  plugins: [react(), basicSsl()],
  // ...
});
```

### Run on Custom Host

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    host: '0.0.0.0',  // Allow external access
    port: 3000,
  },
});
```

**Access from other devices:**
- `http://<your-ip>:3000`
- Vite shows Network URL in terminal

---

## Environment Variables

### Development Environment

**File:** `frontend/.env.local` (gitignored)

```bash
# Currently only used in AI Studio context
GEMINI_API_KEY=your_key_here
```

**Note:** This app doesn't use environment variables in production. The `GEMINI_API_KEY` is for AI Studio development only and is **not** included in the built app.

### Adding New Environment Variables

**1. Create `.env.local`:**
```bash
VITE_API_URL=https://api.example.com
VITE_FEATURE_FLAG=true
```

**2. Update `vite.config.ts`:**
```typescript
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL),
    },
  };
});
```

**3. Use in code:**
```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```

**Important:** Only variables prefixed with `VITE_` are exposed to client code!

---

## TypeScript Configuration

### Current Configuration

**File:** `frontend/tsconfig.json`

Key settings:
- `target: "ES2022"` - Modern JavaScript features
- `jsx: "react-jsx"` - New JSX transform (no `import React`)
- `moduleResolution: "bundler"` - Vite-optimized
- `noEmit: true` - Type checking only (Vite handles building)

### Type Checking

```bash
# Check types without building
npx tsc --noEmit

# Watch mode
npx tsc --noEmit --watch
```

### VS Code Integration

**Settings:**
- TypeScript errors show inline
- Auto-imports on paste
- Organize imports on save

**Recommended VS Code Extensions:**
- TypeScript Vue Plugin (for TSX)
- Tailwind CSS IntelliSense
- Error Lens (show errors inline)

---

## Tailwind CSS (CDN)

### Current Setup

**File:** `frontend/index.html`

```html
<script src="https://cdn.tailwindcss.com"></script>
```

**Pros:**
- ✅ No build configuration needed
- ✅ Works immediately
- ✅ Always up-to-date

**Cons:**
- ⚠️ ~3MB uncompressed (not purged)
- ⚠️ Slightly slower initial load
- ⚠️ Requires internet connection

### Switch to Local Tailwind (Optional)

If you want smaller production bundles:

```bash
# Dependencies already installed in devcontainer -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Update `tailwind.config.js`:**
```javascript
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: { extend: {} },
  plugins: [],
}
```

**Create `src/index.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Import in `index.tsx`:**
```typescript
import './index.css';
```

**Remove CDN script from `index.html`**

**Result:** ~10KB CSS file in production (purged)

---

## Testing (Future Enhancement)

### Setup Vitest (Recommended)

```bash
# Dependencies already installed in devcontainer -D vitest @testing-library/react @testing-library/jest-dom
```

**Create `vitest.config.ts`:**
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
  },
});
```

**Run tests:**
```bash
npm run test
```

---

## Troubleshooting

### Port Already in Use

```
Error: Port 3000 is already in use
```

**Solutions:**
1. Kill process using port 3000:
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

2. Use different port:
   ```bash
   npm run dev -- --port 3001
   ```

### Module Not Found

```
Error: Cannot find module 'react'
```

**Solution:**
```bash
rm -rf node_modules package-lock.json
# Dependencies already installed in devcontainer
```

### TypeScript Errors in node_modules

```
Error: Type errors in node_modules/...
```

**Solution:**
```typescript
// tsconfig.json - already configured
{
  "compilerOptions": {
    "skipLibCheck": true  // Skip type checking node_modules
  }
}
```

### Vite Cache Issues

```
[vite] Outdated optimize dep detected
```

**Solution:**
```bash
rm -rf node_modules/.vite
npm run dev
```

### Browser Not Auto-Opening

**Manually open:** `http://localhost:3000`

**Or force open:**
```bash
npm run dev -- --open
```

---

## Performance Tips

1. **Keep Dependencies Updated:** `npm outdated` → `npm update`
2. **Use Production Build for Testing:** `npm run build && npm run preview`
3. **Monitor Bundle Size:** Check `dist/` folder size after build
4. **Profile with React DevTools:** Find slow components
5. **Lazy Load Heavy Components:** Use `React.lazy()` if needed

---

## Next Steps

- **Production Deployment:** See [DEPLOYMENT_AZURE.md](DEPLOYMENT_AZURE.md)
- **Backend Integration:** See [INTEGRATION.md](INTEGRATION.md)
- **Architecture Details:** See [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md)

---

## Quick Reference

### Essential Commands

| Command | Purpose |
|---------|---------|
| `# Dependencies already installed in devcontainer` | Install dependencies |
| `npm run dev` | Start dev server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npx tsc --noEmit` | Check TypeScript types |

### File Locations

| File | Purpose |
|------|---------|
| `frontend/App.tsx` | Main app component |
| `frontend/index.html` | HTML template |
| `frontend/vite.config.ts` | Build configuration |
| `frontend/package.json` | Dependencies |
| `frontend/.env.local` | Local environment variables |

### URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:3000` | Dev server |
| `http://localhost:4173` | Preview server |
| `http://localhost:5173` | Alternative Vite port |

---

**End of Development Guide**
