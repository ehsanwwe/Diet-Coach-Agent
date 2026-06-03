# Pitfalls Research

**Domain:** AI-powered multilingual health/nutrition coaching app (FastAPI + Next.js App Router, Persian-first RTL)
**Researched:** 2026-06-03
**Confidence:** HIGH (technical patterns well-established; MEDIUM for medical guardrail adequacy which requires clinical validation)

---

## Critical Pitfalls

### Pitfall 1: SQLAlchemy 2.x Async — Lazy Loading Causes DetachedInstanceError at Runtime

**What goes wrong:**
SQLAlchemy async sessions cannot use implicit lazy loading. Any relationship accessed outside the active session context raises `MissingGreenlet` or `DetachedInstanceError`. This is invisible in sync code but explodes in async FastAPI routes. Example: returning a `User` object from a route after the session closes, then accessing `user.profile` in a Pydantic serializer triggers the error.

**Why it happens:**
Developers copy patterns from SQLAlchemy 1.x / sync code. The ORM *looks* the same — the error only surfaces at serialization time, not at query time, making it hard to trace.

**How to avoid:**
- Always use `selectinload()` or `joinedload()` explicitly for every relationship accessed in the response.
- Use `lazy="raise"` on all relationships in model definitions so violations fail loudly at development time, not silently in production.
- Never return ORM model instances from FastAPI response handlers — always convert to Pydantic schemas *inside* the session context block.
- Structure all DB access inside `async with AsyncSession() as session:` or a proper dependency-injected session that closes after the response is built.

**Warning signs:**
- `sqlalchemy.exc.MissingGreenlet` or `DetachedInstanceError` in logs
- Works in tests (sync fixture) but fails in production routes
- Pydantic validation errors on nested models that "should" be populated

**Phase to address:** Infrastructure / Backend foundation phase (before any feature routes are built)

---

### Pitfall 2: Alembic + SQLite — ALTER TABLE Not Supported, Migrations Silently Succeed but Do Nothing

**What goes wrong:**
SQLite does not support most `ALTER TABLE` operations (add non-nullable column, drop column, rename column, change column type, add constraints). Alembic's default `op.add_column()` with `nullable=False` and no server default will either crash or — worse — silently succeed with SQLite's permissive parser while creating a schema that differs from what Alembic thinks exists.

**Why it happens:**
Alembic's `render_as_batch=False` (the default) generates standard SQL DDL. SQLite ignores or errors on unsupported DDL. The `--autogenerate` command produces migrations that look correct but fail at apply time.

**How to avoid:**
- In `env.py`, set `render_as_batch=True` globally: `context.configure(..., render_as_batch=True)`. This makes Alembic use the "copy table" strategy for all SQLite migrations.
- Every `op.add_column()` for a non-nullable column MUST include `server_default` (even a dummy one that gets dropped later).
- Test every migration on a fresh database, not only on the current dev database (which may have the column from an earlier manual change).
- Add a CI step: `alembic upgrade head` against a blank SQLite file as part of the test suite.

**Warning signs:**
- `OperationalError: Cannot add a NOT NULL column with default value NULL`
- Migration says "Done" but column is missing when you query the schema
- `alembic check` shows pending changes even after `upgrade head`

**Phase to address:** Infrastructure / Database setup phase (must be solved before any migration is written)

---

### Pitfall 3: FastAPI + JWT — Tokens Never Expire in Practice, No Revocation Path

**What goes wrong:**
A JWT with a 30-day expiry is issued at OTP verification. No refresh token, no token blacklist. When the user logs out, the frontend deletes the cookie/localStorage entry, but the token remains valid. If stolen (XSS, shared device), it cannot be revoked. For a health app storing medical data, this is a serious compliance risk.

**Why it happens:**
JWT is stateless by design. Developers implement the happy path (issue, verify, use) and defer revocation. "We'll add a blacklist later" becomes never.

