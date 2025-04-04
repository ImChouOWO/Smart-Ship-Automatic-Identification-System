import React, { useState,useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Compass, Navigation, Webcam, Signal, AlertTriangle, BatteryCharging, Move } from 'lucide-react';
import { Card, CardContent, CardHeader, Box, Typography, LinearProgress } from '@mui/material';
import Ship from './page/ship';
import {io} from "socket.io-client"

// 修復 Leaflet 的 icon 問題
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
    position: {
      time:0,
      latitude: 0,
      longitude: 0,
      altitude:0,
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
    socket.on('server_imu', (data) => {
      console.log("📥 IMU data from server:", data);
      setShipData((prev) => ({
        ...prev,
        imu: {
          roll: parseFloat(data.roll),
          pitch: parseFloat(data.pitch),
          yaw: parseFloat(data.yaw),
        },
      }));
    });

    return () => {
      socket.off('server_imu');
    };
  }, []);
  useEffect(()=>{
    socket.on('server_gps', (data) => {
      console.log("📥 IMU data from server:", data);
      setShipData((prev) => ({
        ...prev,
          position: {
          "time":data.time,
          latitude: parseFloat(data.latitude),
          longitude: parseFloat(data.longitude),
          altitude: parseFloat(data.altitude),
        },
      }));
    });

    return () => {
      socket.off('server_gps');
    };
  },[]);


  return (
    <Box sx={{ width: '100%', minHeight: '100vh', bgcolor: '#1E3A5F', p: 3 }}>
      <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
        <Box mb={3}>
          <Typography variant="h3" component="h1" color="#FFFFFF" gutterBottom>
            Ship AIS Monitoring System
          </Typography>
          <Typography color="#D1D5DB">Real-time Monitoring and Data Analysis</Typography>
        </Box>

        {/* 第一區：Camera + IMU */}
        <Box display="flex" gap={3} mb={3}>
          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="Real-time Camera Feed" avatar={<Webcam color="#00AEEF" />} />
            <CardContent>
              <Box
                sx={{
                  aspectRatio: '16/9',
                  bgcolor: '#0A2239',
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

          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardHeader title="IMU Data" avatar={<Compass color="#00AEEF" />} />
            <CardContent>
              <Ship shipData={shipData.imu}/>
              <Typography>Roll: {shipData.imu.roll}°</Typography>
              <Typography>Pitch: {shipData.imu.pitch}°</Typography>
              <Typography>Yaw: {shipData.imu.yaw}°</Typography>
            </CardContent>
          </Card>
        </Box>

        {/* 第二區：Status + GPS */}
        <Box display="flex" gap={3} mb={3}>
          <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', flex: 1 }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <AlertTriangle color="#FFA500" />
                <Typography color="#FFA500">System Operating Normally</Typography>
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

        {/* 第三區：舵角、電池、訊號 */}
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

        {/* 地圖維持原本格式 */}
        <Card sx={{ gridColumn: { xs: 'span 1', lg: 'span 2' }, bgcolor: '#2C3E50', color: '#FFFFFF' }}>
          <CardHeader title="Map Location" avatar={<Navigation color="#00AEEF" />} />
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
  );
};

export default App;
