# kiko-parsers-base

Shared base library providing common models, domain validation rules, ingestion sink abstractions, and parser lifecycle templates for Kiko job scrapers.

## Features

- **Models**: Standardized OpenAPI-compliant DTOs (`CreateVacancyRequest`, `BatchCreateVacanciesRequest`, `BatchCreateVacanciesResponse`, `SalaryDTO`, `LocationDTO`).
- **Validation**: Reusable domain validator `VacancyValidator` enforcing backend invariants (salary rules, text length constraints, publication date bounds, source whitelist).
- **Sink**: HTTP ingestion sink `BackendApiSink` for batching and sending vacancies to the backend ingestion endpoint.
- **Parser Lifecycle**: Abstract `BaseParser` implementing the streaming parse-validate-batch-sink workflow with stats tracking and lifecycle hooks.
