# datastore/

This folder contains utilities and notebooks for working with **Discovery Engine / Vertex AI Search** and **BigQuery** in the ask-fusion project.

---

## What’s inside

- **utils/**  
  Helper scripts for managing DataStores, Search Engines, and running queries.

- **notebooks/**  
  Prototypes and experiments for DataStore creation, ingestion, and querying.

---

## Typical workflow

1. **Provision infra** (if not already set up):  
   Use `make setup-dev-env` at the project root.  
   > Requires a **service account** with Discovery Engine and BigQuery roles.

2. **Create a DataStore / Engine**  
   Utilities in `utils/` can help, or use the [Discovery Engine REST API](https://cloud.google.com/generative-ai-app-builder/docs/reference/rest).

3. **Ingest content**  
   Upload documents, metadata, or schemas into your DataStore.  
   Keep searchable fields minimal and well-typed to improve ranking.

4. **Run search queries**  
   Test queries locally with the `VertexAiSearchTool` wired in  
   `app/agents/intents/core_search_hierarchy/intent.py`.

---

## Using the notebooks

- Open the Jupyter notebooks in the `notebooks/` folder to test ingestion, query execution, or schema configuration.  
- These notebooks are intended for prototyping and interactive exploration.  
- **TODO:** Convert key notebooks into production-ready Python scripts under `datastore/utils/` so they can be run in CI/CD or automated jobs.

---

## Required roles

For infra setup or ingestion, the service account must have:
- `roles/discoveryengine.admin` (or Search Admin + Editor as needed)
- `roles/bigquery.dataEditor` & `roles/bigquery.jobUser`
- `roles/storage.objectAdmin` (if uploading content from GCS)

---