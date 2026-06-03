# Feature Landscape: AI-Powered Multilingual Diet Coach Agent

**Domain:** AI nutrition and diet coaching (mobile-first PWA, Persian-first, RTL-native)
**Researched:** 2026-06-03
**Confidence:** MEDIUM (training knowledge + project-context analysis; WebSearch unavailable)

---

## Table Stakes

Features users expect from any AI-powered diet/nutrition app. Missing = product feels incomplete or users leave within first week.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Personalized nutrition plan | Core value proposition — "generic diet" kills retention immediately | High | Must account for goals, medical flags, activity, food culture |
| Calorie and macro targets | Users expect numbers (kcal, protein, carbs, fat) as a baseline signal | Med | Must be calculated from anthropometrics + goals, not hardcoded |
| Meal logging or meal suggestions | Without this, "diet app" feels hollow — users need daily action | High | This project skips self-logging; uses AI suggestion + what-to-eat flow instead |
| Daily check-in | Users need a feedback loop; without it app feels like a static PDF | Med | Weight, hunger, sleep, stress, adherence — all needed for adaptive coaching |
| Progress tracking | Users leave if they can't see movement; even small wins matter | Med | Must NOT be weight-only — behavior wins, adherence, consistency matter |
| Medical screening / safety gate | Without this, AI advice can be dangerous; also required for trust and legal defensibility | High | Diabetes, kidney, pregnancy, eating disorders require either a guardrail or referral |
| Conversational chat interface | In 2025, users expect to "talk" to their AI coach, not just fill forms | Med | Text-first is table stakes; voice is a differentiator |
| Onboarding that feels personal | Generic health apps with cold starts have terrible retention | High | Users must feel understood in step 1; 7-step flow in this project is the right depth |
| Goal selection (not just "lose weight") | Modern users have nuanced goals — PCOS, pregnancy, sports, muscle gain | Med | 12+ goal types are needed to serve this market |
| Food culture relevance | Persian-speaking users expect Iranian foods — not just pizza and salad | High | Ghormeh sabzi, ash, doogh, rice dishes must be in vocabulary |
| Multilingual + RTL UI | Persian and Arabic speakers will not tolerate LTR-forced layouts | High | RTL is not cosmetic — it fundamentally affects perceived quality for this market |
| Auth that fits local norms | Persian market uses phone number, not email — email OTP feels foreign | Med | Phone OTP is correct choice; email/password would be a friction point |
| Privacy and data trust signaling | Health data is sensitive; users need to trust the product visually and legally | Med | Medical data handling statements, clear consent in onboarding |

---

## Differentiators

Features that set this product apart from generic calorie trackers or Western-only apps. Not universally expected, but create strong retention and word-of-mouth.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Persian food intelligence | No English-language diet app covers Iranian cuisine deeply — huge gap in market | High | Rice dishes, stews, ash, fast food (kotlet, omelet), doogh, halim, must-have |
| Voice input in Persian | Speaking to AI in Farsi is rare in any health app; strong emotional resonance | High | STT for Persian is the hard part; architecture prepared but deferred to post-v1 |
| Behavior-aware coaching | Most apps track food; few address emotional eating, night eating, binge cycles | High | Behavior profile from onboarding enables truly personalized coaching |
| Adaptive plan modification | "My plan changed today" — user context updates should reshape the plan | High | `adapt-plan` endpoint is the right investment; most apps ignore this |
| Weekly insight reports | Users love summaries with narrative — not just charts | Med | Sleep/stress/adherence correlation is a differentiator; most apps show only weight |
| Risk stratification + clinical referral | Surfacing "you need a dietitian" at the right moment builds trust | Med | `clinical_review_required` flag with appropriate messaging is rare and valuable |
| Waveform visualizer for voice | Tiny UX detail with outsized trust signal — "this thing is listening" | Med | Web Audio API AnalyserNode; keeps users engaged during recording |
| "What should I eat now?" flow | Real-time contextual meal suggestion is different from a static plan | High | Must be context-aware (time of day, recent meals, goals, fridge) |
| Direction-aware animations | RTL slide direction in onboarding feels native to Persian speakers | Med | Almost no competitor does this; high perceived quality signal |
| Habit and behavior gap detection | Detecting night eating, meal skipping, emotional eating patterns and naming them | High | Requires behavior profile + AI synthesis; creates aha moments for users |
| Culturally-aware language tone | Formal vs. informal Persian, respectful tone for health topics, culturally appropriate framing | Med | Prompts must be tuned for Persian cultural norms — not translated English |
| Iranian goal archetypes | PCOS is extremely prevalent in Iran; pregnancy nutrition is high-stakes; sports + fasting are culturally relevant goals | High | These goal types are often absent from Western apps — local differentiation |

