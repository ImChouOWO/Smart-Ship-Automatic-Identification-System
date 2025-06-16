void setup() {
  Serial.begin(9600);  // 開啟 Serial 通訊
}

void loop() {
  Serial.println("Hello from Arduino");
  delay(1000); // 每秒傳送一次
}
