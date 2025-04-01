import cv2

# 設定擷取卡設備編號（通常是 0 或 1，可自行調整）
device_index = 0

# 嘗試開啟擷取卡
cap = cv2.VideoCapture(device_index)

# 設定影像解析度（可選）
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("無法開啟擷取卡")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("讀取畫面失敗")
        break

    # 顯示畫面
    cv2.imshow('HDMI Capture', frame)

    # 按下 q 離開
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
