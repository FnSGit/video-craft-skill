import React from 'react';
import {Svg, CText, Box, LineArrow, PURPLE, PURPLE_DEEP, PURPLE_LIGHT, GREY, GREY_LINE, GREY_MID, WHITE, GLOW_PURPLE} from './ui';
import {HeroGlow} from './fx';
import {clamp01, easeInOutPow, easeOutCubic, FONT_MONO, FONT_SERIF, FONT_TECH} from './common';

/**
 * 数学/物理教学片 图元库
 * - 纯函数、确定性（无 Math.random）
 * - 坐标系：AxesSpec 定义 x/y/w/h/xDomain/yDomain，数据点 → 画布像素由 map2() 得到
 * - 视觉规则（详见 SPEC.md §3 与 PROBE_PRIMS.md）：
 *   · 白描边 2–3px、黑填充；紫 #6630F8 只给「当前重点」，其它一律白/灰
 *   · 最小字号 22px（刻度、坐标轴名、图元标签全部 ≥22px）
 *   · 网格线 #4A4A4A 1px
 *   · 主角必须「有光」——图元库不自动加光，镜头层用 HeroGlow 包住主角区
 */

// ---------- 坐标系 ----------

export type AxesSpec = {
  x: number; y: number; w: number; h: number;
  xDomain: [number, number];
  yDomain: [number, number];
};

export type Map2 = (x: number, y: number) => {px: number; py: number};

/** 数据坐标 → 画布像素 的映射（给动点、标注、图元复用） */
export const map2 = (ax: AxesSpec): Map2 => (dx, dy) => ({
  px: ax.x + ((dx - ax.xDomain[0]) / (ax.xDomain[1] - ax.xDomain[0])) * ax.w,
  py: ax.y + ax.h - ((dy - ax.yDomain[0]) / (ax.yDomain[1] - ax.yDomain[0])) * ax.h,
});

type Tick = {v: number; major: boolean};

/**
 * 生成轴刻度：n 段平均切分 [a,b]，去掉与 a 相等的重复项；major = 步长为整数或含 0 的那格
 * （数学轴上 0 处会 major，作为原点的视觉锚）
 */
const genTicks = (a: number, b: number, n: number): Tick[] => {
  const out: Tick[] = [];
  if (n <= 0 || !isFinite(b - a)) return out;
  const step = (b - a) / n;
  for (let i = 0; i <= n; i++) {
    const v = a + i * step;
    out.push({v, major: Math.abs(v) < 1e-9 || (step % 1 === 0 && Math.abs(v % 1) < 1e-9)});
  }
  return out;
};

const fmtNum = (v: number, major: boolean): string => {
  const av = Math.abs(v);
  if (av < 1e-9) return '0';
  // 数学课常遇到的整/半/1/2 分度 → 直接给小数；其它用一位精度
  if (Math.abs(v - Math.round(v * 2) / 2) < 1e-6) return (Math.round(v * 2) / 2).toString();
  if (major) return Math.round(v * 100) / 100 === 0 ? '0' : String(Math.round(v * 100) / 100);
  return String(Math.round(v * 10) / 10);
};

export type AxesProps = AxesSpec & {
  xDomain: [number, number];
  yDomain: [number, number];
  ticks?: number;
  grid?: boolean;
  xLabel?: string; yLabel?: string;
  p?: number;
  color?: string;
  gridColor?: string;
  labelSize?: number;
  opacity?: number;
};

/**
 * 坐标轴 + 刻度 + 数值标签 + 可选网格
 * p=draw-on 进度 0..1：先画网格，再画两轴，最后画刻度标签
 */
