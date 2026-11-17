# 互動離線地圖實作計畫

> **執行方式：** 使用 `superpowers:executing-plans`，逐項完成並驗證本計畫。

**目標：** 將單一標記的 OSM iframe 改為 Leaflet + OpenStreetMap 標準街道圖，同時顯示當日所有已定位景點與明確標示為行程順序的連線；只有使用者提供的五張參考圖可離線查看。

**架構：** 保留靜態單頁網站與現有 `mapDays` 資料。使用本機 Leaflet 1.9.4 搭配 OSM 標準街道圖，呈現縮放／平移、編號標記，以及串接已核實座標的行程順序線；保留完整景點清單與各景點 Google Maps 導航。Service Worker 只攔截五個原始圖片 URL，初次連線快取其不透明回應，離線時使用相同 URL 回放。

**技術：** 原生 HTML/CSS/JavaScript、Leaflet 1.9.4、OpenStreetMap raster tiles、Service Worker Cache API、Python `unittest`。

**規格來源：** 2026-11-13 對話中的使用者需求。

## 裁定
- 本機 PowerShell 與 curl 下載五個圖源皆被網路代理重置，無法將原始二進位檔提交到 repo。瀏覽器實測又發現，把不透明跨網域回應經同源別名回傳時圖片無法解碼。因此保留原始外站 `img src`，讓 Service Worker 僅攔截五個指定外站圖片 URL，並以同一外站 URL 做 Network-First／快取回退。圖片本體不會成為 repo 內的實體檔案；每台裝置需先成功連線載入或安裝快取。
- Leaflet 作為本機應用程式資產快取；OSM 標準瓦片維持線上、不預抓或離線快取。離線時互動底圖不顯示，景點清單與已快取的五張參考圖仍可用。

## 全域限制
- 使用 OpenStreetMap 標準街道圖，不使用地形圖磚。
- 一次顯示所選日期的所有景點；只替已核實座標的景點編號及連線。
- 清楚標示連線只代表停留順序，不是實際道路或步道。
- 所有景點都保留 Google Maps 導航，包括尚未核實座標的景點。
- 只有五張指定外部參考圖加入離線快取；不快取地圖圖磚。
- 不修改 `sunrise-status.json`。
- 保留既有靜態網站結構，不新增建置系統。

## 審查重點
- 缺少座標時不得自行推測；景點仍顯示在清單中，但不放標記，也不納入路線線段。
- 切換日期時，先清除前一日圖層，再繪製所選日期的標記與順序線。
- 離線時五張已快取參考圖仍可查看，並清楚說明線上底圖需要網路。
- Service Worker 快取 Leaflet 本機靜態檔與五張指定參考圖，不快取 OSM 瓦片。
- 保留 OpenStreetMap 署名，且不可將順序線描述成已核實路徑。

## 檔案範圍
- 修改 `index.html`：以 Leaflet 地圖容器取代單點地圖；加入圖層清除／繪製、路線圖例。
- 修改 `index.html`：五張圖保留原始外站 `src`、原圖連結與來源署名。
- 新增 `vendor/leaflet/leaflet.js`、`vendor/leaflet/leaflet.css`、`vendor/leaflet/LICENSE` 與 CSS 使用的控制項圖示；版本固定為 1.9.4。
- 修改 `sw.js`：快取 Leaflet 本機檔案；只攔截五個指定外站圖片 URL，安裝時嘗試快取五張圖，圖片請求採 Network-First、失敗時以同一 URL 回退快取，並將快取版號升至 v23。
- 修改 `tools/test_ui_structure.py`：擴充既有地圖／圖庫測試，檢查 CARTO、所有有座標的標記與路線、圖片來源 allowlist 及 Service Worker 快取行為。

## 工作項目

### 工作 1：新增失敗的回歸測試
- 驗證地圖使用 OSM 標準街道圖與正確署名、顯示編號景點和行程順序線，且不再包含舊的 OSM export iframe。
- 驗證五張圖片保留原始來源 URL、具有替代文字與來源署名，且 Service Worker 只攔截這五個指定 URL。
- 執行 `python -m unittest discover -s tools -p test_ui_structure.py`，確認新檢查會在現況下失敗。

### 工作 2：準備地圖資產
- 從 Leaflet 1.9.4 npm 封存複製正式 JS、CSS、授權及 CSS 引用的圖示至 `vendor/leaflet/`，不加入建置系統。
- 在 `sw.js` 建立五個使用者提供圖片 URL 的 allowlist，不修改 `sunrise-status.json`。
- 只快取這五張參考圖；來源下載失敗時不得使 Service Worker 安裝失敗。

### 工作 3：實作全景點 Leaflet 地圖
- 載入本機 Leaflet 1.9.4，使用 OSM 官方標準 URL `https://tile.openstreetmap.org/{z}/{x}/{y}.png`，清楚顯示 OpenStreetMap attribution。
- 切換日期時清除舊圖層；為有效座標建立編號標記、縮放至當日標記範圍，並依行程順序繪製連線。
- 保留完整景點清單與 Google Maps 連結；說明未定位景點不會有標記，連線不是實際道路／步道。
- 保留五張圖庫圖片的原始外站 `src`／連結、圖說、來源、替代文字、尺寸與延遲載入設定。

### 工作 4：快取地圖程式與指定圖片
- 安裝時以 `no-cors` 請求五個來源，將不透明回應存入原始外站 URL 快取鍵；每個下載失敗都需獨立處理。
- 對 allowlist 外站 URL 採 Network-First，網路失敗時以同一 URL 回傳已快取回應；並把 `CACHE_NAME` 升至 v23。
- Leaflet 本機靜態檔列為應用程式資產快取；不得預抓或快取 OSM 瓦片。

### 工作 5：驗證完整體驗
- 執行完整 Python 測試、`node --check sw.js`、編輯器診斷，以及針對修改檔案的 `git diff --check`。
- 使用瀏覽器確認每一天會呈現預期數量的有座標標記與一條順序線、景點清單仍可操作、五張圖片載入成功，且 320／375／1280px 版面沒有水平溢出。
- 驗證每張圖在初次連網後會進入 Service Worker 快取；離線重新載入可顯示已快取圖庫，線上底圖則明確顯示需要網路。
