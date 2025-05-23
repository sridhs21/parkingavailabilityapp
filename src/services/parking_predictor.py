from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import googlemaps
import numpy as np
import requests
from math import radians, sin, cos, sqrt, atan2

# First define the ParkingLocation class
@dataclass
class ParkingLocation:
    id: str
    name: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    hours_of_operation: Optional[str] = None
    source: Optional[str] = None
    fee: Optional[bool] = None
    access_type: Optional[str] = None

@dataclass
class NearbyEvent:
    name: str
    venue_name: str
    latitude: float
    longitude: float
    place_type: str
    is_operational: bool
    current_popularity: Optional[int] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

class ParkingPredictor:
    def __init__(self):
        # Time-based factors - adjusted for typical work/class schedules
        self.time_factors = {
            'weekday': {
                'early_morning': (5, 7, 0.2),    # Very few people
                'morning_rush': (7, 9, 1.6),     # Peak arrival time
                'mid_morning': (9, 11, 1.3),     # Still busy
                'lunch_rush': (11, 14, 1.2),     # Lunch turnover
                'afternoon': (14, 16, 1.1),      # Steady
                'afternoon_exit': (16, 18, 0.9), # People leaving
                'evening': (18, 22, 0.6),        # Quieter
                'late_night': (22, 5, 0.2)       # Minimal activity
            },
            'weekend': {
                'early_hours': (5, 9, 0.2),      # Very quiet
                'morning': (9, 12, 0.5),         # Some activity
                'afternoon': (12, 17, 0.7),      # Busier
                'evening': (17, 22, 0.5),        # Moderate
                'late_night': (22, 5, 0.2)       # Minimal
            }
        }

        # Location-specific base capacities and sensitivities
        self.lot_characteristics = {
            'public': {
                'base_capacity': 0.7,            # Generally busy
                'weather_sensitivity': 1.0,      # Standard weather impact
                'event_sensitivity': 1.3,        # High event impact
                'time_sensitivity': 1.0,         # Standard time impact
                'weekend_modifier': 0.6          # Less busy on weekends
            },
            'private': {
                'base_capacity': 0.8,            # Usually quite full
                'weather_sensitivity': 0.7,      # Less affected by weather
                'event_sensitivity': 0.8,        # Less affected by events
                'time_sensitivity': 1.2,         # More time-dependent
                'weekend_modifier': 0.3          # Much quieter on weekends
            },
            'visitor': {
                'base_capacity': 0.5,            # Often has space
                'weather_sensitivity': 1.2,      # More weather-affected
                'event_sensitivity': 1.5,        # Highly event-sensitive
                'time_sensitivity': 0.9,         # Less time-dependent
                'weekend_modifier': 1.2          # Busier on weekends
            },
            'faculty': {
                'base_capacity': 0.85,           # Usually very full
                'weather_sensitivity': 0.6,      # Less weather-affected
                'event_sensitivity': 0.7,        # Less event-affected
                'time_sensitivity': 1.4,         # Highly time-dependent
                'weekend_modifier': 0.2          # Empty on weekends
            },
            'resident': {
                'base_capacity': 0.9,            # Nearly always full
                'weather_sensitivity': 0.5,      # Minimal weather impact
                'event_sensitivity': 0.6,        # Low event impact
                'time_sensitivity': 0.4,         # Stable throughout day
                'weekend_modifier': 0.9          # Similar on weekends
            }
        }

        # Seasonal factors (based on month)
        self.seasonal_factors = {
            1: 1.1,   # January - Winter weather impact
            2: 1.1,   # February
            3: 1.0,   # March
            4: 1.0,   # April
            5: 0.9,   # May - End of academic year
            6: 0.7,   # June - Summer
            7: 0.7,   # July - Summer
            8: 0.8,   # August - Summer
            9: 1.4,   # September - Start of academic year
            10: 1.2,  # October
            11: 1.1,  # November
            12: 0.9   # December - Holiday season
        }

        # Weather impact factors - adjusted for parking behavior
        self.weather_factors = {
            'Clear': 1.0,
            'Clouds': 1.0,
            'Rain': 1.4,        # People less likely to walk/bike
            'Snow': 1.6,        # Significant impact on transportation
            'Thunderstorm': 1.5,
            'Mist': 1.1,
            'Fog': 1.2,
            'Drizzle': 1.2,
            'Smoke': 1.3,       # Poor air quality increases driving
            'Haze': 1.1
        }

        # Temperature factors adjusted for behavior patterns
        self.temperature_factors = [
            (-float('inf'), 15, 1.5),  # Very cold - more driving
            (15, 32, 1.4),             # Cold - more driving
            (32, 45, 1.2),             # Cool - some walking/biking
            (45, 65, 1.0),             # Ideal - mixed transport
            (65, 75, 0.9),             # Pleasant - more walking/biking
            (75, 85, 1.0),             # Warm - mixed transport
            (85, float('inf'), 1.2)    # Hot - more driving
        ]

        # Special day types
        self.special_day_factors = {
            'holiday': 0.4,            # Holiday
            'weekend': 0.6,            # Regular weekend
            'academic_break': 0.5,     # School breaks
            'exam_period': 1.3,        # Exam times
            'move_in': 1.6,            # Move-in days
            'move_out': 1.6,           # Move-out days
            'career_fair': 1.5,        # Career fairs
            'orientation': 1.4,        # Orientation days
            'game_day': 1.7,          # Sports events
            'graduation': 1.8          # Graduation
        }

        # Distance from main attractions factor
        self.distance_factors = {
            'central': 1.4,            # Central location
            'peripheral': 0.8,         # Edge of campus
            'remote': 0.6              # Remote location
        }

        # Lot size impact (bigger lots tend to have more availability)
        self.size_factors = {
            'small': 1.2,              # <50 spaces
            'medium': 1.0,             # 50-200 spaces
            'large': 0.8               # >200 spaces
        }

    def predict_occupancy(self, location: ParkingLocation,
                         gmaps_client: googlemaps.Client,
                         lot_type: str = 'public',
                         timestamp: Optional[datetime] = None,
                         weather_api_key: Optional[str] = None) -> Dict:
        """
        Enhanced prediction incorporating all factors
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Get base characteristics
        lot_info = self.lot_characteristics.get(lot_type, self.lot_characteristics['public'])
        base_occupancy = lot_info['base_capacity']

        # Apply seasonal factor
        month = timestamp.month
        seasonal_factor = self.seasonal_factors[month]
        base_occupancy *= seasonal_factor

        # Apply weekend modifier if applicable
        is_weekend = timestamp.weekday() >= 5
        if is_weekend:
            base_occupancy *= lot_info['weekend_modifier']

        # Get time impact
        time_impact = self.get_time_factor(timestamp, lot_type)
        
        # Get weather impact
        weather_impact = self.get_weather_impact(
            location.latitude, 
            location.longitude,
            weather_api_key
        )
        weather_factor = 1 + ((weather_impact['factor'] - 1) * lot_info['weather_sensitivity'])

        # Get nearby events impact
        events = self.get_nearby_events(
            gmaps_client,
            location.latitude,
            location.longitude
        )
        event_impact = self.calculate_event_impact(location, events, timestamp)
        event_factor = 1 + ((event_impact['factor'] - 1) * lot_info['event_sensitivity'])

        # Calculate special day impact if applicable
        special_day_factor = self.get_special_day_factor(timestamp)

        # Calculate distance factor (you'll need to implement logic to determine if central/peripheral/remote)
        distance_factor = self.get_distance_factor(location)

        # Calculate final occupancy with all factors
        occupancy = (base_occupancy * 
                    time_impact['factor'] * 
                    weather_factor * 
                    event_factor * 
                    special_day_factor * 
                    distance_factor)

        # Add small random variation (reduced from 0.03 to 0.02 for more stability)
        occupancy += np.random.normal(0, 0.02)
        occupancy = max(0.0, min(1.0, occupancy))

        # Determine status and color with more granular thresholds
        if occupancy >= 0.9:
            status = "Full"
            color = "red"
        elif occupancy >= 0.7:
            status = "Nearly Full"
            color = "orange"
        elif occupancy >= 0.4:
            status = "Moderate"
            color = "yellow"
        else:
            status = "Available"
            color = "green"

        return {
            "status": status,
            "color": color,
            "occupancy": round(occupancy * 100, 1),
            "factors": {
                "seasonal": round(seasonal_factor, 2),
                "time_impact": round(time_impact['factor'], 2),
                "weather_impact": round(weather_factor, 2),
                "event_impact": round(event_factor, 2),
                "special_day": round(special_day_factor, 2),
                "distance": round(distance_factor, 2)
            },
            "details": {
                "time": time_impact['description'],
                "weather": weather_impact['description'],
                "significant_venues": event_impact['venues'],
                "season": f"{timestamp.strftime('%B')} factor",
                "lot_type": lot_type
            }
        }

    # Add these new helper methods
    def get_special_day_factor(self, timestamp: datetime) -> float:
        return 1.0

    def get_distance_factor(self, location: ParkingLocation) -> float:
        return self.distance_factors['central']

    def get_nearby_events(self, gmaps_client: googlemaps.Client, 
                         lat: float, lon: float, 
                         radius_m: int = 1000) -> List[NearbyEvent]:
        """
        Fetch nearby events and venues using Google Places API
        """
        try:
            # Search for active venues and potential event locations
            event_venues = gmaps_client.places_nearby(
                location=(lat, lon),
                radius=radius_m,
                type=['stadium', 'movie_theater', 'shopping_mall', 'restaurant',
                      'night_club', 'museum', 'university', 'church', 'convention_center']
            )

            nearby_events = []
            
            for venue in event_venues.get('results', []):
                # Get detailed place information
                place_details = gmaps_client.place(venue['place_id'])['result']
                
                # Extract current popularity if available
                current_popularity = None
                if 'current_popularity' in place_details:
                    current_popularity = place_details['current_popularity']
                
                event = NearbyEvent(
                    name=place_details.get('name', 'Unknown Venue'),
                    venue_name=place_details.get('name', 'Unknown Venue'),
                    latitude=venue['geometry']['location']['lat'],
                    longitude=venue['geometry']['location']['lng'],
                    place_type=next((t for t in venue.get('types', []) 
                                   if t in self.venue_type_weights), 'other'),
                    is_operational=place_details.get('business_status') == 'OPERATIONAL',
                    current_popularity=current_popularity,
                    rating=place_details.get('rating'),
                    user_ratings_total=place_details.get('user_ratings_total')
                )
                nearby_events.append(event)

            return nearby_events

        except Exception as e:
            print(f"Error fetching nearby events: {e}")
            return []

    def calculate_event_impact(self, lot_location: ParkingLocation, 
                             events: List[NearbyEvent], 
                             current_time: datetime) -> Dict:
        """Calculate the impact of nearby events on parking occupancy"""
        total_impact = 1.0
        significant_venues = []
        
        for event in events:
            # Only consider operational venues
            if not event.is_operational:
                continue
                
            # Calculate distance to event
            event_distance = calculate_distance(
                lot_location.latitude, lot_location.longitude,
                event.latitude, event.longitude
            )

            if event_distance <= 1.0:  # Within 1km
                # Base impact calculation
                venue_weight = self.venue_type_weights.get(event.place_type, 1.0)
                distance_factor = 1 - (event_distance / 1.0)  # Linear decay with distance
                
                # Factor in venue popularity if available
                popularity_factor = 1.0
                if event.current_popularity is not None:
                    popularity_factor = 1 + (event.current_popularity / 100)
                
                # Factor in venue rating and number of ratings
                rating_factor = 1.0
                if event.rating is not None and event.user_ratings_total is not None:
                    rating_weight = min(1.0, event.user_ratings_total / 1000)  # Cap at 1000 ratings
                    rating_factor = 1 + (((event.rating / 5) - 0.5) * rating_weight)
                
                # Combine all factors
                event_impact = 1 + (
                    venue_weight * 
                    distance_factor * 
                    popularity_factor * 
                    rating_factor - 1
                ) * 0.5  # Dampen the overall impact
                
                # Update total impact (use max for overlapping high-impact events)
                total_impact = max(total_impact, event_impact)
                
                # Track significant venues for reporting
                if event_impact > 1.1:  # Only include venues with notable impact
                    significant_venues.append({
                        'name': event.venue_name,
                        'type': event.place_type,
                        'distance_km': round(event_distance, 2),
                        'impact': round(event_impact - 1, 2)
                    })

        return {
            'factor': total_impact,
            'venues': significant_venues
        }

    def get_weather_impact(self, lat: float, lon: float, api_key: Optional[str] = None) -> Dict:
        """Get weather impact using weather API"""
        default_weather = {'factor': 1.0, 'description': 'Unknown'}
        
        if not api_key:
            return default_weather

        try:
            # Make weather API call (example using OpenWeatherMap)
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
            response = requests.get(url)
            data = response.json()

            weather = data['weather'][0]['main']
            temp = data['main']['temp']

            # Calculate weather impact
            weather_factor = self.weather_factors.get(weather, 1.0)
            
            # Apply temperature impact
            for min_temp, max_temp, impact in self.temperature_factors:
                if min_temp <= temp < max_temp:
                    weather_factor *= impact
                    break

            return {
                'factor': weather_factor,
                'description': f"{weather}, {temp}°F"
            }
        except Exception as e:
            print(f"Weather API error: {e}")
            return default_weather

    def get_time_factor(self, timestamp: datetime, lot_type: str) -> Dict:
        """Calculate time-based impact"""
        is_weekend = timestamp.weekday() >= 5
        current_hour = timestamp.hour
        
        # Get appropriate time factors
        time_periods = self.time_factors['weekend'] if is_weekend else self.time_factors['weekday']
        
        # Find applicable time period
        time_factor = 1.0
        period_name = "Normal hours"
        
        for period, (start, end, factor) in time_periods.items():
            if start <= current_hour < end or (start > end and (current_hour >= start or current_hour < end)):
                time_factor = factor
                period_name = period
                break

        # Adjust for lot type
        lot_sensitivity = self.lot_characteristics[lot_type]['time_sensitivity']
        adjusted_factor = 1 + ((time_factor - 1) * lot_sensitivity)

        return {
            'factor': adjusted_factor,
            'description': period_name
        }