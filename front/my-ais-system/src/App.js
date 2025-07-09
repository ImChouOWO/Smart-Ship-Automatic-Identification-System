import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  Compass, Navigation, Webcam, Signal, AlertTriangle, BatteryCharging, Move
} from 'lucide-react';
import {
  Card, CardContent, CardHeader, Box, Typography, LinearProgress,
} from '@mui/material';
import Ship from './page/ship';
import { io } from "socket.io-client";
import CONFIG from './config';

// Leaflet 修復圖示
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const MapUpdater = ({ position }) => {
  const map = useMap();
  useEffect(() => {
    if (position.latitude !== 0 && position.longitude !== 0) {
      map.setView([position.latitude, position.longitude], map.getZoom());
    }
  }, [position, map]);
  return null;
};

const App = () => {
  const socket = io(CONFIG.SOCKET_IO_URL);
  const [motionStatus, setMotionStatus] = useState(false);
  const [powerStatus, setPowerStatus] = useState(false);
  const [shipData, setShipData] = useState({
    heading: 45,
    speed: 12.5,
    position: {
      time: 0,
      latitude: 0,
      longitude: 0,
      altitude: 0,
    },
    imu: {
      roll: 0,
      pitch: 0,
      yaw: 0,
    },
    signalStrength: 85,
    batteryLevel: 78,
    rudderAngle: 10,
  });

  useEffect(() => {
    socket.on('ship_status', (data) => {
      console.log("📥 ship_status data:", data);

      setShipData({
        ...shipData,
        imu: data.imu ? {
          roll: parseFloat(data.imu[0]),
          pitch: parseFloat(data.imu[1]),
          yaw: parseFloat(data.imu[2]),
        } : shipData.imu,
        position: data.gps ? {
          time: data.gps.time,
          latitude: parseFloat(data.gps.latitude),
          longitude: parseFloat(data.gps.longitude),
          altitude: parseFloat(data.gps.altitude),
        } : shipData.position,
      });

      if (data.status) {
        setMotionStatus(!!data.status.motion);
        setPowerStatus(!!data.status.power);
      }
    });

    return () => socket.off('ship_status');
  }, [shipData]);

  return (
    <Box sx={{ width: '100%', minHeight: '100vh', bgcolor: '#1E3A5F', p: 3 }}>
      <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
        <Box mb={3}>
          <Typography variant="h3" component="h1" color="#FFFFFF" gutterBottom>
            Ship AIS Monitoring System
          </Typography>
          <Typography color="#D1D5DB">Real-time Monitoring and Data Analysis</Typography>
        </Box>

        <Box display="flex" gap={3} mb={3}>
          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="Real-time Camera Feed" avatar={<Webcam color="#00AEEF" />} />
            <CardContent>
              <Box sx={{
                aspectRatio: '16/9',
                bgcolor: '#0A2239',
                borderRadius: 2,
                overflow: 'hidden',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <iframe
                  src={CONFIG.VIDEO_STREAM_URL}
                  style={{ width: '100%', height: '100%', border: 'none', borderRadius: 8 }}
                  allow="autoplay; fullscreen; camera; microphone"
                  title="WebRTC Player"
                />
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="IMU Data" avatar={<Compass color="#00AEEF" />} />
            <CardContent>
              <Ship shipData={shipData.imu} />
              <Typography>Roll: {shipData.imu.roll}°</Typography>
              <Typography>Pitch: {shipData.imu.pitch}°</Typography>
              <Typography>Yaw: {shipData.imu.yaw}°</Typography>
            </CardContent>
          </Card>
        </Box>

        <Box display="flex" gap={3} mb={3}>
          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="Module Status" avatar={<AlertTriangle color="#00AEEF" />} />
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Box display="flex" alignItems="center" gap={1}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: motionStatus ? '#00FF00' : '#FF0000' }} />
                  <Typography>Motion</Typography>
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: powerStatus ? '#00FF00' : '#FF0000' }} />
                  <Typography>Power</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="GPS Location" avatar={<Navigation color="#00AEEF" />} />
            <CardContent>
              <Typography>Latitude: {shipData.position.latitude}°N</Typography>
              <Typography>Longitude: {shipData.position.longitude}°E</Typography>
              <Typography>Speed: {shipData.speed} knots</Typography>
            </CardContent>
          </Card>
        </Box>

        <Box display="flex" gap={3} mb={3}>
          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="Rudder Angle" avatar={<Move color="#00AEEF" />} />
            <CardContent>
              <Typography>Rudder Angle: {shipData.rudderAngle}°</Typography>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="Battery Level" avatar={<BatteryCharging color="#00AEEF" />} />
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography>Battery Level: {shipData.batteryLevel}%</Typography>
                <Box sx={{ width: '50%' }}>
                  <LinearProgress variant="determinate" value={shipData.batteryLevel} color="success" />
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="5G Signal" avatar={<Signal color="#00AEEF" />} />
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography>Signal Strength: {shipData.signalStrength}%</Typography>
                <Box sx={{ width: '50%' }}>
                  <LinearProgress variant="determinate" value={shipData.signalStrength} color="info" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {
          shipData.position.latitude !== 0 && shipData.position.longitude !== 0 && (
            <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF' }}>
              <CardHeader title="Map Location" avatar={<Navigation color="#00AEEF" />} />
              <CardContent>
                <MapContainer
                  center={[shipData.position.latitude, shipData.position.longitude]}
                  zoom={13}
                  style={{ height: 500, borderRadius: '8px', overflow: 'hidden' }}
                >
                  <MapUpdater position={shipData.position} />
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; OpenStreetMap contributors'
                  />
                  <Marker
                    key={`${shipData.position.latitude}-${shipData.position.longitude}`}
                    position={[shipData.position.latitude, shipData.position.longitude]}
                  >
                    <Popup>
                      Ship Position: {shipData.position.latitude}°N, {shipData.position.longitude}°E
                    </Popup>
                  </Marker>
                </MapContainer>
              </CardContent>
            </Card>
          )
        }
      </Box>
    </Box>
  );
};

export default App;
