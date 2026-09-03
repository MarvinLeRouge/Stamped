# ADR 0007: SSE for real-time progress, not WebSockets

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/ai/decisions.md` ADR-007

## Context

The import pipeline and thumbnail generation are long-running background operations. The frontend needs a way to receive progress updates without polling.

## Decision

Server-Sent Events (SSE), via `GET /api/events`, is used for all real-time server-to-client communication (import progress, thumbnail generation status). No WebSocket connection is used anywhere in the app.

## Consequences

- Communication over the event channel is strictly unidirectional (server to client); any client-to-server action goes through regular REST endpoints, never the event channel.
- SSE is trivially implemented in FastAPI (`StreamingResponse` with `text/event-stream`) with no extra dependency for the basic case.
- As of this pass, the backend exposes this endpoint but the frontend does not yet consume it (see [frontend architecture](../architecture/frontend_architecture.md)) - this is a gap tracked in the [roadmap](../roadmap.md), not a reversal of this decision.

## Alternatives considered

**WebSockets** - rejected: adds bidirectional complexity (connection lifecycle, message framing) that the app does not need, since all client-to-server actions are naturally request/response and already served well by REST.
