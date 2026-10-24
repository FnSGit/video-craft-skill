# Hyperframes 后端（V1 预留，未实现）

> 状态：⏸ 未实现 · 2026-10-24 · 计划 V3

---

## 定位

**产品宣传 / 社交短视频 / PR walkthrough / HTML 原生动效**。

上游项目：[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes)
（Apache 2.0，71k star，tagline「Write HTML. Render video. Built for agents.」）

## 为什么单列一个后端

Hyperframes 与 Remotion **同属"代码即帧"派**，都是 headless Chrome + FFmpeg 渲染，
但作者模型不同：

| | Hyperframes | Remotion（我们的 remotion 后端） |
|---|---|---|
| 作者模型 | 纯 HTML + CSS + `data-start/duration` 属性 | React 组件树 |
| 构建 | 无——`index.html` 直接播 | 必须 bundler |
| 动画 | 可寻址（seekable）适配器：GSAP / CSS / Lottie / Three.js / WAAPI | React 声明式 + `useCurrentFrame()` |
| 时钟 | 帧精确（library-clock） | 帧精确 |
| 许可 | Apache 2.0 | source-available |

**关键差异是"无构建步骤"和"agent 友好"**：agents 天生会写 HTML，不需要理解 React 组件模型
和 JSX 语法。对"让 AI 直接产出一条宣传片"这个场景，Hyperfaces 的作者门槛明显更低。

另外它自带 **450 个 catalog 组件**（transitions / captions / charts / maps / 3D / camera moves），
以及 `frame.md`（把品牌 design.md 反写成视频可用的设计系统）。

## 何时应路由到这里

判据见 `../../routing/router.md` R2：

- 用户明确提到产品名 / 版本号 / 发布 / changelog
- 时长倾向 <60 秒
- 目标是"展示"而非"讲解"
- 需要竖屏 9:16 等社媒比例、品牌视觉、动效炫技

## V1 的降级行为

路由命中 R2 时，主会话必须告知用户：

> 「这个题材更适合 hyperframes 后端，但 V1 还没实现。
> 先用 remotion 做——会按横屏 1280×720 出片。
> 想要竖屏 / 强品牌视觉 / 免构建的 HTML 工作流，需要等 V3。」

## V3 实现要点

### 工程骨架

```text
backends/hyperframes/template/
├── index.html                 # 主合成：data-composition-id + data-start/duration/track-index
├── package.json               # 只有 hyperframes CLI + devDependencies
├── frame.md                   # 品牌设计系统（视频适配版）
├── script/
│   ├── narration.txt
│   └── timeline.json          # core/tts_build.py 产出（同 remotion 后端）
├── compositions/
│   ├── 01-intro.html
│   └── ...
└── scripts/
    ├── new_project.sh
    ├── render.sh              # npx hyperframes render
    ├── still.sh
    └── preview.sh
```

### 字幕如何对接

Hyperframes 用 HTML 元素 + `data-start/duration` 上时间轨。字幕由
`core/tts_build.py` 产出的 `timeline.json` 驱动——需要一个生成器把
`timeline.json` 的 subs 数组转成带 `data-*` 属性的 HTML 块。

**这是唯一需要新写的桥接代码**（预计 100 行内）。

### 与 core 的兼容性

| core 资产 | 可用性 | 说明 |
|---|---|---|
| `research-brief.md` | ✅ 直接可用 | 渲染器无关 |
| `narration-guidance.md` | ✅ 直接可用 | 渲染器无关 |
| `narration-storyboard.md` | ✅ 基本可用 | 分镜格式中性；HTML 后端用"段落=场景"而非"段落=镜头" |
| `tts_build.py` | ✅ 直接可用 | 已参数化；`src/common` 不存在时自动跳过 TS 产物 |
| `render_storyboard.py` | ✅ 直接可用 | 令牌系统与后端无关 |
| `motion_check.py` | ✅ 直接可用 | 读帧；宣传片阈值需调（短视频节奏快，静止上限应更严，如 2.0s） |
| `frame_metrics.py` | ⚠️ 需加 `--bg flat` | 主角/光判据是 remotion 审美，宣传片不适用 |
| `sheet.py` | ✅ 直接可用 | 读帧 |

### 需要新写的部分

1. `backends/hyperframes/template/` 工程骨架
2. `scripts/gen_subtitles_html.py` —— timeline.json → 带 data-* 的 HTML 字幕块
3. 4 个脚本（new_project / render / still / preview）
4. `reference/agent-build-rules.md` —— HTML 合成规范
5. `frame_metrics.py` 增加"非 MG 片"判据集

### 实现前需验证的问题

- [ ] `npx hyperframes render` 的 CLI 参数与输出目录结构
- [ ] 中文字体在 headless Chrome 里的可用性（可能需要装 font-noto-sans-sc）
- [ ] catalog 组件（450 个）的安装方式与版本锁定
- [ ] `frame.md` 的实际格式与消费方式
- [ ] 竖屏 9:16 的配置方法

## 不做的部分

- 不做 Remotion → Hyperframes 的自动迁移（上游有自己的 `/remotion-to-hyperframes` skill，
  真需要时直接用它，不在本 skill 里重复造）
- 不接入 HeyGen 托管服务（本 skill 只做本地渲染）
