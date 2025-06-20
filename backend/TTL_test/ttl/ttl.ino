// === 模式開關 ===
bool use_simulation = false;  // 設為 false 可切換為實際 GPS 模式，設為 true 可切換為模擬 GPS 模式

// === 模擬資料 ===
float simulated_lat = 23.567000;
float simulated_lon = 120.985000;
float simulated_heading = 0.0;  // 45=東北方向

// === 目標座標 ===
float target_lat = 23.567000;
float target_lon = 120.985000;

// === GPS / IMU 解析資料 ===
float gps_lat = 0.0;
float gps_lon = 0.0;
float imu_heading = 0.0;

// === 計算地球距離（Haversine）===
float haversine(float lat1, float lon1, float lat2, float lon2) {
  const float R = 6371000.0; // 地球半徑（公尺）
  float dLat = radians(lat2 - lat1);
  float dLon = radians(lon2 - lon1);
  float a = sin(dLat / 2) * sin(dLat / 2) +
            cos(radians(lat1)) * cos(radians(lat2)) *
            sin(dLon / 2) * sin(dLon / 2);
  float c = 2 * atan2(sqrt(a), sqrt(1 - a));
  return R * c;
}

// === 計算方位角（Bearing）===
float bearing(float lat1, float lon1, float lat2, float lon2) {
  float dLon = radians(lon2 - lon1);
  float y = sin(dLon) * cos(radians(lat2));
  float x = cos(radians(lat1)) * sin(radians(lat2)) -
            sin(radians(lat1)) * cos(radians(lat2)) * cos(dLon);
  float brng = atan2(y, x);
  return fmod(degrees(brng) + 360.0, 360.0);
}

// === 封包用 XOR 計算 BCC ===
byte calculate_bcc(byte *data, int len) {
  byte bcc = 0;
  for (int i = 0; i < len; i++) {
    bcc ^= data[i];
  }
  return bcc;
}

// === 發送導航封包 ===
void send_packet(int speed, int direction) {
  byte packet[] = {
    0x1B, 0x04, 0x01, 0x01, 0x03,
    (byte)speed, 0x7C, (byte)direction,
    0x03, 0x01
  };
  byte bcc = calculate_bcc(packet, sizeof(packet));
  
  for (int i = 0; i < sizeof(packet); i++) {
    Serial.write(packet[i]); 
  }
  Serial.write(bcc);
}


// === 導航核心邏輯 ===
void compute_and_send(float lat, float lon, float heading) {
  float dist = haversine(lat, lon, target_lat, target_lon);
  float brng = bearing(lat, lon, target_lat, target_lon);
  float offset = brng - heading;

  // 將偏差角正規化到 [-180, 180]
  if (offset < -180) offset += 360;
  if (offset > 180) offset -= 360;

  // 假設方向偏差 -90 ~ +90 對應到 0~100
  int direction = map((int)offset, -90, 90, 0, 100);
  direction = constrain(direction, 0, 100);

  // 距離控制速度，最多為 100
  int speed = constrain((int)(dist / 2), 0, 100);

  Serial.println("🚀 導航資訊:");
  Serial.print("距離(m): "); Serial.println(dist);
  Serial.print("方位角: "); Serial.println(brng);
  Serial.print("偏移角: "); Serial.println(offset);
  Serial.print("Speed: "); Serial.print(speed); Serial.print(" | Direction: "); Serial.println(direction);

  send_packet(speed, direction);
}

// === 處理模擬資料 ===
void simulate_navigation() {
  compute_and_send(simulated_lat, simulated_lon, simulated_heading);
}

// === 處理實際 GPS+IMU 封包資料 ===

#define PACKET_LEN 22
#define HEADER_BYTE 0x1B

#define PACKET_LEN 22
#define HEADER_BYTE 0x1B

void parse_real_packet() {
  static byte buf[PACKET_LEN];

  // 確保有足夠資料
  while (Serial.available() >= PACKET_LEN) {
    // Peek 確認同步開頭
    if (Serial.peek() != HEADER_BYTE) {
      Serial.read();  // 丟掉不同步資料
      continue;
    }

    // 讀取一整包
    Serial.readBytes(buf, PACKET_LEN);

    // 驗證 BCC
    byte bcc = calculate_bcc(buf, PACKET_LEN - 1);
    if (bcc != buf[PACKET_LEN - 1]) {
      Serial.println("❌ BCC 驗證失敗");
      return;
    }

    // ✅ 顯示封包內容（HEX 格式）
    Serial.print("📩 接收封包 HEX: ");
    for (int i = 0; i < PACKET_LEN; i++) {
      if (buf[i] < 0x10) Serial.print("0");  // 若小於 0x10 補 0
      Serial.print(buf[i], HEX);
      Serial.print(" ");
    }
    Serial.println();

    // 解析封包資料（除以 10000 是因為你是 x10000 傳過來）
    gps_lat = ((unsigned long)buf[5] << 16 | buf[6] << 8 | buf[7]) / 10000.0;
    gps_lon = ((unsigned long)buf[9] << 16 | buf[10] << 8 | buf[11]) / 10000.0;
    imu_heading = buf[15];

    Serial.println("✅ 封包接收完成");
    Serial.print("緯度: "); Serial.println(gps_lat, 6);
    Serial.print("經度: "); Serial.println(gps_lon, 6);
    Serial.print("角度: "); Serial.println(imu_heading);

    compute_and_send(gps_lat, gps_lon, imu_heading);
  }
}



void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("🟢 Arduino Mega 導航系統啟動中...");
}

void loop() {
  if (use_simulation) {
    simulate_navigation();
  } else {
    delay(10);
    parse_real_packet();
  }

  delay(500);  // 每 5 秒更新一次導航
}