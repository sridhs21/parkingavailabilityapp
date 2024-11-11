let map;
        let userMarker;
        let parkingMarkers = [];
        let lastUpdateTime = new Date();
        
        function initMap() {
            map = L.map('map').setView([42.729869, -73.676871], 16);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            const userIcon = L.divIcon({
                className: 'user-marker',
                html: `<div style="
                    background-color: blue;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    border: 3px solid white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.5);"
                ></div>`,
                iconSize: [26, 26],  // Bigger than the div to account for border
                iconAnchor: [13, 13] // Center of the icon
            });
            
            userMarker = L.marker([0, 0], {icon: userIcon}).addTo(map);
            
            startLocationTracking();
            startPeriodicUpdates();
        }
        
        let accuracyCircle;
        
        function startLocationTracking() {
            if ("geolocation" in navigator) {
                const options = {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                };
                navigator.geolocation.watchPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const accuracy = position.coords.accuracy;
                        
                        // Update user marker
                        userMarker.setLatLng([lat, lon]);
                        
                        // Update accuracy circle
                        if (accuracyCircle) {
                            map.removeLayer(accuracyCircle);
                        }
                        accuracyCircle = L.circle([lat, lon], {
                            radius: accuracy,
                            color: 'blue',
                            fillColor: '#3388ff',
                            fillOpacity: 0.1,
                            weight: 1
                        }).addTo(map);
                        
                        document.getElementById('locationStatus').innerHTML = 
                            `Location: ${lat.toFixed(6)}, ${lon.toFixed(6)}<br>Accuracy: ±${accuracy.toFixed(1)}m`;
                            
                        if (!map.userLocationInitialized) {
                            map.setView([lat, lon], 16);
                            map.userLocationInitialized = true;
                        }
                    },
                    function(error) {
                        document.getElementById('locationStatus').textContent = 
                            `Location Error: ${error.message}`;
                    },
                    options
                );
            } else {
                document.getElementById('locationStatus').textContent = 
                    'Location: Browser does not support geolocation';
            }
        }
        
        async function updateParkingData() {
            try {
                const position = await getCurrentPosition();
                
                const response = await fetch('/update_parking', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    })
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                const parkingData = await response.json();
                
                parkingMarkers.forEach(marker => marker.remove());
                parkingMarkers = [];
                
                parkingData.forEach(lot => {
                    const marker = L.circleMarker(
                        [lot.latitude, lot.longitude],
                        {
                            radius: 10,
                            color: lot.color,
                            fillColor: lot.color,
                            fillOpacity: 0.7,
                            weight: 2
                        }
                    ).addTo(map);
                    
                    marker.bindPopup(createPopupContent(lot));
                    parkingMarkers.push(marker);
                });
                
                lastUpdateTime = new Date();
                document.getElementById('updateStatus').textContent = 
                    `Last Update: ${lastUpdateTime.toLocaleTimeString()}`;
                    
            } catch (error) {
                console.error('Error updating parking data:', error);
                document.getElementById('updateStatus').textContent = 
                    `Update Error: ${error.message}`;
            }
        }
        
        function createPopupContent(lot) {
            return `
                <div style="font-family: Arial, sans-serif; font-size: 13px;">
                    <h4 style="margin: 0 0 5px 0;">${lot.name}</h4>
                    <div>Address: ${lot.address || 'Not available'}</div>
                    <div>Hours: ${lot.hours_of_operation || 'Not specified'}</div>
                    <div>Type: ${lot.lot_type}</div>
                    <div style="margin-top: 5px;">
                        <strong>Current Status:</strong> ${lot.status}
                        <div>Occupancy: ${lot.occupancy}%</div>
                    </div>
                    <div style="margin-top: 5px;">
                        <strong>Factors:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            <li>Time Impact: ${lot.factors.time_impact}x</li>
                            <li>Weather Impact: ${lot.factors.weather_impact}x</li>
                            <li>Event Impact: ${lot.factors.event_impact}x</li>
                        </ul>
                    </div>
                </div>
            `;
        }
        
        function getCurrentPosition() {
            return new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                });
            });
        }
        
        function startPeriodicUpdates() {
            updateParkingData();
            setInterval(updateParkingData, 10000);
        }
        
        window.onload = initMap;