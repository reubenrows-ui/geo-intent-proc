import logging
import copy


from typing import Optional
from google.adk.tools import BaseTool, ToolContext
from typing import Any, Dict, Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def store_results_in_context(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict, 
) -> Optional[Dict]:

  # We are setting a state for the data science agent to be able to use the sql
  # query results as context 
  tool_context.state["geocode_result"] = tool_response

  return None
