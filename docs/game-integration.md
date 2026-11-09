# 遊戲接入與素材交接

## Web 遊戲：不需要展示頁 UI

將 `web/character.mjs` 和 `web/assets/character/` 一起放入遊戲的同來源靜態資源。SVG 與 manifest 必須保持相同版本。下列範例在瀏覽器 ES module 中執行；只載入專案信任的 SVG，不接受任意外部 SVG 上傳。

```js
import {LayeredCharacter} from './character.mjs';

const [art, metadata] = await Promise.all([
  fetch('./assets/character/character.svg'),
  fetch('./assets/character/manifest.json'),
]);
if (!art.ok || !metadata.ok) throw new Error('Character asset unavailable');
const documentSVG = new DOMParser().parseFromString(await art.text(), 'image/svg+xml');
const svg = document.importNode(documentSVG.documentElement, true);
document.querySelector('#actor').append(svg);
const actor = new LayeredCharacter(svg, await metadata.json(), {
  reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
});
actor.setOptions({talk:false});
actor.setExpression('neutral');

// 遊戲對話系統提供 0..1 的口型值；若使用音量，需另做平滑與門檻。
actor.setParameter('mouthOpen', 0.65);
actor.setParameter('headAngle', 2);
// 若需要完全手控，先停止對應自動 channel：
actor.setOptions({blink:false, breathe:false, sway:false, hair:false});
actor.setParameter('eyeOpen', 0.2);
actor.setParameter('hairSway', -1.5);
actor.triggerReaction();
actor.addEventListener('interaction', event => console.log(event.detail.type));
// 畫面離開／關卡銷毀時：
actor.dispose();
```

容器要設定尺寸，SVG 建議 `width:100%;height:100%;object-fit:contain`。runtime 不接管輸入事件；遊戲自行把觸控、點擊或鍵盤綁到 `triggerReaction()`。網站展示頁 `app.mjs` 提供完整範例。`window.character` 只為該展示頁的整合除錯入口，不是其他遊戲必須依賴的全域。

API：

| 方法 | 效果 |
| --- | --- |
| `setParameter(name, number)` | 設定手動參數；超出範圍會 clamp，未知名稱／NaN 拋錯 |
| `setOptions({blink,talk,breathe,sway,hair})` | 各值為 boolean；開啟的自動 channel 會覆蓋對應手動值（頭角、髮擺作為偏移） |
| `setExpression('neutral'/'happy'/'surprised')` | 表情會覆蓋部分眼嘴表現 |
| `setLook(-1..1)` | 左右微幅注視，映射頭角，非真實側面轉頭 |
| `triggerReaction()` | 2.4 秒微笑／手臂輕擺並發出 `interaction` 事件；事件詳情為 `{type:'greeting'}` |
| `setPaused(boolean)` | 暫停／恢復動畫；暫停時 API 仍可設定靜態姿勢 |
| `reset()` | 重設時間、姿勢、表情；保留自動選項與暫停狀態，展示頁另行重設它們 |
| `dispose()` | 取消 RAF 與 visibility listener；終止該實例 |

參數：`eyeOpen` / `mouthOpen` / `breath` 是 0..1，`headAngle` 是 -5..5 度，`hairSway` 是 -4..4 度。頭部 pivot 為 (300,218)，呼吸基點為 (300,449)，各髮束與手臂另有 pivot。所有素材使用 600×1100 左上原點座標；SVG runtime 使用明確數字 transform，不依賴 Safari 的 CSS transform-origin 解讀。

髮絲是固定 stiffness / damping 的阻尼彈簧近似，不是碰撞解算器。視窗隱藏後停止 RAF，回來會重設時間步，單步最多 50ms，避免積分爆炸。只有微小轉動適用這些補圖，大幅動作會露出紙片接縫。

## Unity / Godot / 原生引擎

最快接入方式是以合適的 WebView 載入這套靜態頁並透過遊戲端橋接 API；WebView 插件及其授權由整合方選定，本專案未附帶。若不使用 WebView，將 27 張 PNG 當透明 sprite、依 `order` 排序，按照 manifest 的 pivot 及 runtime 的參數公式自行建立場景階層。PNG 共用完整畫布；若引擎會裁切透明區，必須保留 trim offset，不能直接把裁切後中心當 pivot。左右眼開閉、嘴形還需要由 SVG 子節點另行輸出或使用引擎遮罩；目前 PNG 是中性靜態圖層，未附完整表情 sprite atlas。沒有提供或驗證 Unity/Godot 原生插件。

## 日後轉換 Cubism

保留 SVG 母版、RGBA PNG、完整遮擋底圖、manifest 名稱／順序／pivot 及參數範圍。這些是可交給美術與綁定師的素材，**不是可直接匯入的 Cubism 模型**。預計流程：在授權合適的影像工具整理符合當期 Editor 要求的 PSD → Cubism Editor 建立 ArtMesh、變形器、參數鍵形、裁切與物理 → 由官方支援的匯出流程產生 `.moc3` 及附屬資料 → 以適用授權的 SDK 測試。現有 SVG transform 與彈簧設定不能無損轉成 Cubism rig。

本專案未打包任何官方 Core、官方角色素材或第三方模型權重。新增程式及向量路徑由本專案製作，外觀依使用者提供的設計參考；正式商用前仍需由素材提供者確認設計權利與選定專案散布授權。
