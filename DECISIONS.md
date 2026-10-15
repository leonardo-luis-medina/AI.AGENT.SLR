# SolarQC Agent — Architecture Decisions

## Decision 001 — Project Scope
SolarQC Agent is a genuine AI agent for quality-checking
fictional Australian solar installation sales records.

The project uses synthetic data.
No physical solar panels or customer records are required.

## Decision 002 — Preserve Original Requirements
All original 16 phases (Phase 0–15) must be preserved.

New features are additions, not replacements.

The Version 3 guide is our detailed project reference.

## Decision 003 — Strict Zero-Cost Budget
The project must use ₱0 in paid services.

Rules:
- No paid subscriptions.
- No paid API usage.
- No automatic billing.
- No cloud resources with uncontrolled charges.
- Verify free-tier eligibility before using a service.
- Use local alternatives when necessary.

## Decision 004 — Dual-Model AI Architecture
Visitors can select between:

1. Ollama + Qwen (local AI)
2. Gemini API (cloud AI)

Both models must use the same agent tools,
quality-control rules, and evaluation framework.

## Decision 005 — Docker
Use Docker Compose to manage the local application.

Planned services:
- Python/FastAPI backend
- Ollama
- Persistent model storage

Docker does not automatically improve model performance.

## Decision 006 — Public Portfolio Website
Use Next.js and TypeScript for the frontend.

Host the public website using an eligible free hosting plan.

The website must remain accessible even when the
local Ollama backend is offline.

Live Gemini inspections require an available agent backend.

## Decision 007 — Interview Mode
Local Ollama access must be controllable.

Requirements:
- Enable or disable local access.
- Detect whether the backend is online.
- Never expose Ollama directly to the public.
- Use authentication and rate limiting.
- Display accurate availability status.

## Decision 008 — RAG and Semantic Search
Implement document retrieval using fictional
solar-company policies.

Use free local embeddings and vector search.

The agent must cite retrieved policy evidence.

## Decision 009 — Integrations
Planned integrations:
- HubSpot developer test environment
- Google Sheets API
- REST APIs

Use fictional customer and sales records only.

## Decision 010 — Evaluation
Evaluate the agent using known test cases.

Compare Gemini and Qwen using:
- QC accuracy
- Tool-selection accuracy
- False positives and false negatives
- Response time
- Policy citation accuracy

Do not fabricate benchmark results.

## Decision 011 — Development Workflow
Use:
- VS Code for development
- Git for version control
- GitHub for remote backups
- Markdown files for project continuity

Work one step at a time.

Test each completed feature before proceeding.

## Decision 012 — Learning Objective
The developer must understand the code and architecture.

ChatGPT should:
- Explain what each command does.
- Explain why each tool is needed.
- Provide beginner-friendly instructions.
- Wait for checkpoints before continuing.
- Help troubleshoot errors.
- Prepare the developer to explain the project
  during technical interviews.