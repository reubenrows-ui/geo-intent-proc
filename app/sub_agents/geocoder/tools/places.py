import os
import json
from typing import Any, Dict, List, Optional, Tuple, Union

import requests


class PlacesAggregateAPI:
    """Base class for querying the Google Area Insights API."""

    BASE_URL = "https://areainsights.googleapis.com/v1"

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initializes the Area Insights API client.

        Args:
            api_key: The Google Cloud API key. If not provided, it will
                     try to get it from the 'GOOGLE_MAPS_API_KEY' environment variable.

        Raises:
            ValueError: If the API key is not provided or found in the environment.
        """
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key must be provided or set as GOOGLE_MAPS_API_KEY "
                "environment variable."
            )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
            }
        )

    def _post_request(
        self, endpoint: str, payload: Dict[str, Any], field_mask: Optional[List[str]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Makes a POST request to the specified endpoint.

        Args:
            endpoint: The API endpoint to call (e.g., ':computeInsights').
            payload: The JSON body for the request.
            field_mask: A list of fields to include in the response.

        Returns:
            A tuple containing (success, result):
            - If success is True, result contains the API response.
            - If success is False, result contains error information.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self.session.headers.copy()
        
        if field_mask:
            headers["X-Goog-FieldMask"] = ",".join(field_mask)

        try:
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.HTTPError as e:
            # Simple error reporting
            error_info = {
                "error": "API request failed",
                "reason": str(e),
                "status_code": e.response.status_code if hasattr(e, 'response') else None
            }
            
            # Try to extract error message from response
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    error_json = json.loads(e.response.text)
                    if 'error' in error_json and 'message' in error_json['error']:
                        error_info["reason"] = error_json['error']['message']
                except:
                    pass
                    
            return False, error_info
        except Exception as e:
            # General error handling for other types of errors
            return False, {
                "error": "Request failed",
                "reason": str(e)
            }

    def compute_insights(
        self,
        insights: List[str],
        included_types: Union[str, List[str]],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[float] = None,
        custom_area: Optional[Dict[str, Any]] = None,
        excluded_types: Optional[List[str]] = None,
        rating_min: Optional[float] = None,
        rating_max: Optional[float] = None,
        operating_status: Optional[Union[str, List[str]]] = None,
        price_levels: Optional[Union[str, List[str]]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Compute insights for places in a specified area.

        The area can be defined by either a circle (latitude, longitude, radius)
        or a custom polygon (custom_area). One of these must be provided.

        Optional filters (excluded_types, rating_min/max, etc.) are only included
        in the request when provided.
        """
        # Build the location filter
        location_filter = {}
        final_insights = insights[:] # Make a copy

        if custom_area:
            location_filter["customArea"] = custom_area
            # The Area Insights API only supports INSIGHT_COUNT for polygon searches.
            # We force this here to prevent API errors.
            if "INSIGHT_COUNT" not in final_insights or len(final_insights) > 1:
                final_insights = ["INSIGHT_COUNT"]
        elif latitude is not None and longitude is not None and radius is not None:
            location_filter["circle"] = {
                "latLng": {"latitude": latitude, "longitude": longitude},
                "radius": radius,
            }
        else:
            raise ValueError(
                "Either a circular area (latitude, longitude, radius) or a "
                "custom_area (polygon) must be provided for the location filter."
            )

        # Ensure includedTypes is a list
        if isinstance(included_types, str):
            included_types = [included_types]

        # Build the type filter with only provided optional fields
        type_filter: Dict[str, Any] = {
            "includedTypes": included_types,
        }
        if excluded_types:
            type_filter["excludedTypes"] = excluded_types

        # Build the complete filter object
        filter_obj: Dict[str, Any] = {
            "locationFilter": location_filter,
            "typeFilter": type_filter,
        }

        # Add optional filters if they are provided
        if operating_status is not None:
            filter_obj["operatingStatus"] = (
                [operating_status] if isinstance(operating_status, str) else operating_status
            )

        if price_levels is not None:
            filter_obj["priceLevels"] = (
                [price_levels] if isinstance(price_levels, str) else price_levels
            )

        rating_filter: Dict[str, Any] = {}
        if rating_min is not None:
            rating_filter["minRating"] = rating_min
        if rating_max is not None:
            rating_filter["maxRating"] = rating_max
        if rating_filter:
            filter_obj["ratingFilter"] = rating_filter

        # Build the complete payload
        payload = {
            "insights": final_insights,
            "filter": filter_obj,
        }

        # Make the API request
        return self._post_request(endpoint=":computeInsights", payload=payload)
    
    def compute_insights_raw(self, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Directly send a raw payload to the computeInsights endpoint.
        
        Args:
            payload: Complete API request payload
            
        Returns:
            A tuple containing (success, result):
            - If success is True, result contains the API response.
            - If success is False, result contains error information.
        """
        return self._post_request(endpoint=":computeInsights", payload=payload)
