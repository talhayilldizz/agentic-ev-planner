import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in leaflet with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icon for charging stations
const chargeIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const EVRouteMap = ({ data }) => {
  if (!data || !data.start || !data.end) return null;

  // Calculate bounds to fit all markers
  const lats = [data.start[0], data.end[0], ...data.stops.map(s => s.lat)];
  const lons = [data.start[1], data.end[1], ...data.stops.map(s => s.lon)];
  
  const bounds = [
    [Math.min(...lats), Math.min(...lons)],
    [Math.max(...lats), Math.max(...lons)]
  ];

  const positions = [data.start, ...data.stops.map(s => [s.lat, s.lon]), data.end];

  return (
    <div style={{ height: '400px', width: '100%', borderRadius: '12px', overflow: 'hidden', marginTop: '16px', border: '1px solid rgba(255,255,255,0.1)', position: 'relative', zIndex: 1 }}>
      <MapContainer 
        bounds={bounds} 
        scrollWheelZoom={false} 
        style={{ height: '100%', width: '100%', zIndex: 1 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Draw a line connecting the route points approximately */}
        <Polyline positions={positions} color="#3b82f6" weight={4} dashArray="10, 10" />

        <Marker position={data.start}>
          <Popup>Başlangıç Noktası</Popup>
        </Marker>
        
        <Marker position={data.end}>
          <Popup>Varış Noktası</Popup>
        </Marker>

        {data.stops.map((stop, index) => (
          <Marker key={index} position={[stop.lat, stop.lon]} icon={chargeIcon}>
            <Popup>
              <div style={{ padding: '4px', textAlign: 'center' }}>
                <strong style={{ display: 'block', marginBottom: '8px' }}>{stop.title}</strong>
                <p style={{ margin: '0 0 8px 0', color: '#666' }}>{stop.popup}</p>
                <a 
                  href={stop.maps_link} 
                  target="_blank" 
                  rel="noreferrer"
                  style={{
                    display: 'inline-block',
                    padding: '6px 12px',
                    background: '#10b981',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '4px',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}
                >
                  📍 Haritada Aç
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default EVRouteMap;