export const Axes: React.FC<AxesProps> = ({
  x, y, w, h, xDomain, yDomain, ticks = 8, grid = true, xLabel, yLabel,
  p = 1, color = WHITE, gridColor = GREY_LINE, labelSize = 22, opacity = 1,
}) => {
  const M = map2({x, y, w, h, xDomain, yDomain});
  const xs = genTicks(xDomain[0], xDomain[1], ticks);
  const ys = genTicks(yDomain[0], yDomain[1], Math.max(2, Math.round(ticks / 2)));
  const gridP = clamp01(p / 0.3);
  const axisP = clamp01((p - 0.15) / 0.4);
  const tickP = clamp01((p - 0.5) / 0.5);
  if (p <= 0 || opacity <= 0) return null;
  const sw = 2;

  const x0p = M(xDomain[0], yDomain[0]).py;
  const x1p = M(xDomain[1], yDomain[0]).py;
  const y0p = M(xDomain[0], yDomain[0]).px;
  const y1p = M(xDomain[1], yDomain[0]).px;

  return (
    <div style={{opacity}}>
      {/* 网格：水平线 + 竖线，按轴上刻度值 */}
      {grid && gridP > 0 && (
        <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: gridP, overflow: 'hidden'}}>
          {xs.map((t, i) => {
            const px = M(t.v, 0).px - x;
            return <div key={'gv' + i} style={{position: 'absolute', left: px, top: 0, width: 1, height: h, background: gridColor}} />;
          })}
          {ys.map((t, i) => {
            const py = M(0, t.v).py - y;
            return <div key={'gh' + i} style={{position: 'absolute', left: 0, top: py, width: w, height: 1, background: gridColor}} />;
          })}
        </div>
      )}
      {/* 两轴主线 + 箭头 */}
      <div style={{position: 'absolute', left: x, top: x1p - sw / 2, width: 0, height: 0, opacity: axisP}}>
        <div style={{position: 'absolute', left: 0, top: 0, width: w * axisP, height: sw, background: color}} />
        <LineArrow x0={x + w * axisP - 26} y0={x1p - 8} x1={x + w * axisP} y1={x1p} p={axisP} rodW={sw} headL={18} headW={18} color={color} />
      </div>
      <div style={{position: 'absolute', left: y1p - sw / 2, top: y, width: 0, height: 0, opacity: axisP}}>
        <div style={{position: 'absolute', left: 0, top: h - h * axisP, width: sw, height: h * axisP, background: color}} />
        <LineArrow x0={y1p + 8} y0={y + h - h * axisP + 26} x1={y1p} y1={y + h - h * axisP} p={axisP} rodW={sw} headL={18} headW={18} color={color} />
      </div>
      {/* 刻度短横 + 数值标签 */}
      {tickP > 0 && xs.map((t, i) => {
        const px = M(t.v, yDomain[0]).px;
        const isOrigin = Math.abs(t.v) < 1e-9;
        return (
          <div key={'tx' + i} style={{opacity: tickP}}>
            {!isOrigin && (
              <div style={{position: 'absolute', left: px - sw / 2, top: x1p, width: sw, height: t.major ? 10 : 6, background: color, opacity: t.major ? 1 : 0.75}} />
            )}
            <CText cx={px} cy={x1p + 24} size={labelSize} weight={600} family={FONT_MONO} color={t.major ? WHITE : GREY} opacity={t.major ? 1 : 0.85}>
              {fmtNum(t.v, t.major)}
            </CText>
          </div>
        );
      })}
      {tickP > 0 && ys.map((t, i) => {
        const py = M(0, t.v).py;
        const isOrigin = Math.abs(t.v) < 1e-9;
        return (
          <div key={'ty' + i} style={{opacity: tickP}}>
            {!isOrigin && (
              <div style={{position: 'absolute', left: y1p - (t.major ? 10 : 6), top: py - sw / 2, width: t.major ? 10 : 6, height: sw, background: color, opacity: t.major ? 1 : 0.75}} />
            )}
            <CText cx={y1p - 34} cy={py} size={labelSize} weight={600} family={FONT_MONO} color={t.major ? WHITE : GREY} opacity={t.major ? 1 : 0.85}>
              {fmtNum(t.v, t.major)}
            </CText>
          </div>
        );
      })}
      {xLabel && (
        <CText cx={x + w + 22} cy={x1p + 22} size={labelSize} weight={700} family={FONT_TECH} color={WHITE} italic scaleX={0.9} opacity={tickP}>
          {xLabel}
        </CText>
      )}
      {yLabel && (
        <CText cx={y1p + 8} cy={y - 30} size={labelSize} weight={700} family={FONT_TECH} color={WHITE} italic scaleX={0.9} opacity={tickP}>
          {yLabel}
        </CText>
      )}
    </div>
  );
};

// ---------- 曲线 / 参数曲线 ----------

type PlotBase = {axes: AxesSpec; p?: number; color?: string; sw?: number; glow?: boolean; opacity?: number};

