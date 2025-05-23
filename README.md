# Parking Availability Prediction App

A parking availability prediction system that provides insights into parking occupancy using numerical processing, location data, and environmental factors.

## Features

- **Real-time Parking Visualization**: Interactive map displaying current parking availability with color-coded status indicators.
- **Intelligent Predictions**: Heuristic-based occupancy predictions driven by real-time data on time, weather, nearby events, and seasonal patterns.
- **Live Location Tracking**: GPS enabled user location tracking with accuracy indicators.
- **Dynamic Updates**: Automatic 10-second refresh cycles for parking information.
- **Multi-factor Analysis**: Considers weather conditions, time of day, nearby events, and venue popularity.

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Mapping**: Leaflet.js, Folium
- **APIs**: Google Maps Places API, Google Geocoding API, OpenWeatherMap API
- **Numerical Processing**: NumPy for numerical analysis and data manipulation.

## Project Structure

```
parkingavailabilityapp/
├── src/
│   ├── main.py                 # Flask application entry point
│   ├── models/
│   │   └── parking_spot.py     # Data models for parking locations
│   └── services/
│       ├── parking_finder.py   # Google Places API integration
│       ├── parking_predictor.py # ML prediction algorithms
│       └── parking_visualizer.py # Map visualization logic
├── display/
│   ├── liveparkingmap.html     # Real-time tracking interface
│   ├── parking_map.html        # Static map view
│   ├── script.js               # Frontend JavaScript logic
│   └── styles.css              # Application styling
└── requirements.txt
```

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sridhs21/parkingavailabilityapp
   cd parkingavailabilityapp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file with:
   ```
   GOOGLE_API_KEY=your_google_maps_api_key
   WEATHER_API_KEY=your_openweathermap_api_key
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

5. **Access the application**
   - Static map: `http://localhost:5000/`
   - Live tracking: `http://localhost:5000/live`

## API Endpoints

- `GET /` - Static parking map view
- `GET /live` - Real-time tracking interface
- `POST /update_parking` - Fetch updated parking data for given coordinates

## Prediction Algorithm

The system uses a sophisticated multi-factor prediction model that considers:

- **Temporal Factors**: Time of day, day of week, seasonal variations
- **Weather Impact**: Temperature, precipitation, visibility conditions
- **Event Influence**: Nearby venues, current popularity, ratings
- **Location Characteristics**: Parking lot type, capacity, accessibility
- **Academic Calendar**: University schedules, exam periods, holidays

## Status Indicators

- 🟢 **Available** (< 40% full)
- 🟡 **Moderate** (40-70% full)
- 🟠 **Nearly Full** (70-90% full)
- 🔴 **Full** (> 90% full)
