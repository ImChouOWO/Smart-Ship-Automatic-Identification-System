\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\]/ === 模式開關 ===
bool use_simulation = false;  // true 為模擬模式，false 為實際 GPS/IMU 封包

// === 模擬資料 ===
float simulated_lat = 23.567000;
float simulated_lon = 120.985000;
float simulated_heading = 0.0;  // 0°=北，45°=東北方向

// === 多目標座標陣列 ===
#define POINT_COUNT 4
float target_lat_list[POINT_COUNT] = {
  23.567000, 23.567200, 23.567000, 23.566800
};
float target_lon_list[POINT_COUNT] = {
  120.985000, 120.985200, 120.985400, 120.985200
};
int current_target_index = 0;

// === 速度模擬變數 ===
float simulated_speed = 0.0;
float max_simulated_speed = 2.0;
float acceleration = 0.2;
float deceleration_distance = 5.0;
float loop_interval = 1.0;

// === GPS / IMU 資料 ===
float gps_lat = 0.0;
float gps_lon = 0.0;
float imu_heading = 0.0;

// === 計算距離（Haversine）===
float haversine(float lat1, float lon1, float lat2, float lon2) {
  const float R = 6371000.0;
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
  return fmod(degrees(brng) + 360.0, 360.0)
  \
}

// === XOR 計算 BCC ===
byte calculate_bcc(byte *data, int len) {
  byte bcc = 0;
  for (int i = 0; i < len; i++) {
    bcc ^= data[i];
  }
  return bcc;
}

// === 傳送導航封包 ===
void send_packet(int speed, int direction) {
  byte packet[] = {
    0x1B, 0x04, 0x01, 0x01, 0x03,
    (byte)speed, 0x7C, (byte)direction,
    0x01, 0x03
  };
  byte bcc = calculate_bcc(packet, sizeof(packet));
  for (int i = 0; i < sizeof(packet); i++) {
    Serial.write(packet[i]);
  }
  Serial.write(bcc);
  Serial.flush();
  Serial.println("\nSent navigation packet");
}

// === 導航邏輯 ===
void compute_and_send(float lat, float lon, float ) {
  float target_lat = target_lat_list[current_target_index];
  float target_lon = target_lon_list[current_target_index];

  float dist = haversine(lat, lon, target_lat, target_lon);
  float brng = bearing(lat, lon, target_lat, target_lon);
  float offset = brng - heading;

  if (offset < -180) offset += 360;
  if (offset > 180) offset -= 360;

  int direction = map((int)offset, -90, 90, 0, 100);
  direction = constrain(direction, 0, 100);

  if (dist > deceleration_distance) {
    simulated_speed += acceleration * loop_interval;
    if (simulated_speed > max_simulated_speed) simulated_speed = max_simulated_speed;
  } else {
    simulated_speed -= acceleration * loop_interval;
    if (simulated_speed < 0.2) simulated_speed = 0.0;
  }

  int speed = map((int)(simulated_speed * 100), 0, (int)(max_simulated_speed * 100), 0, 100);
  speed = constrain(speed, 0, 100);

  Serial.println("Navigation Info:");
  Serial.print("Target "); Serial.println(current_target_index + 1);
  Serial.print("Lat: "); Serial.print(lat, 6); Serial.print(" | Lon: "); Serial.println(lon, 6);
  Serial.print("Dist: "); Serial.print(dist); Serial.print(" m | Bearing: "); Serial.println(brng);
  Serial.print("Offset: "); Serial.print(offset); Serial.print(" | Heading: "); Serial.println(heading);
  Serial.print("Speed: "); Serial.print(speed); Serial.print(" | Dir: "); Serial.println(direction);

  send_packet(speed, direction);

  if (dist <= 4.0) {
    Serial.println("Reached target. Moving to next.");
    current_target_index++;
    if (current_target_index >= POINT_COUNT) {
      current_target_index = 0;
    }
  }
}

// === 模擬導航 ===
void simulate_navigation() {
  compute_and_send(simulated_lat, simulated_lon, simulated_heading);
}

// === 處理實際封包 ===
void parse_real_packet() {
  const int PACKET_LEN = 31;
  const byte EXPECTED_HEADER = 0x1B;
  const byte EXPECTED_COMMAND = 0x04;

  while (Serial.available() >= PACKET_LEN) {
    if (Serial.peek() != EXPECTED_HEADER) {
      Serial.read();
      continue;
    }

    byte buf[PACKET_LEN];
    Serial.readBytes(buf, PACKET_LEN);

    if (buf[1] != EXPECTED_COMMAND) {
      Serial.println("Invalid command byte");
      continue;
    }

    byte expected_bcc = calculate_bcc(buf, PACKET_LEN - 1);
    byte received_bcc = buf[PACKET_LEN - 1];
    if (expected_bcc != received_bcc) {
      Serial.println("BCC check failed");
      continue;
    }

    gps_lat = ((unsigned long)buf[5] << 16 | buf[6] << 8 | buf[7]) / 10000.0;
    gps_lon = ((unsigned long)buf[9] << 16 | buf[10] << 8 | buf[11]) / 10000.0;
    int16_t yaw_raw = (buf[23] << 8) | buf[24];
    imu_heading = yaw_raw / 1000.0;

    Serial.println("Parsed real GPS/IMU packet");
    compute_and_send(gps_lat, gps_lon, imu_heading);
  }
}

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("System started");
}

void loop() {
  if (use_simulation) {
    float target_lat = target_lat_list[current_target_index];
    float target_lon = target_lon_list[current_target_index];

    float dist = haversine(simulated_lat, simulated_lon, target_lat, target_lon);
    float brng = bearing(simulated_lat, simulated_lon, target_lat, target_lon);

    if (dist > 0.5) {
      float move_distance = simulated_speed * loop_interval;
      if (move_distance > dist) move_distance = dist;

      float delta_lat = move_distance * cos(radians(brng)) / 111320.0;
      float delta_lon = move_distance * sin(radians(brng)) / (111320.0 * cos(radians(simulated_lat)));

      simulated_lat += delta_lat;
      simulated_lon += delta_lon;

      Serial.print("Simulating move: ");
      Serial.print(dist); Serial.println(" m left");
    } else {
      Serial.println("Sim target reached");
    }

    simulate_navigation();
  } else {
    parse_real_packet();
  }

  delay(500);
}
