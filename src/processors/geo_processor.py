"""
Geographic Processor for WATCHKEEPER

This module implements geographic coordinate extraction from intelligence items.
"""

import re
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple

from src.processors.base_processor import BaseProcessor
from src.utils.logger import get_logger
from src.utils.config import get_config

class GeoProcessor(BaseProcessor):
    """
    Geographic processor for intelligence items
    
    This processor extracts geographic locations from text and enriches them with coordinates.
    It uses a combination of techniques:
    1. Pattern matching for common location formats
    2. Named entity recognition for location names
    3. Geocoding API for coordinate resolution
    """
    
    def __init__(self):
        """Initialize the geographic processor"""
        super().__init__("geo_processor")
        self.config = get_config().get("processors", {}).get("geo", {})
        
        # Geocoding API configuration
        self.geocoding_api = self.config.get("geocoding_api", "nominatim")
        self.api_key = self.config.get("api_key", "")
        self.api_url = self._get_api_url()
        
        # Rate limiting
        self.rate_limit = self.config.get("rate_limit", 1)  # requests per second
        self._last_request_time = 0
        
        # Cache for geocoding results
        self.cache = {}
        self.max_cache_size = self.config.get("max_cache_size", 1000)
        
        # Regular expressions for location patterns
        self.patterns = {
            "coordinates": r'(\d+\.?\d*)[°\s]?(?:N|S|North|South)[\s,]+(\d+\.?\d*)[°\s]?(?:E|W|East|West)',
            "city_country": r'(?:in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            "address": r'(\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)(?:,\s+[A-Za-z\s]+)?)'
        }
    
    async def process(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single intelligence item to extract geographic information
        
        Args:
            item: Intelligence item to process
            
        Returns:
            Dict[str, Any]: Processed intelligence item with geographic information
        """
        if not item.get("content"):
            self.logger.warning("Item has no content to process")
            return item
        
        # Create a copy of the item to avoid modifying the original
        processed_item = item.copy()
        
        # Add geo_data section if it doesn't exist
        if "geo_data" not in processed_item:
            processed_item["geo_data"] = {
                "locations": [],
                "coordinates": []
            }
        
        try:
            # Extract locations from text
            content = item.get("content", "")
            title = item.get("title", "")
            
            # Combine title and content for extraction
            text = f"{title}\n\n{content}"
            
            # Extract locations using pattern matching
            pattern_locations = self._extract_pattern_locations(text)
            
            # Extract locations from AI analysis if available
            ai_locations = []
            if "ai_analysis" in item and "locations" in item["ai_analysis"]:
                ai_locations = self._extract_ai_locations(item["ai_analysis"]["locations"])
            
            # Combine and deduplicate locations
            all_locations = self._deduplicate_locations(pattern_locations + ai_locations)
            
            # Geocode locations to get coordinates
            locations_with_coords = await self._geocode_locations(all_locations)
            
            # Update geo_data
            processed_item["geo_data"]["locations"] = locations_with_coords
            
            # Extract explicit coordinates
            coordinates = self._extract_coordinates(text)
            processed_item["geo_data"]["coordinates"] = coordinates
            
            self.logger.debug(f"Extracted {len(locations_with_coords)} locations and {len(coordinates)} explicit coordinates")
            
        except Exception as e:
            self.logger.error(f"Error in geographic processing: {e}", exc_info=True)
        
        return processed_item
    
    def _extract_pattern_locations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract locations using pattern matching
        
        Args:
            text: Text to extract locations from
            
        Returns:
            List[Dict[str, Any]]: List of extracted locations
        """
        locations = []
        
        # Extract city-country pairs
        city_country_matches = re.finditer(self.patterns["city_country"], text)
        for match in city_country_matches:
            city, country = match.groups()
            locations.append({
                "name": f"{city}, {country}",
                "type": "city",
                "confidence": 0.8,
                "source": "pattern"
            })
        
        # Extract addresses
        address_matches = re.finditer(self.patterns["address"], text)
        for match in address_matches:
            address = match.group(1)
            locations.append({
                "name": address,
                "type": "address",
                "confidence": 0.7,
                "source": "pattern"
            })
        
        return locations
    
    def _extract_ai_locations(self, ai_locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract locations from AI analysis
        
        Args:
            ai_locations: Locations from AI analysis
            
        Returns:
            List[Dict[str, Any]]: Formatted locations
        """
        locations = []
        
        for loc in ai_locations:
            locations.append({
                "name": loc.get("name", ""),
                "type": loc.get("type", "unknown").lower(),
                "confidence": loc.get("confidence", 0.5),
                "source": "ai"
            })
        
        return locations
    
    def _extract_coordinates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract explicit coordinates from text
        
        Args:
            text: Text to extract coordinates from
            
        Returns:
            List[Dict[str, Any]]: List of extracted coordinates
        """
        coordinates = []
        
        # Extract coordinates in format "X°N, Y°E" or similar
        coord_matches = re.finditer(self.patterns["coordinates"], text)
        for match in coord_matches:
            lat_str, lon_str = match.groups()
            
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                
                # Check if coordinates are valid
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    coordinates.append({
                        "latitude": lat,
                        "longitude": lon,
                        "source": "text",
                        "confidence": 0.9
                    })
            except ValueError:
                pass
        
        return coordinates
    
    def _deduplicate_locations(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate locations by name
        
        Args:
            locations: List of locations
            
        Returns:
            List[Dict[str, Any]]: Deduplicated locations
        """
        deduplicated = {}
        
        for loc in locations:
            name = loc["name"].lower()
            
            if name in deduplicated:
                # Keep the location with higher confidence
                if loc["confidence"] > deduplicated[name]["confidence"]:
                    deduplicated[name] = loc
            else:
                deduplicated[name] = loc
        
        return list(deduplicated.values())
    
    async def _geocode_locations(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Geocode locations to get coordinates
        
        Args:
            locations: List of locations
            
        Returns:
            List[Dict[str, Any]]: Locations with coordinates
        """
        result = []
        
        for loc in locations:
            name = loc["name"]
            
            # Check cache first
            if name in self.cache:
                # Use cached coordinates
                coords = self.cache[name]
                loc.update(coords)
                result.append(loc)
                continue
            
            # Geocode the location
            try:
                coords = await self._geocode(name)
                
                if coords:
                    # Add coordinates to location
                    loc.update(coords)
                    
                    # Add to cache
                    self.cache[name] = coords
                    
                    # Trim cache if needed
                    if len(self.cache) > self.max_cache_size:
                        # Remove a random item (simple approach)
                        self.cache.pop(next(iter(self.cache)))
                
                result.append(loc)
            
            except Exception as e:
                self.logger.error(f"Error geocoding '{name}': {e}")
                # Still include the location without coordinates
                result.append(loc)
        
        return result
    
    async def _geocode(self, location_name: str) -> Dict[str, Any]:
        """
        Geocode a location name to get coordinates
        
        Args:
            location_name: Name of the location
            
        Returns:
            Dict[str, Any]: Coordinates and metadata
        """
        # Implement rate limiting
        now = asyncio.get_event_loop().time()
        if now - self._last_request_time < 1.0 / self.rate_limit:
            await asyncio.sleep(1.0 / self.rate_limit - (now - self._last_request_time))
        
        self._last_request_time = asyncio.get_event_loop().time()
        
        # Use the appropriate geocoding API
        if self.geocoding_api == "nominatim":
            return await self._geocode_nominatim(location_name)
        elif self.geocoding_api == "google":
            return await self._geocode_google(location_name)
        else:
            self.logger.error(f"Unsupported geocoding API: {self.geocoding_api}")
            return {}
    
    async def _geocode_nominatim(self, location_name: str) -> Dict[str, Any]:
        """
        Geocode using Nominatim (OpenStreetMap)
        
        Args:
            location_name: Name of the location
            
        Returns:
            Dict[str, Any]: Coordinates and metadata
        """
        try:
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                "q": location_name,
                "format": "json",
                "limit": 1
            }
            
            headers = {
                "User-Agent": "WATCHKEEPER/1.0"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        self.logger.error(f"Nominatim API error: {response.status}")
                        return {}
                    
                    data = await response.json()
                    
                    if not data:
                        return {}
                    
                    result = data[0]
                    
                    return {
                        "latitude": float(result["lat"]),
                        "longitude": float(result["lon"]),
                        "display_name": result.get("display_name", ""),
                        "type": result.get("type", ""),
                        "importance": result.get("importance", 0.0),
                        "source": "nominatim"
                    }
        
        except Exception as e:
            self.logger.error(f"Error in Nominatim geocoding: {e}", exc_info=True)
            return {}
    
    async def _geocode_google(self, location_name: str) -> Dict[str, Any]:
        """
        Geocode using Google Maps API
        
        Args:
            location_name: Name of the location
            
        Returns:
            Dict[str, Any]: Coordinates and metadata
        """
        if not self.api_key:
            self.logger.error("Google Maps API key not configured")
            return {}
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": location_name,
                "key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        self.logger.error(f"Google Maps API error: {response.status}")
                        return {}
                    
                    data = await response.json()
                    
                    if data["status"] != "OK" or not data["results"]:
                        return {}
                    
                    result = data["results"][0]
                    location = result["geometry"]["location"]
                    
                    return {
                        "latitude": location["lat"],
                        "longitude": location["lng"],
                        "formatted_address": result.get("formatted_address", ""),
                        "place_id": result.get("place_id", ""),
                        "types": result.get("types", []),
                        "source": "google"
                    }
        
        except Exception as e:
            self.logger.error(f"Error in Google geocoding: {e}", exc_info=True)
            return {}
    
    def _get_api_url(self) -> str:
        """Get the API URL based on the configured geocoding API"""
        if self.geocoding_api == "nominatim":
            return "https://nominatim.openstreetmap.org/search"
        elif self.geocoding_api == "google":
            return "https://maps.googleapis.com/maps/api/geocode/json"
        else:
            return ""
