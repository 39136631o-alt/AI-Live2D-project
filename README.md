# 銀鈴 Silverbell · 可互動的全身 2D 測試角色

目前交付重點是**一名可運行的遊戲測試角色**，不是通用自動建模工具。依使用者提供的設計板，以程式繪製簡化向量角色，保留銀白長髮、紫色眼睛、左側花飾緞帶、白紫黑幻想服裝、露肩袖、黑色束腰、非對稱裙擺與長襪。

**這是 2D 分層動畫原型，不是官方 Live2D Cubism 模型，也不是高品質 AI 立繪。** 沒有生成 `.cmo3` / `.moc3`。原有圖片檢查、遮罩拆層及其 14 項測試完整保留；使用方式見 [原始圖片處理文件](docs/image-pipeline.md)。

## iPhone 直接預覽與 GitHub Pages

只有 iPhone、不方便執行伺服器時，請看 [手機預覽與手動部署指南](docs/mobile-preview.md)。目前 Cloud 工具沒有可提供的 Safari 預覽連結；已準備 `.github/workflows/pages.yml`，推送不會觸發部署，需另外手動啟動 GitHub Pages。**程式碼推送不會啟用 Pages；目前未公開部署，也沒有可宣稱已上線的網址。**

## 立即預覽

成品已包含所有素材，**預覽不需要安裝 Python 依賴、Node 套件、GPU、SDK 或 API key**；只需任一靜態 HTTP 伺服器。使用 Python：

```bash
cd /workspace/AI-Live2D-project
python -m http.server 8000 --bind 0.0.0.0 --directory web
```

在執行伺服器的電腦瀏覽器開啟本機的 8000 埠。不要以 `file://` 直接開 HTML，ES module 與素材 fetch 需要 HTTP。

手機預覽：將 `web/` 複製到自己的電腦，執行上述伺服器（將路徑調整至專案），iPhone 與電腦連相同 Wi-Fi，再於 Safari 輸入 `http://<電腦區域網路IP>:8000`。只綁定自己信任的網路。雲端內部埠不會自動成為手機可存取的網址；本次**未公開部署或發布新環境版本**。若要公開預覽，須另行取得使用者同意。

頁面功能：

- 自動眨眼、說話口型、呼吸、頭部微擺、髮束的阻尼彈簧擺動。
- 眼睛、嘴巴、頭角、呼吸、頭髮五個手動參數；拖動即停用相應自動項目。
- 平靜 / 微笑 / 驚訝，點擊或觸控角色打招呼，支援鍵盤 Enter / Space。
- 暫停、繼續、重設；背景分頁暫停 requestAnimationFrame，尊重系統減少動態偏好。

## 實際檔案

| 路徑 | 內容 |
| --- | --- |
| `web/index.html`、`style.css`、`app.mjs` | 響應式角色展示與控制面板 |
| `web/character.mjs` | 獨立 SVG 分層動畫 runtime，無第三方前端依賴 |
| `web/assets/character/character.svg` / `.png` | 完整正面全身立繪，透明背景、600×1100 |
| `web/assets/character/layers/` | **27 層**獨立 SVG 與 RGBA PNG；同畫布、可重新合成 |
| `web/assets/character/manifest.json` | 部件順序、ID、名稱、pivot、rig 分組、SHA-256 與參數範圍 |
| `tools/build_character.py` | 原創路徑繪圖與素材重建程式，隱藏區域以完整底圖補畫 |
| `docs/game-integration.md` | 遊戲接入 API、生命週期與 Cubism 交接說明 |
| `docs/validation.md` | 本次測試證據、Safari 驗證限制與待完成內容 |

27 個部件包含：後髮底、左右後髮束、後裙、身體、左右腿、靴子、左右臂、左右袖、前裙、胸衣、頸飾、腰飾、臉、左右眼、左右眉、嘴、前髮、左右側髮及髮飾。左右命名以**畫面方向**為準；manifest 中文標籤另註明角色方向。

臉底、頸部、肩、軀幹、手臂連接與後髮都畫到遮擋區內，避免小幅動畫出現洞；沒有使用 AI 修補、外部角色貼圖、第三方模型權重或附件上的文字作為資產。這是參考導向的簡化重繪，不是附件逐像素拆層；花飾、蕾絲、服裝剪裁與比例仍有簡化，需後續美術審核。

## 開發與測試

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-preview.txt
.venv/bin/python -m pip install -e .
# 重建全部 SVG / PNG；覆寫產生的素材，不要在產出檔直接手改
.venv/bin/python tools/build_character.py
# Python + 圖層資料 + 真實 Chromium 預覽測試
.venv/bin/python -m pytest -q
# 無依賴的 JavaScript 參數測試
node --test tests/browser/runtime.test.mjs
```

`requirements.txt` 保留舊版圖片工具依賴；`requirements-preview.txt` 另外安裝 CairoSVG（重建 PNG，系統需有 libcairo）及 Playwright（瀏覽器驗證）。成品預覽不載入它們。

瀏覽器測試預設使用 `/usr/bin/chromium`；其他位置設 `CHROMIUM_PATH`。未安裝 Playwright 時 pytest 會明確跳過瀏覽器模組；不代表已驗證 UI。瀏覽器測試自行啟動並關閉內部 HTTP 服務。WebKit 測試指令與下載限制見驗證文件。

## 目前邊界

可用於 Web 遊戲中的待機角色、對話場景及互動演示；尚非生產級美術或完整遊戲角色控制器。沒有網格變形、真實頭部轉面、肢體 IK、物理碰撞、語音辨識／音訊同步、自動語意拆圖、PSD 匯出或 Cubism 編譯。說話動畫是週期口型，不是聲音驅動。設計上優先 iPhone Safari 的標準 SVG / ES module API，但目前只有 Chromium 桌面與觸控模擬通過；WebKit 下載遭網路政策阻擋，**尚未在實機 Safari 驗證**。

官方 SDK 的「載入 Editor 匯出模型」不等於能建立模型。已查證與尚待核實的格式／授權資訊見 [Cubism 調查](docs/cubism-research.md)。
