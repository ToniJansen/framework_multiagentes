# Feature: /health endpoint

## Goal
Add a `/health` endpoint that returns the service status and version.

## Acceptance criteria
- `GET /health` returns HTTP 200
- Response body: `{"status": "healthy", "version": "1.0.0"}`
- No authentication required

## Files to change
- `cases/dev_agent/sample_repo/main.py` — add the endpoint
