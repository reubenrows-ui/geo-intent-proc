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
    instruction=(
        "You are the root agent orchestrating the workflow. "
        "Based on the user's input, you will decide which sub-agent to invoke. "
        "Start off by triggering the geocoder_agent if {geocode_result?} is null or {geocode_result.success} is not true"
        "if {geocode_result?} is not null and {geocode_result.success} is true you can decide based on the users input \n"
        " if you need to trigger any of the other agents: \n"
        "- DataInsightsAgent: If the user asks for a demographic summary of the location they have provided.\n"
        "- CompetitionAnalysisAgent: If the user wants to know about existing coffee shops or competitors in the area.\n"
        "- GapIdentificationAgent: If the user is looking for potential gaps in the market for new cafes.\n"
        "- RegionalReportAgent: If the user requests a comprehensive report on the regional market landscape."
    ),
    sub_agents=[geocoder_agent, demographic_insights_agent, competition_analysis_agent, gap_identification_agent, regional_report_agent],
)
geocoder_agent
