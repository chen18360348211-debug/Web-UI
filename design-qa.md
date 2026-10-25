# Figma PC 视觉核对

final result: passed

范围：黑五 PC端（541:1054），静态默认状态，14 个板块；仅 PC。

## 证据

- Figma 原始截图：`C:/Users/60922/.codex/visualizations/2026/10/23/01a16694-20ec-78d2-b0b1-f7ed35a17715/figma-original.png`
- 浏览器整页截图：`C:/Users/60922/.codex/visualizations/2026/10/23/01a16694-20ec-78d2-b0b1-f7ed35a17715/implementation-final-1920.png`
- 整页并排对照（左 Figma、右网页）：`C:/Users/60922/.codex/visualizations/2026/10/23/01a16694-20ec-78d2-b0b1-f7ed35a17715/comparison-final-overview.png`
- 同坐标局部并排对照：`C:/Users/60922/.codex/visualizations/2026/10/23/01a16694-20ec-78d2-b0b1-f7ed35a17715/comparison-final-details.png`
- 素材渲染几何记录：同目录 `asset-geometry.json`。
- Figma 原始坐标与网页坐标：同目录 `figma-geometry.json`、`dom-geometry.json`。
- 1440 PC 验证截图：同目录 `preview-1440.png`。

基准视口 1920 × 1080 CSS px；Figma 和网页整页输出均为 1920 × 10639 px。浏览器设备像素比为 1.5，截图 API 已输出 CSS 像素尺寸，无需再缩放。对照图两侧使用相同裁切区域和缩放倍率。另验证 1440 × 900，画布缩放至 1440 × 7979.25，无横向溢出。

## 核对结果

| 项目 | 结果 |
| --- | --- |
| 页面身份、完整内容、无空白或框架错误 | 通过 |
| 首屏、活动阶梯、主推套装、两组商品、抽奖、页脚 | 已逐段对照 |
| 字体 | Barlow 400/500/600/700、Jersey 10、Press Start 2P、Roboto 400/800 均本地化；全角冒号使用本地 Noto Sans SC 单字子集回退 |
| 间距与布局 | 707 个可比较可见图层的位置误差均小于 1 px，最大 x/y 差 0.867 px；旋转图层按最终包围盒核对 |
| 颜色、描边、渐变、透明度 | 依据图层原始属性核对；恢复套餐外框与选中框的渐变描边 |
| 图片与 SVG | 54 个原始素材非空；155 处引用均加载完成、有有效自然尺寸、渲染宽高非零，位置与裁切对照通过 |
| 按钮与 Tab | 使用 Figma 原始 SVG 和默认字体排版，未重绘或替换 |
| 文案 | 与设计稿一致，保留前导空格、全角货币符号、重复标签和静态数值 |
| Console | 无 error / warn |
| 静态页面浏览 | Ctrl+End 可抵达页脚，United States / English 可见；Ctrl+Home 回到首屏 |

## 修正记录

1. 初版发现倒计时透明文字上的 CSS text-shadow 遮盖渐变字面。改为字面外部发光，重新对照通过。
2. YOUR PACKAGE 的前导空格被 HTML 普通空白处理折叠。恢复预格式空格，位置已与原稿一致。
3. 导出代码未表达套餐外框的渐变描边。通过 Figma 原始 strokes 读取并恢复，重新对照通过。
4. 小选项标题硬裁切、商品标题缺两行省略号。固定原始文字容器宽高并应用单行/两行结束截断，重新对照通过。
5. 浏览器字体的分数像素度量导致自动布局轻微累积偏移。应用 Figma 原始文字容器尺寸，707 个可比图层坐标核对通过。
6. Press Start 2P 不含全角冒号，浏览器系统回退造成字形偏移。使用官方 Noto Sans SC 单字子集并校正视觉居中，最终局部对照通过。

## 剩余限制

无待修复 P0/P1/P2。浏览器与 Figma 的字体抗锯齿、细描边光栅化仍可能有亚像素差异（P3）。本次已验证 Codex 内置 Chromium 浏览器的两个 PC 宽度；未验证其他浏览器、手机或业务交互，这些不在本次静态交付范围内。

Modern Web Guidance：已检索文字截断并读取 typography 指引；通用字体重排建议未套用到本次固定 Figma 排版，避免改变用户指定的字体、换行与像素尺寸。

## 增量交互验证

按浏览器批注增加以下行为，原页面几何、字体和默认素材保持：

- 倒计时截止于 **2026-11-30 23:59:59 America/New_York**，对应 `2026-12-01T04:59:59Z`。每次读取真实时钟计算，页面恢复可见或从浏览器缓存恢复时重新校时，到期全零并停止调度。
- 选中的 BLACK FRIDAY 悬停/键盘焦点，使用 Figma `541:2116` 中背景组 `541:2117` 的原始导出。背景与 HTML 文字分离，裁切和 192×46 的容器尺寸与设计一致。
- 四个未选中导航悬停/键盘焦点，使用 `541:2181` 的 SVG；不同宽度沿用原矢量素材的横向适配。
- **88 个按钮、导航和链接容器**及**18 个完整产品卡片/主推面板**的计算样式均为 `cursor: pointer`。产品卡片的图片、文字、背景整卡覆盖；装饰背景和计时信息保持普通指针。

