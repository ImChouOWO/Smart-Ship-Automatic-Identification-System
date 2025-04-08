import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber'; // Canvas 來自 fiber
import { Suspense } from 'react'; // Suspense 是 React 的
import { Card, CardContent, Box } from '@mui/material'; // MUI 的部份

function YachtModel({ imu }) {
  const { scene } = useGLTF('/model/Yacht.glb');
  const ref = useRef();

  // 使用 IMU 數據旋轉模型
  useFrame(() => {
    if (ref.current && imu) {
      ref.current.rotation.x = imu.pitch * Math.PI / 180; // pitch (上下)
      ref.current.rotation.y = imu.yaw * Math.PI / 180;   // yaw (轉向)
      ref.current.rotation.z = imu.roll * Math.PI / 180;  // roll (翻滾)
    }
  });

  return <primitive ref={ref} object={scene} scale={1} />;
}

const Ship = ({shipData}) => {
  return (
    <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', height: 300 }}>
      {/* <CardHeader title="3D Ship Model" avatar={<Compass color="#00AEEF" />} /> */}
      <CardContent>
        <Box sx={{ height: 200 }}>
          <Canvas camera={{ position: [0, 2, 4], fov: 60 }}>
            <ambientLight intensity={0.6} />
            <directionalLight position={[5, 5, 5]} />
            <Suspense fallback={null}>
              <YachtModel imu={shipData}/>
            </Suspense>
            <OrbitControls />
          </Canvas>
        </Box>
      </CardContent>
    </Card>
  );
};

export default Ship;
