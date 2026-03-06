# Focus AI Service — Knowledge Base Ingestion Endpoint

## Goal

Add an API endpoint that allows the knowledge-base-processor service to push processed documents into pgvector. This replaces the manual `db:ingest` script with an HTTP API that supports real-time upserts and deletes.

## What changes

### 1. Document repository (`focus-ai-service/src/db/repositories/documents.ts`)

Two new methods:

- **`findByFilename(filename)`** — looks up a document by its unique filename. Needed for upsert logic (check if doc exists before replacing).
- **`deleteByFilename(filename)`** — deletes a document by filename. Because of `ON DELETE CASCADE` on the embeddings table, this automatically removes all associated embeddings too.

### 2. Request context bypass (`focus-ai-service/src/plugins/external/requestContext.ts`)

Currently, every request must have an `x-tl-account-id` header or it gets a 401. The knowledge-base-processor is a service-to-service call — there's no Teamleader account involved. So we skip the account_id check for routes starting with `/api/knowledge-base/`. No additional auth needed — follows the existing pattern where internal services communicate directly on `tlnetwork`.

### 3. New route (`focus-ai-service/src/routes/api/knowledge-base/documents.ts`)

**POST /api/knowledge-base/documents**

Receives a processed document and stores it in pgvector:

```json
{
  "filename": "zendesk-12345",
  "article_id": 12345,
  "title": "How to create an invoice",
  "url": "https://support.teamleader.eu/...",
  "locale": "en-150",
  "content": "# How to create an invoice\n\nSummary: ...\n\n...",
  "metadata": {
    "summary": "Guide on creating invoices",
    "keywords": ["invoice", "billing"],
    "doc_type": "how-to"
  }
}
```

What it does:
1. If a doc with this filename already exists → delete it (upsert)
2. Insert the document into the `documents` table
3. Build enriched content (title + summary + keywords + body — same pattern as `focus-ai-service/src/scripts/ingestDocuments.ts`)
4. Embed content via `text-embedding-3-small`
5. Store embeddings in the `embeddings` table

Note: handling of long articles is still WIP — see `knowledge-base.md` for the options being considered.

**DELETE /api/knowledge-base/documents/:articleId**

Removes a document when an article is unpublished in Zendesk:
1. Deletes document with filename `zendesk-{articleId}`
2. CASCADE removes all embeddings

## How to review

All changes are isolated — no existing behavior changes. The new route is accessible only from the internal network. The requestContext bypass only affects the new `/api/knowledge-base/` prefix.
