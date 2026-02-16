# Product Specification — TaskFin V2

## 1) Product overview

**TaskFin** is a conversational bill-payment assistant. Users interact via a chat UI to:

- View unpaid bills
- Pay a bill (with explicit confirmation)
- Check account balance
- View payment history

The system uses an LLM **only for intent detection**. All financial logic (balances, payments, risk checks, idempotency, audit logging) is deterministic and implemented in backend “agents”.

## 2) Goals and non-goals

### Goals

- Provide a simple conversational interface for common bill-payment tasks.
- Ensure payment correctness with a confirmation step and deterministic execution.
- Prevent accidental/dangerous behavior with rate limiting and risk controls.
- Provide auditability via immutable audit logs for key actions.
- Run locally via Docker Compose with Postgres + Redis + Backend + Frontend.

### Non-goals (current version)

- No real-money transfers (uses a mock banking service).
- No multi-user onboarding UI (frontend currently uses a seeded demo user).
- No bill ingestion from external providers (bills are seeded demo data).
- No advanced NLU beyond basic intent detection.

## 3) Target users and personas

- **Demo end user**: wants to quickly see/pay bills and verify balance/history via chat.
- **Developer/operator**: runs the stack locally, tunes risk policies, extends intents, and reviews audit logs.

## 4) Key user journeys

### A) List unpaid bills

1. User types: “show my bills”
2. Assistant responds with a list of unpaid bills and amounts.

### B) Pay a bill (two-step confirmation)

1. User types: “pay electricity”
2. Assistant asks: “Confirm payment of ₹1200 for Electricity? (yes/no)”
3. User confirms: “yes”
4. System executes deterministic checks and payment:
   - Risk policy check
   - Prevent double execution (short lock)
   - Verify sufficient balance
   - Mark bill as paid
   - Create transaction record
   - Update risk counters
   - Write audit logs
5. Assistant replies: “Electricity bill paid successfully.”

### C) Check balance

1. User types: “show balance”
2. Assistant replies with current balance and audits the event.

### D) View payment history

1. User types: “show history”
2. Assistant replies with timestamped transaction history.

## 5) Functional requirements

### 5.1 Conversational intent handling

- The assistant must support the following intents:
  - **LIST_BILLS**: list unpaid bills
  - **PAY_BILL \<bill name\>**: initiate payment confirmation flow
  - **SHOW_HISTORY**: list transaction history
  - **SHOW_BALANCE**: show account balance
- If a request is unclear/unrelated, the assistant provides guidance and example phrases.
- Greetings/small talk should respond naturally (no internal action keywords).

### 5.2 Payment confirmation

- Payment initiation must **not** immediately debit funds.
- System must prompt for explicit confirmation with **yes/no**.
- Confirmation must expire (current implementation uses a 60-second TTL).
- Cancel must clean up pending confirmation state and record an audit entry.

### 5.3 Risk controls

- Enforce a per-user **daily amount limit** and **max payments per day**.
- If risk checks fail, payment must be blocked with a user-visible reason and an audit entry.

### 5.4 Idempotency and duplicate prevention

- Prevent double execution of the same payment action (e.g., rapid repeat confirmations).
- A short-lived distributed lock should be used (current implementation uses Redis `SET NX` with expiry).

### 5.5 Audit logging

- Key events must be recorded:
  - Payment requested / confirmed / cancelled / executed / blocked / failed
  - Balance viewed
- Audit logs must be append-only at the application level (no in-place edits).

### 5.6 Authentication

- Backend must issue JWT access tokens via a login endpoint.
- Chat endpoint must require an Authorization header with a bearer token.
- A “who am I” endpoint should return the resolved user id.

## 6) System design (current implementation)

### 6.1 Services

The Docker Compose stack provisions:

- **PostgreSQL** (with `pgvector/pgvector:pg15` image)
- **Redis** (for rate limiting, confirmation state, and risk counters)
- **Backend**: FastAPI + SQLAlchemy + agent modules
- **Frontend**: Next.js chat UI

