# Manim 后端 QC 判据（V2 样片校准）

> 来源：《梯度下降的公式》样片实测（2026-10-25）
> 样片：3379 帧 = 112.6s，12 个推导步，2 章，38 句解说
> 校准方法：全分辨率逐帧差分 + 亮紫质心追踪，与 `core/motion_check.py` 的降采样口径对照

---

## 一、最重要的结论：`motion_check.py` 的降采样口径对 manim 内容会误报

`core/motion_check.py` 用 **320×180 降采样 + 平均灰度变化 <0.35** 判静止。
这个口径是为 remotion MG 片定的（那里"可察觉动作 = 大面积 × 实心 × 快"，
见 `core/lessons.md`）。

**manim 推导片的运动语言不同**：

| 运动类型 | 视觉尺度 | 降采样后 |
|---|---|---|
| 点沿曲线走（DP01 走山人） | 半径 0.11 ≈ 8px，每帧位移 2–30px | 被 320×180 抹掉 |
| 箭头转向（DP06 梯度方向） | 长 ~1.7 单位 ≈ 120px，但变化的是角度 | 平均 diff 极低 |
| 曲线 draw-on | 一次性，结束后全静 | 画完即静止 |
| 公式逐 token 出现 | 每 3 帧一个字符 | 降采样后几乎不可见 |

**实测**：DP01 的走山人质心从 (517,340) 连续移动到 (590,350)，
`motion_check.py` 报 `still 7.0s 真静`；而全分辨率逐帧 diff 同样判静止
（点太小），但质心追踪证明它在动。

**所以：manim 端不能只信 `motion_check.py` 的静止判定。**

---

## 二、manim 端 QC 判据（三层，从松到严）

### 第 1 层：`motion_check.py --still-max 5.0 --no-hold`（粗筛）

```bash
python3 core/motion_check.py --frames fin_frames \
  --shots DP01:86-385,DP02:436-689,... \
  --still-max 5.0 --no-hold
```

- `--still-max 5.0`：推导片操作后要留时间看清式子，比 remotion 的 3.0 宽
- `--no-hold`：推导步没有"末拍离场"概念，关掉
- **报 fail 不一定是问题**，进第 2 层确认

### 第 2 层：全分辨率静止检测（确认是否真死寂）

```python
import subprocess, numpy as np, json
subprocess.run(['ffmpeg','-v','error','-y','-i','renders/<slug>_v1.mp4',
                '-f','rawvideo','-pix_fmt','gray','/tmp/q.gray'], check=True)
a = np.fromfile('/tmp/q.gray', dtype=np.uint8).reshape(-1, 720, 1280).astype(np.int16)
off = json.load(open('.frame_offsets.json'))
for k in sorted(off):
    seg = a[off[k]['start']-1:off[k]['end']]
    diffs = np.abs(np.diff(seg, axis=0)).sum(axis=(1,2)) / (1280*520)
    still = diffs < 0.15
    # 最长连续静止
    best = run = 0
    for v in still:
        run = run + 1 if v else 0
        best = max(best, run)
    print(f'{k}: 最长静止 {best/30:.1f}s', 'FAIL' if best > 150 else 'OK')
```

判据：**连续静止 > 150 帧（5s）且该段内没有任何元素位置变化** → 真死寂。

### 第 3 层：质心追踪（确认小幅运动是否存在）

对"报 fail 但应该有运动"的场景，追踪关键颜色的质心：

```python
# DP01 的走山人：亮紫 (r>150, g>100, b>240)
mask = (f[:,:,0]>150) & (f[:,:,1]>100) & (f[:,:,2]>240)
ys, xs = np.where(mask)
cx, cy = xs.mean(), ys.mean()      # 质心
```

质心持续位移 = 有运动，`motion_check` 的 fail 是误报。

---

## 三、样片实测数据（12 个推导步）

| DP | 帧数 | 最长静止(降采样) | 最长静止(全分辨率) | 判定 |
|---|---|---|---|---|
| DP01 | 300 | 7.0s | 7.1s | 误报（走山人持续移动，质心 517→590） |
| DP02 | 254 | 4.4s | 4.5s | OK |
| DP03 | 248 | 3.2s | 5.5s | 边界 |
| DP04 | 181 | 3.8s | 3.9s | OK |
| DP05 | 117 | 3.2s | 2.2s | OK |
| DP06 | 186 | 6.1s | 6.2s | 误报（箭头连续转向 80 帧） |
| DP07 | 273 | 3.9s | 4.8s | OK |
| DP08 | 146 | 4.7s | 4.7s | OK |
| DP09 | 292 | 9.6s | 4.0s | **降采样严重误报**（三个小球演示，全分辨率只 4.0s） |
| DP10 | 402 | 6.2s | 5.8s | 误报（动点沿线 60 帧） |
| DP11 | 275 | 9.1s | 6.2s | 误报（短轴箭头扫动 40 帧） |
| DP12 | 708 | 7.4s | 5.4s | 误报（小球 9 步迭代 360 帧） |

