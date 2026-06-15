# Unified Campus Intelligence Dashboard
## PRD + SRS + TRD + Implementation Plan
**Version 1.0 — Draft for Coding Agent Execution**

---

# PART 1: PRODUCT REQUIREMENTS DOCUMENT (PRD)

## 1.1 Vision

A unified web dashboard for students that aggregates four campus data sources (Library, Cafeteria, Events, Academics) — each served by an independent, read-only MCP server — and provides an AI assistant capable of answering natural-language queries by routing to one or more MCP servers and synthesizing grounded, non-hallucinated answers.

## 1.2 Goals

- Eliminate the need for students to check 4 separate systems for campus information.
- Demonstrate a clean MCP-based architecture (no central scraped database; each source is an independent server).
- Provide personalization via user profiles (borrowed books, flagged events, liked menu days) stored separately from MCP source data.
- AI assistant must answer strictly from MCP server data — no fabrication.

## 1.3 Out of Scope (v1)

- Real campus data integration (all data is mocked).
- Library reservations / borrowing transactions against the Library MCP server (borrowed books are profile-only — see Model A, SRS 3.6).
- Roles other than Student (no Admin, Faculty).
- Academics PDF moderation/approval workflow (uploads are immediately public).
- Real-time push notifications.

## 1.4 Success Criteria

- All 4 MCP servers operational and independently queryable.
- AI assistant correctly answers single-source queries (e.g., "is X book available?") and multi-source AND queries (e.g., "show events this week that don't clash with my book due dates").
- AI assistant explicitly states "no data found" when MCP servers return empty results — never invents data.
- Functional auth (signup/login) with personalized homescreen widgets.
- Deployed, working demo (frontend on Vercel, backend on Render).

---

# PART 2: STAKEHOLDERS & PERSONAS

## 2.1 Roles

| Role | Description |
|---|---|
| Student (only role) | Authenticated user with a profile; views widgets, chats with AI, manages personal calendar items, uploads/downloads academic PDFs |

## 2.2 Persona — Student

