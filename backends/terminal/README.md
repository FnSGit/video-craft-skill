# Terminal 后端（V1 预留，V2 必做）

> 状态：⏸ 未实现 · 2026-10-24 · **计划 V2（用户已确认：必须真终端录制）**

---

## 定位

**真终端操作教学**：安装 / 配置 / 部署 / 环境搭建 / 命令执行。

用户原话（2026-10-24 决策）：「3 V2 要做真终端」——
即**不接受**用 remotion 的 `CodeBlock` 图元冒充真实终端。

## 为什么必须真录制

`py-course/py-install-first`（已交付）用 remotion 的 `CodeBlock` 图元做了 Python 安装教学，
验证了**概念讲解**可行。但教学片里有几类内容，代码卡演不出来：

| 内容类型 | 为什么 CodeBlock 不行 |
|---|---|
| 命令的真实输出 | 输出内容、格式、换行、颜色必须是真的，画出来的会漏细节 |
| 报错现场 | traceback 的堆栈、行号、错误类型必须真实，否则教不会排错 |
| 交互式提示 | `pip` 的进度条、`git` 的 pager、`python` REPL 的 `>>>` |
| 耗时操作的真实节奏 | `npm install` 到底等多久，观众需要真实预期 |
| 终端快捷键效果 | Tab 补全、Ctrl-C、方向键翻历史 |

这类片子用画的代码卡，观众照着敲会发现"我的输出怎么和视频里不一样"——**教学片失信一次就完了**。

## 技术路线：asciinema 录制 + 后期合成

### 为什么选 asciinema 而不是 OBS 录屏

| | asciinema | OBS 录屏 |
|---|---|---|
| 产物 | `.cast` 文本文件（JSON lines） | mp4 像素 |
| 体积 | 几 KB | 几十 MB/分钟 |
| 分辨率 | 矢量文本，任意缩放不糊 | 固定像素，放大就糊 |
| 可编辑 | **可脚本化修改、重排版式、换配色** | 只能剪 |
| 帧精确 | 自带时间戳，可精确对齐配音 | 靠 ffmpeg 裁 |
| 可复现 | 脚本重跑生成同样结果 | 手动操作不可复现 |

对"多 agent 并行生产 + 帧号要对齐 timeline.json"这个需求，asciinema 是唯一合理选择。

### 流水线

```text
① 写录制脚本（commands.sh）——要演示的命令序列
② asciinema rec --overwrite -c "bash commands.sh" session.cast
      ↓ 真实执行，产出 .cast（带精确时间戳）
③ agg session.cast raw.gif --font-size 20 --cols 100 --rows 30
      ↓ 或先转中间格式
④ 后期合成：把终端画面 + core/tts_build.py 的 audio.wav + 字幕 合成 mp4
      ↓ 帧号由 timeline.json 统一
⑤ core/motion_check.py 读 fin_frames 做节奏 QC
```

**关键点**：③④ 之间要能**按 timeline.json 的帧号重定时基**——
asciinema 的时间戳是真实的（命令跑多快就多快），但配音是 TTS 生成的，
两者节奏必然不一致。需要一段"时间重映射"逻辑：把 .cast 的每行按
`timeline.json` 里对应句子的帧区间拉伸/压缩。

这是本后端**唯一有技术难度**的部分。

## V1 的降级行为

路由命中 R3 时，主会话必须告知用户：

> 「真终端录制后端 V2 才做。V1 用 remotion 的 `CodeBlock` 图元做代码卡演示——
> 能讲清概念和代码结构，但**不是真实执行的终端**，看不到真实输出和报错。
> 如果你的片子必须有真实命令输出，建议等 V2，或现在就用 OBS 录屏 + 后期配音。」

## V2 实现要点

### 工程骨架

