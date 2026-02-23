@note
  This spec generates API documentation with code examples.
  It uses @generate_examples for realistic request/response pairs,
  @revise to iteratively improve the docs, @structural_constraints
  to enforce consistent formatting, and @output_format for the
  final deliverable structure.

@structural_constraints
  Each API endpoint section must contain:
  1. HTTP method and path
  2. One-line description
  3. Authentication requirements
  4. Request parameters (path, query, body) in a table
  5. Request body schema (JSON, with types and constraints)
  6. Response schema (JSON, with types)
  7. Status codes table (code, meaning, when it occurs)
  8. At least 2 code examples (success + error case)
  9. Rate limiting information
  10. Changelog (version where endpoint was added/modified)

Write comprehensive API reference documentation for the
**{{api_name}}** (version {{api_version}}).

## Overview

{{api_description}}

Base URL: `{{base_url}}`

Authentication: {{auth_method}}

## Endpoints

{{#endpoints}}
### {{method}} `{{path}}`

{{description}}

@generate_examples "2"
  Generate realistic request/response examples for the
  {{method}} {{path}} endpoint. Include:
  - A successful request with a complete response body
  - An error request that triggers a {{error_code}} response
  Use realistic data that matches the {{api_name}} domain.

{{/endpoints}}

@revise
  Review the generated documentation for:
  - Consistency of terminology across all endpoints
  - Completeness of error codes (ensure 400, 401, 403, 404, 500 are covered)
  - Accuracy of JSON schemas (no missing required fields)
  - Clarity of parameter descriptions (avoid vague terms like "data" or "info")

@output_format "markdown"
  Use developer documentation conventions:
  - Fenced code blocks with `json`, `bash`, or `http` language tags
  - Tables for parameters and status codes
  - Inline code for field names, paths, and values
  - Collapsible sections (`<details>`) for lengthy response schemas
