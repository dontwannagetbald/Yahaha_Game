# Yahaha Design System

## 1. Visual Theme & Atmosphere

Yahaha 官网整体是沉浸式、游戏化、偏未来感的娱乐产品视觉，面向玩家、创作者和 3D 互动内容用户。首屏使用全屏 3D 世界截图作为真实产品氛围载体，导航和标题直接叠加在画面上。

主设计语言是深色底色承接大面积 3D 视觉资产，再用高亮黄色胶囊按钮作为主要行动点。页面下半部分延续深色背景、大标题、横向内容卡片和宽间距模块，整体比传统 SaaS 更像游戏社区和内容平台。

说明：由于 Yahaha CDN 样式表存在跨域限制，无法读取完整 CSS rule；以下具体值来自浏览器 computed style、1440x900 首屏截图和 390px 移动视口 computed style。

### Key Characteristics

- 全屏 3D 场景图作为首屏主视觉
- 深色页面底色承接白色文字和高饱和 CTA
- 主 CTA 使用黄色、黑字、99px 胶囊圆角
- 桌面端导航透明叠加在首屏图片上
- 大标题使用 60px 或 72px 高冲击字号
- 内容区使用 64px 桌面边距和大段垂直留白
- 几乎不依赖阴影，主要靠图片、色块、边框和留白分层
- 移动端首屏保留沉浸式图片，但标题缩小到 40px

## 2. Color Palette & Roles

配色是深色底、白色文字、黄色主行动色的高对比组合。品牌感主要来自 3D 图片资产和黄色按钮，而不是复杂渐变或多色 UI token。

### Primary

| Hex | Role | Where seen |
| --- | --- | --- |
| `#0F1112` | 页面基础深色背景、按钮文字 | `main.home` background, `footer.page-footer-v2` background, `.download-button` color |
| `#FFFFFF` | 主文字、导航文字、标题文字 | desktop nav links, `.title`, body text, footer links |
| `#FFC200` | 主 CTA 背景 | `button.button`, `a.download-button` background |

### Accent

| Hex | Role | Where seen |
| --- | --- | --- |
| `rgba(255,255,113,0.32)` | 活动/专题按钮的半透明亮色底 | `.afterform-button` background |
| `#000000` | 活动按钮文字、部分外部组件边框 | `.afterform-button` color |

### Surfaces

| Hex | Role | Where seen |
| --- | --- | --- |
| `#0F1112` | 主页面和页脚底色 | `main.home`, `footer.page-footer-v2` |
| `transparent` | 导航、链接、内容标题容器 | `nav.desktop-navigation`, `.title`, ordinary links |

### Borders

| Hex | Role | Where seen |
| --- | --- | --- |
| `rgba(255,255,255,0.5)` | 次级胶囊按钮描边 | `.feature-scroll-button` border |
| `#0F1112` | 黄色 CTA 内部图标/暗色对比 | `.download-button` color and related icon area |

### Shadows

| Hex | Role | Where seen |
| --- | --- | --- |
| `none` | 大部分品牌 UI 不使用阴影 | nav, CTA, cards, footer computed `box-shadow: none` |

### Notes

黄色只用于强行动按钮，如官网 `Sign In`、`Download now` 或本 MVP 的 `登录`、`Publish`。不要用于正文或普通链接。深色背景和白色文字是平台主基调，卡片和工具界面可以使用更克制的深灰层级，但必须保留黄色作为唯一主要 CTA 色。

## 3. Typography Rules

字体系统以 `Inter, Arial, sans-serif` 为正文和普通标题基础，官网关键大标题使用 `Mona-Sans-BoldWide`，小型技术/活动说明使用 `"IBM Plex Mono"`。部分按钮 computed style 显示为 `Arial`，但产品实现中建议统一回 `Inter`，保留相同字号、字重和按钮尺寸。

### Hierarchy

| Role | Font | Size | Weight | Line height | Letter spacing |
| --- | --- | --- | --- | --- | --- |
| Display | `Mona-Sans-BoldWide` | 72px | 400 | 76px | normal |
| H1 | `Inter, Arial, sans-serif` | 60px desktop / 40px mobile | 700 | 64px desktop / 46px mobile | normal |
| H2 | `Inter, Arial, sans-serif` | 40px | 700 | 46px | normal |
| H3 | `Inter, Arial, sans-serif` | 30px | 400 | 36px | normal |
| Body | `Inter, Arial, sans-serif` | 14px | 400 | normal | normal |
| Small | `"IBM Plex Mono"` | 12px | 500 | normal | normal |
| Mono | `"IBM Plex Mono"` | 12px | 500 | normal | normal |

### Principles

