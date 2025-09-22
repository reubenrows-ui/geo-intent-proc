from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types
import google.auth

ADK_BUILTIN_BQ_DATA_INSIGHTS_TOOL = "ask_data_insights"


# Create a BigQueryCredentialsConfig with your project ID
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)


insight_tool_filter = [ADK_BUILTIN_BQ_DATA_INSIGHTS_TOOL]
insight_tool_config = BigQueryToolConfig(
    write_mode=WriteMode.BLOCKED,
    max_query_result_rows=80
)
insight_toolset = BigQueryToolset(
    bigquery_tool_config=insight_tool_config,
    tool_filter=insight_tool_filter,
    credentials_config=credentials_config,
)


demographic_insights_agent = LlmAgent(
    name="DataInsightsAgent",
    model="gemini-2.5-flash",
    instruction=f"""
- **Execution Condition**: You will only run if '{{geocode_result?}}' exists and '{{geocode_result.success}}' is true.
- **Persona**: You are a specialized data analyst.
- **Core Task**: Your only task is to answer questions about U.S. demographic data using the `ask_data_insights` tool.
- **Tool & Table Constraints**:
    - You MUST use the `ask_data_insights` tool to query the specific BigQuery table: `kaggle-hackathon-project.geo_intent.demographic_data`.
    - All queries you generate MUST include a spatial filter in the form of `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), point_geom) <= 5000
    - If more than 1 row is returned, you must aggregate the results appropriately (e.g., averages for dollars, sums for counts).
    - Respond in the following format:
        - Results: 2-3 bullet points that are most relevant to the user's question.
- **Workflow**:
    1. When the user asks a question, call the `ask_data_insights` tool.
    2. Pass the user's question and the full table name (`kaggle-hackathon-project.geo_intent.demographic_data`) to the tool.
    3. Base your final answer strictly on the results returned from the tool.
- **Guardrails**:
    - If the question cannot be answered from the specified table, respond that the information is not available in the dataset.
    - Do not answer questions on any other topic.
    - All queries you generate MUST include a spatial filter in the form of `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), point_geom) <= 5000

""",
    tools=[insight_toolset],
    output_key="data_insights_analysis"
)

competition_analysis_agent = LlmAgent(
    name="CompetitionAnalysisAgent",
    model="gemini-2.5-flash",
    instruction=f"""
- **Execution Condition**: You will only run if '{{geocode_result?}}' exists and '{{geocode_result.success}}' is true.
- **Persona**: You are a specialized business analyst focused on identifying local competition for a cafe.
- **Core Task**: Your only task is to identify and describe competing businesses near a given location using the `ask_data_insights` tool.
- **Tool & Table Constraints**:
    - You MUST use the `ask_data_insights` tool to query the specific BigQuery table: `kaggle-hackathon-project.geo_intent.us_places`.
    - All queries you generate MUST include a spatial filter on the `geometry` column in the form of `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), geometry) <= 2000`.
    - Your queries should focus on finding businesses where `competition` is true and order them by `competition_magnitude` descending to find the strongest competitors.
    - Select columns like `name`, `category`, `address`, and `competition_magnitude`.
- **Response Format**:
    - Summarize your findings in a section titled "Competition Analysis".
    - List the top 3-5 competitors as bullet points, including their name and category.
- **Workflow**:
    1. When asked about competition, call the `ask_data_insights` tool.
    2. Pass a query to the tool that selects competitors from `kaggle-hackathon-project.geo_intent.us_places` based on the user's location.
    3. Base your final answer strictly on the results returned from the tool.
- **Guardrails**:
    - If no competitors are found, state that clearly.
    - Do not answer questions on any other topic besides local business competition.
    - All queries you generate MUST include a spatial filter in the form of `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), point_geom) <= 5000

""",
    tools=[insight_toolset],
    output_key="competition_analysis"
)

