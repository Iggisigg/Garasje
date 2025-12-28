"""
Geocoding utilities for converting GPS coordinates to addresses
"""

import httpx
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


async def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Convert GPS coordinates to address using Nominatim (OpenStreetMap)

    Args:
        latitude: GPS latitude
        longitude: GPS longitude

    Returns:
        Address string or None if geocoding fails
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    'lat': latitude,
                    'lon': longitude,
                    'format': 'json',
                    'addressdetails': 1,
                    'accept-language': 'no'  # Norwegian addresses
                },
                headers={
                    'User-Agent': 'ChargingManager/1.0'  # Required by Nominatim
                }
            )

            if response.status_code == 200:
                data = response.json()

                # Build a nice address string
                address_parts = []
                address = data.get('address', {})

                # Add road/street
                if 'road' in address:
                    road = address['road']
                    if 'house_number' in address:
                        road += f" {address['house_number']}"
                    address_parts.append(road)

                # Add city/town/village
                city = address.get('city') or address.get('town') or address.get('village')
                if city:
                    address_parts.append(city)

                # Add postcode if available
                if 'postcode' in address:
                    address_parts.append(address['postcode'])

                if address_parts:
                    full_address = ", ".join(address_parts)
                    logger.debug(f"Geocoded ({latitude}, {longitude}) → {full_address}")
                    return full_address
                else:
                    # Fallback to display_name
                    return data.get('display_name')

            logger.warning(f"Geocoding failed: HTTP {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None


def format_coordinates(latitude: Optional[float], longitude: Optional[float]) -> str:
    """
    Format GPS coordinates as a readable string

    Args:
        latitude: GPS latitude
        longitude: GPS longitude

    Returns:
        Formatted coordinate string
    """
    if latitude is None or longitude is None:
        return "Ukjent posisjon"

    return f"{latitude:.6f}, {longitude:.6f}"