/** 函数曲线 f(x) 沿 p 从左到右画出（可选光晕描边） */
export const Plot: React.FC<PlotBase & {f: (x: number) => number; samples?: number; clip?: boolean}> = ({
  axes, f, samples = 180, p = 1, color = WHITE, sw = 3, glow = false, opacity = 1, clip = true,
}) => {
  if (p <= 0 || opacity <= 0) return null;
  const M = map2(axes);
  const N = Math.max(2, Math.ceil(samples * p));
  const pts: string[] = [];
  for (let i = 0; i < N; i++) {
    const x = axes.xDomain[0] + ((axes.xDomain[1] - axes.xDomain[0]) * i) / (samples - 1);
    let y = f(x);
    if (!isFinite(y)) y = NaN;
    if (clip) {
      if (y < axes.yDomain[0] || y > axes.yDomain[1]) {
      // 越界：跳过（保留前一段）
      }
    }
    const q = M(x, y);
    pts.push(`${q.px.toFixed(2)},${q.py.toFixed(2)}`);
  }
  if (pts.length < 2) return null;
  return (
    <Svg bloom={false} opacity={opacity}>
      {glow && <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth={sw * 2.4} opacity={0.35} style={{filter: `drop-shadow(0 0 6px ${color})`}} />}
      <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
};

/** 参数曲线 (x(t), y(t)) 沿 p 从 t0→t1 画出 */
export const ParamCurve: React.FC<PlotBase & {x: (t: number) => number; y: (t: number) => number; t0: number; t1: number; samples?: number}> = ({
  axes, x, y, t0, t1, samples = 180, p = 1, color = WHITE, sw = 3, opacity = 1,
}) => {
  if (p <= 0 || opacity <= 0) return null;
  const M = map2(axes);
  const N = Math.max(2, Math.ceil(samples * p));
  const pts: string[] = [];
  for (let i = 0; i < N; i++) {
    const t = t0 + (t1 - t0) * (i / (samples - 1));
    const dx = x(t), dy = y(t);
    if (!isFinite(dx) || !isFinite(dy)) continue;
    const q = M(dx, dy);
    pts.push(`${q.px.toFixed(2)},${q.py.toFixed(2)}`);
  }
  if (pts.length < 2) return null;
  return <Svg bloom={false} opacity={opacity}><polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" /></Svg>;
};

// ---------- 动点 ----------

export type MovingPointProps = {
  axes: AxesSpec; cx: number; cy: number; r?: number; color?: string;
  dropLines?: boolean; glow?: boolean; label?: string; labelSize?: number;
  labelOffset?: [number, number]; opacity?: number;
};

/** 曲线上的一点：圆点 + 可选垂线到 x/y 轴 + 可选标签 */
export const MovingPoint: React.FC<MovingPointProps> = ({
  axes, cx, cy, r = 9, color = PURPLE, dropLines = false, glow = true, label, labelSize = 22,
  labelOffset = [22, -22], opacity = 1,
}) => {
  if (opacity <= 0) return null;
  const M = map2(axes);
  const q = M(cx, cy);
  const x1 = M(axes.xDomain[0], axes.yDomain[0]).py;
  const y1 = M(axes.xDomain[0], axes.yDomain[0]).px;
  return (
    <div style={{opacity}}>
      {dropLines && (
        <>
          <div style={{position: 'absolute', left: q.px - 1, top: Math.min(q.py, x1), width: 2, height: Math.abs(q.py - x1), background: GREY_MID}} />
          <div style={{position: 'absolute', left: Math.min(q.px, y1), top: q.py - 1, width: Math.abs(q.px - y1), height: 2, background: GREY_MID}} />
        </>
      )}
      {glow && <HeroGlow x={q.px - r * 2} y={q.py - r * 2} w={r * 4} h={r * 4} r={r * 2} color={color} />}
      <div style={{position: 'absolute', left: q.px - r, top: q.py - r, width: r * 2, height: r * 2, borderRadius: '50%', background: color, border: '2px solid #000', boxShadow: glow ? `0 0 12px 3px ${color}99` : undefined}} />
      {label && (
        <CText cx={q.px + labelOffset[0]} cy={q.py + labelOffset[1]} size={labelSize} weight={700} color={color} shadow="0 0 8px rgba(0,0,0,.9)">
          {label}
        </CText>
      )}
    </div>
  );
};

// ---------- 割线 → 切线 ----------

/**
 * 割线 + 切线：
 *   dx(n) 由调用方传入随帧递减的 Δx；内部自动计算 x0±dx 两端点、割线 y 值
 *   tangentP 用于当 dx→0 时切换到切线（调用方传 t 值）
 */
export const SecantTangent: React.FC<{
  axes: AxesSpec; f: (x: number) => number; fp?: (x: number) => number; // fp = f'(x)（选填）
  x0: number; dx: (n: number) => number; // dx 递减到 0
  n: number; p?: number; opacity?: number;
  secantColor?: string; tangentColor?: string;
  sw?: number; pointColor?: string;
  showLabels?: boolean; labelSize?: number;
}> = ({
  axes, f, fp, x0, dx, n, p = 1, opacity = 1,
  secantColor = WHITE, tangentColor = PURPLE, sw = 3, pointColor = WHITE,
  showLabels = true, labelSize = 22,
}) => {
  if (opacity <= 0 || p <= 0) return null;
  const d = Math.max(1e-4, dx(n));
  const M = map2(axes);
  // 割线端点：x0 ± d
  const xa = x0 - d, xb = x0 + d;
  const ya = f(xa), yb = f(xb);
  const A = M(xa, ya), B = M(xb, yb), P0 = M(x0, f(x0));
  // 切线：从 y=f'(x0)(x-x0)+f(x0) 两端画满 x 范围
  let T1: {px: number; py: number} | null = null;
  let T2: {px: number; py: number} | null = null;
  if (fp) {
    const k = fp(x0);
    const y1 = f(x0) + k * (axes.xDomain[0] - x0);
    const y2 = f(x0) + k * (axes.xDomain[1] - x0);
    T1 = M(axes.xDomain[0], y1);
    T2 = M(axes.xDomain[1], y2);
  }
  const secantOp = clamp01(1 - p); // 割线随 p 淡出
  const tangentOp = clamp01(p);
  return (
    <Svg bloom={false} opacity={opacity}>
      {tangentOp > 0 && T1 && T2 && (
        <line x1={T1.px} y1={T1.py} x2={T2.px} y2={T2.py} stroke={tangentColor} strokeWidth={sw + 1} opacity={tangentOp} style={{filter: `drop-shadow(0 0 6px ${tangentColor})`}} />
      )}
      {secantOp > 0 && (
        <>
          <line x1={A.px} y1={A.py} x2={B.px} y2={B.py} stroke={secantColor} strokeWidth={sw} opacity={secantOp} />
          <circle cx={A.px} cy={A.py} r={6} fill={pointColor} stroke="#000" strokeWidth="1.5" opacity={secantOp} />
          <circle cx={B.px} cy={B.py} r={6} fill={pointColor} stroke="#000" strokeWidth="1.5" opacity={secantOp} />
        </>
      )}
      <circle cx={P0.px} cy={P0.py} r={8} fill={tangentColor} stroke="#000" strokeWidth="2" opacity={opacity} />
    </Svg>
  );
};

// ---------- 定积分 / 面积 ----------

/**
 * 曲线下面积 + 可选黎曼矩形：
 *   rects=0 → 只画填充面积
 *   rects>0 → 画 n 条矩形，activeRect 高亮为紫
 */
export const AreaFill: React.FC<{
  axes: AxesSpec; f: (x: number) => number; a: number; b: number;
  rects?: number; p?: number; opacity?: number;
  fill?: string; stroke?: string; rectFill?: string; rectStroke?: string;
  activeRect?: number; activeColor?: string;
}> = ({
  axes, f, a, b, rects = 0, p = 1, opacity = 1,
  fill = `${PURPLE}26`, stroke = PURPLE_DEEP, rectFill = `${PURPLE}33`, rectStroke = WHITE,
  activeRect = -1, activeColor = PURPLE,
}) => {
  if (opacity <= 0 || p <= 0 || !isFinite(b - a) || b <= a) return null;
  const M = map2(axes);
  const yBase = axes.yDomain[0];
  const N = Math.max(1, Math.min(rects, Math.ceil(rects * p)));
  const step = (b - a) / N;
  const rectsEnd = a + Math.min(1, p) * (b - a);
  const path = (() => {
    const parts: string[] = [];
    parts.push(`M ${M(a, yBase).px.toFixed(2)} ${M(a, yBase).py.toFixed(2)}`);
    const S = 60;
    for (let i = 0; i <= S; i++) {
      const x = a + ((rectsEnd - a) * i) / S;
      if (x > b) break;
      let y = f(x);
      if (!isFinite(y)) y = yBase;
      y = Math.max(axes.yDomain[0], Math.min(axes.yDomain[1], y));
      const q = M(x, y);
      parts.push(`L ${q.px.toFixed(2)} ${q.py.toFixed(2)}`);
    }
    parts.push(`L ${M(Math.min(rectsEnd, b), yBase).px.toFixed(2)} ${M(0, yBase).py.toFixed(2)}`);
    parts.push('Z');
    return parts.join(' ');
  })();
  return (
    <Svg bloom={false} opacity={opacity}>
      <path d={path} fill={fill} stroke={stroke} strokeWidth={2} />
      {N > 0 && Array.from({length: N}, (_, i) => {
        const x1 = a + i * step, x2 = x1 + step;
        if (x1 >= rectsEnd) return null;
        const xShow = Math.min(x2, rectsEnd);
        const yv = f((x1 + xShow) / 2);
        const Y = Math.max(axes.yDomain[0], Math.min(axes.yDomain[1], isFinite(yv) ? yv : 0));
        const P1 = M(x1, yBase), P2 = M(xShow, Y);
        const isActive = i === activeRect;
        return (
          <rect
            key={i}
            x={P1.px}
            y={Math.min(P1.py, P2.py)}
            width={Math.abs(P2.px - P1.px)}
            height={Math.abs(P1.py - P2.py)}
            fill={isActive ? `${activeColor}66` : rectFill}
            stroke={isActive ? activeColor : rectStroke}
            strokeWidth={isActive ? 3 : 1.5}
            style={isActive ? {filter: `drop-shadow(0 0 6px ${activeColor})`} : undefined}
          />
        );
      })}
    </Svg>
  );
};

// ---------- 向量场 ----------

export type VectorFieldProps = {
  x: number; y: number; w: number; h: number;
  cols: number; rows: number;
  vec: (px: number, py: number) => [number, number]; // 输入/输出均为画布像素
  scale?: number; maxLen?: number;
  p?: number; opacity?: number;
  color?: string; activeColor?: string;
  activeAt?: (px: number, py: number) => boolean;
  sw?: number; head?: number;
};

/**
 * 网格化向量场：cols×rows 个点，每点画一支箭头；activeAt 为真的格子换成紫色
 */
export const VectorField: React.FC<VectorFieldProps> = ({
  x, y, w, h, cols, rows, vec, scale = 1, maxLen = 46,
  p = 1, opacity = 1, color = WHITE, activeColor = PURPLE,
  activeAt, sw = 2.5, head = 10,
}) => {
  if (opacity <= 0 || p <= 0) return null;
  const items: React.ReactNode[] = [];
  const stepX = cols > 1 ? w / (cols - 1) : 0;
  const stepY = rows > 1 ? h / (rows - 1) : 0;
  const total = cols * rows;
  const drawn = Math.max(1, Math.ceil(total * p));
  let k = 0;
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const idx = j * cols + i;
      if (idx >= drawn) continue;
      const px = x + i * stepX;
      const py = y + j * stepY;
      const [vx, vy] = vec(px, py);
      const L = Math.hypot(vx, vy) || 1;
      const len = Math.min(maxLen, L * scale);
      const ux = vx / L, uy = vy / L;
      const x1 = px + ux * len, y1 = py + uy * len;
      const isActive = activeAt ? activeAt(px, py) : false;
      const col = isActive ? activeColor : color;
      items.push(<LineArrow key={idx} x0={px} y0={py} x1={x1} y1={y1} rodW={sw} headL={head} headW={head * 1.3} color={col} opacity={isActive ? 1 : 0.72} />);
      k++;
    }
  }
  return <Svg bloom={false} opacity={opacity}>{items}</Svg>;
};