- **Goals:** Quickly find campus information (book availability, today's menu, upcoming events, course PDFs) without visiting multiple systems; get personalized reminders (due dates, flagged events).
- **Pain points:** Information scattered across systems; no single place to ask "what's happening today that matters to me."
- **Permissions:** Full access to own profile/calendar; read access to all 4 data sources; write access only to: own profile fields, own calendar entries (flags/likes), Academics PDF uploads (public to all).

---

# PART 3: FUNCTIONAL REQUIREMENTS (SRS)

## 3.1 Authentication

| ID | Requirement |
|---|---|
| FR-AUTH-01 | The system shall allow a new user to register using a unique email, a name, a roll number, and a password (minimum 8 characters). |
| FR-AUTH-02 | The system shall authenticate users via email and password, returning a JWT access token valid for 24 hours. |
| FR-AUTH-03 | The system shall reject registration if the email or roll number already exists, returning an error message identifying which field is duplicated. |
| FR-AUTH-04 | The system shall require a valid JWT for all API endpoints except `/auth/register` and `/auth/login`. |

## 3.2 MCP Server — Library

| ID | Requirement |
|---|---|
| FR-LIB-01 | The Library MCP server shall expose a read-only dataset of at least 10 mock books, each with fields: `id`, `title`, `author`, `category`, `total_copies`, `available_copies`. |
| FR-LIB-02 | The Library MCP server shall provide a tool to search books by title or author (case-insensitive partial match). |
| FR-LIB-03 | The Library MCP server shall provide a tool to retrieve a single book's availability status (`available_copies` > 0 → "Available", else "Unavailable") given a book ID or exact title. |
| FR-LIB-04 | The Library MCP server's dataset shall not be modified by any user action (read-only, per Model A). |

## 3.3 MCP Server — Cafeteria

| ID | Requirement |
|---|---|
| FR-CAF-01 | The Cafeteria MCP server shall expose a read-only 7-day mock menu, each day containing fields: `day`, `breakfast`, `lunch`, `snacks`, `dinner`. |
| FR-CAF-02 | The Cafeteria MCP server shall provide a tool to retrieve the menu for a specified day (e.g., "Monday", "today"). |
| FR-CAF-03 | The Cafeteria MCP server shall provide a tool to retrieve the full 7-day menu. |

## 3.4 MCP Server — Events

| ID | Requirement |
|---|---|
| FR-EVT-01 | The Events MCP server shall expose a read-only dataset of at least 10 mock club/campus events, each with fields: `id`, `title`, `club`, `date`, `time`, `location`, `description`. |
| FR-EVT-02 | The Events MCP server shall provide a tool to list all events within a specified date range. |
| FR-EVT-03 | The Events MCP server shall provide a tool to search events by club name or title (case-insensitive partial match). |

## 3.5 MCP Server — Academics

| ID | Requirement |
|---|---|
| FR-ACA-01 | The Academics MCP server shall expose a read/append dataset of at least 10 mock textbook PDF entries, each with fields: `id`, `title`, `subject`, `uploaded_by`, `file_data` (base64-encoded PDF content, stored in SQLite), `file_url` (internal download route `/academics/download/{id}`), `upload_date`. |
| FR-ACA-02 | The system shall allow an authenticated student to upload a PDF file (max size 20MB) with a title and subject, which becomes immediately visible to all students (no approval step, per confirmed decision). |
| FR-ACA-03 | The Academics MCP server shall provide a tool to search PDF entries by title or subject (case-insensitive partial match). |
| FR-ACA-04 | The system shall allow any authenticated student to download any academic PDF entry via its `file_url`. |

## 3.6 User Profile & Personal Calendar (Model A — App Database, Separate from MCP Servers)

| ID | Requirement |
|---|---|
| FR-PROF-01 | The system shall store, per user: `name`, `roll_number`, `email`, `borrowed_books` (list), `flagged_events` (list), `liked_menu_days` (list). |
| FR-PROF-02 | The system shall allow a user to add a book (by title, referencing the Library MCP dataset) to their `borrowed_books` list, along with a manually entered due date. Adding a book to this list shall have no effect on the Library MCP server's `available_copies` field. |
| FR-PROF-03 | The system shall allow a user to remove a book from their `borrowed_books` list. |
| FR-PROF-04 | The system shall allow a user to flag/unflag an event (by event ID, referencing the Events MCP dataset) to add/remove it from their `flagged_events` list. |
| FR-PROF-05 | The system shall allow a user to like/unlike a specific cafeteria menu day to add/remove it from their `liked_menu_days` list. |
| FR-PROF-06 | The system shall generate a personal calendar view by aggregating: due dates from `borrowed_books`, dates from `flagged_events`, and dates from `liked_menu_days`, sorted chronologically. |

## 3.7 Dashboard UI

| ID | Requirement |
|---|---|
| FR-UI-01 | The system shall display a home screen containing four widgets — Library, Cafeteria, Events, Academics — each showing a summary view of that source's data (e.g., Cafeteria widget shows today's menu). |
| FR-UI-02 | The system shall display a persistent chat panel on every page of the application. |
| FR-UI-03 | The system shall display the user's personal calendar as a widget or section on the home screen. |

## 3.8 AI Assistant

| ID | Requirement |
|---|---|
| FR-AI-01 | The AI assistant shall route natural-language queries to one or more of the 4 MCP servers based on query intent, using LLM tool/function-calling. |
| FR-AI-02 | The AI assistant shall automatically have access to the authenticated user's identity (`user_id`, `name`, `roll_number`) and profile data (borrowed books, flagged events, liked menu days) without requiring the user to specify "my" explicitly. |
| FR-AI-03 | The AI assistant shall support queries requiring results from two or more MCP servers combined with an AND condition (e.g., events on dates that do not coincide with borrowed-book due dates), by querying each relevant server and filtering combined results. |
| FR-AI-04 | The AI assistant shall respond only using data returned by MCP server tool calls or the user's profile data; it shall not generate, infer, or guess factual details (book titles, menu items, event details, PDF titles) not present in tool results. |
| FR-AI-05 | If a tool call returns no matching data, the AI assistant shall explicitly state that no results were found, rather than producing a plausible-sounding but fabricated answer. |
| FR-AI-06 | For queries resolved via multiple MCP servers, the system shall display a natural-language summary answer in the chat panel AND highlight/render the relevant source widgets on the home screen (per confirmed UI decision: NL answer + highlighted widgets). |

