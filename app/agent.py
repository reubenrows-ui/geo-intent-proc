# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent
from .sub_agents.geocoder.agent import geocoder_agent
from .sub_agents.execute_sql.agent import demographic_insights_agent, competition_analysis_agent, gap_identification_agent, regional_report_agent

root_agent = LlmAgent(
    name="RootAgent",
    model="gemini-2.5-flash",
    instruction="""
- **Role**: You are a master orchestrator agent. Your ONLY purpose is to analyze the user's request and route it to the correct sub-agent. You MUST NOT answer the user's question directly.

- **Decision Logic**:
    1.  **IF** '{{geocode_result?}}' is null OR '{{geocode_result.success}}' is false, you MUST trigger the `geocoder_agent` to get the location.
    2.  **IF** '{{geocode_result.success}}' is true, analyze the user's latest query and trigger the most appropriate agent based on the following intents:

        - **Trigger `demographic_insights_agent`** for specific questions about population, income, or housing.
            - *Examples*: "What is the median income here?", "Tell me about the population age.", "How many people rent vs. own?"

        - **Trigger `competition_analysis_agent`** for questions about direct competitors.
            - *Examples*: "Who are my main competitors?", "Are there other coffee shops nearby?", "List the top 5 cafes in this area."

        - **Trigger `gap_identification_agent`** for questions about market opportunities or underserved areas.
            - *Examples*: "Where are the opportunities?", "Are there any market gaps?", "Find places with lots of offices but few cafes."

        - **Trigger `regional_report_agent`** for broad, open-ended questions asking for a summary or recommendation.
            - *Examples*: "Is this a good place to open a coffee shop?", "Give me a full report for this area.", "Summarize the market landscape."
""",
    sub_agents=[geocoder_agent, demographic_insights_agent, competition_analysis_agent, gap_identification_agent, regional_report_agent],
)
geocoder_agent
