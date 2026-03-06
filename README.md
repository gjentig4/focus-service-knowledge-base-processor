# focus-service-knowledge-base-processor

Processes Zendesk help center articles into enriched markdown documents and pushes them to the focus-ai-service for embedding into pgvector. Handles HTML-to-markdown conversion, image deduplication with perceptual hashing, LLM-generated alt text, and document enrichment (summary, keywords, question variations). Triggered by Zendesk webhooks or manual admin calls.

## Prerequisites

- Docker
- The `tlnetwork` Docker network must exist (`docker network create tlnetwork` if it doesn't)
- The [focus-ai-service](http://api.ai-assistant.focus.teamleader.dev) running on `tlnetwork` (receives the processed documents)
- A Zendesk API token for the `teamleaderfocus` subdomain
- An [OpenRouter](https://openrouter.ai) API key (used for Gemini Flash via OpenAI-compatible API)

## Setup

```bash
# 1. Copy the environment file
cp .env.dist .env

# 2. Fill in your credentials in .env:
#    - ZENDESK_API_EMAIL    (your Zendesk email)
#    - ZENDESK_API_TOKEN    (Zendesk API token)
#    - OPENROUTER_API_KEY   (OpenRouter API key)
#    Optionally:
#    - ZENDESK_WEBHOOK_SECRET (for verifying Zendesk webhook signatures)

# 3. Build and start
docker compose up -d

# Or use the Makefile (also builds the image):
make install
docker compose up -d
```

The Python service runs on port **8886**, nginx on port **8887**. The virtual host is `api.knowledge-base-processor.focus.teamleader.dev`.

## Testing it

### Health check

```bash
# Via nginx (port 8887) — returns plain "ok" from nginx directly
curl http://localhost:8887/health-check

# Via Python service (port 8886) — returns JSON
curl http://localhost:8886/health-check
# {"status":"ok"}
```

### Process a single article

Trigger processing of a Zendesk article by its ID (runs in the background, returns 202 immediately):

```bash
curl -X POST http://localhost:8887/admin/process/360001234567
# {"status":"accepted","article_id":360001234567}
```

Replace `360001234567` with a real Zendesk article ID from the `teamleaderfocus` help center.

### Check logs

```bash
# Follow all logs
docker compose logs -f

# Python service only
docker logs -f focus-service-knowledge-base-processor-python
```

### What a successful run looks like

```
INFO   Manual trigger: processing article 360001234567
INFO   Processing article 360001234567
INFO   Fetched: How to create an invoice
INFO   Sent document zendesk-360001234567 to focus-service
INFO   Successfully processed article 360001234567: How to create an invoice
```

If enrichment or image processing fails, the pipeline still completes with fallback values — check for `WARNING` and `ERROR` lines.

## Bulk import

Processes all articles from the Zendesk help center in one run. Uses `./bin/python` which runs Python inside Docker with the same image and network:

```bash
make bulk-import
```

Or directly:

```bash
./bin/python -m src.cli.bulk_import
```

This fetches all articles (paginated, 100 per page), processes each one sequentially (HTML conversion, image dedup, LLM enrichment), and sends each to the focus-ai-service. Progress is logged per article:

```
[1/656] Processing: How to create an invoice
[1/656] Done: How to create an invoice
[2/656] Processing: How to add a contact
...
Bulk import complete: 654 succeeded, 2 failed out of 656
```

## Zendesk webhooks

The webhook endpoint is `POST /webhooks/zendesk`. It expects a JSON body:

```json
{
  "type": "article.published",
  "article_id": 360001234567
}
```

Supported event types:
- `article.published` — fetches, processes, and sends the article to focus-ai-service
- `article.unpublished` — deletes the article from focus-ai-service

If `ZENDESK_WEBHOOK_SECRET` is set, the `X-Zendesk-Webhook-Signature` header is verified via HMAC-SHA256. If not set, signature verification is skipped.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ZENDESK_SUBDOMAIN` | No | `teamleaderfocus` | Zendesk subdomain for API calls |
| `ZENDESK_API_EMAIL` | Yes | | Email address for Zendesk API authentication |
| `ZENDESK_API_TOKEN` | Yes | | Zendesk API token (used with `/token` auth) |
| `ZENDESK_WEBHOOK_SECRET` | No | | Secret for verifying Zendesk webhook signatures. If empty, verification is skipped |
| `OPENROUTER_API_KEY` | Yes | | OpenRouter API key for LLM calls (alt text generation and document enrichment) |
| `FOCUS_SERVICE_URL` | No | `http://api.ai-assistant.focus.teamleader.dev` | URL of the focus-ai-service that receives processed documents |
| `PORT` | No | `8886` | Port the Python/uvicorn server listens on |
| `LOG_LEVEL` | No | `info` | Logging level (`debug`, `info`, `warning`, `error`) |

## Project structure

```
src/
  main.py                        # FastAPI app, health check, router setup
  config.py                      # Pydantic settings (env vars)
  api/
    admin.py                     # POST /admin/process/{id} and /admin/retry/{id}
    webhooks.py                  # POST /webhooks/zendesk (webhook receiver)
  cli/
    bulk_import.py               # Bulk import all articles from Zendesk
  clients/
    focus_service.py             # HTTP client for focus-ai-service
    openrouter.py                # OpenAI-compatible client for OpenRouter (Gemini Flash)
  models/
    article.py                   # ZendeskArticle model
    processed_document.py        # ProcessedDocument model (sent to focus-ai-service)
    webhook.py                   # ZendeskWebhookPayload model
  pipeline/
    orchestrator.py              # Main pipeline: fetch -> convert -> images -> enrich -> send
    zendesk_client.py            # Zendesk API client (fetch single/all articles)
    html_to_markdown.py          # HTML to markdown conversion via markdownify
    image_processor.py           # Image dedup (perceptual hashing) + alt text generation
    enrichment.py                # LLM enrichment (summary, keywords, doc_type, etc.)
    document_builder.py          # Builds final ProcessedDocument with metadata
  store/
    image_dedup.py               # SQLite store for image perceptual hashes
bin/
  python                         # Docker wrapper — runs python inside the container
data/
  image_dedup.db                 # SQLite database for image hash dedup (auto-created)
```

## `./bin/python`

Similar to `./bin/pnpm` in other services, `./bin/python` is a wrapper that runs Python inside the Docker container. It:

- Builds the image on first run if it doesn't exist
- Mounts the project directory into the container
- Loads env files in order: `.env.dist`, `secrets.env`, `.env` (later overrides earlier)
- Connects to `tlnetwork`

Use it for any one-off commands:

```bash
./bin/python -m src.cli.bulk_import
./bin/python -c "from src.config import settings; print(settings.model_dump())"
```