// ---------- 角度弧 / 直角 / 等长刻度 ----------

/**
 * 角度弧：以 (cx,cy) 为圆心，角度 a0..a1（度，SVG 屏幕坐标：y 向下），
 * label 居中放在弧中点外侧
 */
export const AngleArc: React.FC<{
  cx: number; cy: number; r: number; a0: number; a1: number;
  sw?: number; color?: string; label?: string; labelSize?: number;
  p?: number; opacity?: number; labelRadiusOffset?: number;
}> = ({cx, cy, r, a0, a1, sw = 3, color = PURPLE, label, labelSize = 22, p = 1, opacity = 1, labelRadiusOffset = 20}) => {
  if (opacity <= 0 || p <= 0) return null;
  // SVG 坐标系：0° 在 +x，y 向下，所以 a 度 → (cos a, sin a)
  const deg2rad = (d: number) => (d * Math.PI) / 180;
  const ang = a0 + (a1 - a0) * p;
  const x0 = cx + r * Math.cos(deg2rad(a0)), y0 = cy + r * Math.sin(deg2rad(a0));
  const x1 = cx + r * Math.cos(deg2rad(ang)), y1 = cy + r * Math.sin(deg2rad(ang));
  const large = Math.abs(ang - a0) > 180 ? 1 : 0;
  const sweep = a1 > a0 ? 1 : 0;
  const mid = (a0 + a1) / 2;
  const lxr = r + labelRadiusOffset;
  const lx = cx + lxr * Math.cos(deg2rad(mid));
  const ly = cy + lxr * Math.sin(deg2rad(mid));
  return (
    <div style={{opacity}}><Svg bloom={false}>
      <path d={`M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${r} ${r} 0 ${large} ${sweep} ${x1.toFixed(2)} ${y1.toFixed(2)}`} fill="none" stroke={color} strokeWidth={sw} style={{filter: `drop-shadow(0 0 4px ${color})`}} />
    </Svg>{label ? <CText cx={lx} cy={ly} size={labelSize} weight={700} color={color} shadow="0 0 6px rgba(0,0,0,.9)">{label}</CText> : null}</div>
  );
};