**How to avoid:**
- Store JWT `jti` (JWT ID) claim and maintain a `revoked_tokens` table (or Redis set) checked on every request.
- For SQLite MVP: keep access tokens short (15 minutes), issue refresh tokens (stored in DB, revokable), use `httpOnly` cookies (not localStorage).
- Implement logout as a server-side operation that revokes the token, not just a client-side cookie deletion.
- The `AuthOTP` table should have an `invalidated_at` field; issued tokens should carry the `issued_at` timestamp from this record so forced re-auth is possible by updating the record.

**Warning signs:**
- Logout implemented only as `localStorage.removeItem('token')`
- No `jti` claim in JWT payload
- No server-side logout endpoint (or it exists but just returns 200 without any DB write)

**Phase to address:** Authentication phase

---

### Pitfall 4: RTL/LTR — Hard-Coded `left`/`right` CSS Properties Break Entire Layout in RTL

**What goes wrong:**
A component built in LTR uses `margin-left`, `padding-right`, `border-left`, `left: 0`, `text-align: left`. When `dir="rtl"` is applied to `<html>`, none of these flip. The layout breaks: icons are on the wrong side, text overflows, dropdowns open in the wrong direction, slide animations go the wrong way.

**Why it happens:**
Tailwind's default utilities (`ml-4`, `pr-2`, `left-0`) are physical properties. RTL retrofitting requires changing every physical property to its logical equivalent — a laborious audit. Developers add RTL as an afterthought.

**How to avoid:**
- Use CSS logical properties from day 1: `ms-4` (margin-inline-start) instead of `ml-4`, `pe-2` (padding-inline-end) instead of `pr-2`, `inset-inline-start` instead of `left`. Tailwind v3+ supports these with the `ms-`, `me-`, `ps-`, `pe-` prefix family.
- Set up an ESLint rule or custom linter that flags `ml-`, `mr-`, `pl-`, `pr-`, `left-`, `right-` (physical) in component files.
- Build a `useDirection()` hook that returns `{ dir, isRTL }` from the current locale — consume it anywhere direction-conditional logic is needed (animation direction, icon mirroring).
- Direction-aware icon utility: chevrons (`<`, `>`) must flip in RTL. Use a wrapper component `<DirectionalIcon>` that applies `scale-x: -1` when `isRTL` and the icon is directional.

**Warning signs:**
- Any `ml-`, `mr-`, `pl-`, `pr-` in component CSS/Tailwind classes
- Slide animations hard-coded as `translateX(-100%)` / `translateX(100%)` instead of computed from direction
- `text-align: left` anywhere (should be `text-align: start`)
- Dropdown/popover positioned with `left: 0` / `right: 0` instead of `inset-inline-start: 0`

**Phase to address:** i18n / RTL foundation phase (before building any UI components — retrofitting is 3x the work)

---

### Pitfall 5: Medical Safety Guardrail — Conditions Checked at Onboarding But Not Re-Evaluated

**What goes wrong:**
The app checks medical conditions in Step 3 of onboarding and sets `risk_level`. But: (1) users lie or don't know their conditions at onboarding time; (2) conditions change (user gets diagnosed with diabetes post-onboarding); (3) the AI response layer does not re-check risk level on every chat message — it trusts the stale profile. A `clinical_review_required` user gets a diet plan because the guardrail is only in `NutritionPlanService`, not in `ChatService`.

**Why it happens:**
Guardrail logic is implemented once and considered "done." The safety check is a single point of enforcement rather than a cross-cutting concern.

**How to avoid:**
- `SafetyGuardrailService` must be invoked in EVERY endpoint that generates AI output: plan generation, chat messages, meal analysis, what-to-eat-now, adapt-plan.
- Add a `settings` screen that allows medical condition updates, and re-run risk assessment on save.
- For `clinical_review_required` users, every AI response must prepend a disclaimer; the system should never silently downgrade a risk level without explicit user confirmation.
- Log every guardrail evaluation in `AuditLog` with the triggering conditions — critical for liability.
- Implement a "dead man's switch": if the user has not completed onboarding or their risk assessment is stale (>90 days), block AI plan generation with a re-assessment prompt.

