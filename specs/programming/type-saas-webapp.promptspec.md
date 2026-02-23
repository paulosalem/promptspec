## Software Type: SaaS Web Application

### Multi-Tenancy
- Tenant isolation via `tenant_id` column on every tenant-scoped table.
- All queries MUST filter by `tenant_id` — enforce at ORM/middleware level.
- Tenant-aware caching: cache keys MUST include tenant_id prefix.
- Cross-tenant data access is NEVER allowed, even for admin users.

### Onboarding Flow
1. Sign up (email + password or OAuth).
2. Email verification (6-digit code, 10-minute expiry).
3. Create organization (name, optional logo upload).
4. Invite team members (email invitations with role selection).
5. Guided tour: highlight key features with tooltip walkthrough (skippable).

### Subscription & Billing
- Tiers: Free, Pro, Enterprise. Feature-gated via feature flags.
- Integration: Stripe Checkout for payment, Stripe Webhooks for lifecycle events.
- Webhook events to handle: `checkout.session.completed`, `invoice.paid`,
  `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`.
- Grace period: 7 days after payment failure before downgrade.
- Usage metering: track API calls / storage / seats per billing period.

### Notifications
- In-app: notification bell with unread count badge, dropdown list, mark-as-read.
- Email: transactional emails via SendGrid/Resend (welcome, password reset, billing alerts).
- Preferences: per-notification-type opt-in/opt-out, stored per user.

### Audit Log
- Record every write operation: `(timestamp, user_id, tenant_id, action, resource_type, resource_id, changes_json)`.
- Changes stored as JSON diff (old value → new value for each modified field).
- Queryable by admin: filter by user, resource, action, date range.
- Retention: 90 days in hot storage, archive to cold storage after.
