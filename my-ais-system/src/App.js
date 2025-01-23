import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Compass, Navigation, Webcam, Signal, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, Box, Typography, LinearProgress } from '@mui/material';

// 解決 Leaflet marker 圖標問題
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const App = () => {
  const [shipData, setShipData] = useState({
    heading: 45,
    speed: 12.5,
    // 22.609277252039476, 120.27353590281415
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
  });

  return (
    <Box sx={{ width: '100%', minHeight: '100vh', bgcolor: '#ede6e6', p: 3 }}>
      <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
        <Box mb={3}>
          <Typography variant="h3" component="h1" color="text.primary" gutterBottom>
            Ship AIS Monitoring System
          </Typography>
          <Typography color="text.secondary">Real-time Monitoring and Data Analysis</Typography>
        </Box>

        <Box display="grid" gridTemplateColumns={{ xs: '1fr', lg: '1fr 1fr' }} gap={3}>
          {/* 左側攝影機畫面 */}
          <Box display="flex" flexDirection="column" gap={3}>
            <Card>
              <CardHeader title="Real-time Camera Feed" avatar={<Webcam />} />
              <CardContent>
                <Box
                  sx={{
                    aspectRatio: '16/9',
                    bgcolor: 'grey.800',
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <img
                    src="/api/placeholder/800/450"
                    alt="攝影機畫面"
                    style={{ borderRadius: '8px', width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                </Box>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1}>
                  <AlertTriangle />
                  <Typography color="warning.main">System Operating Normally</Typography>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* 右側感測器數據 */}
          <Box display="flex" flexDirection="column" gap={3}>
            <Card>
              <CardHeader title="GPS Location" avatar={<Navigation />} />
              <CardContent>
                <Typography>Latitude: {shipData.position.latitude}°N</Typography>
                <Typography>Longitude: {shipData.position.longitude}°E</Typography>
                <Typography>Speed: {shipData.speed} knots</Typography>
              </CardContent>
            </Card>

            <Card>
              <CardHeader title="IMU Data" avatar={<Compass />} />
              <CardContent>
                <Typography>Roll: {shipData.imu.roll}°</Typography>
                <Typography>Pitch: {shipData.imu.pitch}°</Typography>
                <Typography>Yaw: {shipData.imu.yaw}°</Typography>
              </CardContent>
            </Card>

            <Card>
              <CardHeader title="5G Signal" avatar={<Signal />} />
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography>Signal Strength: {shipData.signalStrength}%</Typography>
                  <Box sx={{ width: '50%' }}>
                    <LinearProgress variant="determinate" value={shipData.signalStrength} />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* 地圖卡片 - 跨越兩列 */}
          <Card sx={{ gridColumn: { xs: 'span 1', lg: 'span 2' } }}>
            <CardHeader title="Map Location" avatar={<Navigation />} />
            <CardContent>
              <MapContainer
                center={[shipData.position.latitude, shipData.position.longitude]}
                zoom={13}
                style={{ height: 500, borderRadius: '8px', overflow: 'hidden' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
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
  );
};

export default App;