**Warning signs:**
- `SafetyGuardrailService` is only called from `NutritionPlanService`
- Chat endpoint calls AI directly without consulting the user's `risk_level`
- No `AuditLog` entries for guardrail decisions
- Risk level can only be set, never updated post-onboarding

**Phase to address:** AI Agent / Safety Guardrails phase, and verified again in Chat Companion phase

---

### Pitfall 6: Next.js App Router i18n — Dictionary-Based i18n Without Locale in URL Breaks Back/Forward and SEO

**What goes wrong:**
The project uses a custom dictionary-based i18n (no next-intl/i18next). If locale is stored only in `localStorage` or a React context (not in the URL), the following breaks: (1) server components cannot access the locale without a cookie/header read; (2) browser back/forward navigation loses locale context; (3) sharing a URL sends the wrong language to the recipient; (4) Next.js App Router's static optimization and caching is per-URL — locale in state means one cached page for all languages.

**Why it happens:**
Dictionary-based i18n feels simpler. Developers put the locale in a React context initialized from localStorage. Server components don't have access to localStorage at all.

**How to avoid:**
- Store locale in a cookie (readable server-side via `cookies()` in server components). Set it as `httpOnly: false` so client can read it for instant hydration without flicker.
- OR use Next.js route segments: `/[lang]/...` so locale is in the URL. This is the recommended App Router pattern.
- A `middleware.ts` that reads the `Accept-Language` header and the cookie, redirects to the correct locale segment, and sets `x-locale` header for server components.
- The `UserLanguagePreference` model storing locale in DB is correct — sync it to the cookie on login.

**Warning signs:**
- `useContext(LocaleContext)` called in a server component (will fail silently — returns undefined)
- `localStorage.getItem('lang')` used to initialize locale (inaccessible during SSR)
- All 3 languages sharing the same URL (no `/fa/`, `/en/`, `/ar/` segments)
- Direction flicker on page load (RTL page momentarily renders LTR before JS hydrates)

**Phase to address:** i18n / Frontend Foundation phase

---

### Pitfall 7: MediaRecorder API — Cross-Browser Audio Format Incompatibility Causes Silent Upload Failures

**What goes wrong:**
`MediaRecorder` defaults to different codecs per browser: Chrome records `audio/webm;codecs=opus`, Safari records `audio/mp4` (when supported at all — Safari < 14.1 has no MediaRecorder), Firefox records `audio/ogg;codecs=opus`. The backend receives audio blobs with wrong MIME types and cannot transcode. The upload "succeeds" (200 response) but the audio file is unplayable or rejected by the STT service later.

**Why it happens:**
Developers test only in Chrome. `MediaRecorder.isTypeSupported()` is rarely called. The backend accepts `multipart/form-data` and saves whatever bytes it receives without validating the audio container.

**How to avoid:**
- Use `MediaRecorder.isTypeSupported()` at initialization time to select the best supported format in priority order: `audio/webm;codecs=opus` → `audio/mp4` → `audio/ogg;codecs=opus`.
- Always pass the selected `mimeType` to `new MediaRecorder(stream, { mimeType })` — never let the browser choose silently.
- Send the MIME type as a form field alongside the blob: `formData.append('mime_type', mimeType)`.
- Backend: store the original MIME type in `AudioMessage.mime_type` and reject unsupported types with 415.
- For preview playback, use `URL.createObjectURL(blob)` with the blob's type set explicitly: `new Blob(chunks, { type: mimeType })`.
- iOS Safari (15+) supports MediaRecorder but requires `audio/mp4` — test on real iOS, not just Chrome DevTools mobile emulation.

**Warning signs:**
- `new MediaRecorder(stream)` without `mimeType` option
- Audio preview works in Chrome but fails on Safari
- Backend receives `application/octet-stream` instead of a valid audio MIME type
- STT architecture shows `status: pending` but no MIME type stored in DB

**Phase to address:** Voice Recording / Onboarding Chat phase

---

### Pitfall 8: AI Provider Abstraction — Prompt Context Window Blown by Untruncated Conversation History

