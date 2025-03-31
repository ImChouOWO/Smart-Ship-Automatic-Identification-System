import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Compass, Navigation, Webcam, Signal, AlertTriangle, Battery, MoveHorizontal, Home } from 'lucide-react';
import { Card, CardContent, CardHeader, Box, Typography, LinearProgress } from '@mui/material';

// 解決 Leaflet marker 圖標問題
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const HomePage = () => {
  const [shipData] = useState({
    heading: 45,
    speed: 12.5,
    position: {
      latitude: 22.609277252039476,
      longitude: 120.27353590281415,
    },
    imu: {
      roll: 2.1,
      pitch: 1.3,
      yaw: 45.2,
    },
    signalStrength: 85,
    batteryLevel: 76,
    rudderAngle: 10,
    rudderSpeed: 40,
  });

  return (
    <Box sx={{ width: '100%', minHeight: '100vh', bgcolor: '#ede6e6', p: 4 }}>
      <Box sx={{ maxWidth: 1300, mx: 'auto' }}>
        <Box textAlign="center" mb={4}>
          <Typography variant="h3" fontWeight="bold">
            Ship AIS Monitoring System
          </Typography>
          <Typography variant="subtitle1" color="gray">
            Real-time Data Tracking & Visualization
          </Typography>
        </Box>

        <Box display="grid" gridTemplateColumns={{ xs: '1fr', lg: '2fr 3fr' }} gap={4}>
          <Box display="flex" flexDirection="column" gap={4}>
            <Card>
              <CardHeader title="Map Location" avatar={<Navigation />} />
              <CardContent>
                <MapContainer
                  center={[shipData.position.latitude, shipData.position.longitude]}
                  zoom={13}
                  style={{ height: 500, borderRadius: '8px', overflow: 'hidden' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; OpenStreetMap contributors'
                  />
                  <Marker position={[shipData.position.latitude, shipData.position.longitude]}>
                    <Popup>
                      Ship Position: {shipData.position.latitude}°N, {shipData.position.longitude}°E
                    </Popup>
                  </Marker>
                </MapContainer>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default HomePage;
