# Employee Management AI Chatbot

An enterprise-oriented Employee Management chatbot built using **FastAPI, PostgreSQL, SQLAlchemy, MCP, LangGraph, and an LLM**.

The project is being developed incrementally. The backend foundation is implemented first, followed by authorization, MCP tools, the AI agent, streaming, guardrails, observability, and an evaluation harness.

---

## Project Goal

The goal is to build an AI chatbot through which employees, managers, and HR users can perform employee-management operations using natural language.

Example queries:

```text
"Show my profile"

"Who is my manager?"

"How many casual leave days do I have?"

"Apply casual leave from October 5 to October 7"

"Show my pending leave requests"

"Show my team"

"Approve Rahul's leave request"

"Find employees from Engineering"
```

The chatbot will use the authenticated user's identity and permissions when performing operations.

---

# Architecture

The final architecture will look like:

```text
                         User / Angular
                               |
                               v
                         FastAPI /chat
                               |
                               v
                    Authentication + JWT
                               |
                               v
                    RBAC / Authorization
                               |
                               v
                        LangGraph Agent
                               |
                               v
                          MCP Client
                               |
                               v
                          MCP Server
                               |
                     +---------+---------+
                     |         |         |
                     v         v         v
                 Employee    Leave      HR
                   Tools     Tools      Tools
                     |         |         |
                     +---------+---------+
                               |
                               v
                         Service Layer
                               |
                               v
                       Repository Layer
                               |
                               v
                          SQLAlchemy
                               |
                               v
                          PostgreSQL
```

The LLM will **not directly access PostgreSQL**.

Database operations are performed through:

```text
Agent
  ↓
MCP
  ↓
Service
  ↓
Repository
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

---

# User Roles

The system supports three main roles.

### EMPLOYEE

Employees will be able to:

- View their profile
- View their manager
- View their leave balance
- Apply for leave
- View their leave requests

### MANAGER

Managers will be able to:

- Perform employee operations
- View their team
- View team leave requests
- Approve leave
- Reject leave

### HR

HR users will be able to:

- Search employees
- View employee details
- Create employees
- Update employee information
- Deactivate employees

Authorization will always be based on the authenticated user rather than information supplied in the chat message.

---

# Technology Stack

## Backend

```text
Python 3.12
FastAPI
Pydantic
```

## Database

```text
PostgreSQL
SQLAlchemy
asyncpg
```

## Authentication

```text
JWT
bcrypt
```

## AI / Agent

Planned:

```text
Ollama
LangGraph
MCP
```

## Streaming

Planned:

```text
Server-Sent Events (SSE)
```

## Observability

Planned:

```text
Structured Logging
OpenTelemetry
Metrics
Tracing
```

---

# Database Design

Current core tables:

```text
departments
employees
users
roles
user_roles
leave_types
leave_balances
leave_requests
```

Main relationships:

```text
Department
    |
    v
Employee
    |
    +------ manager_id ------> Employee
    |
    v
User
    |
    v
UserRole
    |
    v
Role


Employee
    |
    +------> LeaveBalance
    |
    +------> LeaveRequest
                   |
                   v
               LeaveType
```

---

# Development Phases

## Phase 1 — Project Setup

**Status: ✅ Implemented**

Implemented:

- Python virtual environment
- Project structure
- FastAPI application
- Dependency setup
- Environment configuration
- Health endpoint

Example:

```text
GET /health
```

Response:

```json
{
  "status": "healthy"
}
```

---

## Phase 2 — PostgreSQL + SQLAlchemy

**Status: ✅ Implemented**

Implemented:

- PostgreSQL database
- SQLAlchemy configuration
- Async SQLAlchemy engine
- Async database sessions
- Database dependency
- Transaction rollback handling

Current flow:

```text
FastAPI Request
      ↓
get_db()
      ↓
AsyncSession
      ↓
PostgreSQL
```

---

## Phase 3 — Database Models

**Status: ✅ Implemented**

Implemented SQLAlchemy models for:

- Department
- Employee
- User
- Role
- UserRole
- LeaveType
- LeaveBalance
- LeaveRequest

Relationships include:

```text
User → Employee