**What goes wrong:**
`NutritionMemoryService` retrieves full chat history and feeds it all into the prompt. After 20-30 exchanges, the context window limit is hit. The AI call fails with a 400/429 error, or the provider silently truncates — cutting out the system prompt (which contains safety rules and medical flags) rather than old messages. The guardrails disappear from the conversation without any warning.

**Why it happens:**
MVP uses mock AI — context limits are never hit during development. When a real provider is wired in, the first production user with a long session hits the limit.

**How to avoid:**
- `PromptBuilder` must count tokens (estimate: 1 token ≈ 4 chars for Latin text, ≈ 2-3 chars for Persian/Arabic) and truncate conversation history from the *oldest* end, never from the system prompt or recent messages.
- Set a hard budget: reserve 20% for system prompt + medical flags + current message. Use the remaining 80% for history.
- Implement summary compression: after 15 turns, summarize the oldest 10 turns into a single "conversation summary" message and replace them.
- Always place the safety/medical context in the system prompt, never in user/assistant history — so it cannot be truncated by history pruning.

**Warning signs:**
- `NutritionMemoryService.get_history()` returns all messages with no limit
- `PromptBuilder` concatenates history without token counting
- No `max_tokens` budget in prompt configuration
- API errors in logs containing "context_length_exceeded" or similar

**Phase to address:** AI Agent / Provider Abstraction phase

---

### Pitfall 9: Onboarding Flow State — Multi-Step Form State Lost on Browser Refresh or Back Navigation

**What goes wrong:**
The 7-step onboarding stores state in React `useState`. A browser refresh on step 4 sends the user back to step 1 with all data cleared. Back navigation (browser back button) bypasses the step logic and goes to the previous URL instead of the previous step. On mobile, the keyboard covering the input triggers a layout shift that causes accidental navigation away from the current step.

**Why it happens:**
Multi-step forms are complex state machines. React state is in-memory only. Developers use URL hash or query params for step tracking but don't persist partial form data.

**How to avoid:**
- Persist partial onboarding state to `sessionStorage` (not `localStorage` — onboarding is a one-time session event) after each step completion. On mount, hydrate from `sessionStorage`.
- Use URL-based step navigation (`/onboarding?step=4`) so the back button goes to step 3, not out of onboarding. Intercept popstate events to handle the back button correctly.
- On each successful step API call, mark the step complete in the DB via the onboarding step endpoints. On session restore, query the last completed step from the backend and resume from there.
- Disable browser back button exit from onboarding: intercept `beforeunload` / `popstate` and confirm exit intent.
- Keep `sessionStorage` hydration synchronous (in layout effect) to avoid a flash of step 1 before restoring step 4.

**Warning signs:**
- All onboarding state in a single top-level `useState` with no persistence
- `/onboarding` is a single URL regardless of which step is active
- No step-completion tracking in the backend during onboarding (only the final `complete` endpoint)
- Refresh on step 5 sends user to step 1

**Phase to address:** Onboarding flow phase

---

### Pitfall 10: FastAPI + Phone OTP — OTP Brute-Force Not Throttled, Enumeration Possible

**What goes wrong:**
The `verify-otp` endpoint accepts unlimited attempts. An attacker can enumerate valid phone numbers by observing "OTP invalid" vs "phone not found" response differences. With 6-digit OTPs and no rate limiting, brute-forcing a specific phone takes at most 1 million requests (often far fewer if the OTP is a sequential timestamp-seeded value).

**Why it happens:**
Dev mode uses `123456` fixed OTP — nobody tests brute-forcing against a static code. Rate limiting is "a production concern" that never gets added.

**How to avoid:**
- Implement per-phone-number rate limiting on both `request-otp` (max 3 requests per 10 minutes) and `verify-otp` (max 5 attempts per OTP, then invalidate).
- After 5 failed verifications, mark the `AuthOTP` record as `invalidated` and require requesting a new OTP.
- Return identical error messages for "phone not found" and "OTP invalid" to prevent enumeration (`"Invalid OTP or phone number"`).
- OTP generation must use `secrets.randbelow(1000000)` — never `random.randint()`, which is not cryptographically secure.
- In dev mode, rate limiting should be configurable off, but the code path must exist.

