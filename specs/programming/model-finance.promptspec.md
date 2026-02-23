## Data Model: Financial Entities

### Account
| Field | Type | Constraints | Default | Index |
|-------|------|-------------|---------|-------|
| id | UUID | PK, generated | uuid_generate_v4() | PK |
| user_id | UUID | FK → users.id, NOT NULL | — | YES |
| name | VARCHAR(100) | NOT NULL | — | — |
| type | ENUM('checking', 'savings', 'credit_card', 'investment', 'loan', 'cash') | NOT NULL | — | YES |
| currency | CHAR(3) | NOT NULL, ISO 4217 | 'USD' | — |
| balance_cents | BIGINT | NOT NULL | 0 | — |
| credit_limit_cents | BIGINT | NULL (only for credit_card/loan) | NULL | — |
| institution | VARCHAR(200) | NULL | NULL | — |
| is_active | BOOLEAN | NOT NULL | true | YES |
| deleted_at | TIMESTAMP | NULL | NULL | — |
| created_at | TIMESTAMP | NOT NULL | now() | — |
| updated_at | TIMESTAMP | NOT NULL | now() | — |

**Constraints**: `balance_cents` MAY be negative only for `credit_card` and `loan` types.
**Unique**: `(user_id, name)` — a user cannot have two accounts with the same name.

### Transaction
| Field | Type | Constraints | Default | Index |
|-------|------|-------------|---------|-------|
| id | UUID | PK, generated | uuid_generate_v4() | PK |
| account_id | UUID | FK → accounts.id, NOT NULL | — | YES |
| amount_cents | BIGINT | NOT NULL, non-zero | — | — |
| type | ENUM('income', 'expense', 'transfer') | NOT NULL | — | YES |
| category_id | UUID | FK → categories.id, NULL | NULL | YES |
| description | VARCHAR(500) | NOT NULL | — | — |
| date | DATE | NOT NULL | — | YES (composite with account_id) |
| is_recurring | BOOLEAN | NOT NULL | false | — |
| recurring_rule_id | UUID | FK → recurring_rules.id, NULL | NULL | — |
| tags | TEXT[] | NULL | '{}' | GIN |
| deleted_at | TIMESTAMP | NULL | NULL | — |
| created_at | TIMESTAMP | NOT NULL | now() | — |
| updated_at | TIMESTAMP | NOT NULL | now() | — |

**Sign convention**: `amount_cents` is always positive; `type` determines the direction.
For transfers, create TWO transactions: expense on source, income on destination,
linked by a shared `transfer_group_id UUID`.

### Category
| Field | Type | Constraints | Default | Index |
|-------|------|-------------|---------|-------|
| id | UUID | PK, generated | uuid_generate_v4() | PK |
| user_id | UUID | FK → users.id, NOT NULL | — | YES |
| name | VARCHAR(50) | NOT NULL | — | — |
| icon | VARCHAR(30) | NULL (emoji or icon name) | NULL | — |
| color | CHAR(7) | NULL (hex, e.g., #FF5733) | NULL | — |
| parent_id | UUID | FK → categories.id, NULL (self-ref for subcategories) | NULL | YES |
| is_system | BOOLEAN | NOT NULL | false | — |

**Unique**: `(user_id, name, parent_id)` — no duplicate names at the same level.
**System categories**: seeded on user creation (Groceries, Rent, Salary, etc.); `is_system=true`, user cannot delete.

### Budget
| Field | Type | Constraints | Default | Index |
|-------|------|-------------|---------|-------|
| id | UUID | PK, generated | uuid_generate_v4() | PK |
| user_id | UUID | FK → users.id, NOT NULL | — | YES |
| category_id | UUID | FK → categories.id, NOT NULL | — | YES |
| amount_cents | BIGINT | NOT NULL, positive | — | — |
| period | ENUM('weekly', 'monthly', 'yearly') | NOT NULL | 'monthly' | — |
| start_date | DATE | NOT NULL | — | — |
| end_date | DATE | NULL (NULL = ongoing) | NULL | — |

**Unique**: `(user_id, category_id, period, start_date)` — one budget per category per period.