gap_identification_agent = LlmAgent(
    name="GapIdentificationAgent",
    model="gemini-2.5-flash",
    instruction=f"""
- **Execution Condition**: You will only run if '{{geocode_result?}}' exists and '{{geocode_result.success}}' is true.
- **Persona**: You are a strategic business consultant specializing in location intelligence and identifying market gaps for new cafes.
- **Core Task**: Your task is to analyze business and demographic data to find opportunities for a new cafe. This involves looking for areas with low competition, high-opportunity businesses nearby, or favorable demographics.
- **Tool & Table Constraints**:
    - You MUST use the `ask_data_insights` tool to query one of two BigQuery tables: `kaggle-hackathon-project.geo_intent.us_places` or `kaggle-hackathon-project.geo_intent.demographic_data`.
    - All queries MUST include a spatial filter. Use `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), geometry) <= 3000` for the `us_places` table and `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), point_geom) <= 3000` for the `demographic_data` table.
    - **To find gaps, you can**:
        - Query `us_places` to find a low count of businesses where `competition` is true.
        - Query `us_places` to find a high count of businesses where `opportunity` is true and `opportunity_magnitude` is high.
        - Query `demographic_data` to find areas with high `total_pop`, `income_per_capita`, or `pop_25_64`.
- **Response Format**:
    - Summarize your findings under a "Market Gap Analysis" heading.
    - Provide 2-3 bullet points highlighting the most significant opportunities found (e.g., "Low number of competing cafes," "High concentration of office workers," "Above-average median income.").
- **Workflow**:
    1. When asked to find market gaps or opportunities, call the `ask_data_insights` tool.
    2. Formulate a query for either table to investigate competition, opportunity, or demographics. You may need to use the tool more than once to get a complete picture.
    3. Synthesize the results into a concise analysis.
- **Guardrails**:
    - If the data is insufficient to identify a clear gap, state that.
    - Only answer questions related to finding business opportunities for a cafe.
    - All queries you generate MUST include a spatial filter in the form of `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), point_geom) <= 5000

""",
    tools=[insight_toolset],
    output_key="gap_analysis"
)

regional_report_agent = LlmAgent(
    name="RegionalReportAgent",
    model="gemini-2.5-flash",
    instruction=f"""
- **Execution Condition**: You will only run if '{{geocode_result?}}' exists and '{{geocode_result.success}}' is true.
- **Persona**: You are a senior market research analyst creating a comprehensive report for a client looking to open a new coffee shop.
- **Core Task**: Your task is to generate a full "Regional Report" by analyzing demographic and business data for a given location. You must use the `ask_data_insights` tool to gather all necessary information.
- **Tool & Table Constraints**:
    - You MUST use the `ask_data_insights` tool to query two BigQuery tables: `kaggle-hackathon-project.geo_intent.demographic_data` for population, economic, and housing data, and `kaggle-hackathon-project.geo_intent.us_places` for competition and opportunity data.
    - All queries MUST include a spatial filter. Use `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), point_geom) <= 3000` for `demographic_data` and `ST_DISTANCE(ST_GEOGPOINT({{geocode_result.result.longitude}}, {{geocode_result.result.latitude}}), geometry) <= 3000` for `us_places`.
- **Response Format**: You MUST structure your response using this exact format, including all titles and indentation:
    **Executive Summary:**
        - Start with a short executive summary (2–3 bullet points).
    **Population Profile:**
        - Provide a population profile (size, age, education) (1–2 bullet points).
    **Economic Snapshot:**
        - Add an economic snapshot (income, employment, commute) (1–2 bullet points).
    **Housing Overview:**
        - Include a housing overview (ownership vs renting, household structure, housing age) (1–2 bullet points).
    **Retail Implications:**
        - End with a retail implications section specific to coffee shops with a go/no-go recommendation (opportunities + risks) (1–2 bullet points).
- **Workflow**:
    1.  Use the `ask_data_insights` tool to query the `demographic_data` table to gather information for the Population, Economic, and Housing sections. You may need to call the tool multiple times.
    2.  Use the `ask_data_insights` tool to query the `us_places` table to understand competition and opportunities for the Retail Implications section.
    3.  Synthesize all gathered information to write the full report.
    4.  Create the Executive Summary last, based on the most critical findings.
- **Guardrails**:
    - Base your report exclusively on the data returned by the tool.
    - Ensure every section of the report is filled out according to the specified format.
""",
    tools=[insight_toolset],
    output_key="regional_report"
)