**Warning signs:**
- `verify-otp` returns `"Phone not found"` as a distinct error from `"OTP invalid"`
- No `attempt_count` field on `AuthOTP` model
- `random.randint(100000, 999999)` in OTP generation (not `secrets`)
- No rate limiting middleware on auth routes

**Phase to address:** Authentication phase

---

### Pitfall 11: Mobile-First in Next.js — Viewport Height (`100vh`) Breaks on iOS Safari Due to Dynamic Address Bar

**What goes wrong:**
Setting `height: 100vh` on full-screen layouts (splash, onboarding steps, chat) causes content to be cut off on iOS Safari because `100vh` equals the full viewport height *including* the collapsible address bar. When the address bar is visible, content is clipped at the bottom. The chat input field ends up behind the system keyboard + address bar.

**Why it happens:**
Chrome on desktop and Android handles `100vh` differently from iOS Safari. Developers test on Chrome DevTools mobile emulation, which doesn't replicate iOS Safari's dynamic viewport.

**How to avoid:**
- Use `min-height: 100dvh` (`dvh` = dynamic viewport height) where available. Add `min-h-[100dvh]` in Tailwind (custom config) with `min-h-screen` as fallback.
- For the chat input that needs to stay above the keyboard: use `position: fixed; bottom: 0` with `padding-bottom: env(safe-area-inset-bottom)` to account for iOS home indicator.
- Set `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` — required for `safe-area-inset-*` CSS env variables to work.
- Avoid JavaScript-based viewport height calculation (`window.innerHeight`) for layout — it fires after layout, causing visible jump.

**Warning signs:**
- `h-screen` or `min-h-screen` on full-page layouts without `dvh` fallback
- Chat input not using `env(safe-area-inset-bottom)`
- Viewport meta tag missing `viewport-fit=cover`
- Testing only in Chrome DevTools, not real iOS Safari

**Phase to address:** Frontend foundation / Mobile layout phase (before building any full-screen view)

---

### Pitfall 12: Direction-Aware Slide Animations — Using Framer Motion `x` Values Without Direction Awareness

**What goes wrong:**
The 7-step onboarding uses slide animations: step N slides out to the left, step N+1 slides in from the right (LTR). In RTL, this should be reversed: step N slides out to the right, step N+1 slides in from the left. Hard-coding `initial: { x: '100%' }` and `exit: { x: '-100%' }` means Persian users see the opposite of natural reading direction, which feels disorienting and broken.

**Why it happens:**
Animation libraries default to LTR. RTL animation direction is not a first-class feature in most animation libraries. Developers test in English and miss this entirely.

**How to avoid:**
- Create a `useSlideDirection(stepDelta: number)` hook that returns `{ initial, exit }` based on `isRTL` and whether navigating forward or backward:
  - LTR forward: `initial: { x: '100%' }`, exit: `{ x: '-100%' }`
  - RTL forward: `initial: { x: '-100%' }`, exit: `{ x: '100%' }`
  - Reverse for backward navigation
- Never use pixel or percent values for slide direction — always derive from direction context.
- Test the onboarding flow with `lang=fa` on the first animation written, not after all 7 steps are built.

**Warning signs:**
- Hard-coded `x: '100%'` / `x: '-100%'` in animation variants without a direction multiplier
- Animations only tested in English locale
- No `isRTL` variable in animation configuration files