- Hero 标题直接压在图片上，使用 60px/64px 的紧凑大字。
- 内容模块标题可使用 72px 宽体字，形成强游戏活动海报感。
- 正文介绍可使用 30px/36px，比普通 Web 正文更大，适合沉浸式品牌页。
- 常规导航使用 16px、400 weight，保持轻量。
- 卡片标题使用 18px/24px，避免与大标题竞争。
- 字距保持 normal，不使用负字距。

## 4. Component Stylings

### Buttons

Primary button：背景 `#FFC200`，文字 `#0F1112`，圆角 `99px`。桌面导航按钮尺寸约 `101px x 44px`，padding `12px 24px`，字号 `16px`，字重 `700`；大 CTA 尺寸约 `217px x 72px`，padding `12px 12px 12px 26px`。

Secondary button：透明背景，白色文字，`1px solid rgba(255,255,255,0.5)`，圆角 `99px`。示例为 `.feature-scroll-button`，尺寸约 `242px x 66px`，padding `8px 8px 8px 32px`。

Ghost button：导航链接为透明背景、白色文字、无边框，桌面端 `16px`、400 weight。

Destructive button：官网未观察到 destructive 样式。当前产品中应避免新增红色主按钮，除非用于删除确认弹窗。

### Cards

官网的内容卡片更像无底色的图片+标题列表，而不是带阴影卡片。Latest updates 列表项约 `199px` 宽，图片约 `199px x 250px`，标题 `18px/24px`，padding-top `16px`，背景透明，阴影为 `none`。

### Inputs

官网首页未观察到品牌输入框。当前 MVP 的输入框应基于 Ant Design 控件定制：深色 surface、白色主文字、弱白边框；focus ring 可使用 `#FFC200`，但需在实现中实际定义后再固化为 token。

### Navigation

桌面导航为透明层，位于首屏顶部，容器高度 `64px`，页面顶部偏移约 `16px`。Logo 位于左侧，链接横向排列，文字白色 `16px`，官网右侧有社交图标和黄色 `Sign In` 胶囊按钮；本 MVP 中对应为默认头像 + `登录`，登录后显示头像和昵称。移动端使用 `.mobile-navigation`，宽度为视口减左右 `16px`，高度 `100px`，padding `16px 0`，保留右侧登录入口。

### Image Treatment

首屏图片使用 `object-fit: cover`，桌面视口下图片尺寸为 `1440px x 900px`，全屏铺满。新闻图片使用固定竖向比例，约 `199px x 250px`。官网未对首屏主图使用卡片圆角，图片是全屏背景式展示。

### Distinctive Components

Marquee / Carousel hero：首屏存在横向轮播位移，多个 hero slide 横向排布，当前 slide 内标题在底部左侧，CTA 位于标题下方。

Wide poster heading：`Experience the fun.` 和 `Unleash your creativity.` 使用 `Mona-Sans-BoldWide`、`72px/76px`，适合游戏活动型区块标题。

Feature scroll button：透明胶囊按钮配弱白边框，内容为白色粗体 `16px`，适合 “Browse all games” 这类次级行动。

Download panel：底部下载区内容容器宽 `1312px`，padding `160px 64px`，圆角 `40px`，内部继续使用黄色 CTA。

## 5. Layout Principles

### Spacing Scale

观测到的常用间距包括 `8, 12, 16, 24, 26, 30, 32, 40, 60, 64, 75, 100, 120, 150, 160, 200, 350px`。桌面主内容左右边距常见为 `64px`，移动端主内容左右边距常见为 `24px` 或导航容器左右 `16px`。

### Grid

桌面宽屏以 `1440px` 视口为主要设计基准，内容最大宽度常见为 `1312px`，即左右各 `64px`。Latest updates 使用 6 列横向列表，每列约 `199px`，列间距约 `24px`。功能点区域使用 3 列布局，单项宽度约 `384px`。

### Whitespace

页面使用非常大的垂直分区留白，典型 section padding 包括 `100px`, `150px`, `200px`。这让页面更像游戏品牌宣传页，而不是高密度后台系统。当前 MVP 可以在 Home 和 Play 使用较强视觉留白，但 Create 后台型页面应适度压缩密度。

### Radius Scale

- `none`: 图片、导航、普通内容容器
- `sm`: 10px，用于活动按钮
- `lg`: 40px，用于大下载面板
- `pill`: 99px，用于 CTA 和胶囊按钮
- `circle`: 50%，用于浮动圆形控件

## 6. Depth & Elevation

### Levels