/**
 * 直角符号：在 (cx,cy) 画一个 size×size 的直角方形（rot 度旋转）
 * 常见于「垂直」证明
 */
export const RightAngle: React.FC<{
  cx: number; cy: number; size: number; rot?: number; sw?: number; color?: string; p?: number; opacity?: number;
}> = ({cx, cy, size, rot = 0, sw = 2.5, color = WHITE, p = 1, opacity = 1}) => {
  if (opacity <= 0 || p <= 0) return null;
  const s = size * p;
  return (
    <div style={{position: 'absolute', left: cx, top: cy, width: 0, height: 0, transform: `rotate(${rot}deg)`, opacity}}>
      <Svg bloom={false} style={{left: -s, top: -s}}>
        <path d={`M 0 0 L ${s.toFixed(2)} 0 L ${s.toFixed(2)} ${s.toFixed(2)} L 0 ${s.toFixed(2)}`} fill="none" stroke={color} strokeWidth={sw} />
      </Svg>
    </div>
  );
};

/**
 * 等长刻度：线段 (x1,y1)→(x2,y2) 上均匀加 n 段（默认 n 个刻度，含两端），
 * 每段长度为 seg 的短横。用于「两边相等」标记
 */
export const TickMark: React.FC<{
  x1: number; y1: number; x2: number; y2: number;
  ticks?: number; size?: number; sw?: number; color?: string; p?: number; opacity?: number;
}> = ({x1, y1, x2, y2, ticks = 1, size = 10, sw = 3, color = WHITE, p = 1, opacity = 1}) => {
  if (opacity <= 0 || p <= 0) return null;
  const n = Math.max(1, Math.ceil(ticks * p));
  const dx = x2 - x1, dy = y2 - y1;
  const L = Math.hypot(dx, dy) || 1;
  const ux = dx / L, uy = dy / L;
  const nx = -uy, ny = ux;
  const items: React.ReactNode[] = [];
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0.5 : (i + 1) / (n + 1);
    const cx = x1 + dx * t, cy = y1 + dy * t;
    items.push(<line key={i} x1={cx - nx * size} y1={cy - ny * size} x2={cx + nx * size} y2={cy + ny * size} stroke={color} strokeWidth={sw} />);
  }
  return <Svg bloom={false} opacity={opacity}>{items}</Svg>;
};

