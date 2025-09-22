"""
Agent functions that leverage the Google Maps APIs for geocoding and place search.
These functions are designed to be used by the agent system.
"""

import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from .geocoding import GeocodingAPI
from .grid import TileGenerator
from .places import PlacesAggregateAPI

logger = logging.getLogger(__name__)


def geocode_address(address: str) -> Dict[str, Any]:
    """
    Geocode an address string into coordinates and formatted address.
    
    This is a wrapper around the GeocodingAPI class that returns results in a format
    suitable for direct use by agents.
    
    Args:
        address: A string containing the address to geocode
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,  # True if geocoding was successful
            "query": str,     # The original address that was queried
            "result": {       # Only present if success is True
                "latitude": float,
                "longitude": float,
                "formatted_address": str
            },
            "error": str,     # Only present if success is False
            "reason": str     # Only present if success is False
        }
    """
    try:
        # Initialize the geocoding API
        geocoder = GeocodingAPI()
        
        # Clean the address
        clean_address = address.strip() if isinstance(address, str) else ""
        
        # Check for valid input
        if not clean_address:
            return {
                "success": False,
                "query": address,
                "error": "Invalid input",
                "reason": "Address must be a non-empty string"
            }
        
        # Geocode the address using the correct method
        success, result = geocoder.geocode(clean_address)
        
        # Return in a standardized format
        if success:
            return {
                "success": True,
                "query": clean_address,
                "result": result  # The result from geocode() is already in the correct format
            }
        else:
            return {
                "success": False,
                "query": clean_address,
                "error": result.get("error", "Unknown error"),
                "reason": result.get("reason", "Geocoding failed")
            }
            
    except Exception as e:
        logger.error(f"Error in geocode_address: {str(e)}", exc_info=True)
        return {
            "success": False,
            "query": address if isinstance(address, str) else str(address),
            "error": "Exception",
            "reason": str(e)
        }


