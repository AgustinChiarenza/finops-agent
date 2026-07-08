# FinOps Knowledge Base

The RAG knowledge base lives in `agent/knowledge/` and is **empty by design**.
No documents are loaded into the repository. Each tenant ingests their own
FinOps material so recommendations are grounded in the pricing and policies
that actually apply to their environment.

## What to put here

Documents that make a FinOps agent useful for **Huawei Cloud** cost optimization:

| Category | Examples | `detect_tipo` filename hint |
|---|---|---|
| `pricing` | Huawei ECS/EVS/OBS/RDS price lists, billing-mode docs (pay-per-use vs reserved) | `pricing`, `precio`, `tarifa`, `rate` |
| `well_architected` | Well-Architected Framework — cost optimization pillar | `well-architected`, `waf` |
| `playbook` | Rightsizing runbooks, storage-tiering guides, commitment-based purchasing playbooks | `playbook`, `runbook`, `guia`, `guide` |
| `policy` | Tagging policies, budget-approval policy, environment promotion policy | `policy`, `politica`, `tagging`, `etiquetad` |
| `case_study` | Internal post-mortems of past optimization wins/losses | `case`, `caso`, `estudio` |
| `best_practice` | Reserved-instance best practices, spot usage guidance, idle-resource disposal | `best`, `mejor`, `practica` |
| `reference` | Anything else (architecture notes, vendor whitepapers) | (default) |

## Ingesting

```bash
# 1. Drop documents into the knowledge dir
cp ~/finops-docs/*.pdf agent/knowledge/

# 2. Run ingest (one-time per refresh)
python -m app.rag.ingest

# Or just see what would be ingested:
python -m app.rag.ingest --dry-run
```

Ingest extracts text (PDF/DOCX/MD/TXT), cleans and overlap-chunks it (1200-char
chunks, 200-char overlap — same parameters as `uade-rag`), embeds each chunk
with the configured provider (Ollama `nomic-embed-text` by default), and upserts
into the Chroma collection with metadata `{source, tipo, chunk, char_len}`.

## Why empty by default

1. **Tenant-specific.** Pricing, commitments, and policies differ per tenant;
   shipping a generic KB would produce confidently-wrong recommendations.
2. **Licensing.** Vendor price lists and internal case studies are not
   redistributable.
3. **Freshness.** Cloud pricing changes; a static KB in the repo would rot.

The agent explicitly tells the user when the KB is empty and answers from live
dashboard data only, marking recommendations as unvalidated against the KB.