**Phase to address:** Onboarding animation phase

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single `AsyncSession` dependency across all routes without connection pooling config | Simple setup | SQLite write contention under concurrent requests; "database is locked" errors | MVP with single user — add WAL mode immediately: `PRAGMA journal_mode=WAL` |
| Storing JWT in `localStorage` instead of `httpOnly` cookie | Simpler client code | XSS vulnerability exposes all health/medical data | Never for a health app |
| Mock AI responses as string literals in service code | Fast MVP | Impossible to test prompt logic; mock and real have divergent behavior | Only if mocks are in a separate fixture file, not inline in production service |
| Physical Tailwind classes (`ml-`, `mr-`) with separate RTL overrides (`rtl:ml-0 rtl:mr-4`) | Familiar syntax | Doubles every spacing declaration; easy to miss overrides | Never — use logical properties from the start |
| Inline `dir` toggling with JS after hydration instead of SSR-rendered `dir` attribute | Avoids SSR complexity | Direction flicker on every page load; bad UX for RTL users | Never — render `dir` server-side from cookie/locale |
| Calling `alembic revision --autogenerate` without reviewing the generated migration | Faster development | Autogenerate misses SQLite incompatibilities and type changes; migrations drift | Always review generated migrations before applying |
| No `AuditLog` table in Phase 1 | Simpler data model | Cannot reconstruct what guardrail decisions were made for a given user session | Never for a medical app — AuditLog must be in Phase 1 |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastAPI + SQLAlchemy async | Using `Session` (sync) instead of `AsyncSession` in async routes — works locally, causes thread blocking in production | Import `AsyncSession` from `sqlalchemy.ext.asyncio`; never mix sync and async session in the same request |
| Alembic + SQLite | Running `env.py` without `render_as_batch=True` — first migration with a column type change silently corrupts schema | Set `render_as_batch=True` in `env.py` `configure()` call before writing any migrations |
| Next.js App Router + server components + i18n | Accessing locale from React context or localStorage in server components — returns undefined at render time | Read locale from `cookies()` (server) or `useParams()` (client); pass as prop to shared components |
| MediaRecorder + backend | Sending audio blob without MIME type information — backend stores as `application/octet-stream`, later STT fails | Always append `mime_type` field to FormData; validate MIME type on backend before storing |
| JWT + FastAPI + httpOnly cookies | Setting cookie with `SameSite=Strict` — CORS preflight for API calls from different port in dev fails; cookie not sent | Use `SameSite=Lax` for cookie auth; add explicit CORS config for dev origins |
| AI provider abstraction + Pydantic v2 | Using `BaseModel` with `model_validate(obj)` where `obj` is a SQLAlchemy ORM instance — Pydantic v2 does not auto-convert ORM models | Use `model_validate(obj, from_attributes=True)` or configure `model_config = ConfigDict(from_attributes=True)` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full chat history on every `/chat/message` call to build prompt context | Chat slows as conversation grows; response latency grows linearly | Paginate history retrieval in `NutritionMemoryService`; cache summarized context | After ~30 messages per session |
| No SQLite WAL mode — default journal mode causes "database is locked" on concurrent reads+writes | Random 500 errors when multiple API calls hit simultaneously (e.g., onboarding API + chat API in same session) | Enable `PRAGMA journal_mode=WAL` at DB init via SQLAlchemy event listener | With 2+ concurrent connections |
| Fetching entire `NutritionProfile` with all relationships on every AI call | Slow AI responses; heavy DB queries on every message | Cache the nutrition profile in Redis/memory for the session duration; invalidate on profile update | After 50+ active users |
| React re-renders on every keystroke in the chat input rebuilding the full message list | Visible lag in chat UI, especially on lower-end mobile | Memoize message list with `React.memo`; separate input state from message list state | On mid-range Android devices |
| Audio blob created as single large `Blob` after all chunks — blocks main thread on long recordings | Browser freezes during audio processing for recordings >30 seconds | Stream chunks to a Web Worker or use `ReadableStream`; process chunks incrementally | Recordings over ~20-30 seconds |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Medical condition data returned in public API response without auth check | User's diabetes, pregnancy, eating disorder status exposed to anyone with a phone number | Every endpoint returning `NutritionProfile` or `MedicalCondition` data must require valid JWT; add integration test asserting 401 without token |
| OTP generated with `random.randint()` | Predictable OTP if attacker knows server time (seeded PRNG) | Use `secrets.randbelow(1_000_000)` from Python's `secrets` module |
| Audio files stored with user-guessable filenames (`user_123_recording_1.webm`) | Medical voice recordings accessible by guessing URL patterns | Store with UUID filenames; serve through authenticated endpoint, never as static files |
| `CORS(app, allow_origins=["*"])` in production | Any website can make authenticated requests to the API using the user's cookies | Enumerate explicit allowed origins; never use wildcard with `allow_credentials=True` |
| Pydantic models exposing internal fields (risk_level, audit flags) in API responses | Internal risk classification exposed to client; user can see their own `clinical_review_required` flag in a raw form that causes alarm without context | Use separate response schemas that explicitly include only safe-to-expose fields; never use ORM models as response schemas directly |
| JWT secret loaded from code default (`SECRET_KEY = "changeme"`) | Token forgery if secret is known | Load from `settings.SECRET_KEY` with no default; startup fails if not set via environment |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing BMI number prominently on the dashboard | BMI is a poor proxy for health; Persian/Iranian users (and users with PCOS, hypothyroid) may have clinically misleading BMI values; leads to distorted self-image | Show behavioral wins and trend direction, not absolute BMI; if shown, always contextualise with "not a complete health measure" |
| Progress screen showing only weight graph | Discourages users on plateau weeks; weight fluctuates daily due to water retention | Show multi-metric dashboard: behavior wins, protein intake consistency, fiber, water, sleep adherence — not just weight |
| Disabling "send" while audio is recording (no visual feedback that recording is active) | User taps send repeatedly, causing confusion | Show clear recording state (animated waveform, recording duration timer); disable send with a tooltip "Recording in progress — tap stop first" |
| Hard "clinical review required" block with no path forward shown to user | User hits the wall with no explanation and abandons the app | Always show "clinical review required" state with: (1) explanation in plain language, (2) what to do next (consult a dietitian), (3) what the app CAN still do for them (general healthy eating guidance) |
| Language switcher changes locale but resets all unsaved onboarding form state | Persian user starts onboarding in English, switches mid-way — loses 3 steps of data | Persist form state to `sessionStorage` before any locale change; restore after redirect |
| Onboarding "7 steps" shown as step counter without progress indicator | Users don't know how long the form is; drop-off increases with each step | Show a progress bar (e.g., "Step 4 of 7") and estimated time remaining ("~2 minutes left") from step 3 onward |

