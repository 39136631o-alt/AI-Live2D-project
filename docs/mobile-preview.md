# 只用 iPhone 預覽角色

## 現在的狀態

角色網站是完整靜態成品，位於 `web/`；沒有後端、套件建置或外部 API 需求。Cloud 內部能啟動並以瀏覽器測試，但目前這個對話提供的工具沒有可分享的 preview URL、port forwarding 或 `open_in_codex` / 桌面控制工具。環境宣告 remote_desktop enabled、state unknown；宣告支援不代表已有可開啟的桌面或 Safari 連結。

因此目前**沒有已驗證能從 iPhone Safari 直接開啟的 Cloud 預覽網址**。手機上的 localhost 指向手機本身，不能指向 Cloud。下載 ZIP 或 GitHub 原始碼頁也不是可互動的網站預覽。本文件不要求你另找電腦執行 Python。

沒有開啟臨時公開 tunnel，也沒有部署任何公共網站。

## 已準備：GitHub Pages，僅手動發布

`.github/workflows/pages.yml` 只接受 `workflow_dispatch`，沒有 `push` 或 PR 自動部署事件。只有 default branch 可執行部署，僅 `web/` 會進入 Pages artifact；測試、Python 原始碼、虛擬環境與參考附件都不會上站。角色和素材會公開可見，發布前應先確認接受這點。

使用者已確認保存此版本並授權 commit / push。**推送同意與公開部署同意分開**；本輪不啟用 Pages、不執行公開部署。實際提交結果以 GitHub 的分支與 commit 紀錄為準。

同意並完成推送、審查及合併至預設分支後，可完全在 iPhone Safari 操作：

1. 開啟 GitHub 儲存庫，登入有設定及部署權限的帳號。如果手機版看不到設定／Actions 控制，使用 Safari「要求桌面網站」。
2. 在儲存庫 **Settings → Pages → Build and deployment → Source** 選 **GitHub Actions**。能否啟用取決於儲存庫可見性、帳號方案、組織政策及權限；不需要把原始碼改成公開來繞過限制。
3. 確認要公開此角色預覽後，到 **Actions → Deploy character preview to GitHub Pages (manual) → Run workflow**，選預設分支。這一步會真正發布網站，不應在未同意公開時點擊。
4. 如果 `github-pages` environment 設有審核，完成部署核准。等待 build 與 deploy 都成功。
5. 開啟部署工作回傳的 `page_url` 或 Settings → Pages 的 **Visit site**，即可在 iPhone Safari 直接預覽。不需在手機執行 Python。

預期專案網址格式為 `https://39136631o-alt.github.io/AI-Live2D-project/`，**這只是預期格式，尚未部署，不是目前可用的連結**；請以 GitHub 實際回傳 URL 為準。

## 相容性與手機驗收

CSS、ES modules、SVG、manifest 及圖層都使用相對路徑，已加入 `/AI-Live2D-project/` 子目錄的真實瀏覽器測試，避免部署到 Pages 後資源 404。`web/.nojekyll` 明確標示純靜態網站。

目前確認 Chromium 觸控模擬可眨眼、開口、呼吸、擺頭、擺髮及點擊招呼。iPhone Safari 實機尚未驗證；Linux WebKit 下載仍受環境網路政策限制。發布後請在 Safari 檢查：

- 角色載入，27 個圖層顯示完整，無橫向溢出。
- 眨眼自動發生；打開「說話口型」後嘴巴開合（預設關閉）。
- 呼吸與頭／髮微擺；手機若開啟「減少動態效果」，這三項預設關閉，可以手動開啟。
- 觸控角色出現招呼及微笑；滑桿、暫停、繼續、重設正常。

若網站 404：先檢查 workflow 是否真正執行成功、分支是否為 default branch、Pages source 是否為 Actions、環境是否等待審核。這些是 GitHub 設定或發布狀態，不應以反覆改動角色素材解決。