---

## Anti-Features

Features to explicitly NOT build — they waste engineering time, degrade UX, or create liability.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Barcode / food label scanner | Complex computer vision, food databases require licensing, maintenance is high — not core to the user journey here | Use AI text chat to ask "what did you eat?" or structured meal suggestion |
| Wearable integration (Fitbit, Apple Health, Garmin) | API maintenance burden, platform fragmentation, scope creep; most users in target market don't use wearables | Manual activity input in daily check-in is sufficient for v1 |
| Social / community features | Requires moderation, content policies, abuse handling; adds complexity before core is solid | Focus on 1:1 AI companion; community can be a v2 play |
| Recipe database browser | Recipe crawling is a separate product; copyright issues; not core to coaching | Generate meal suggestions with ingredients, link to external recipes if needed |
| Gamification (streaks, badges, leaderboards) | Gamification without a strong core product is noise; streak anxiety is a known retention anti-pattern | Progress wins and narrative reports are the right motivation layer |
| In-app calorie calculator / manual food log | Logging fatigue is the #1 reason users abandon diet apps (proven by Noom's pivot away from calorie counting) | Use AI to infer and advise; check-in captures adherence signal instead |
| Detailed micronutrient tracking (all 30+ vitamins/minerals) | Overwhelms users; creates anxiety without clinical benefit for general population | Surface only actionable deficits (protein, fiber, water) — not exhaustive nutrition labels |
| Push notifications (v1) | High effort, platform-specific, and notification fatigue is real; users will disable them quickly | Daily check-in as a habit loop is sufficient; defer notifications to post-v1 |
| Payment / subscription (v1) | Premature monetization before product-market fit is validated is a distraction | Validate core value first; payment infrastructure can be added in one sprint |
| Email/password auth | Persian market does not use email as primary auth; password recovery adds support burden | Phone OTP is correct and sufficient |
| AI-generated meal images | Generative images have quality issues, hallucinate impossible dishes, and add cost without trust | Text-based meal description is more useful and trustworthy for this use case |
| Multi-user / family plan | Adds role complexity, data isolation challenges, and support burden — not validated by any user yet | Focus on single-user excellence first |
| Native iOS/Android app (v1) | React Native / Swift / Kotlin is a separate project; PWA covers the use case | PWA with mobile-first layout is sufficient for v1 validation |
| Human nutritionist live chat | Requires staffing, scheduling, liability; also blurs the AI coaching proposition | Surface `clinical_review_required` state with referral suggestion instead |

---

## Feature Dependencies

```
Phone OTP Auth
  └─> Onboarding (requires authenticated user)
        └─> Behavior Profile (step 6)
              └─> NutritionProfile creation
                    └─> Risk Assessment (medical flags from step 3)
                          └─> Plan Generation (blocked if clinical_review_required)
                          └─> Daily Chat Companion (context from profile)
                          └─> "What to Eat Now" (context from profile + recent check-ins)
                    └─> Weekly Report (requires DailyCheckIn history)
                          └─> Adaptive Plan (uses weekly report signals)

Voice Input (onboarding chat)
  └─> MediaRecorder API
        └─> Audio upload to backend
              └─> STT architecture (prepared, not wired in v1)
                    └─> Transcript fed to NutritionAgent (post-v1)

i18n / RTL
  └─> Direction-aware animations (depends on locale detection)
  └─> Persian food intelligence (depends on locale = fa)
  └─> Culturally-aware prompts (depends on locale in AI prompt builder)
```

---

## Persian / Iranian Market-Specific Features

These are features that are irrelevant or low-value in Western markets but critical for the target audience.