**关键发现**：DP09 降采样报 9.6s，全分辨率只 4.0s——**差 5.6s**。
降采样口径在 manim 内容上系统性偏严，不可作为唯一判据。

---

## 四、帧率与画幅：frames 参数必须与 manim 实际帧率解耦（V2 修）

`_frames_to_run_time` 曾硬编码 `style.FPS = 30`，但：

| 画质标志 | 分辨率 | 帧率 |
|---|---|---|
| `-ql` | 854×480 | **15fps** |
| `-qm` | 1280×720 | **30fps** |
| `-qh` | 1920×1080 | 60fps |

硬编码 30 时，`-ql` 下 `frames=70` 被算成 70/30=2.33s=**35 帧**（15fps），
导致测渲与正式渲染帧数不一致。

**实测踩坑**：DP01 在 `-ql` 下渲出 674 帧，而声明 300 帧。

**修复**：`common/timed_scene.py` 的 `_frames_to_run_time()` 与
`_update_subtitle()` 都改为读 `manim.config.frame_rate`。
`test_render.sh` 改用 `-qm -r 480,270`（降分辨率不降帧率）。

---

## 五、帧预算自动核对（V2 新增）

`TimedScene.render()` 包装了 `check_frame_budget()`，construct 结束后自动核对：

```text
⚠ DP01: frame_offset=85 声明区间 86-385，实际结束于 f186（差 -199 帧）。
   后续 Scene 的字母会偏移——改场景的 frames= 参数，或更新分镜表。
```

**为什么自动**：V2 样片实测 12 个场景全部忘记调用手写的
`check_frame_budget()`，导致每场景帧数比声明少 56–463 帧，成片 1585 帧
vs 预期 3962 帧，字幕与画面整体错位。

样片最终达成：**12/12 场景帧数与分镜表精确匹配**（3 个差 1 帧，浮点取整）。

---

## 六、多 Scene 字幕对齐（V2 新增）

`scripts/gen_frame_offsets.py` 从 `分镜表.md` 解析 DPxx 帧区间 →
`.frame_offsets.json` → `TimedScene._apply_frame_offset()` 读取并设
`self.frame_offset` → `_update_subtitle()` 用 `self.time * fps + 1 + offset`
算全片绝对帧号。

分镜表两种格式都认：

```markdown
| DP01 | 1-60 |
```

或

```markdown
## 推导步 DP01
- 帧区间：1-60
```

**验证**：DP01/DP02 各 60 帧，S01 在 f1-60、S02 在 f61-120，
offset 分别 0 和 60。成片逐帧统计字幕带：DP01 时段有字幕、
DP02 时段字幕从 f101 起出现（FadeIn 前 32 帧不可见），各自归位。

---

## 七、中文不能进 LaTeX（V2 新增）

`\text{中文}` 会报 `Unicode character 步 (U+6B65)`。中文标注一律用
`common.plain()`（走 `Text`）：

```python
from common import Formula, plain

f = Formula(r"\theta_{new} = \theta_{old} - \eta\nabla f")   # 纯符号
note = plain("减号：往下走")                                   # 中文走 Text
```

---

## 八、判据汇总（manim 端）

| 项 | 判据 | 命令/方法 |
|---|---|---|
| 帧数匹配 | 每场景实际帧 = 分镜表声明（±2 帧） | 自动（`check_frame_budget`） |
| 静止 | 全分辨率连续静止 > 5s 且无元素位移 → 修 | 第 2 层脚本 |
| 静止（降采样） | `motion_check` 报 fail 只是线索，需第 2/3 层确认 | `--still-max 5.0 --no-hold` |
| 末拍稳定期 | **不适用**（推导步无离场概念） | `--no-hold` |
| 主角带光 | **不适用**（推导片无"主角"概念） | 不用 `frame_metrics` 的主角判据 |
| 公式可见性 | SVG `use` 数 = `defs` 数 | `rg -o "xlink:href='#" \| wc -l` |
| 字幕对齐 | 各时段字幕出现在声明帧区间内 | 第 3 层质心/像素统计 |
| 中文 | 不走 LaTeX | `plain()` |
