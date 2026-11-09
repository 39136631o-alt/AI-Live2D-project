# Cubism 相容性與自動化調查

調查日期：2026-11-07。以下區分已取得的官方證據與尚待直接核實的產品文件；不把格式名稱當成可用的編譯 API。

## 已取得的官方來源

- [Native Framework README](https://github.com/Live2D/CubismNativeFramework/blob/45de21229a9faab9675525bc59deddbe089b0e95/README.md)：SDK 用於在應用程式顯示、操作 **Editor 輸出的模型**；載入需搭配 Core。該儲存庫未包含 Core。
- [官方 LICENSE](https://github.com/Live2D/CubismNativeFramework/blob/45de21229a9faab9675525bc59deddbe089b0e95/LICENSE.md)：Components 使用 Live2D Open Software License，Core 使用 Proprietary Software License，不能把整套 SDK 視為一般寬鬆授權的開源依賴。文件並列出 business 使用者的 SDK Release License 要求與 1,000 萬日圓年營收門檻；正式散布前須讀當期完整條款及適用範圍，不由本專案代判資格。
- [官方模型設定讀取程式](https://github.com/Live2D/CubismNativeFramework/blob/45de21229a9faab9675525bc59deddbe089b0e95/src/CubismModelSettingJson.cpp)：讀取 `FileReferences` 內的 `Moc`、`Textures`、`Physics`、`Expressions`、`Motions` 等欄位。這是模型載入端，不是 Editor 專案產生器。
- [Native Samples](https://github.com/Live2D/CubismNativeSamples)：包含 OpenGL、Vulkan 等範例，仍要求另行取得 Core。這次未安裝 SDK、下載官方角色素材或驗證 SDK Linux ABI；本原型只有 Pillow，Linux 可直接運行。

## 格式與待核實事項

| 類別 | 用途與本專案邊界 |
| --- | --- |
| 分層 PSD | 預期作為 Cubism Editor 的美術素材匯入路徑；正式實作 PSD 匯出前，需直接核實官方對色彩模式、群組、混合模式、透明度與命名的限制。本階段只輸出 RGBA PNG 圖層，**不聲稱可直接整包匯入 Editor**。 |
| `.cmo3` | Editor 可編輯模型專案；未找到、也未驗證官方支援的外部寫入或 headless 編譯 API，不實作寫入。 |
| `.moc3` | SDK 使用的編譯模型資料；SDK 的模型載入能力不等於模型編譯能力，不能從 PNG 或 JSON 直接改副檔名取得。 |
| `.model3.json`、貼圖及 motion/expression/physics JSON | 執行時模型資產與參照資料；即使 JSON 可編輯，也不能取代有效的 compiled model、參數 ID 與 rig。原型 manifest 使用自有 schema，避免冒充這些格式。 |

下列官方網站的實際 HTTPS 請求都遭環境代理 `403 Forbidden`，因此本次**未能完成匯入格式、Editor 平台支援、完整 EULA 與自動化限制的直接核實**：

- https://docs.live2d.com/en/cubism-editor-manual/file-types/
- https://docs.live2d.com/en/cubism-editor-manual/psd/
- https://www.live2d.com/en/sdk/about/
- https://www.live2d.com/en/sdk/license/

需要在環境設定加入 `docs.live2d.com`、`www.live2d.com` 後重新查閱，並檢查重新導向的目的地主機。本階段不依賴上述存取。未取得證據前，不承諾官方 CLI、無頭 Editor、自動產生 `.cmo3` / `.moc3`、Linux 原生 Editor 或 SDK 再散布許可。

## 後續系統設計

1. 權利聲明、來源雜湊、人工檢查與 EXIF 方向正規化。
2. 本階段：外部灰階遮罩 → 安全部件名稱 → RGBA 圖層 → 預覽及稽核 manifest。
3. 後續 AI adapter：在模型權重和授權確認後加入提示式分割；記錄模型版本、提示與人工修正。遮擋補全必須另存生成區域遮罩及來源，不能當作原畫真實內容。
4. 後續中介資料：網格頂點/三角形、遮罩、座標系、變形器階層、參數範圍/關鍵形狀、表情與動作計畫、物理輸入輸出及預覽求解器。必須有拓樸與變形品質驗證，不能只以規則網格宣稱完成 rig。
5. 人工在授權的 Cubism Editor 完成匯入、綁定、調整及正式匯出；再使用相容 SDK 驗證。除非日後找到官方支援的自動化介面，這仍是必要交接步驟。

## 2026-11-08（台北時間）角色原型更新

本次重新請求官方文件站仍遭代理 CONNECT 403；上列已鎖定 commit 的 Framework README 可正常讀取，再次確認其用途是操作 Editor 匯出的模型。沒有新證據支持雲端 headless 編譯 `.moc3`，也未取得可再散布的 Core。本輪改以標準 SVG/JavaScript 製作可運行的分層動畫；不使用或仿冒 Cubism 檔案格式。PNG 與 SVG 可以保留作為將來人工整理素材與綁定的來源，但不承諾自動轉換。
