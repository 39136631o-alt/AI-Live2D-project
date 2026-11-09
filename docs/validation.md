# 銀鈴第一個可運行版本：驗證紀錄

使用目前已發布並恢復正常的雲端環境。保留既有圖片處理程式、範例與測試，新增角色素材和 Web runtime；沒有發布、推送或部署公開預覽。

## 本次實際執行

| 檢查 | 結果 |
| --- | --- |
| `.venv/bin/python tools/build_character.py` | 產生 27 個 SVG + 27 個透明 PNG、母版 SVG/PNG、manifest |
| `.venv/bin/python -m pytest -q` | **21 passed**：既有 14 項 + 新素材 3 項 + 真實瀏覽器 4 項 |
| `node --test tests/browser/runtime.test.mjs` | **3 passed**，0 failed / skipped |
| `.venv/bin/python -m pip check` | No broken requirements found |
| `git diff --check` | 通過 |
| HTTP 靜態預覽 | 在雲端內部 8000 埠啟動並實際載入素材與 runtime |

Python 素材測試驗證：必要部件、透明度、共享畫布、SHA-256、母版／分層合成的反鋸齒誤差、SVG ID 唯一、無外部影像依賴，以及重建輸出的可重現性。

Playwright 以系統 `/usr/bin/chromium` 真實執行：

- 桌面 1440×1100，載入全部部件，確認自動眨眼、頭髮／頭部 transform 隨時間變化、口型變化；暫停前後比較 SVG，恢復後再次確認變化。
- 手動眼睛 0、嘴巴 1、頭角 5、呼吸 1、頭髮 -4，檢查可見 SVG 節點與自動 channel 停用；驚訝、重設正常。
- 390×844、2 倍像素比、觸控模式，確認沒有橫向捲動；點擊角色、鍵盤 Enter、招呼文字、表情與重設正常。
- `prefers-reduced-motion` 預設關閉呼吸／頭擺／髮動；404 模擬後呈現明確載入錯誤且停用控制。
- 正常路徑沒有捕捉到 JavaScript pageerror。

本次截圖與交付封裝（忽略於 Git 的產出目錄，可重新生成）：

- `outputs/desktop-preview.png`：完整桌面頁。
- `outputs/mobile-preview.png`：390px 寬觸控模擬完整頁。
- `outputs/happy-preview.png`：微笑表情。
- `outputs/silverbell-preview.zip`：成品 `web/` 與整合說明；不含虛擬環境和外部 SDK。

## Safari / 官方資料存取限制

實際嘗試安裝 WebKit：

```bash
PLAYWRIGHT_BROWSERS_PATH=/workspace/.browser-cache .venv/bin/python -m playwright install webkit
```

`cdn.playwright.dev` 及 `playwright.download.prss.microsoft.com` 的下載被代理回覆 `403 Domain forbidden`。未停用 TLS、未繞過網路政策，也未把 Chromium iPhone 尺寸模擬稱為 Safari 驗證。允許目的地並安裝成功後，可執行：

```bash
PLAYWRIGHT_BROWSERS_PATH=/workspace/.browser-cache CHARACTER_BROWSER=webkit \
  .venv/bin/python -m pytest tests/browser/test_preview.py -q
```

系統若缺少 WebKit 的原生依賴，還需安裝對應套件。即使 Linux WebKit 通過，仍需在實際 iPhone Safari 檢查觸控、背景切換、耗電與長時間動畫。這些尚未驗證。

官方 docs.live2d.com 的重新請求仍遭 CONNECT 403。官方 GitHub Framework README 可讀，並明確描述 SDK 載入 Editor 輸出模型；本次沒有發現可在此環境直接編譯 `.moc3` 的官方介面。不產出假模型，也不包含官方 Core。

## 尚未完成

- 附件精緻立繪品質、完全相同的剪裁／蕾絲／花飾與比例；目前是參考導向的程式簡化重繪。
- 真正的頭部轉面、連續網格變形、ArtMesh、肢體 IK、大幅動作與碰撞。
- 音訊／語音驅動口型、表情 atlas、Unity/Godot 原生 runtime。
- 自動從附件拆層、AI 遮擋補全、PSD 匯出、Cubism Editor 編輯專案與 `.moc3`。
- Safari 實機驗證及公開可存取預覽；後者需先取得使用者同意。


## 2026-11-09：僅用 iPhone 的預覽與提交準備

- 確認 Cloud 環境 running / connected；所有 27 個圖層及原有程式保留，本輪沒有修改角色素材或動畫 runtime。
- 發現 remote_desktop enabled / state unknown，但目前沒有可呼叫的 desktop JS、open_in_codex、分享預覽或 port-forwarding 工具；未能提供經驗證的 iPhone Safari Cloud 連結。
- 新增只接受手動 dispatch 的 GitHub Pages workflow、純靜態標記及手機部署指南。沒有 push 自動部署事件，沒有執行 Actions、變更 GitHub 設定或公開站點。
- 新增專案子目錄的瀏覽器測試：同時驗證素材載入、呼吸 transform、自動眨眼、口型、觸控招呼與窄畫面；合計 **22 項 Python 測試通過（0 skipped）及 3 項 JavaScript 測試通過**。
- workflow YAML 使用可用的 YAML parser 檢查語法及手動觸發設定；尚未在 GitHub Actions 上執行，因此沒有宣稱部署成功。
- 程式碼整理及暫存完成；尚未建立 commit、推送或公開部署，等待使用者確認。部署操作步驟見 `docs/mobile-preview.md`。