验证结果：

| 项目 | 结果 |
| --- | --- |
| 倒计时真实运行 | 浏览器数值随真实时间递减，跨分钟进位正确，截止瞬间与配置一致 |
| 倒计时边界与时区 | `node scripts/countdown.test.mjs` 通过：天/时/分/秒进位、到期与过期、最后不足一秒、夏令时、不同观看时区、时钟跳跃恢复 |
| 兼容实现 | 本地固定版本 Temporal 兼容文件的浏览器全局导出测试通过；运行时无需外部 CDN |
| 五个导航悬停 | CSS 状态、实际底图路径、移开恢复、容器几何均核对通过 |
| 键盘焦点 | Tab 能移至下一导航，focus-visible 同步使用原悬停物料 |
| 手型范围 | 88 个控制容器、18 个卡片容器及卡片内图片/文字的 computed cursor 全部通过 |
| 控制台与图片 | 无 error / warn，原 155 个图像引用均正常加载 |

最终浏览器证据：`C:/Users/60922/.codex/visualizations/2026/10/23/01a16694-20ec-78d2-b0b1-f7ed35a17715/interactive-nav-countdown.png`。

本轮应用的 Modern Web Guidance：

- `calculate-event-differentials`：使用时区感知的 Temporal，并按需加载本地兼容实现，遵守 “For browsers that do not yet support the native `Temporal` API, use feature detection and a polyfill.”
- `css`：通过组件标记限定手型范围，避免将装饰图片也设为手型；悬停与焦点规则用 `:is()` 合并，遵守 “Write selectors in a way that expresses intent.”

增量结果：passed。未增加购物、跳转或表单业务逻辑。

## 像素揭示、视频与主推容器更新

- Figma 原始白底为 `551:3475`，1920×925，纯白不透明素材；已下载至 `assets/figma/power-level-white/551-3475.png`。以原图作为白底和 24×12 个遮罩格，初始保留中心 4 格画面，按确定性的中心距离和少量空间扰动逐格揭示，向上滚动同路径回收。
- 闯关画面仍为原始分层图片和 HTML 文字，未烘焙整区截图。包装容器保留原 `(0,314,1920,925)`，内部定位回移314px，不改计时区与 SIDE QUEST 的位置。遮罩底层补足原深色背景，避免原72%透明图层与白底混合变灰；邻接格重叠0.75px防止等比缩放出现细缝。全部展开后白底退出，恢复完整原画。
- 原生 `view-timeline` 驱动，无 wheel 拦截、定时动画或额外滚动距离。画布裁切从 `overflow:hidden` 改为 `overflow:clip`，使时间线使用真实页面视口。浏览器实测同一滚动位置244.667px前后两次揭示的104格完全相同，完全展开为288格。
- 提供的视频按原文件复制，SHA-256一致；1920×1080、约5.056秒、H.264/AAC。填入原1920×960背景槽位，`object-fit:cover`；保留原渐变、标题、CTA、下方流程与周次卡。静音、内联、自动循环，临近视口加载，离开视口/后台暂停；减少动态效果时保持静态。
- 本地服务器新增 MP4 MIME 与范围请求支持。HEAD、完整请求、206范围、尾部范围、416错误范围均校验通过。浏览器实测 `readyState=4`、`paused=false`、`muted=true`、`loop=true`，画面与播放时间持续变化，无解码错误。
- 最新 `541:1320`「主推板块缩放交互」为1920×1080；新文字组553:3510，文字及旋转预览整体下移60px，背景不透明度28%。原始背景和缩略图已从最新context下载。主推产品从y3811开始，其余后续板块均+120，全页高10759。
- 1920px浏览器截图与同尺寸Figma截图核对：标题、说明、旋转预览、背景位置相符。1366px视口实测容器高768.375px，等于1080×1366/1920，无横向溢出，所有图片成功加载。1639px实测像素展开/回收、视频播放与原有计时功能正常。构建、脚本语法和倒计时边界测试通过。

本轮证据保存于可视化目录：`power-white-partial.png`、`power-white-complete.png`、`weekly-bonus-complete.png`、`customize-updated-1920-exact.png`，参考源为`figma-customize-latest-1920.png`及用户录屏抽帧。

本轮应用的 Modern Web Guidance：

- `motion`：采用原生滚动时间线与不连续像素遮罩，遵守 “Use `clip-path` and `mask-image` for custom geometric reveals and smooth fade-outs.”；减少动态效果时直接显示完整画面。
- `css`：样式限定于闯关容器和视频容器，遵守 “Write selectors in a way that expresses intent.”，不改变其他产品区域。
- `accessibility`：遮罩定义和背景视频为装饰内容，保留文字的可访问性，遵守 “Use `alt=\"\"` to remove decorative images from the accessibility tree so they aren't announced.”
- `lazy-load-video-and-audio`、`html`：视频声明原始尺寸、静音和内联播放，并按视口延迟加载，遵守 “Always specify integer width and height attributes (in CSS pixels) on `<video>`.”，避免下方视频抢占首屏资源。
