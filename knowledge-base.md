# Knowledge Base Pipeline — Architecture Decisions

## The problem

The AI assistant's knowledge base is manually maintained. Current flow: scrape Zendesk → run 10 Python scripts locally → copy markdown files into the repo → run `db:ingest`. We currently have 33 docs — not because we can't add more, but because we deliberately kept it small rather than bloating the repo without a proper pipeline in place. There are 656+ articles available in Zendesk.

## The approach: two repos

### `focus-service-knowledge-base-processor` (new, Python/FastAPI)

Handles everything between Zendesk and the focus-ai-service:
- Receives Zendesk webhooks
- Fetches article content via Zendesk API
- Converts HTML → markdown
- Deduplicates images (perceptual hashing) and generates alt text
- Enriches documents with LLM-generated metadata (summary, keywords, doc_type, question_variations)
- Sends the processed document to the focus-ai-service

### `focus-ai-service` (existing, changes via PR)

New endpoint `POST /api/knowledge-base/documents` that:
- Receives processed docs from the knowledge-base-processor
- Embeds them (text-embedding-3-small)
- Upserts into pgvector

For long articles, two options are on the table (WIP):
- **Chunking at ingestion time** — split documents >~1500 tokens at paragraph boundaries into ~4000 char chunks, embed each separately
- **Pre-processing in Python** — identify the specific long articles (mostly tables that get mangled by HTML→markdown conversion) and split them upstream into logical sub-documents before they reach the focus-ai-service

See `plan.md` for the full breakdown of focus-ai-service changes.

### Why two repos instead of one?

- **Separation of concerns** — article processing (Python, LLM calls, image handling) is a different domain from embedding + serving (TypeScript, pgvector, Fastify). Mixing them would make the focus-ai-service responsible for Zendesk API interactions, HTML parsing, image processing, etc.
- **Independent deployment** — we can update processing logic (enrichment prompts, markdown conversion) without redeploying the focus-ai-service.
- **Language fit** — Python is the better tool for the processing pipeline (markdownify, Pillow, imagehash). The focus-ai-service stays TypeScript.
- **Failure isolation** — if the knowledge-base-processor crashes or Zendesk rate-limits us, the AI assistant keeps serving.

## Why webhooks?

Event-driven via Zendesk's native webhook support. An article gets published or unpublished → we process only that article. No polling, no diffing, no wasted API calls.

## Document enrichment

Each article is enriched with LLM-generated metadata (summary, keywords, question variations, doc_type, etc.) before embedding. The reasoning and research behind this is documented separately.

## Focus-service changes summary

| File | Change |
|------|--------|
| `focus-ai-service/src/db/repositories/documents.ts` | Add `findByFilename()` + `deleteByFilename()` |
| `focus-ai-service/src/plugins/external/requestContext.ts` | Skip account_id check for `/api/knowledge-base/` |
| `focus-ai-service/src/routes/api/knowledge-base/documents.ts` | New POST + DELETE endpoints |

No inter-service auth — follows the existing pattern where services communicate directly on `tlnetwork` without additional authentication.

I've created a draft PR for these changes but I still need to test it as I didn't have time to do so.

## Alternatives considered

---

#### 1. All-in-one inside the focus-ai-service

> Add the webhook endpoint, Zendesk fetching, HTML conversion, image processing, and LLM enrichment directly into the focus-ai-service. No second service.

**Rejected** — Bloats the focus-ai-service with an entirely different domain (Zendesk API, HTML parsing, image processing). TypeScript ecosystem is weaker for image processing (no Pillow/imagehash equivalents). Every change to processing logic requires redeploying the focus-ai-service. If Zendesk rate-limits or the enrichment pipeline breaks, it could impact the assistant.

---

#### 2. Cron-based periodic sync

> A scheduled job fetches all articles from Zendesk, diffs against what's stored, and re-processes anything that changed.

**Rejected** — Zendesk natively supports webhooks, so polling reinvents what's already built. Wasteful: most runs would find nothing changed, still costs API calls. Adds state management complexity (tracking what changed since last run). Delay between article update and knowledge base update (minutes to hours vs seconds). This is going to serve tens of thousands of users — doing it properly matters.

---

#### 3. Processing inside focus-ai-service, webhook receiver as a thin proxy

> A minimal webhook receiver forwards article IDs to the focus-ai-service, which does all the processing itself.

**Rejected** — Same language-fit problem: TypeScript isn't ideal for the processing work. The focus-ai-service becomes responsible for Zendesk API auth, HTML parsing, image dedup, LLM enrichment calls. Tighter coupling: focus-ai-service now depends on Zendesk being available.

---

#### 4. Shared database with role separation (suggested by Brecht)

> Instead of the knowledge-base-processor sending documents over HTTP, have it write directly to pgvector (including embedding). The focus-ai-service only needs read access — its existing `searchSimilar` query works without any changes.

This came up after the initial brainstorm, which is why the HTTP approach was the starting point. It's a strong alternative worth comparing directly.

**How it works:** The knowledge-base-processor handles the full pipeline end-to-end — fetching, processing, embedding, and writing to the same `documents` + `embeddings` tables the focus-ai-service already reads from. The focus-ai-service doesn't change at all. DB role separation ensures the knowledge-base-processor has write access and the focus-ai-service has read-only access. Schema ownership stays with the focus-ai-service (drizzle migrations), the knowledge-base-processor just writes compatible rows.

### HTTP approach vs shared database — comparison

| | HTTP | Shared DB |
|---|---|---|
| **Focus-ai-service changes** | New endpoint, new route, draft PR | None |
| **Embedding ownership** | Focus-ai-service | Knowledge-base-processor |
| **Coupling type** | API contract (JSON payload) | Schema contract (table structure) |
| **Failure mode** | HTTP errors, timeouts | DB connection issues |
| **Schema changes** | Only focus-ai-service cares | Both services need to stay in sync |
| **Runtime complexity** | Two hops (HTTP + DB write) | One hop (direct DB write) |
| **Setup** | No DB config needed | One-time: create DB roles, grant permissions |
| **Knowledge-base-processor scope** | Processing only | Processing + embedding |

**HTTP pros:** Clean API boundary — the knowledge-base-processor doesn't need to know about the DB schema or embedding model. If the embedding strategy changes, only the focus-ai-service needs updating.

**Shared DB pros:** Simpler overall — no new endpoint, no inter-service HTTP calls, no changes to the focus-ai-service at all. The knowledge-base-processor owns the full pipeline. Role separation prevents accidental writes from the wrong service, which is the more future-proof setup as the team grows or more services connect to this data.

Both approaches keep the two-repo split and webhooks. The difference is just how processed documents get into pgvector.