```text
backends/terminal/template/
├── narration.txt               # 解说词（core 格式）
├── script/
│   ├── timeline.json           # core/tts_build.py 产出
│   └── audio.wav               # 同上
├── recordings/
│   ├── commands.sh             # 要演示的命令序列（可复现）
│   ├── session.cast            # asciinema 产出
│   └── setup.sh                # 录制前的环境准备（建干净容器/venv）
├── scenes/
│   ├── SC01.json               # 场景描述：用哪段 cast + 时间段 + 字幕区间
│   └── ...
└── scripts/
    ├── new_project.sh
    ├── record.sh               # asciinema rec 包装
    ├── cast2frames.py          # .cast + timeline.json → 逐帧终端画面
    ├── compose.sh              # 合成 mp4（画面+音频+字幕）
    ├── still.sh
    └── preview.sh
```

### 核心技术：cast2frames.py

```python
# 伪代码——时间重映射是核心
cast = load_cast('recordings/session.cast')     # [(t, data), ...]
tl = json.load(open('script/timeline.json'))

for sentence in tl['sentences']:
    # 该句对应的 cast 时间段（由 scenes/SCxx.json 指定）
    src_from, src_to = scene.map(sentence['id'])
    # 重映射到该句的帧区间
    dst_from, dst_to = sentence['from'], sentence['to']
    for frame in range(dst_from, dst_to):
        t = remap(frame, (dst_from, dst_to), (src_from, src_to))
        render_cast_at(cast, t, out=f'fin_frames/f_{frame:04d}.png')
```

### 环境隔离（重要）

录制要在**干净环境**里跑，否则：
- 输出里带个人路径（`/Users/fengshuai/...`）
- 已装的包导致"装过了"的假输出
- 历史命令污染

所以 `recordings/setup.sh` 负责建隔离环境：
- Python：`uv venv /tmp/vc-clean-rec`
- Node：Docker 容器（**本机无 docker，需先 `brew install --cask docker`**，或接受用临时 HOME + 干净 PATH）

### 与 core 的兼容性

| core 资产 | 可用性 | 说明 |
|---|---|---|
| `research-brief.md` | ✅ 直接可用 | |
| `narration-guidance.md` | ✅ 直接可用 | 但教学片的文案原则偏"指令清晰"而非"悬念节奏" |
| `tts_build.py` | ✅ 直接可用 | 这是关键——配音与帧号的统一来源 |
| `render_storyboard.py` | ✅ 直接可用 | |
| `motion_check.py` | ⚠️ 阈值要调 | 教学片允许命令执行时的长时间静止（等待输出），上限可能要放到 8–10s |
| `frame_metrics.py` | ❌ 基本不适用 | MG 构图判据全不适用；只可能用"内容区占比"之类 |
| `sheet.py` | ✅ 直接可用 | |

### 需要新写的部分

1. `template/` 骨架 + `recordings/setup.sh`（环境隔离）
2. `scripts/record.sh`（asciinema 包装）
3. `scripts/cast2frames.py`（**核心：时间重映射**）
4. `scripts/compose.sh`（ffmpeg 合成 画面+音频+字幕）
5. 3 个辅助脚本
6. `reference/agent-build-rules.md`（录制规范：命令必须真能跑、输出不得造假、注册 MANIFEST）

### 实现前需验证的问题

- [ ] asciinema 与 agg 的安装方式（`brew install asciinema agg`）
- [ ] `.cast` 的时间戳精度与 agg 的帧控制能力
- [ ] 无 docker 时的环境隔离方案
- [ ] 中文字体在 agg 里的渲染
- [ ] 字幕叠加：用 ffmpeg drawtext 还是预渲染 PNG 序列
- [ ] `motion_check.py` 对终端画面的判据是否还有意义（终端输出本身就是"变化"）

## 与 py-course 的关系

`~/Projects/ai-video/py-course` 已用 remotion 后端做完一集（py-install-first）。
V2 的 terminal 后端上线后：
- **不重做已交付的集**（那集的概念讲解用 CodeBlock 是合格的）
- 新集按路由判定：涉及真实命令执行/报错现场的集走 terminal，纯概念集继续走 remotion