---

# PART 4: USE CASE MODELING

## UC-01: Multi-Source AND Query

- **Actor:** Authenticated Student
- **Preconditions:** User is logged in; Events and Library MCP servers are reachable.
- **Main Flow:**
  1. User types a query in the chat panel (e.g., "Which events this week don't clash with my book due dates?").
  2. AI assistant identifies intent requires Events MCP (date range query) and user's profile `borrowed_books` (due dates).
  3. AI calls Events MCP tool to retrieve events for the current week.
  4. AI retrieves user's `borrowed_books` due dates from profile.
  5. AI filters events whose date does not match any due date.
  6. System displays NL summary in chat and highlights the Events widget on the home screen with the filtered list.
- **Alternate Flows:**
  - A1: No `borrowed_books` exist → AI returns all events for the week with a note that no due-date conflicts could be checked because no books are recorded.
- **Exceptions:**
  - E1: Events MCP server unreachable → AI informs user that event data is temporarily unavailable; does not fabricate event data.

## UC-02: Single-Source Query (Book Availability)

- **Actor:** Authenticated Student
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User asks "Is [book title] available?"
  2. AI calls Library MCP search tool with the title.
  3. If found, AI returns availability status based on `available_copies`.
  4. System highlights the Library widget with the matched book.
- **Alternate Flows:**
  - A1: Multiple books match the title → AI lists all matches and asks user to clarify.
- **Exceptions:**
  - E1: No match found → AI states no book with that title exists in the catalog.

## UC-03: Add Borrowed Book to Profile

- **Actor:** Authenticated Student
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User searches for a book via Library widget or chat.
  2. User selects "Add to my borrowed books" and enters a due date.
  3. System saves entry to user's `borrowed_books` profile list.
  4. Personal calendar updates to reflect the new due date.
- **Exceptions:**
  - E1: Due date is in the past → System rejects with validation error: "Due date must be today or later."

## UC-04: Academic PDF Upload

- **Actor:** Authenticated Student
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User navigates to Academics widget/page.
  2. User uploads a PDF (≤20MB) with title and subject.
  3. System stores file, creates Academics MCP dataset entry, makes it immediately visible to all students.
- **Exceptions:**
  - E1: File exceeds 20MB → System rejects with error: "File size exceeds 20MB limit."
  - E2: File is not a PDF → System rejects with error: "Only PDF files are supported."

---

# PART 5: NON-FUNCTIONAL REQUIREMENTS

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | The system shall return single-source AI query responses within 5 seconds under normal load (mock data, ≤10 records per source). |
| NFR-02 | Performance | The system shall return multi-source AND query responses within 10 seconds. |
| NFR-03 | Security | The system shall store passwords using bcrypt hashing (never plaintext). |
| NFR-04 | Security | The system shall validate JWT tokens on every protected endpoint and reject expired/invalid tokens with HTTP 401. |
| NFR-05 | Usability | The system shall display a loading indicator in the chat panel while an AI query is being processed. |
| NFR-06 | Availability | The deployed system shall be accessible via public URLs for both frontend and backend with uptime sufficient for live demo (no formal SLA for prototype). |
| NFR-07 | Data Integrity (Anti-Hallucination) | The AI assistant shall, for every factual claim about books, menus, events, or PDFs, be traceable to a specific MCP tool-call result; the system should log tool calls and responses for verification during demo. |
| NFR-08 | Robustness | The system shall display a clear, user-facing message ("AI assistant is currently unavailable — missing API configuration") and shall not crash if `GEMINI_API_KEY` is not set or invalid. |

---

# PART 6: CONSTRAINTS & ASSUMPTIONS

## 6.1 Constraints

