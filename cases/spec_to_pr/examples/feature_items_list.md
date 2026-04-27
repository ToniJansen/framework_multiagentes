# Feature: list all items

## Goal
Add a `GET /items` endpoint that returns a static list of items.

## Acceptance criteria
- `GET /items` returns HTTP 200
- Response body: `{"items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]}`
- No pagination required for now

## Files to change
- `cases/spec_to_pr/sample_repo/main.py` — add the list endpoint