| Level | Use | Shadow |
| --- | --- | --- |
| 0 | 页面背景、导航、标题、CTA、新闻列表 | `none` |
| 1 | 弱分层按钮或边框控件 | `none`; use `1px solid rgba(255,255,255,0.5)` |
| 2 | 大面板 | `none`; use radius `40px`, image/background contrast |
| 3 | Modal / overlay in MVP | 官网未观察到；建议用 Ant Design 默认遮罩并减少阴影强度 |

### Philosophy

Yahaha 官网几乎不靠 box-shadow 建立层级。深度主要来自 3D 图像本身、全屏背景、透明叠层、白色文字、黄色 CTA、边框胶囊和大面积留白。实现时应优先使用对比和空间层级，而不是叠加重阴影。

## 7. Interaction & Motion

### Hover States

按钮和链接 computed style 中观察到 `transition: 0.2s` 或 `transition: 0.2s ease-out`，社交/页脚链接使用 `0.2s` 到 `0.3s`。官网未直接暴露 hover 后颜色值；实现中可让黄色按钮 hover 轻微降低亮度或上移 `1px`，但该 transform 属于 inferred。

### Focus States

官网首屏未观察到明确 focus ring token。MVP 需要补足键盘可访问性：对按钮、链接、输入框使用可见 focus ring，建议围绕 `#FFC200` 建立 2px ring，但该值属于产品实现建议，需在代码中定义。

### Transitions

观测到的 transition 包括 `0.2s`、`0.2s ease-out`、`0.3s`、`0.3s linear`。主要用于按钮、链接、图标和浮动控件。动画应优先作用于 color、background-color、opacity、transform，避免影响布局尺寸。

## 8. Responsive Behavior

### Breakpoints

由于跨域限制未能读取 CDN CSS 中的 `@media` 规则，以下为浏览器视口观测值，不是 CSS 源码断点。

| Name | Min width | Primary changes |
| --- | --- | --- |
| mobile observed | 390px viewport | 使用 `.mobile-navigation`，导航高 `100px`，左右边距约 `16px`；hero 标题为 `40px/46px`；内容左右边距约 `24px` |
| desktop observed | 1440px viewport | 使用 `.desktop-navigation`，导航高 `64px`；hero 图片 `1440px x 900px`；内容最大宽 `1312px`；hero 标题为 `60px/64px` |

### Touch Targets

移动端官网 `Sign In` 按钮约 `101px x 44px`，符合 44px 最小触控高度；本 MVP 的 `登录`、`Publish` 和主要操作按钮也应遵循该触控高度。浮动圆形控件约 `46px x 46px`。MVP 中所有主要按钮和工具栏 icon button 不应小于 `44px` 高。

### Collapsing Strategy

桌面端显示完整横向导航；移动端隐藏完整链接组，显示 `.mobile-navigation`，保留 Logo 区域和右侧登录入口。对于当前游戏平台 MVP，移动端 Home 可保留关键 CTA，Create 的复杂工具栏应折叠为顶部操作栏 + 底部/抽屉式辅助面板。

### Image Behavior

Hero 图片使用 `object-fit: cover`，在桌面和移动端都应裁切而不是拉伸。游戏封面和新闻卡片应保持固定宽高比；列表中的图片可使用 `object-fit: cover`，避免封面变形。

## 9. Agent Prompt Guide

### Quick Color Reference

```text
#0F1112  // surface-base, footer, dark text on yellow CTA
#FFFFFF  // text-primary, nav text, title text
#FFC200  // primary CTA background
rgba(255,255,255,0.5)  // secondary pill border
rgba(255,255,113,0.32) // event/promo translucent accent
#000000  // special promo button text
```

### Example Prompts

1. Build a dark, game-platform Home page inspired by Yahaha: use `#0F1112` as the base, full-bleed 3D/game cover imagery, white nav text, and `#FFC200` pill CTAs with `99px` radius.

2. Design a Play page that keeps Yahaha's immersive style: full viewport game iframe, transparent top navigation, white controls, yellow primary action, and no heavy shadows.

3. Create a game catalog using Yahaha-style cards: dark background, image-led cards, white 18px titles, minimal borders, 64px desktop gutters, and wide spacing between sections.

### Iteration Guide

- Keep yellow reserved for primary actions only; do not turn tags, body text, or secondary controls yellow.
- Favor real game screenshots, generated covers, and interactive previews over abstract gradients.
- Use shadows sparingly; prefer dark surfaces, borders, image contrast, and spacing.
- Preserve large desktop gutters around 64px and reduce to 16-24px on mobile.
- Use `99px` pills for CTAs and `40px` radius only for large feature panels.
- Do not make admin-style pages overly decorative; carry the brand through color, typography, and cover imagery while keeping workflows efficient.
