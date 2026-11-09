# AI 輔助 Live2D 製作管線 — 第一階段

這是 Linux/Python 圖片前處理原型，目標是逐步建立有來源紀錄、可人工審核的 AI 輔助製作流程。**目前不包含 AI 分割、遮擋補全、網格綁定、動作或物理模擬，也不產生 `.cmo3` / `.moc3`。** Cubism 格式、SDK 授權與未核實事項見 [調查文件](cubism-research.md)。

## 安裝與執行

Python 3.10+（本次驗證使用 3.12）。無 GPU、API key 或 Cubism SDK 需求。

```bash
cd /workspace/AI-Live2D-project
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .
.venv/bin/python -m pytest -q

# 原創幾何圖，無外部角色素材；輸出目錄必須不存在
.venv/bin/python examples/generate_demo.py outputs/demo
.venv/bin/live2d-pipeline inspect outputs/demo/character.png
.venv/bin/live2d-pipeline layers outputs/demo/character.png outputs/demo/layers.json outputs/result
```

實際素材須自行確認角色圖片、遮罩與衍生處理的使用權。`rights_confirmed: true` 是使用者聲明，程式不能驗證著作權。圖片不會上傳到外部服務。

## 輸入規格

圖片會依 EXIF 旋轉並轉成 RGBA；不自動去背。每張上限 1,600 萬像素，不接受動畫。遮罩必須是單張、8-bit 灰階 `L`，尺寸等於**方向正規化後**的來源。0 排除、255 保留，中間值乘上來源 alpha。彩色或 RGBA 遮罩直接拒絕，避免誤讀。

`layers.json` 範例（路徑相對於 JSON 所在位置）：

```json
{
  "schema_version": 1,
  "rights_confirmed": true,
  "layers": [
    {"name": "PartBody", "mask": "body-mask.png"},
    {"name": "PartHead", "mask": "head-mask.png"}
  ]
}
```

順序為由下至上。名稱限英文字母起頭的英數底線、最多 64 字元，不分大小寫唯一；不推測語意名稱。遮罩路徑是使用者信任的本機輸入，此 CLI 不是不可信上傳服務的安全隔離層。

## 產出

| 檔案 | 說明 |
| --- | --- |
| `layers/000_PartBody.png` 等 | 與來源畫布等大的 RGBA 圖層，保留位置與來源 alpha |
| `preview.png` | 由下至上 alpha 合成的靜態預覽，非 Live2D 動態預覽 |
| `uncovered.png` | 來源 alpha 減各圖層 alpha 最大值的診斷遮罩；不是隱藏區域或補全結果 |
| `manifest.json` | 自有版本化中介格式，包含來源/遮罩 SHA-256、尺寸、名稱、順序、像素 bbox 與限制 |

bbox 使用 Pillow 的右、下不包含界線座標。輸出目錄若已存在會拒絕覆寫。無效輸入回傳 exit code 2。磁碟寫入失敗可能留下部分輸出，請檢查後使用新的目錄重試。

互不重疊的二元遮罩可重建原始可見畫面；重疊遮罩會重複合成，柔邊遮罩也可能改變透明度。未覆蓋、隱藏與畫面外區域不會憑空補畫。灰階遮罩、圖層順序與拆分品質需要人工檢查。

## 開發與後續階段

- `src/live2d_pipeline/`：圖片檢查、遮罩拆層、CLI。
- `tests/`：像素級重建、透明度、錯誤輸入、來源紀錄與 CLI 測試。
- `examples/`：自行生成的幾何示例，不含第三方角色資產。
- 後續：可替換的 AI 分割/補全模組 → 網格與變形中介格式 → 表情/動作/物理規劃及預覽 → 人工 Editor 交接與官方 SDK 驗證。詳見調查文件。

依賴使用固定版本；尚未建立含雜湊的完整跨平台 lockfile。本專案未指定程式碼散布授權，發佈前應由擁有人選定；依賴與未來模型權重仍受各自授權約束。
