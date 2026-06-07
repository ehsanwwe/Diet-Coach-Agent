# Diet Coach Agent

AI-powered multilingual diet coach agent with **FastAPI**, **Next.js**, **SQLite**, **OpenAI tool-calling**, **meal-plan calendar**, **voice-ready onboarding**, and **health-safety guardrails**.

Diet Coach Agent is not just a chatbot and not just a meal-plan generator.  
It is a production-oriented nutrition companion that can onboard users, understand their health context, generate adaptive meal plans, track progress, and use backend tools from inside the chat.

---

## What it does

- Phone OTP authentication
- 7-step nutrition onboarding
- Medical/risk screening with clinical-review states
- Persian-first multilingual UI: `fa`, `en`, `ar`
- RTL/LTR-aware mobile-first frontend
- Onboarding video + text/voice habit chat
- AI nutrition companion chat
- OpenAI tool-calling agent with backend tool registry
- Meal analysis from chat
- “What should I eat now?” guidance
- Rolling 7-day meal-plan calendar
- Next-week meal-plan generation
- Progress check-ins and weekly reports
- Settings and language management
- Safe fallback mock AI provider for local/offline development

---

## Agent capabilities

The chat is powered by a backend **Agent Orchestrator**.

The AI does not directly access the database.  
Instead, it sees a controlled list of backend tools and decides which tool to call.

Current tool capabilities include:

- Analyze a meal or food item
- Log food events
- Suggest what to eat now
- Read the user’s meal-plan calendar
- Generate the next 7-day meal plan
- Safely update tomorrow’s plan
- Adapt nutrition guidance
- Log daily check-ins
- Read progress summary
- Clear chat memory with confirmation

Example:

```text
User: من امشب شیرینی خامه‌ای خوردم، برنامه فردامو سبک‌تر کن

Agent:
- analyzes the food event
- checks the current plan
- safely updates tomorrow’s plan
- replies with a concise summary
```

---

## Tech stack

### Backend

- Python
- FastAPI
- SQLAlchemy 2.x
- Alembic migrations
- SQLite
- Pydantic v2
- PyJWT
- httpx
- OpenAI provider with SOCKS5 proxy enforcement
- Modular service/repository architecture
- Tool-based AI agent orchestration

### Frontend

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- Framer Motion
- React Hook Form
- Zod
- Dictionary-based i18n
- RTL/LTR-aware UI
- Mobile-first PWA-ready architecture

---

## AI provider modes

The backend can run without any external AI provider.

```env
AI_PROVIDER=mock
```

For real AI behavior:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5.4-nano
OPENAI_REQUIRE_PROXY=true
OPENAI_PROXY_URL=socks5://127.0.0.1:1080
```

OpenAI requests are blocked unless a SOCKS5 proxy is configured.  
This prevents accidental direct calls from the backend.

---

## Run locally

### 1. Clone

```bash
git clone https://github.com/ehsanwwe/Diet-Coach-Agent.git
cd Diet-Coach-Agent
```

### 2. Backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

OpenAPI:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Default development OTP:

```text
123456
```

---

## Repository structure

```text
Diet-Coach-Agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── dictionaries/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   └── package.json
│
├── .planning/
├── PROJECT_STATE.md
├── NEXT_STEPS.md
├── CHANGELOG.md
└── README.md
```

---

## Safety note

This project is designed as a nutrition and wellness companion.  
It is not a replacement for a physician, registered dietitian, emergency care, or clinical treatment.

High-risk users should be routed toward professional review before receiving strict or disease-specific diet prescriptions.

---

## Who is this for?

This repository is useful for:

- AI health-product teams
- nutrition startups
- wellness platforms
- medical software teams
- developers building tool-using agents
- companies that need a production-ready foundation for a personalized diet coach

You can run it locally, extend it, adapt it to your own product, or collaborate with us to turn it into a production system.

---

## Collaboration

If you want to build a custom AI nutrition agent, integrate this system into your own platform, or collaborate on product development, feel free to open an issue or contact the maintainer.

Maintainer:

```text
Ehsan Moradi
GitHub: ehsanwwe
```

---

## Donate / Support

If this project helped you, saved development time, or gave you a useful foundation, consider supporting its continued development.

You can sponsor, donate, or simply star the repository.

```text
GitHub: https://github.com/ehsanwwe
Repository: https://github.com/ehsanwwe/Diet-Coach-Agent
```

---

## License

MIT
