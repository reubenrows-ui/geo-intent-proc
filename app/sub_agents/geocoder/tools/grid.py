import math

class TileGenerator:
    """
    A class to generate a grid of geographic tile centroids
    within a specified bounding box.
    """

    def __init__(self, target_tile_count=100):
        """
        Initializes the TileGenerator.

        Args:
            target_tile_count (int): The approximate number of tiles to divide the bounding box into.
                                     This will be used to determine the grid size (e.g., 100 -> 10x10 grid).
        """
        if target_tile_count <= 0:
            raise ValueError("Target tile count must be a positive number.")
        self.target_tile_count = target_tile_count

    def _calculate_tile_size(self, bounds):
        """
        Calculates the latitude and longitude dimensions for each tile.

        Args:
            bounds (tuple): A tuple representing the bounding box in the format
                            (south_west_lat, south_west_lon, north_east_lat, north_east_lon).

        Returns:
            dict: A dictionary containing the calculated 'lat_tile_size' and 'lon_tile_size'.
        """
        sw_lat, sw_lon, ne_lat, ne_lon = bounds
        lat_diff = ne_lat - sw_lat
        lon_diff = ne_lon - sw_lon
        
        tiles_per_side = math.sqrt(self.target_tile_count)
        
        return {
            "lat_tile_size": lat_diff / tiles_per_side,
            "lon_tile_size": lon_diff / tiles_per_side,
        }

    def generate_tiles_from_center(self, center_lat: float, center_lon: float, box_size_meters: float):
        """
        Creates a bounding box around a center point and then generates tiles within it.

        Args:
            center_lat: The center latitude for the grid.
            center_lon: The center longitude for the grid.
            box_size_meters: The width and height of the total grid area in meters.

        Returns:
            A list of generated tiles, same as generate_tiles().
        """
        # Calculate the bounding box from the center point and size
        m_per_deg_lat = 111132.954
        m_per_deg_lon = 111319.488 * math.cos(math.radians(center_lat))
        
        # Avoid division by zero at the poles, though highly unlikely for this use case
        if m_per_deg_lon == 0:
            m_per_deg_lon = 0.001 

        half_box_lat_deg = (box_size_meters / 2) / m_per_deg_lat
        half_box_lon_deg = (box_size_meters / 2) / m_per_deg_lon

        sw_lat = center_lat - half_box_lat_deg
        sw_lon = center_lon - half_box_lon_deg
        ne_lat = center_lat + half_box_lat_deg
        ne_lon = center_lon + half_box_lon_deg
        bounds = (sw_lat, sw_lon, ne_lat, ne_lon)

        return self.generate_tiles(bounds)

    def generate_tiles(self, bounds):
        """
        Generates a list of tiles covering the given bounding box.

        Args:
            bounds (tuple): A tuple representing the bounding box in the format
                            (south_west_lat, south_west_lon, north_east_lat, north_east_lon).

        Returns:
            list: A list of dictionaries, where each dictionary represents a tile and
                  contains 'id', 'centroid', 'polygon', 'area_sq_meters', and 'area_sq_km'.
        """
        sw_lat, sw_lon, ne_lat, ne_lon = bounds
        if not (ne_lat > sw_lat and ne_lon > sw_lon):
            raise ValueError("Invalid bounds: North-East corner must be north and east of South-West corner.")

        tiles = []
        tile_id = 0
        tile_size = self._calculate_tile_size(bounds)
        lat_tile_size = tile_size["lat_tile_size"]
        lon_tile_size = tile_size["lon_tile_size"]

        # Constants for area calculation (in meters)
        m_per_deg_lat = 111132.954  # meters per degree latitude
        m_per_deg_lon_base = 111319.488 # meters per degree longitude at the equator
        
        # Epsilon to handle floating point inaccuracies in loop conditions
        epsilon = 1e-9

        current_lat = sw_lat
        while current_lat < ne_lat - epsilon:
            current_lon = sw_lon
            while current_lon < ne_lon - epsilon:
                centroid_lat = current_lat + lat_tile_size / 2
                centroid_lon = current_lon + lon_tile_size / 2

                # Calculate tile area in square meters
                tile_height_m = lat_tile_size * m_per_deg_lat
                tile_width_m = lon_tile_size * m_per_deg_lon_base * math.cos(math.radians(centroid_lat))
                tile_area_sq_m = tile_height_m * tile_width_m
                tile_area_sq_km = tile_area_sq_m / 1_000_000

                # Define the vertices of the tile polygon
                coords = [
                    {"latitude": current_lat, "longitude": current_lon},
                    {"latitude": current_lat, "longitude": current_lon + lon_tile_size},
                    {"latitude": current_lat + lat_tile_size, "longitude": current_lon + lon_tile_size},
                    {"latitude": current_lat + lat_tile_size, "longitude": current_lon},
                    {"latitude": current_lat, "longitude": current_lon}  # Close the polygon
                ]

                tiles.append({
                    "id": tile_id,
                    "centroid": {
                        "lat": centroid_lat,
                        "lon": centroid_lon,
                    },
                    "polygon": {
                        "coordinates": coords
                    },
                    "area_sq_meters": round(tile_area_sq_m, 2),
                    "area_sq_km": round(tile_area_sq_km, 4)
                })
                tile_id += 1
                current_lon += lon_tile_size
            current_lat += lat_tile_size
            
        return tiles