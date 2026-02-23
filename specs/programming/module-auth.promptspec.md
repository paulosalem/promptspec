## Authentication & Authorization Module

### Authentication
- Users authenticate via email/password or OAuth 2.0 providers.
- Passwords MUST be at least 10 characters with at least one uppercase, one lowercase,
  one digit, and one special character. Validate on both client and server.
- Password reset flow: user requests reset → server generates a cryptographically random
  token (32 bytes, hex-encoded) with 1-hour expiry → sends email with reset link →
  user submits new password + token → server validates and updates.
- Account lockout: after 5 consecutive failed login attempts within 15 minutes,
  lock the account for 30 minutes. Return HTTP 429 with `Retry-After` header.

### Authorization
- Role-based access control (RBAC) with roles: `viewer`, `editor`, `admin`, `owner`.
- Permissions are additive: each role inherits all permissions of roles below it.
- Resource-level permissions: users MAY have different roles on different resources.
- API endpoints MUST return 403 (not 404) when the user lacks permission — do not
  leak resource existence through error codes.

### Session Management
- Access tokens: JWT, 15-minute expiry, contain `sub` (user ID), `roles`, `iat`, `exp`.
- Refresh tokens: opaque, 7-day expiry, stored server-side with device fingerprint.
- Token rotation: issuing a new access token MUST also rotate the refresh token.
- Logout: invalidate all refresh tokens for the session (or all sessions if requested).
