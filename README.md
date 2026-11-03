# 阿里山嘉義慢旅

GitHub Pages 靜態網站專案。網站內容位於 `index.html`，不需要安裝套件或執行建置程序。

## 發布到 GitHub Pages

1. 將本資料夾內容推送到 GitHub repository 的 `main` 分支。
2. 在 repository 開啟 **Settings → Pages**。
3. 在 **Build and deployment** 選擇 **Deploy from a branch**，分支選 `main`、資料夾選 `/(root)`，再按 **Save**。
4. 等待部署完成，從 Pages 設定頁開啟網站網址。

個人帳號若要從私人 repository 發布 GitHub Pages，需要 GitHub Pro。repository 可以保持私人，但發布的網站是公開的，任何知道網址的人都能瀏覽。免費個人方案可改用公開 repository 發布。

## 主畫面與離線使用

- 將整個專案（包含 manifest、Service Worker 與 PNG 圖示）一起部署至 HTTPS GitHub Pages。
- 第一次需連網開啟，讓瀏覽器完成離線資源快取。
- Android Chrome：使用瀏覽器的安裝選項，或頁尾出現的「加入主畫面」。瀏覽器不保證每次都會出現自動安裝提示。
- iOS Safari：分享 → 加入主畫面；建議在主畫面 App 內先連網開啟一次，確認離線資料準備完成。
- 行程、時刻表、住宿資訊與清單可離線使用；Google Maps、官方網站、LINE 分帳與最新天氣仍需網路。離線時不會顯示過期天氣為即時數據。
- 祝山線公告由 GitHub Actions 每日台灣時間約 16:45（UTC 08:45）自動讀取林鐵官方頁面。每次成功檢查都更新 `checkedAt`；只有公告日期或時刻改變時才更新 `updatedAt`。網站分開顯示兩個時間，超過 26 小時沒有成功檢查時會標示公告可能過期；離線時使用最近同步資料。每日成功檢查會更新 JSON 並由工作流程提交。若 repository 限制工作流程權限，請在 **Settings → Actions → General → Workflow permissions** 開啟 **Read and write permissions**。
- 為相容林鐵官方伺服器缺少 Subject Key Identifier 的憑證鏈，抓取器不啟用 OpenSSL 嚴格 X.509 格式檢查；受信任憑證鏈與主機名稱驗證仍保持啟用。
- 清單存在各裝置／瀏覽器自己的儲存空間，不會跨裝置同步。清除網站資料或系統回收儲存空間可能移除快取與清單。
- 修改離線素材時，同步遞增 `sw.js` 的 `CACHE_NAME` 版本尾碼。有新版時，頁尾會提供「更新離線版本」；只刪除此專案舊快取，不會刪除其他網站快取或 localStorage。
- 本機 `file://` 不能註冊 Service Worker。可用 `py -m http.server 8000`，從 `http://localhost:8000/` 測試。
