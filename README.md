# 阿里山慢旅

GitHub Pages 靜態網站專案。網站內容位於 `index.html`，不需要安裝套件或執行建置程序。

## 發布到 GitHub Pages

1. 將本資料夾內容推送到 GitHub repository 的 `main` 分支。
2. 在 repository 開啟 **Settings → Pages**。
3. 在 **Build and deployment** 選擇 **Deploy from a branch**，分支選 `main`、資料夾選 `/(root)`，再按 **Save**。
4. 等待部署完成，從 Pages 設定頁開啟網站網址。

個人帳號若要從私人 repository 發布 GitHub Pages，需要 GitHub Pro。repository 可以保持私人，但發布的網站是公開的，任何知道網址的人都能瀏覽。免費個人方案可改用公開 repository 發布。

## 主畫面與離線使用

- 將整個專案（包含 manifest、Service Worker 與 PNG 圖示）一起部署至 HTTPS GitHub Pages。
- 第一次需連網開啟，等待頁尾顯示「行程與清單已可離線查看」。
- Android Chrome：使用瀏覽器的安裝選項，或頁尾出現的「加入主畫面」。瀏覽器不保證每次都會出現自動安裝提示。
- iOS Safari：分享 → 加入主畫面；建議在主畫面 App 內先連網開啟一次，確認離線資料準備完成。
- 行程、時刻表、住宿資訊與清單可離線使用；Google Maps、官方網站、LINE 分帳與最新天氣仍需網路。離線時不會顯示過期天氣為即時數據。
- 清單存在各裝置／瀏覽器自己的儲存空間，不會跨裝置同步。清除網站資料或系統回收儲存空間可能移除快取與清單。
- 修改離線素材時，同步遞增 `sw.js` 的 `CACHE_NAME` 版本尾碼（例如 v1 → v2）。有新版時，頁尾會提供「更新離線版本」；只刪除此專案舊快取，不會刪除其他網站快取或 localStorage。
- 本機 `file://` 不能註冊 Service Worker。可用 `py -m http.server 8000`，從 `http://localhost:8000/` 測試。