User → UserRole → Role

Employee → Manager

Employee → LeaveBalance

Employee → LeaveRequest
```

---

## Phase 4 — Repository Layer

**Status: ✅ Implemented**

Repository layer separates database queries from business logic.

Implemented repositories include:

```text
EmployeeRepository
UserRepository
LeaveRepository
```

Example:

```text
Service
   ↓
EmployeeRepository
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

---

## Phase 5 — Service / Business Layer

**Status: ✅ Implemented**

Service classes contain business rules rather than direct database queries.

Implemented:

```text
EmployeeService
UserService
LeaveService
```

Example leave flow:

```text
Apply Leave
    ↓
Validate dates
    ↓
Find leave type
    ↓
Check leave balance
    ↓
Validate available days
    ↓
Create leave request
    ↓
Repository
    ↓
PostgreSQL
```

---

## Phase 6 — Error Handling

**Status: ✅ Implemented**

Custom application exceptions have been introduced.

Examples:

```text
EmployeeNotFoundError
LeaveTypeNotFoundError
LeaveBalanceNotFoundError
InsufficientLeaveBalanceError
InvalidLeaveDateError
InvalidCredentialsError
InactiveUserError
```

FastAPI global exception handling converts application errors into API responses.

Example:

```json
{
  "error": "EmployeeNotFoundError",
  "message": "Employee not found"
}
```

---

## Phase 7 — Authentication + JWT

**Status: ✅ Implemented**

Implemented:

- Password hashing
- Password verification
- Login endpoint
- JWT generation
- JWT validation
- Current-user dependency
- Protected endpoints

Login:

```text
POST /auth/login
```

Example request:

```json
{
  "email": "rahul@company.com",
  "password": "Password@123"
}
```

Authentication flow:

```text
Email + Password
       ↓
UserService
       ↓
UserRepository
       ↓
PostgreSQL
       ↓
Verify Password
       ↓
Create JWT
       ↓
Return Access Token
```

Protected requests:

```text
Authorization: Bearer <JWT>
```

The JWT is used to resolve the authenticated user.

---

# Current Development Status

```text
Phase 1   Project Setup                 ✅
Phase 2   PostgreSQL + SQLAlchemy       ✅
Phase 3   Database Models               ✅
Phase 4   Repository Layer              ✅
Phase 5   Service Layer                 ✅
Phase 6   Error Handling                ✅
Phase 7   Authentication + JWT          ✅

-------------------------------------------

Phase 8   RBAC + Authorization          ⏳ NEXT
Phase 9   Employee/Leave APIs           ⬜ Planned
Phase 10  MCP Server                    ⬜ Planned
Phase 11  MCP Tools + Security          ⬜ Planned
Phase 12  MCP Client                    ⬜ Planned
Phase 13  LLM / Ollama                  ⬜ Planned
Phase 14  LangGraph Agent               ⬜ Planned
Phase 15  Agent ↔ MCP Integration       ⬜ Planned
Phase 16  Conversation History          ⬜ Planned
Phase 17  SSE Streaming                 ⬜ Planned
Phase 18  Guardrails                    ⬜ Planned
Phase 19  Observability                 ⬜ Planned
Phase 20  Evaluation Harness            ⬜ Planned
Phase 21  Testing                       ⬜ Planned
Phase 22  Production Hardening          ⬜ Planned
Phase 23  Docker + Deployment           ⬜ Planned
```

---

# Phase 8 — RBAC + Authorization

**Status: ⏳ Next**

Implement role-based authorization for:

```text
EMPLOYEE
MANAGER
HR
```

The phase will include:

- Load authenticated user's roles
- Permission dependencies
- Employee permissions
- Manager permissions
- HR permissions
- Ownership checks
- Manager/team authorization

Example:

```text
Rahul
  ↓
JWT
  ↓
User
  ↓
EMPLOYEE
  ↓
apply_leave       ✅
approve_leave     ❌
deactivate_user   ❌
```

