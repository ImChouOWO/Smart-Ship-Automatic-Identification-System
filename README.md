以下是完整的中英對照文檔和可複製的程式碼：

---

# 船舶AIS監控系統文檔 (Ship AIS Monitoring System Documentation)

## 簡介 (Introduction)
**船舶AIS監控系統**是一個實時應用，用於監控和分析船舶數據，包括GPS位置、IMU數據、5G信號強度和即時攝影畫面。該應用還集成了動態地圖功能，以可視化顯示船舶的當前位置。

---
##相關依賴(Nessary dependencies)

1.Node.js
2.npm

React module

[UI model mui](https://mui.com/material-ui/)
[Map model leaflet](https://react-leaflet.js.org/)
```bash
npm install @mui/material @emotion/react @emotion/styled
```
```bash
npm  install react@rc react-dom@rc leaflet
```
---
## 功能 (Features)
1. **實時攝影機畫面 (Real-time Camera Feed)**
   - 顯示船舶的即時攝影畫面。
   - 在示例中模擬為佔位圖像。

2. **GPS位置顯示 (GPS Location Display)**
   - 顯示船舶的當前緯度、經度和速度。

3. **IMU數據監控 (IMU Data Monitoring)**
   - 顯示船舶的滾轉角(Roll)、俯仰角(Pitch)和偏航角(Yaw)。

4. **5G信號強度指示 (5G Signal Strength Indicator)**
   - 以百分比形式顯示當前5G信號強度。
   - 包括一個進度條以進行可視化展示。

5. **地圖集成 (Map Integration)**
   - 使用交互式地圖顯示船舶的實時位置。
   - 在地圖上添加標記和彈出窗口顯示詳細位置信息。

---

## 技術棧 (Tech Stack)

### 前端框架與庫 (Frontend Frameworks and Libraries)
1. **React.js**
   - 核心框架，用於構建用戶界面。
   - 基於組件的架構實現可重用性和可擴展性。

2. **Material-UI (MUI)**
   - 提供預設設計的UI組件，例如`Card`、`Typography`和`LinearProgress`，用於現代化響應式設計。

3. **Lucide-React**
   - 圖標庫，用於添加與船舶相關的圖標，例如`Webcam`、`Compass`和`Navigation`。

4. **React-Leaflet**
   - 用於在React中集成交互式地圖的輕量級庫。
   - 顯示船舶位置，並添加標記和彈出窗口。

5. **Leaflet**
   - 一個JavaScript庫，用於渲染交互式地圖。

---

### 展示（Demo）

![demo](https://github.com/ImChouOWO/Smart-Ship-Automatic-Identification-System/blob/main/img/AIS.png)



