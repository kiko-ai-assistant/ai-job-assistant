# API Contracts & Schemas

Single Source of Truth (SSOT) for communication protocols between services in the Kiko monorepo.

## Specifications
- `openapi/v1.yaml`: OpenAPI 3.0 specification for the Go Core Backend REST API.

## Workflow
1. Changes to endpoints and data models are defined here first (API-First design).
2. The Go backend (`apps/backend`) implements the server interfaces.
3. Web (`apps/web`) and Telegram Bot (`apps/bot`) generate or type-check their HTTP client models against this schema.
