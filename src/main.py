import os
import folium
import googlemaps
import webbrowser
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from dotenv import load_dotenv
from services.parking_predictor import ParkingPredictor
from services.parking_finder import ParkingFinder
from services.parking_visualizer import ParkingVisualizer
from datetime import datetime

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, 
           template_folder=os.path.join(PROJECT_ROOT, 'display'),  # Updated path
           static_folder=os.path.join(PROJECT_ROOT, 'display'))    # Updated path

load_dotenv()

# Initialize services
predictor = ParkingPredictor()
finder = ParkingFinder(use_mock=False)
gmaps_client = googlemaps.Client(key=os.getenv('GOOGLE_API_KEY'))
weather_api_key = os.getenv('WEATHER_API_KEY')

@app.route('/')
def static_map():
    #this will generate a static map (planning to transition to dynamic)
    try:
        CENTER_LAT = 42.729869
        CENTER_LON = -73.676871
        SEARCH_RADIUS = 1000

        print("Getting parking locations...")
        parking_locations = finder.get_parking_locations(CENTER_LAT, CENTER_LON, SEARCH_RADIUS)
        print(f"Found {len(parking_locations)} parking locations")
        
        print("Creating map...")
        visualizer = ParkingVisualizer(
            parking_locations,
            predictor=predictor,
            gmaps_client=gmaps_client,
            weather_api_key=weather_api_key
        )
        map_obj = visualizer.create_map()
        
        #use absolute path to save the file
        output_file = os.path.join(PROJECT_ROOT, 'display', 'parking_map.html')
        print(f"Saving map to {output_file}")
        map_obj.save(output_file)
        
        print("Serving map file...")
        return send_file(output_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"An error occurred: {str(e)}"

@app.route('/live')
def live_map():
    #serve the live tracking map
    return send_from_directory(os.path.join(PROJECT_ROOT, 'display'), 'liveparkingmap.html')

@app.route('/update_parking', methods=['POST'])
def update_parking():
    #handle real-time parking data updates
    try:
        data = request.json
        user_lat = data['latitude']
        user_lon = data['longitude']
        
        #get parking locations using finder
        parking_locations = finder.get_parking_locations(user_lat, user_lon, radius=1000)
        
        parking_data = []
        for location in parking_locations:
            #get prediction for each location
            prediction = predictor.predict_occupancy(
                location=location,
                gmaps_client=gmaps_client,
                weather_api_key=weather_api_key
            )
            
            #combine location and prediction data
            parking_data.append({
                **prediction,
                'name': location.name,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'lot_type': location.access_type
            })
        
        return jsonify(parking_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    #run flask app
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    main()