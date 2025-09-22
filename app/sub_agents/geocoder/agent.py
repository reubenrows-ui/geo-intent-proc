
import logging
from typing import AsyncGenerator
from typing_extensions import override
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


from .tools.agent_functions import geocode_address
from .callbacks import store_results_in_context

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeoCoderAgent(BaseAgent):
    """
    An agent that geocodes a user-provided location using a geocoding tool.
    This agent prompts the user for a location if none is provided, calls the geocoding tool,
    and stores the geocoding result in the session state.
    """

    # --- Field Declarations for Pydantic ---
    # Declare the agents passed during initialization as class attributes with type hints
    geocoder: LlmAgent
    # model_config allows setting Pydantic configurations if needed, e.g., arbitrary_types_allowed
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        geocoder: LlmAgent
    ):
        """
        Initializes the GeoCoderAgent.

        Args:
            name (str): The name of the agent.
            geocoder (LlmAgent): The agent responsible for geocoding locations.
        """

        # Pydantic will validate and assign them based on the class annotations.
        super().__init__(
            name=name,
            geocoder=geocoder
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the custom orchestration logic for the story workflow.
        Uses the instance attributes assigned by Pydantic (e.g., self.story_generator).
        """
        logger.info(f"[{self.name}] Starting geocoding workflow.")

        # 1. Initial geocoding step
        logger.info(f"[{self.name}] Prompt user to provide a location...")
        async for event in self.geocoder.run_async(ctx):
            logger.info(f"[{self.name}] Event from GeoCoder: {event.model_dump_json(indent=2, exclude_none=True)}")
            yield event

        # Check if geocoding was successful before proceeding
        if "geocode_result" not in ctx.session.state or not ctx.session.state["geocode_result"]:
             logger.error(f"[{self.name}] Failed to generate initial geocode result. Aborting workflow.")
             return # Stop processing if initial geocoding failed
        
        if "success" not in ctx.session.state["geocode_result"] or ctx.session.state["geocode_result"]["success"] is not True:
             logger.error(f"[{self.name}] Geocoding was not successful: {ctx.session.state['geocode_result']}. Aborting workflow.")
             return # Stop processing if initial geocoding failed

        logger.info(f"[{self.name}] Geocode result: {ctx.session.state.get('geocode_result')}")


geocoder = LlmAgent(
    name="GeoCoder",
    model="gemini-2.5-flash",
    instruction=(
        "You are a helpful assistant for geocoding.\n"
        "- Start only if {geocode_result?} is null. Or if the user indicates they want to pick a different location.\n"
        "- Take the users provided string and run the geocode_address tool with the location text exactly as provided"
        "- If {geocode_result.success} is not true, Tell the user that the geocode was not successful and ask them to provide a more specific location (e.g., 'Please provide a more specific city or address.').\n"
        "- If {geocode_result.success} is true, Tell the user that the geocode was successful and proceed with the next steps.\n"

    ),
    tools=[geocode_address],
    after_tool_callback=store_results_in_context,
)

geocoder_agent = GeoCoderAgent(
    name="GeoCoderAgent",
    geocoder=geocoder
)