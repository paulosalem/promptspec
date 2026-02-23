## AI/ML Integration Module

### LLM Integration
- Abstraction layer: provider-agnostic interface supporting OpenAI, Anthropic, local models.
- Configuration: model name, temperature, max_tokens, system prompt — all configurable per use case.
- Retry policy: exponential backoff (1s, 2s, 4s) with max 3 retries on 429/500/503.
- Cost tracking: log token usage (prompt + completion) per request with estimated cost.

### Intelligent Features
- **Smart categorization**: auto-categorize uncategorized items using LLM with few-shot examples from user's existing categorized data.
- **Natural language queries**: users type questions ("How much did I spend on food last month?") → parse to structured query → execute → format response.
- **Insights generation**: weekly/monthly AI-generated summary highlighting trends, anomalies, and suggestions.

### Safety
- All LLM inputs MUST be sanitized — strip PII before sending to external providers.
- Rate limit LLM calls per user: max 50 per hour (Free), 500 per hour (Pro).
- Fallback: if LLM is unavailable, gracefully degrade (show "AI unavailable" badge, use rule-based fallback).
- User data NEVER used for training — include `data_policy: no_training` in API calls where supported.