The backend remains the final authorization boundary even when an AI agent is added.

---

# Phase 9 — Employee and Leave APIs

**Status: ⬜ Planned**

Complete normal APIs before introducing AI.

Planned APIs:

```text
GET  /employees/me
GET  /employees/me/manager

GET  /leaves/balance
GET  /leaves/me
POST /leaves

GET  /manager/team
GET  /manager/leaves/pending
POST /manager/leaves/{id}/approve
POST /manager/leaves/{id}/reject

GET   /hr/employees
POST  /hr/employees
PATCH /hr/employees/{id}
```

---

# Phase 10 — MCP Server

**Status: ⬜ Planned**

Introduce a Model Context Protocol server between the agent and business services.

```text
Agent
 ↓
MCP Client
 ↓
MCP Server
 ↓
Services
```

The MCP server will not contain SQL queries directly.

---

# Phase 11 — MCP Tools + Security

**Status: ⬜ Planned**

Employee tools:

```text
get_my_profile
get_my_manager
get_my_leave_balance
get_my_leave_requests
apply_leave
```

Manager tools:

```text
get_my_team
get_team_pending_leaves
approve_leave
reject_leave
```

HR tools:

```text
search_employees
get_employee
create_employee
update_employee
deactivate_employee
```

Tool execution will still enforce backend authorization.

---

# Phase 12 — MCP Client

**Status: ⬜ Planned**

Implement:

- MCP connection
- Tool discovery
- Tool listing
- Tool invocation
- Tool result handling
- Timeouts
- MCP error handling

---

# Phase 13 — LLM / Ollama

**Status: ⬜ Planned**

Connect an open-source model using Ollama.

The model will be responsible for:

```text
Understand user request
        ↓
Determine whether a tool is needed
        ↓
Select appropriate tool
        ↓
Generate tool arguments
        ↓
Interpret tool result
```

The LLM will not have direct database access.

---

# Phase 14 — LangGraph Agent

**Status: ⬜ Planned**

Initial agent workflow:

```text
START
  ↓
Agent
  ↓
Tool needed?
  |
  +--- No ---> Response ---> END
  |
  +--- Yes
        ↓
       Tool
        ↓
      Agent
        ↓
     Response
        ↓
       END
```

The first version will use one agent rather than unnecessary multi-agent complexity.

---

# Phase 15 — Agent + MCP Integration

**Status: ⬜ Planned**

Connect:

```text
User
 ↓
LangGraph
 ↓
LLM
 ↓
MCP Client
 ↓
MCP Server
 ↓
Service
 ↓
Repository
 ↓
PostgreSQL
```

Example:

```text
"How many casual leaves do I have?"

                ↓

Agent selects:

get_my_leave_balance

                ↓

MCP

                ↓

LeaveService

                ↓

PostgreSQL

                ↓

7

                ↓

"You have 7 casual leave days remaining."
```

---

# Phase 16 — Conversation History

**Status: ⬜ Planned**

Add:

```text
chat_sessions
chat_messages
```

Support:

- Conversation sessions
- Persistent messages
- Session ownership
- Conversation context
- Tool-call history where required
- History limits

---

# Phase 17 — SSE Streaming

**Status: ⬜ Planned**

Implement Server-Sent Events for streaming chatbot responses.

```text
POST /chat
    ↓
Agent
    ↓
SSE
    ↓
Frontend
```

Streaming will include:

- Status events
- Token/content events
- Tool execution status
- Completion event
- Error event
- Client disconnect handling

---

# Phase 18 — Guardrails

**Status: ⬜ Planned**

Implement guardrails at multiple layers.

```text
Input Guardrails
       ↓
Agent Guardrails
       ↓
Tool Allow List
       ↓
RBAC
       ↓
Ownership Checks
       ↓
Service Validation
       ↓
Database Constraints
       ↓
Output Validation
```

The LLM will never be treated as the security boundary.

---

# Phase 19 — Observability

