void setup() {
  Serial.begin(9600);
}

void loop() {
  while (Serial.available() > 0) {
    byte incomingByte = Serial.read();

    Serial.print("0x");
    if (incomingByte < 0x10) Serial.print("0");
    Serial.print(incomingByte, HEX);
    Serial.print(" ");

    if (incomingByte == 0x6E) {
      Serial.println();  // 當遇到封包結尾字元時換行
    }
  }
}
                                          