| Feature | Market Reason | Complexity | Priority |
|---------|---------------|------------|----------|
| Persian food vocabulary | Iranian diet is built on rice, bread, stews, legumes — English food DBs are useless | High | Critical |
| PCOS-specific goal path | Iran has among the highest PCOS rates globally; users will expect PCOS-aware advice | High | Critical |
| Ramadan / fasting mode | Intermittent fasting structured around Islamic fasting norms is a real coaching scenario | Med | v2 |
| Halal diet adherence | Food preferences must include halal/haram awareness; no pork/alcohol in suggestions | Low | Must-have (simple) |
| Dizi, ash, adasi, ghormeh sabzi, chelokabab | Specific dishes that must be in the AI's food vocabulary with accurate nutritional profiles | Med | Critical |
| Doogh, dogh (probiotic drink) | Common daily drink; must be in calorie/nutrition vocabulary | Low | Must-have |
| Persian tea (chai) + sugar cube | Ubiquitous; affects daily sugar intake; must appear in suggestions and logging | Low | Must-have |
| Local fast food (kotlet, omelet, sangak) | Iranian fast food is distinct from Western fast food; must be recognized | Med | High |
| Casual/formal Persian register | AI coaching tone in Persian must match social norms — neither too clinical nor too casual | Med | High |
| Phone number auth (09xx format) | Iranian phone numbers start with 09; validation must accept this format | Low | Critical |

---

## Safety and Medical Guardrail Patterns

Based on clinical best practices and regulatory expectations for AI health apps.

| Guardrail | Trigger Condition | Response Pattern | Complexity |
|-----------|-------------------|-----------------|------------|
| Clinical review gate | Diabetes + medication, kidney disease, pregnancy, eating disorder, bariatric surgery | Block plan generation; surface referral message; do not provide specific advice | Med |
| Conservative calorie floor | Never recommend below 1200 kcal/day for women, 1500 for men regardless of goal | Hard-coded minimum in plan generation | Low |
| Eating disorder flag | Binge history, purging, extreme restriction history in behavior profile | Route to `clinical_review_required`; never engage with restriction coaching | Med |
| Symptom red flags | Chest pain, fainting, extreme fatigue, edema in onboarding step 3 | Immediate referral message; do not proceed to plan | High |
| "I'm not a doctor" framing | Every AI response that touches medical context | Consistent disclaimer pattern in prompt templates | Low |
| Pregnancy nutrition guardrails | Pregnancy goal selected | Only general safe advice; block specific restriction goals; refer to OB | Med |
| Drug-nutrient interaction awareness | Medications field in onboarding | Flag in risk assessment; escalate to `medium` or `high` risk level | High |
| No weight loss target below BMI 18.5 | Underweight users selecting weight loss goal | Redirect to maintenance or muscle gain; do not generate deficit plan | Low |
| Data deletion / user control | GDPR / Iranian data norms | Account deletion must purge all health data; clear in settings | Med |

---

## Voice and Audio Features for Health Apps

| Feature | Value | Complexity | When to Build |
|---------|-------|------------|---------------|
| Voice recording in chat (MediaRecorder) | Reduces friction for meal reporting, emotional check-ins; natural for mobile | Med | v1 (architecture in place) |
| Audio waveform visualizer | Trust signal — user sees app is "listening"; reduces uncertainty during recording | Med | v1 (included in PROJECT.md) |
| Record / pause / cancel / preview controls | Standard UX contract for voice input — missing any of these creates friction | Med | v1 |
| STT transcription (Farsi) | Convert voice to text for AI processing — unlocks full voice coaching | High | Post-v1 (architecture prepared) |
| Text-to-speech AI responses | AI "speaks back" the plan or coaching message in Persian | Very High | v3+ |
| Background noise handling | Health apps often used in kitchen; microphone quality varies | High | Post-v1 |

---

## Onboarding Flow Best Practices for Health Apps

Based on patterns from Noom, Fastic, Lifesum, and research on health app retention.

