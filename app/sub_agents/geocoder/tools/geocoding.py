import os
from typing import Dict, Any, Tuple, Optional
import requests


class GeocodingAPI:
    """
    A simple client for geocoding addresses using the Google Maps Geocoding API.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initializes the Geocoding API client.

        Args:
            api_key: The Google Cloud API key. If not provided, it will
                     be read from the 'GOOGLE_MAPS_API_KEY' environment variable.

        Raises:
            ValueError: If the API key is not provided and cannot be found in the environment.
        """
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "A Google API key must be provided or set as the GOOGLE_MAPS_API_KEY "
                "environment variable."
            )
        self.session = requests.Session()

    def geocode(self, address: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Geocodes a given address string into geographic coordinates.

        Args:
            address: The street address or place name to geocode (e.g., "Eiffel Tower, Paris, France").

        Returns:
            A tuple containing (success, data):
            - If successful (True), `data` is a dictionary with 'latitude', 'longitude',
              and 'formatted_address'.
            - If it fails (False), `data` is a dictionary containing 'error' and 'reason'.
        """
        params = {
            "address": address,
            "key": self.api_key
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if data.get("status") == "OK" and data.get("results"):
                location = data["results"][0]["geometry"]["location"]
                formatted_address = data["results"][0]["formatted_address"]
                
                return True, {
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "formatted_address": formatted_address,
                }
            else:
                # Handle API-level errors like "ZERO_RESULTS" or "REQUEST_DENIED"
                # Return a user-friendly error message instead of the raw API status.
                error_message = "No results found" if data.get("status") == "ZERO_RESULTS" else "Geocoding API error"
                return False, {
                    "error": error_message,
                    "reason": data.get("error_message", f"API returned status: {data.get('status', 'Unknown')}"),
                }
        except requests.exceptions.RequestException as e:
            # Handle network-level errors
            return False, {"error": "Request failed", "reason": str(e)}

    def get_coordinates(self, address: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get the coordinates (latitude and longitude) for an address.
        
        This is a convenience method that returns just the location coordinates.

        Args:
            address: The address to geocode

        Returns:
            A tuple containing (success, result):
            - If success is True, result contains the latitude and longitude.
            - If success is False, result contains error information.
        """
        success, result = self.geocode(address)
        
        if not success:
            return False, result
            
        try:
            # Extract the coordinates from the first result
            location = result["results"][0]["geometry"]["location"]
            
            return True, {
                "latitude": location["lat"],
                "longitude": location["lng"],
                "formatted_address": result["results"][0].get("formatted_address")
            }
            
        except (KeyError, IndexError):
            return False, {
                "error": "Invalid response format",
                "reason": "Could not extract location from geocoding response"
            }