def find_places_nearby(
    latitude: float,
    longitude: float,
    radius: float = 500.0,
    place_types: List[str] = ["restaurant"],
    insights: List[str] = ["INSIGHT_COUNT", "INSIGHT_PLACES"],
    excluded_types: Optional[List[str]] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    operating_status: Optional[List[str]] = None,
    price_levels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Find places near a specified location using the Places Aggregate API.

    Note: No validation is performed here; inputs are assumed to be validated
    by the agent tool input_schema.
    """
    try:
        places_api = PlacesAggregateAPI()

        success, result = places_api.compute_insights(
            insights=insights,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            included_types=place_types,
            excluded_types=excluded_types,
            rating_min=rating_min,
            rating_max=rating_max,
            operating_status=operating_status,
            price_levels=price_levels,
        )

        request_echo = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "place_types": place_types,
            "insights": insights,
            "excluded_types": excluded_types,
            "rating_min": rating_min,
            "rating_max": rating_max,
            "operating_status": operating_status,
            "price_levels": price_levels,
        }
        if success:
            return {"success": True, "request": request_echo, "response": result}
        else:
            return {
                "success": False,
                "request": request_echo,
                "error": result.get("error", "Unknown error"),
                "reason": result.get("reason", "API request failed"),
            }

    except Exception as e:
        logger.error(f"Error in find_places_nearby: {str(e)}", exc_info=True)
        return {"success": False, "error": "Exception", "reason": str(e)}


def find_places_nearby_polygon(
    polygon: Dict[str, Any],
    place_types: List[str] = ["restaurant"],
    insights: List[str] = ["INSIGHT_COUNT", "INSIGHT_PLACES"],
    excluded_types: Optional[List[str]] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    operating_status: Optional[List[str]] = None,
    price_levels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Find places within a specified polygon using the Places Aggregate API.

    Note: The Area Insights API only supports 'INSIGHT_COUNT' for polygon searches.
    This function will force the insight type to 'INSIGHT_COUNT'.
    """
    try:
        places_api = PlacesAggregateAPI()

        # The Area Insights API only supports INSIGHT_COUNT for polygon searches.
        # We force this here to prevent API errors.
        forced_insights = ["INSIGHT_COUNT"]

        # The compute_insights method expects the custom_area argument to contain the polygon.
        success, result = places_api.compute_insights(
            insights=forced_insights,
            custom_area={"polygon": polygon},
            included_types=place_types,
            excluded_types=excluded_types,
            rating_min=rating_min,
            rating_max=rating_max,
            operating_status=operating_status,
            price_levels=price_levels,
        )

        request_echo = {
            "polygon": polygon,
            "place_types": place_types,
            "insights": forced_insights, # Report the insight that was actually used
            "excluded_types": excluded_types,
            "rating_min": rating_min,
            "rating_max": rating_max,
            "operating_status": operating_status,
            "price_levels": price_levels,
        }
        if success:
            return {"success": True, "request": request_echo, "response": result}
        else:
            return {
                "success": False,
                "request": request_echo,
                "error": result.get("error", "Unknown error"),
                "reason": result.get("reason", "API request failed"),
            }

    except Exception as e:
        logger.error(f"Error in find_places_nearby_polygon: {str(e)}", exc_info=True)
        return {"success": False, "error": "Exception", "reason": str(e)}


def find_places_in_grid(
    latitude: float,
    longitude: float,
    box_size_meters: float = 1000.0,
    tile_count: int = 16,
    place_types: List[str] = ["restaurant"],
    insights: List[str] = ["INSIGHT_COUNT"],
    excluded_types: Optional[List[str]] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    operating_status: Optional[List[str]] = None,
    price_levels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Creates a grid around a coordinate and finds places in each tile.

    This function first defines a square bounding box centered on the given
    latitude and longitude. It then divides this box into a grid of smaller
    polygons (tiles) and runs a place search for each one.

    Args:
        latitude: The center latitude for the grid.
        longitude: The center longitude for the grid.
        box_size_meters: The width and height of the total grid area in meters.
        tile_count: The total number of tiles to divide the grid into (e.g., 16 for a 4x4 grid).
        place_types: A list of place types to search for.
        insights: A list of insights to request (e.g., 'INSIGHT_COUNT').
        ...other filters: Optional filters for the place search.

    Returns:
        A dictionary containing the results for each tile in the grid.
    """
    try:
        # 1. Initialize the TileGenerator with the desired number of tiles
        tile_generator = TileGenerator(target_tile_count=tile_count)

        # 2. Generate the grid of tiles from a center point
        tiles = tile_generator.generate_tiles_from_center(
            center_lat=latitude,
            center_lon=longitude,
            box_size_meters=box_size_meters
        )

        # 3. Run find_places_nearby_polygon for each tile and format the result
        results = []
        for tile in tiles:
            # The polygon from TileGenerator is already in the correct format
            polygon_coords = tile["polygon"]["coordinates"]
            
            search_result = find_places_nearby_polygon(
                polygon={"coordinates": polygon_coords},
                place_types=place_types,
                insights=insights,
                excluded_types=excluded_types,
                rating_min=rating_min,
                rating_max=rating_max,
                operating_status=operating_status,
                price_levels=price_levels,
            )
            
            # Simplify the result for the final output
            success = search_result.get("success", False)
            count = 0
            if success and search_result.get("response"):
                # API returns count as a string, convert to int
                count = int(search_result["response"].get("count", 0))

            simplified_result = {
                "tile_id": tile["id"],
                "lat": tile["centroid"]["lat"],
                "lon": tile["centroid"]["lon"],
                "tile_area_sq_km": tile["area_sq_km"],
                "success": success,
                "count": count,
            }
            results.append(simplified_result)

        return {"success": True, "grid_results": results}

    except Exception as e:
        logger.error(f"Error in find_places_in_grid: {str(e)}", exc_info=True)
        return {"success": False, "error": "Exception", "reason": str(e)}