- Tech stack fixed: Next.js (frontend), Python/FastAPI single app with 4 MCP routers (backend), Gemini (LLM with function-calling), SQLite + SQLAlchemy (profile, calendar, AND academic PDFs as base64 blobs), JWT (email/password auth).
- Deployment: Frontend → Vercel, Backend → Render (single service hosting main API + all 4 MCP routers).
- Timeline: Very short — implementation to be executed by a coding agent following this spec.
- All data sources are mocked; no external/live API integrations.
- `GEMINI_API_KEY` not yet available — agent implements env-var pattern with graceful degradation (NFR-08).

## 6.2 Assumptions

- "Today" for cafeteria/calendar purposes is determined by server system date.
- Single FastAPI app architecture (4 routers) is sufficient to satisfy "independent MCP servers" requirement for prototype/demo purposes — separation is logical/code-organizational, not physical/deployment-level.

---

# PART 7: VALIDATION & OPEN QUESTIONS

## 7.1 Open Questions — RESOLVED

| # | Decision |
|---|---|
| 1 | **Single FastAPI app**, 4 MCP servers implemented as logically-separate routers (e.g., `/mcp/library`, `/mcp/cafeteria`, `/mcp/events`, `/mcp/academics`). One Render deployment. |
| 2 | **No Gemini API key yet** — agent must implement using `GEMINI_API_KEY` env var with a placeholder/`.env.example`, and the app should fail gracefully (clear error message in chat) if the key is missing, rather than crashing. |
| 3 | **SQLite** for PDF storage — uploaded PDFs stored as base64-encoded blobs in the Academics table (FR-ACA-01 extended to include a `file_data` field). No external storage service. |

### Additional Notes Driven by These Decisions

- **FR-ACA-01 amendment:** Add `file_data` (base64 PDF content) field to the Academics table schema, in addition to `file_url` (can be a generated internal route like `/academics/download/{id}` rather than an external URL).
- **NFR-08 (new):** The system shall display a clear, user-facing error message ("AI assistant is currently unavailable — missing API configuration") if `GEMINI_API_KEY` is not set, without crashing the application.
- Base64 storage in SQLite is acceptable given the 20MB file cap (FR-ACA-02) and ~10-record mock scale — adequate for prototype/demo, not production-scale.

---

# PART 8: IMPLEMENTATION PLAN (FOR CODING AGENT)

## Phase A — Backend Foundation
1. Set up FastAPI project structure with SQLAlchemy + SQLite.
2. Implement `User` model (FR-PROF-01) and auth endpoints (FR-AUTH-01 to 04).
3. Implement JWT middleware for protected routes.

## Phase B — MCP Servers (Mock Data)
4. Create Library router: seed 10 books (FR-LIB-01), implement search & availability tools (FR-LIB-02, 03).
5. Create Cafeteria router: seed 7-day menu (FR-CAF-01), implement day/full-menu tools (FR-CAF-02, 03).
6. Create Events router: seed 10 events (FR-EVT-01), implement date-range & search tools (FR-EVT-02, 03).
7. Create Academics router: seed 10 PDF entries (FR-ACA-01), implement search tool (FR-ACA-03), upload endpoint (FR-ACA-02), download endpoint (FR-ACA-04).

## Phase C — Profile & Calendar
8. Implement profile endpoints: add/remove borrowed book (FR-PROF-02, 03), flag/unflag event (FR-PROF-04), like/unlike menu day (FR-PROF-05).
9. Implement calendar aggregation endpoint (FR-PROF-06).

## Phase D — AI Assistant Integration
10. Integrate Gemini with function-calling; define tool schemas for all 4 MCP server tools + profile read access.
11. Implement query routing logic with anti-hallucination system prompt (FR-AI-01 to 05).
12. Implement multi-source AND query handling and response formatting (FR-AI-03, 06).

## Phase E — Frontend
13. Build auth pages (login/register) and JWT storage.
14. Build home screen with 4 widgets + calendar widget (FR-UI-01, 03).
15. Build persistent chat panel component (FR-UI-02), wired to AI endpoint.
16. Wire widget highlighting on multi-source AI responses (FR-AI-06).

## Phase F — Deployment & Demo
17. Deploy backend to Render, frontend to Vercel.
18. Record demo video covering: registration/login, each widget, single-source query, multi-source AND query, PDF upload/download, profile/calendar updates.