| Practice | Rationale | Applied in This Project? |
|----------|-----------|--------------------------|
| Front-load motivation and goal selection | Users who articulate a goal in step 1 are 3x more likely to complete onboarding | Yes — step 2 is goal selection |
| Keep medical screening non-alarming | Clinical questions cause drop-off if framed medically; frame as "helping personalize" | Partially — wording matters in implementation |
| Progress indicator (step X of N) | Users abandon multi-step flows without knowing how long they are | Implied in 7-step flow; must be visible |
| Collect behavior patterns, not just physiology | Body metrics are table stakes; behavior drives coaching quality | Yes — step 6 is behavior profile |
| Gate the plan behind a commitment signal | Watching the intro video before getting the plan creates perceived value | Yes — step 7 video gate |
| Celebrate completion | Users need a moment of "you're set up" before entering the app | Should be in the final step transition |
| Save-and-resume (partial onboarding) | Users drop off at medical screening; resuming from where they left is critical for completion | Not explicitly in PROJECT.md — should be added |
| No dead-end on medical flag | Flagged users must receive a clear next step, not just "you can't use this" | Yes — `clinical_review_required` state has a screen |
| Mobile-first input methods | Number pickers, sliders, and option tiles are better than text fields on mobile | Design-level concern; must be in UI |
| Cultural framing for health goals | "Health" framed as vitality and family wellness resonates more than weight stigma in Persian culture | Should inform copy and prompts |

---

## MVP Recommendation

### Must Ship (v1 core)

1. Phone OTP auth (Persian market expectation)
2. 7-step onboarding with medical screening and behavior profile
3. AI-generated personalized nutrition plan (with mock AI fallback)
4. Medical safety guardrails (clinical_review_required gate)
5. Daily check-in (simple, low-friction)
6. "What should I eat now?" contextual suggestion
7. Conversational chat companion (text-first)
8. Persian food intelligence vocabulary
9. Full RTL + i18n (Persian default, English/Arabic ready)
10. Progress dashboard (behavior-centric, not weight-only)
11. Voice recording in onboarding chat (MediaRecorder, STT deferred)

### Defer to Post-v1

- Real STT/transcription for Persian (architecture prepared, deferred)
- Real AI provider wiring (mock AI ships first)
- Adaptive plan based on weekly report (v1.5)
- Image-based meal analysis (v2)
- Ramadan/fasting mode (v2)
- Push notifications (v2)
- Native app (v3)

---

## Feature Risk Register

| Feature | Risk | Mitigation |
|---------|------|------------|
| Persian food intelligence | AI (mocked in v1) may not know accurate kcal for Iranian dishes | Pre-populate a food reference JSON for common dishes |
| Medical guardrails | Wrong risk classification could harm a user | Err conservatively — prefer `clinical_review_required` over guessing |
| Voice recording in browser | MediaRecorder API is not supported in all WebViews (iOS WKWebView has quirks) | Test on iOS Safari explicitly; provide text fallback |
| RTL animations | CSS transform + direction interaction has known Webkit bugs | Test direction-aware transitions on iOS Safari |
| Behavior profile depth (step 6) | Long questionnaires cause drop-off | Make step 6 skippable with defaults; backfill from chat |
| STT deferred | Users who record voice in v1 get no AI response to their voice message | Clear "voice received, coach will process" message; never leave user without acknowledgment |
| Mock AI responses | Users will detect canned responses quickly if not varied | Seed at least 20+ deterministic response variants; randomize by goal type |

---

## Sources

- Project context: `.planning/PROJECT.md` (HIGH confidence — source of truth for this project)
- Noom, MyFitnessPal, Cronometer feature analysis: MEDIUM confidence (training knowledge, ~2024-2025)
- Persian market dietary patterns and PCOS prevalence: MEDIUM confidence (training knowledge)
- Web Audio API AnalyserNode / MediaRecorder API capabilities: HIGH confidence (well-documented Web APIs)
- Medical safety guardrail patterns for health AI apps: MEDIUM confidence (training knowledge; verify against current FDA/EU AI Act guidelines before legal exposure)
- RTL CSS patterns and WebKit animation bugs: MEDIUM confidence (training knowledge; verify with live browser testing)
- Onboarding best practices: MEDIUM confidence (training knowledge from multiple health app studies)

> NOTE: WebSearch was unavailable during this research session. Findings are based on training knowledge (cutoff August 2025) and project context analysis. Claims about specific competitor features or Persian market statistics should be validated with live research before making product bets.