---

## "Looks Done But Isn't" Checklist

- [ ] **JWT Auth:** Logout endpoint exists — verify it actually invalidates the token server-side, not just returns 200
- [ ] **RTL Layout:** Switch app to Persian locale and check every screen — don't just set `dir="rtl"`, actually render Persian text to expose layout bugs
- [ ] **Alembic Migrations:** Run `alembic upgrade head` against a *blank* SQLite file (not the dev DB) — verify all migrations apply cleanly from scratch
- [ ] **Medical Guardrails:** Call the chat endpoint directly (bypass onboarding) with a user who has `risk_level=clinical_review_required` — verify guardrail fires in chat, not only in plan generation
- [ ] **MediaRecorder:** Test voice recording on Safari/iOS (not Chrome DevTools) — verify audio is playable before sending and MIME type is stored in DB
- [ ] **Onboarding State:** Refresh the browser on step 4 of onboarding — verify user is returned to step 4 (not step 1) and data is not lost
- [ ] **OTP Rate Limiting:** Submit incorrect OTP 6 times — verify the OTP is invalidated and a new one must be requested
- [ ] **Animation Direction:** Complete the onboarding flow in Persian — verify slide animations go right-to-left on forward navigation
- [ ] **AI Context Limit:** Send 30+ messages in a session — verify the prompt does not exceed context window and guardrail system prompt is still present
- [ ] **Mobile Viewport:** Open the app on a real iPhone (not emulator) — verify chat input is visible above keyboard and no content is clipped by the address bar

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Alembic migrations broken due to missing `render_as_batch=True` | HIGH | Add `render_as_batch=True` to `env.py`; squash all existing migrations into one baseline migration; test fresh DB apply |
| Physical CSS properties throughout the codebase | HIGH | Automated codemod replacing `ml-` → `ms-`, `mr-` → `me-`, etc.; manual review of each changed component; regression test in RTL locale |
| JWT tokens not revocable | MEDIUM | Add `jti` + `revoked_tokens` table in a new migration; update auth middleware to check; existing sessions expire naturally per their `exp` claim |
| Medical guardrail only in plan generation, not in chat | MEDIUM | Extract `SafetyGuardrailService.check()` call to a FastAPI dependency; inject into all AI-generating endpoints; add test coverage |
| Onboarding state not persisted | LOW | Add `sessionStorage` hydration to onboarding root component; add step-completion tracking to existing onboarding endpoints |
| Audio MIME type not stored | LOW | Add migration to add `mime_type` column to `AudioMessage`; update upload handler to extract and store MIME type |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| SQLAlchemy async lazy loading | Infrastructure / Backend Foundation | `lazy="raise"` on all relationships; `DetachedInstanceError` never appears in test suite |
| Alembic + SQLite `render_as_batch` | Infrastructure / Database Setup | `alembic upgrade head` passes on blank DB in CI |
| JWT revocation gap | Authentication Phase | Logout invalidates token server-side; POST to protected endpoint with revoked token returns 401 |
| RTL physical CSS properties | i18n / Frontend Foundation | ESLint rule or grep finds zero `ml-`, `mr-`, `pl-`, `pr-` in components |
| Medical guardrail — stale re-evaluation | AI Agent / Safety Phase | Integration test: `clinical_review_required` user blocked in chat endpoint |
| i18n locale in React context only | i18n / Frontend Foundation | Server component renders with correct locale without JS; no flicker on load |
| MediaRecorder MIME type | Voice Recording / Onboarding Chat | Real iOS Safari test: recording uploads successfully and MIME type stored |
| AI context window overflow | AI Agent / Provider Abstraction Phase | Token counting in `PromptBuilder`; long-session test hits budget cap gracefully |
| Onboarding state on refresh | Onboarding Flow Phase | Playwright test: navigate to step 4, refresh, verify step 4 rendered with data |
| OTP brute-force | Authentication Phase | 6 failed attempts invalidates OTP; uniform error message for bad phone vs bad OTP |
| iOS `100vh` viewport | Frontend Foundation / Mobile Layout | Real iPhone test: full-screen views not clipped; chat input above keyboard |
| Animation direction in RTL | Onboarding Animation / i18n | Forward navigation in Persian slides right-to-left (verified in Playwright with `dir="rtl"`) |