// ---------- 多边形 ----------

/**
 * 多边形：pts 为画布像素顶点数组，dashed=true 表示「边长相等」用虚线，labels 顶点标签
 */
export const Polygon: React.FC<{
  pts: Array<[number, number]>;
  labels?: string[];
  labelSize?: number;
  p?: number;
  opacity?: number;
  color?: string;
  fill?: string;
  sw?: number;
  dashed?: boolean;
  showVertices?: boolean;
  vertexColor?: string;
  vertexR?: number;
}> = ({
  pts, labels, labelSize = 24, p = 1, opacity = 1, color = WHITE, fill = 'transparent',
  sw = 3, dashed = false, showVertices = false, vertexColor = PURPLE, vertexR = 6,
}) => {
  if (opacity <= 0 || p <= 0 || pts.length < 2) return null;
  const N = Math.max(2, Math.ceil(pts.length * p));
  const d = pts.slice(0, N).map((q, i) => `${i === 0 ? 'M' : 'L'} ${q[0].toFixed(2)} ${q[1].toFixed(2)}`).join(' ') + (N === pts.length ? ' Z' : '');
  const shown = Math.min(N, pts.length);
  return (
    <div style={{opacity}}>
      <Svg bloom={false}>
        <path d={d} fill={fill} stroke={color} strokeWidth={sw} strokeDasharray={dashed ? '10 6' : undefined} strokeLinejoin="round" />
        {showVertices && pts.slice(0, shown).map((q, i) => <circle key={i} cx={q[0]} cy={q[1]} r={vertexR} fill={vertexColor} stroke="#000" strokeWidth="2" />)}
      </Svg>
      {(labels ?? []).slice(0, shown).map((t, i) => {
        // 标签放到顶点 + 相对质心的外扩方向
        const cx = pts.reduce((s, q) => s + q[0], 0) / pts.length;
        const cy = pts.reduce((s, q) => s + q[1], 0) / pts.length;
        const dx = pts[i][0] - cx, dy = pts[i][1] - cy;
        const L = Math.hypot(dx, dy) || 1;
        const lx = pts[i][0] + (dx / L) * 26;
        const ly = pts[i][1] + (dy / L) * 26;
        return <CText key={'l' + i} cx={lx} cy={ly} size={labelSize} weight={700} color={color} shadow="0 0 6px rgba(0,0,0,.9)">{t}</CText>;
      })}
    </div>
  );
};