### 6.2 Backend API (current endpoints)

- `POST /login`
  - Body: `{ "username": string, "password": string }`
  - Returns: `{ "access_token": string }`
- `GET /health`
  - Returns: `{ "status": "healthy" }`
- `POST /agent/chat`
  - Headers: `Authorization: Bearer <token>`
  - Body: `{ "message": string }`
  - Returns: `{ "response": string }`
- `GET /me`
  - Headers: `Authorization: Bearer <token>`
  - Returns: `{ "user_id": number }`

### 6.3 Data model (tables)

Backend creates these tables (SQLAlchemy models):

- **users**
  - `id`, `username` (unique), `password` (hashed)
- **accounts**
  - `id`, `user_id`, `balance`, `type`
- **bills**
  - `id`, `user_id`, `name`, `amount`, `status` (`unpaid`/`paid`)
- **transactions**
  - `id`, `user_id`, `bill_name`, `amount`, `status`, `created_at`
- **audit_logs**
  - `id`, `user_id`, `action`, `status`, `message`, `created_at`

### 6.4 State management in Redis (conceptual keys)

- **Rate limit**: `rate_limit:<user_id>` counter with 60s TTL
- **Payment confirmation**: `confirm:payment:<user_id>` JSON payload with 60s TTL
- **Risk counters** (daily):
  - `risk:amount:<user_id>:<YYYY-MM-DD>`
  - `risk:count:<user_id>:<YYYY-MM-DD>`
- **Payment lock**: `payment_lock:<user_id>:<bill_name>` short TTL

## 7) Policies & limits (current defaults)

- **Rate limiting**: >10 requests per 60 seconds ⇒ “Too many requests. Please slow down.”
- **Risk policy**:
  - Daily total amount limit: **₹5000**
  - Max payments per day: **5**
- **Confirmation TTL**: **60 seconds**

These constants are intended to be easily tunable.

## 8) UX requirements (frontend)

- Chat UI must:
  - Show user and assistant messages in a conversational layout
  - Show a loading indicator during backend calls
  - Handle backend health failures gracefully with a clear message
- Authentication UX:
  - Current frontend performs a background login using a seeded demo user (developer convenience).
  - Future: prompt user for credentials or implement a session-based login UI.

## 9) Security & compliance considerations

- **Secrets management**:
  - API keys and JWT secret should be stored in environment variables, not hardcoded in source.
  - `.env` files should not be committed to source control.
- **Authentication**:
  - JWT tokens must be validated server-side for protected endpoints.
- **LLM safety**:
  - LLM output is constrained to a small action vocabulary for system operations.
  - Payment execution is never performed by the LLM directly.
- **Auditability**:
  - Every payment-related state transition should create an audit log entry.

## 10) Observability & operational requirements

- Health endpoint for basic availability checks.
- Meaningful error messages for:
  - Redis unavailable
  - LLM unavailable
  - Insufficient funds
  - Risk policy violations

## 11) Demo data and assumptions

- A demo user is seeded at backend startup (username/password are defined in the seed script).
- Initial demo account balance and demo bills are seeded for local testing.

## 12) Acceptance criteria (MVP)

- User can list unpaid bills via chat.
- User can initiate a bill payment and must confirm before execution.
- Payment is blocked if:
  - balance is insufficient
  - daily risk limits are exceeded
  - too many payments are attempted in a day
- Payment creates:
  - a transaction record
  - updated bill status
  - corresponding audit logs
- User can check balance and see payment history via chat.
- Stack runs via Docker Compose and frontend can communicate with backend on localhost.

## 13) Future enhancements

- Multi-user UI (register/login form) and user-specific bill management.
- Admin/audit UI (browse audit logs, export reports).
- Additional intents (e.g., “show paid bills”, “add a bill”, “set reminders”).
- Stronger contract between LLM intent detection and backend action parsing (e.g., JSON schema).
- Provider integrations (real billers) and real payment rails (out of demo scope).

