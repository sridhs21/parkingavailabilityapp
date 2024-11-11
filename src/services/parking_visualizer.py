import folium
from folium import plugins
from datetime import datetime
import json
import numpy as np

class ParkingVisualizer:
    def __init__(self, parking_locations, predictor=None, gmaps_client=None, weather_api_key=None):
        self.parking_locations = parking_locations
        self.predictor = predictor
        self.gmaps_client = gmaps_client
        self.weather_api_key = weather_api_key

    def get_status(self, location):
        """Get status using predictor if available, otherwise use basic estimation"""
        if self.predictor and self.gmaps_client:
            try:
                prediction = self.predictor.predict_occupancy(
                    location=location,
                    gmaps_client=self.gmaps_client,
                    weather_api_key=self.weather_api_key
                )
                return prediction['status'], prediction['color'], prediction
            except Exception as e:
                print(f"Error using predictor for {location.name}: {e}")
                return self.estimate_crowdedness(location)
        return self.estimate_crowdedness(location)
        
    def estimate_crowdedness(self, location, current_hour=None):
        """Fallback estimation if predictor is not available"""
        if current_hour is None:
            current_hour = datetime.now().hour
            
        peak_hours = set(range(8, 11)) | set(range(13, 16))
        moderate_hours = set(range(11, 13)) | set(range(16, 18))
        
        if "Visitor" in location.name:
            base_score = 0.5
        elif "North" in location.name or "West" in location.name:
            base_score = 0.8
        else:
            base_score = 0.7
            
        if current_hour in peak_hours:
            time_multiplier = 1.0
        elif current_hour in moderate_hours:
            time_multiplier = 0.7
        else:
            time_multiplier = 0.4
            
        crowdedness = base_score * time_multiplier
        
        if crowdedness > 0.7:
            return "High", "red", None
        elif crowdedness > 0.4:
            return "Medium", "yellow", None
        else:
            return "Low", "green", None
    
    def create_map(self):
        """Create an interactive map with parking locations"""
        print("Initializing map...")
        
        m = folium.Map(
            location=[42.729869, -73.676871],  # RPI coordinates
            zoom_start=16,
            tiles="OpenStreetMap"
        )

        # Add custom CSS for popup styling
        m.get_root().html.add_child(folium.Element("""
            <style>
                .parking-popup {
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    max-width: 200px;
                }
                .parking-popup h4 {
                    margin: 0 0 5px 0;
                    color: #333;
                }
                .parking-status {
                    font-weight: bold;
                    margin-top: 5px;
                }
            </style>
        """))

        # Add location control
        plugins.LocateControl(
            auto_start=True,
            flyTo=False,
            position="topleft",
            strings={"title": "Show my location"},
            icon='fa fa-location-arrow',
            locateOptions={
                'enableHighAccuracy': True,
                'watch': True
            }
        ).add_to(m)
        
        print("Adding parking locations to map...")
        for location in self.parking_locations:
            print(f"Adding location: {location.name}")
            
            # Get status using predictor or basic estimation
            status, color, prediction = self.get_status(location)
            
            # Create popup content
            if prediction:
                popup_html = f"""
                    <div class="parking-popup">
                        <h4>{location.name}</h4>
                        <div>Address: {location.address or 'Not available'}</div>
                        <div>Hours: {location.hours_of_operation or 'Not specified'}</div>
                        <div>Type: {location.access_type}</div>
                        <div class="parking-status" style="color: {color}">
                            Status: {status} ({prediction['occupancy']}% full)
                        </div>
                        <div style="margin-top: 5px;">
                            <strong>Factors:</strong>
                            <ul style="margin: 5px 0; padding-left: 20px;">
                                <li>Time Impact: {prediction['factors']['time_impact']}x</li>
                                <li>Weather Impact: {prediction['factors']['weather_impact']}x</li>
                                <li>Event Impact: {prediction['factors']['event_impact']}x</li>
                            </ul>
                        </div>
                    </div>
                """
            else:
                popup_html = f"""
                    <div class="parking-popup">
                        <h4>{location.name}</h4>
                        <div>Address: {location.address or 'Not available'}</div>
                        <div>Hours: {location.hours_of_operation or 'Not specified'}</div>
                        <div>Type: {location.access_type}</div>
                        <div class="parking-status" style="color: {color}">Status: {status}</div>
                    </div>
                """
            
            # Add marker to map
            folium.CircleMarker(
                location=[location.latitude, location.longitude],
                radius=10,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{location.name} - {status}",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=2
            ).add_to(m)

        # Add legend
        legend_html = """
        <div style="position: fixed; bottom: 50px; right: 50px; width: 150px;
                    background-color: white; padding: 10px; border-radius: 5px;
                    z-index: 1000; box-shadow: 0 0 10px rgba(0,0,0,0.2);">
            <h4 style="margin: 0 0 10px 0;">Parking Status</h4>
            <div style="margin-bottom: 5px;">
                <span style="display: inline-block; height: 12px; width: 12px;
                           background-color: green; border-radius: 50%;"></span>
                <span style="margin-left: 5px;">Available</span>
            </div>
            <div style="margin-bottom: 5px;">
                <span style="display: inline-block; height: 12px; width: 12px;
                           background-color: yellow; border-radius: 50%;"></span>
                <span style="margin-left: 5px;">Moderate</span>
            </div>
            <div style="margin-bottom: 5px;">
                <span style="display: inline-block; height: 12px; width: 12px;
                           background-color: orange; border-radius: 50%;"></span>
                <span style="margin-left: 5px;">Nearly Full</span>
            </div>
            <div>
                <span style="display: inline-block; height: 12px; width: 12px;
                           background-color: red; border-radius: 50%;"></span>
                <span style="margin-left: 5px;">Full</span>
            </div>
            <div style="margin-top: 10px;">
                <span style="display: inline-block; height: 20px; width: 20px;
                           background-color: blue; border-radius: 50%; border: 3px solid white;
                           box-shadow: 0 0 3px rgba(0,0,0,0.3);"></span>
                <span style="margin-left: 5px;">Your Location</span>
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        print("Map creation complete")
        return m