import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import { Card, CardContent, Box } from '@mui/material';

// 🔁 正規化角度（負角度 → 正常 0~360 度範圍）
function normalizeAngle(deg) {
  return ((deg % 360) + 360) % 360;
}

function YachtModel({ imu }) {
  const { scene } = useGLTF('/model/Yacht.glb');
  const ref = useRef();

  // 模型方向預調整（依照你的模型需求可以開啟）
  // scene.rotation.y = Math.PI; // ← 可選，如果模型預設方向不對

  useFrame(() => {
    if (ref.current && imu) {
      // 單位轉換 + 正規化角度
      const roll = normalizeAngle(imu.roll);
      const pitch = normalizeAngle(imu.pitch);
      const yaw = normalizeAngle(imu.yaw);

      // 設定旋轉順序（很重要）
      ref.current.rotation.order = 'ZXY';

      ref.current.rotation.x = pitch * Math.PI / 180; // Pitch → X
      ref.current.rotation.y = yaw * Math.PI / 180;   // Yaw → Y
      ref.current.rotation.z = roll * Math.PI / 180;  // Roll → Z
    }
  });

  return <primitive ref={ref} object={scene} scale={1} />;
}

const Ship = ({ shipData }) => {
  return (
    <Card sx={{ bgcolor: '#2C3E50', color: '#FFFFFF', height: 300 }}>
      <CardContent>
        <Box sx={{ height: 200 }}>
          <Canvas camera={{ position: [0, 2, 4], fov: 60 }}>
            <ambientLight intensity={0.6} />
            <directionalLight position={[5, 5, 5]} />
            <Suspense fallback={null}>
              <YachtModel imu={shipData} />
            </Suspense>
            <OrbitControls />
          </Canvas>
        </Box>
      </CardContent>
    </Card>
  );
};

export default Ship;
