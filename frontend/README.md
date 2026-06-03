# Diet Coach Agent — Frontend

Next.js 16 + TypeScript + Tailwind CSS v4 frontend.

## Requirements

- Node.js 20.9+
- npm (included with Node.js)

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Copy environment file

```bash
cp .env.example .env.local
```

Edit `.env.local` and set `NEXT_PUBLIC_API_URL` to your backend URL.

### 3. Start the development server

```bash
npm run dev
```

App starts on http://localhost:3000
Navigate to http://localhost:3000/fa (Persian) or http://localhost:3000/en (English).

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server with Turbopack |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | TypeScript type check (no emit) |

## Technology Notes

- **Tailwind CSS v4**: CSS logical properties by default. Use `ps-/pe-/ms-/me-`, never `pl-/pr-/ml-/mr-`.
- **App Router**: All routes under `src/app/[lang]/` for i18n support.
- **TypeScript strict**: `"strict": true` in tsconfig.json — all type errors must be fixed.
- **No `any`**: Use strict types; RTL direction bugs are caught by the type system.