---

## Sources

- SQLAlchemy 2.x asyncio documentation — `sqlalchemy.ext.asyncio` — async session patterns and `lazy="raise"` (HIGH confidence, official docs)
- Alembic batch operations documentation — SQLite ALTER TABLE limitations and `render_as_batch` (HIGH confidence, official docs)
- FastAPI security documentation — JWT, cookie security, CORS (HIGH confidence, official docs)
- CSS logical properties specification — MDN Web Docs (HIGH confidence, official)
- Tailwind CSS v3 logical property utilities (`ms-`, `me-`, `ps-`, `pe-`) — (HIGH confidence, Tailwind docs)
- MediaRecorder API — MDN Web Docs, browser compatibility table (HIGH confidence, official)
- Next.js App Router documentation — cookie access in server components, middleware patterns (HIGH confidence, official docs)
- iOS Safari viewport height behavior with dynamic address bar — `dvh` unit browser support (MEDIUM confidence — browser behavior documented in CSS Working Group)
- Medical health app safety guardrail patterns — clinical nutrition app design principles (MEDIUM confidence — domain knowledge, not a single official source)
- Persian/Arabic RTL animation UX guidelines — Material Design RTL documentation, Apple HIG Arabic/RTL (MEDIUM confidence)

---
*Pitfalls research for: AI-powered multilingual diet coach agent (FastAPI + Next.js, Persian-first RTL)*
*Researched: 2026-06-03*
