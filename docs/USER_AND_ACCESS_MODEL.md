# User and Access Model (Phase 2)

## 1. Goals

Phase 2 establishes internal accounts and role-based access for the first private deployment of HanboweiOJ. The system is not open to public self-registration. Accounts are created or invited by authorized staff.

The initial implementation should keep personal data minimal and make authorization decisions on the backend, never only in the frontend.

## 2. Roles

| Role | Scope | Initial permissions |
| --- | --- | --- |
| `admin` | Whole installation | Manage users and roles; manage global configuration; view system-wide teaching data |
| `teacher` | Assigned classes and teaching resources | Manage own classes; add or deactivate students in those classes; create and manage teaching assignments; view learning and submission reports for assigned classes |
| `student` | Own account and learning activity | View assigned courses and problems; submit solutions; view own submissions, progress, and feedback |

A role is a system-level capability boundary. Class membership and resource ownership further restrict teacher access; a teacher must not gain access to another teacher's class merely because both have the `teacher` role.

## 3. Account lifecycle

- No public sign-up endpoint in the first release.
- An administrator creates teacher accounts.
- An administrator or authorized teacher creates/invites student accounts within the teacher's own class scope.
- Accounts can be deactivated without deleting historical submissions or learning records.
- Passwords are stored only as strong one-way password hashes; plaintext passwords are never stored or logged.
- Password reset and invitation flows will be added after the initial account and login foundation.

## 4. Initial data model

### User

| Field | Type / rule | Purpose |
| --- | --- | --- |
| `id` | UUID primary key | Stable internal identifier |
| `username` | Required, unique, normalized | Login identifier |
| `display_name` | Required | Name shown in the learning interface |
| `password_hash` | Required, never returned by API | Password verifier |
| `role` | `admin`, `teacher`, or `student` | System role |
| `is_active` | Boolean, default true | Account availability |
| `created_at` | UTC timestamp | Audit metadata |
| `updated_at` | UTC timestamp | Audit metadata |

Email, phone number, date of birth, and other personal details are deliberately excluded from the first version because they are not required for the initial internal workflow.

### Later related entities

These are not part of the first user-table migration, but the model must leave room for them:

- `Classroom`: a teaching group owned by a teacher.
- `ClassroomMembership`: a student's membership in a classroom, with status and timestamps.
- `AuditEvent`: records important administrative actions without storing passwords or tokens.

## 5. Authorization rules

1. Authentication identifies the account; authorization checks its role and resource scope.
2. The backend is the source of truth for every protected operation.
3. Students may access only their own private account data and learning records.
4. Teachers may access only classes they own and students enrolled in those classes.
5. Administrators may manage installation-wide users and configuration.
6. Deactivated accounts cannot log in or submit new solutions.
7. Sensitive responses never include `password_hash`, password material, access tokens, or secret configuration.

## 6. Planned API surface

The first implementation should introduce versioned endpoints with explicit request and response schemas:

- `POST /api/v1/auth/login`: verify username and password; return a short-lived access token.
- `GET /api/v1/auth/me`: return the current account's safe profile and role.
- `POST /api/v1/users`: create an account; administrator-only initially, with teacher student-creation scope added alongside classrooms.
- `GET /api/v1/users`: administrator-only user listing, with pagination and safe fields only.
- `PATCH /api/v1/users/{user_id}/status`: deactivate/reactivate an account; administrator-only initially.

No endpoint should accept a client-supplied role without server-side authorization. Public registration is intentionally out of scope.

## 7. Security requirements

- Hash passwords with Argon2id (or another maintained, memory-hard password hashing implementation).
- Sign access tokens with a secret supplied through environment configuration; never commit production secrets.
- Validate token signature, expiry, and subject on every authenticated request.
- Use explicit role and resource-scope dependencies in FastAPI.
- Apply request validation, generic login failure messages, and rate limiting before internet exposure.
- Keep the code-execution Runner separate from the API. User authentication does not make submitted source code safe to execute.
- Do not expose database credentials, password hashes, tokens, or secret values in logs or API responses.

## 8. Implementation sequence

1. Add SQLAlchemy database session/base and the User model.
2. Add an Alembic migration for the User table.
3. Add password hashing, token handling, login, and current-user endpoints.
4. Add role-protected account-management endpoints.
5. Add automated tests for account creation, login, disabled accounts, role restrictions, and safe response serialization.
6. Add classroom ownership and membership in a subsequent step before granting teachers student-management access.

## 9. Acceptance criteria

- Database schema is created by versioned migrations, not implicit production startup table creation.
- Passwords are never stored or returned in plaintext.
- Public registration is absent.
- All protected endpoints reject unauthenticated requests.
- Role checks and classroom ownership checks are enforced by the backend.
- Automated tests cover both allowed and denied access paths.