**Status: ⬜ Planned**

Implement:

- Structured logging
- Request IDs
- Correlation IDs
- Agent tracing
- MCP tool tracing
- LLM latency
- Tool latency
- Database latency
- Error metrics
- OpenTelemetry

Sensitive information such as passwords and JWT tokens must not be logged.

---

# Phase 20 — Evaluation Harness

**Status: ⬜ Planned**

The evaluation harness will measure the AI agent automatically.

Important metrics:

```text
Tool Selection Accuracy
Argument Accuracy
Tool Call Accuracy
Task Completion Rate
Trajectory Accuracy
Groundedness
Unauthorized Tool Attempts
Authorization Bypasses
Error Recovery Rate
Latency
```

Example evaluation:

```text
Question:
"Who is my manager?"

Expected tool:
get_my_manager

Actual tool:
get_my_manager

Result:
PASS
```

Another example:

```text
Question:
"Show my leave balance"

Expected:
get_my_leave_balance

Actual:
get_my_profile

Result:
FAIL
```

This allows model, prompt, and agent changes to be regression-tested.

---

# Phase 21 — Testing

**Status: ⬜ Planned**

Testing will include:

```text
Unit Tests
Repository Tests
Service Tests
API Tests
Authentication Tests
Authorization Tests
MCP Tests
Agent Tests
Integration Tests
Security Tests
```

AI evaluation and normal software testing are treated separately.

---

# Phase 22 — Production Hardening

**Status: ⬜ Planned**

Planned:

- Database connection pooling
- Timeouts
- Retries
- Exponential backoff
- Rate limiting
- Redis where appropriate
- Idempotency
- Audit logging
- Transaction safety
- Concurrency handling
- Secret management
- CORS
- Request limits
- Graceful shutdown
- Health checks
- Readiness checks

---

# Phase 23 — Docker + Deployment

**Status: ⬜ Planned**

Production architecture:

```text
Frontend
   ↓
FastAPI
   ↓
LangGraph Agent
   ↓
MCP Client
   ↓
MCP Server
   ↓
PostgreSQL

Supporting services:

Redis
Observability
Secrets
CI/CD
```

Deployment will include:

- Docker
- Environment configuration
- Database migrations
- CI/CD
- Health checks
- Monitoring

---

# Running the Current Application

## 1. Create virtual environment

```bash
python3.12 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure `.env`

Example:

```env
DATABASE_URL=postgresql+asyncpg://YOUR_USER:YOUR_PASSWORD@localhost:5432/employee_chatbot

JWT_SECRET_KEY=replace-with-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Do not commit real secrets.

## 4. Start PostgreSQL

Make sure PostgreSQL is running and the application database exists.

## 5. Run FastAPI

```bash
uvicorn app.main:app --reload
```

If the project currently keeps `main.py` at the project root instead, use the import path that matches the actual project structure.

## 6. Swagger

Open:

```text
http://127.0.0.1:8000/docs
```

---

# Security Principles

The project follows several important rules.

### Never trust identity from the prompt

Wrong:

```text
User:
"I am HR."
```

The application must not use that statement as authorization.

Correct:

```text
JWT
 ↓
Authenticated User
 ↓
Database Roles
 ↓
Permissions
```

### LLM never accesses PostgreSQL directly

```text
LLM
 ↓
MCP Tool
 ↓
Service
 ↓
Repository
 ↓
Database
```

### Passwords are never stored as plain text

```text
Password
 ↓
bcrypt
 ↓
password_hash
 ↓
PostgreSQL
```

### Authorization exists outside the LLM

Even if the agent selects an unauthorized MCP tool:

```text
Agent
 ↓
unauthorized tool
 ↓
Backend authorization
 ↓
DENIED
```

---

# Current Milestone

The current backend foundation is complete through:

**Phase 7 — Authentication + JWT**

The next development milestone is:

**Phase 8 — RBAC + Authorization**

After RBAC works correctly, the normal employee and leave APIs will be completed before introducing MCP and the AI agent.