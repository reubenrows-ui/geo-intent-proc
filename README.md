# geo-intent

A multi-agent system for geospatial business intelligence, built with Google's Agent Development Kit (ADK). This agent analyzes U.S. demographic and business data to provide location-based insights for strategic decisions, such as opening a new coffee shop.

Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.15.0`

## How It Works

The system uses a sequential, multi-agent workflow to answer user queries about specific locations:

1.  **Geocoding**: The `GeocoderAgent` takes a user's query (e.g., "downtown Austin, TX") and uses geocoding tools to find its precise latitude and longitude.
2.  **Parallel Data Analysis**: Once a location is identified, several specialist agents run in parallel to gather intelligence:
    *   `DataInsightsAgent`: Queries the `demographic_data` table for population, income, and housing statistics.
    *   `CompetitionAnalysisAgent`: Queries the `us_places` table to identify and rank nearby competitors.
    *   `GapIdentificationAgent`: Analyzes both tables to find market gaps, such as areas with favorable demographics but low competition.
3.  **Final Reporting**: The `RegionalReportAgent` synthesizes the findings from all the specialist agents into a single, structured executive report, providing a go/no-go recommendation.

## Project Structure

This project is organized as follows:

```
geo-intent/
├── app/                 # Core application code
│   ├── agent.py         # Main agent orchestrator (SequentialAgent)
│   └── sub_agents/      # Directory for specialized agents
│       ├── geocoder/    # Agent for converting locations to coordinates
│       └── execute_sql/ # Agents for querying BigQuery
├── .cloudbuild/         # CI/CD pipeline configurations for Google Cloud Build
├── deployment/          # Infrastructure and deployment scripts
│   └── bigquery_setup_scripts/ # Scripts to create BQ tables
├── notebooks/           # Jupyter notebooks for prototyping and evaluation
├── tests/               # Unit, integration, and load tests
├── Makefile             # Makefile for common commands
└── pyproject.toml       # Project dependencies and configuration
```

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager - [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Terraform**: For infrastructure deployment - [Install](https://developer.hashicorp.com/terraform/downloads)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/)

## Data Setup (Prerequisite)

This agent relies on specific tables and a connection within Google BigQuery. You must set them up before running the application.

1.  **Authenticate gcloud**:
    ```bash
    gcloud auth application-default login
    gcloud config set project <your-gcp-project-id>
    ```
2.  **Launch Jupyter Lab**:
    ```bash
    uv run jupyter lab
    ```
3.  **Run Notebook**: Open and run all cells in the `deployment/bigquery_setup_scripts/notebooks/create_bq_resources.ipynb` notebook. This will:
    *   Create the `geo_intent` BigQuery dataset.
    *   Create the `demographic_data`, `us_places_category` and `us_places` tables.
    *   Create a BigQuery connection to Vertex AI for using generative AI functions in SQL.

## Quick Start (Local Testing)

After completing the Data Setup, install packages and launch the local development environment:

```bash
make install && make playground
```

Once the Streamlit playground launches, ask a question like:
- "Is Austin, TX a good place to open a coffee shop?"
- "Analyze the market for a new cafe near the University of Washington in Seattle."

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make playground`    | Launch Streamlit interface for testing agent locally and remotely |
| `make backend`       | Deploy agent to Agent Engine |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (codespell, ruff, mypy)                                             |
| `make setup-dev-env` | Set up development environment resources using Terraform                         |
| `uv run jupyter lab` | Launch Jupyter notebook                                                                     |

For full command options and usage, refer to the [Makefile](Makefile).

## Deployment

> **Note:** For a streamlined one-command deployment of the entire CI/CD pipeline and infrastructure using Terraform, you can use the [`agent-starter-pack setup-cicd` CLI command](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd.html). Currently supports GitHub with both Google Cloud Build and GitHub Actions as CI/CD runners.

### Dev Environment

You can test deployment towards a Dev Environment using the following command:

```bash
gcloud config set project <your-dev-project-id>
make backend
```

The repository includes a Terraform configuration for the setup of the Dev Google Cloud project.
See [deployment/README.md](deployment/README.md) for instructions.

### Production Deployment

The repository includes a Terraform configuration for the setup of a production Google Cloud project. Refer to [deployment/README.md](deployment/README.md) for detailed instructions on how to deploy the infrastructure and application.


## Monitoring and Observability
> You can use [this Looker Studio dashboard](https://lookerstudio.google.com/reporting/46b35167-b38b-4e44-bd37-701ef4307418/page/tEnnC
) template for visualizing events being logged in BigQuery. See the "Setup Instructions" tab to getting started.

The application uses OpenTelemetry for comprehensive observability with all events being sent to Google Cloud Trace and Logging for monitoring and to BigQuery for long term storage.