// ---------- 附赠小工具：给曲线端点或某点自动加发光 ----------

/** 通用发光小球（不依赖 map2），给 VectorField 高亮或独立动画点用 */
export const GlowDot: React.FC<{cx: number; cy: number; r?: number; color?: string; opacity?: number}> = ({cx, cy, r = 8, color = PURPLE, opacity = 1}) => (
  <div style={{position: 'absolute', left: cx - r * 2, top: cy - r * 2, width: r * 4, height: r * 4, opacity}}><HeroGlow x={r} y={r} w={r * 2} h={r * 2} r={r} color={color} /><div style={{position: 'absolute', left: r, top: r, width: r * 2, height: r * 2, borderRadius: '50%', background: color, border: '2px solid #000'}} /></div>
);

/** 用于「Δx 标注」这种小括号：在 x 轴上水平标注一段长度 */
export const SpanLabel: React.FC<{x1: number; x2: number; y: number; text: string; size?: number; color?: string; opacity?: number}> = ({x1, x2, y, text, size = 22, color = WHITE, opacity = 1}) => {
  if (opacity <= 0) return null;
  const cx = (x1 + x2) / 2;
  const w = Math.abs(x2 - x1);
  return (
    <div style={{opacity}}>
      <Svg bloom={false}>
        <line x1={x1} y1={y} x2={x2} y2={y} stroke={color} strokeWidth={2} />
        <line x1={x1} y1={y - 6} x2={x1} y2={y + 6} stroke={color} strokeWidth={2} />
        <line x1={x2} y1={y - 6} x2={x2} y2={y + 6} stroke={color} strokeWidth={2} />
      </Svg>
      <CText cx={cx} cy={y - 22} size={size} weight={700} color={color} shadow="0 0 6px rgba(0,0,0,.9)">{text}</CText>
    </div>
  );
};

export {Box, PURPLE, PURPLE_DEEP, PURPLE_LIGHT, GREY, GREY_LINE, GREY_MID, WHITE, GLOW_PURPLE};
