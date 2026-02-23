## Notifications & Alerts Engine

### Alert Rules
- Users define alert rules with: condition, threshold, comparison operator, and action.
- Example rule: "Notify me when spending in 'Dining' exceeds $500 this month."
- Conditions evaluated after every relevant transaction is created.
- Supported operators: `>`, `>=`, `<`, `<=`, `==`, `between`.

### Notification Channels
- **In-app**: toast notification + persistent notification center.
- **Email**: daily or weekly digest (user preference), plus immediate for critical alerts.
- **Push** (optional): web push via Service Worker + VAPID keys.

### Deduplication
- Same alert rule MUST NOT fire more than once per evaluation period.
- Track last-fired timestamp per rule; suppress duplicates within cooldown window.

### Templates
- Notification content uses templates with variable substitution:
  `"You've spent {{spent}} of your {{budget}} budget for {{category}} this {{period}}."`
- Templates support locale-aware number and currency formatting.
