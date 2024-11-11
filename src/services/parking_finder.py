import os
import sys
import googlemaps
from typing import List
from dataclasses import dataclass
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.parking_spot import ParkingLocation

#this loads the env variables (api keys)
load_dotenv()

class ParkingFinder:
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        if not use_mock:
            self.api_key = os.getenv('GOOGLE_API_KEY')
            if not self.api_key:
                raise ValueError("Google API key is required")
            self.client = googlemaps.Client(key=self.api_key)

    def get_mock_data(self) -> List[ParkingLocation]:
        """Return mock parking data for testing"""
        return [
            ParkingLocation(
                id="mock_1",
                name="Test Parking Lot 1",
                latitude=42.731419,
                longitude=-73.675290,
                address="Test Address 1",
                hours_of_operation="24/7",
                source="mock_data",
                fee=True,
                access_type="public"
            ),
            ParkingLocation(
                id="mock_2",
                name="Test Parking Lot 2",
                latitude=42.730760,
                longitude=-73.681901,
                address="Test Address 2",
                hours_of_operation="9 AM - 5 PM",
                source="mock_data",
                fee=False,
                access_type="public"
            )
        ]

    def get_parking_locations(self, lat: float, lon: float, radius: int = 1000) -> List[ParkingLocation]:
        if self.use_mock:
            return self.get_mock_data()
            
        try:
            places_result = self.client.places_nearby(
                location=(lat, lon),
                radius=radius,
                keyword='parking'
            )
            
            parking_locations = []
            for place in places_result.get('results', []):
                place_details = self.client.place(place['place_id'])['result']
                location = ParkingLocation(
                    id=place['place_id'],
                    name=place['name'],
                    latitude=place['geometry']['location']['lat'],
                    longitude=place['geometry']['location']['lng'],
                    address=place_details.get('formatted_address'),
                    hours_of_operation=place_details.get('opening_hours', {}).get('weekday_text'),
                    source='google_places',
                    fee=place_details.get('business_status') == 'OPERATIONAL',
                    access_type='public'
                )
                parking_locations.append(location)
            
            return parking_locations
        except Exception as e:
            print(f"Error fetching parking data: {e}")
            print("Falling back to mock data...")
            return self.get_mock_data()