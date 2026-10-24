import React from 'react';
import {clamp01, easeOutCubic} from './common';
import {MATHJAX_SVG} from './common/mathjax_svg';

/**
 * 数学公式（真 LaTeX，离线、确定性）
 *
 * 工作方式：公式的 TeX 源码由 `scripts/gen_mathjax_svg.mjs` 在**构建期**用 MathJax 转成
 * **自包含 SVG**（字形是矢量路径内嵌在 <defs> 里），存进 `src/common/mathjax_svg.ts`。
 * 因此运行期：不需要 LaTeX、不需要字体文件、不访问网络，且同一帧渲染逐字节可复现。
 *
 * 用法：
 *   import {MathFormula} from '../formula';
 *   <MathFormula name="quadratic" fontSize={44} />                     // 白
 *   <MathFormula name="quadratic" fontSize={44} color={PURPLE} />      // 紫
 *   <MathFormula name="quadratic" fontSize={44} glow />                // 白光晕
 *   <MathFormulaReveal N={N} f0={120} name="quadratic" fontSize={44} /> // 从左向右"写出来"
 *
 * 加新公式：把 TeX 加进 `scripts/gen_mathjax_svg.mjs` 的 FORMULAS，然后
 *   npm i && node scripts/gen_mathjax_svg.mjs
 * 会重写 `src/common/mathjax_svg.ts`（提交它）。
 *
 * 尺寸（实测标定，见 reference/math-physics.md）：
 *   嵌套分式墨迹高 ≈ 2.59 × fontSize；单层公式 ≈ 1.2 × fontSize。
 *   要满足「结果项 ink ≥72px」→ 嵌套分式 fontSize ≥28；「大字 ≥96」→ ≥37；「主角 ≥170」→ ≥66。
 *
 * ⚠ 配色走 SVG 的 `currentColor`：**设置外层 div 的 `color` 即可**，不要试图改 SVG 内部。
 * ⚠ 缩放走根 <svg> 的 `ex` 单位：**设置外层 div 的 `fontSize` 即可**，不要覆盖 svg 的 width/height。
 * ⚠ 同一帧可以安全渲染多条公式：每条公式的 SVG id 前缀唯一（MJX-1…MJX-N），不会互相串字形。
 */

export type MathFormulaProps = {
  /** `scripts/gen_mathjax_svg.mjs` 的 FORMULAS 里的键名，如 'quadratic' */
  name: string;
  /** 外层字号（px）——公式整体随之缩放，换算见文件头 */
  fontSize?: number;
  /** 字色（走 currentColor）：白 / PURPLE / PURPLE_LIGHT / ORANGE… */
  color?: string;
  /** 可选光晕，直接给 CSS filter 值，如 'drop-shadow(0 0 14px rgba(102,45,248,.95))' */
  glow?: string;
  opacity?: number;
  dy?: number;
  style?: React.CSSProperties;
};

export const MathFormula: React.FC<MathFormulaProps> = ({
  name, fontSize = 38, color = '#FFFFFF', glow, opacity = 1, dy = 0, style,
}) => {
  const e = MATHJAX_SVG[name];
  if (!e) return null;
  return (
    <div
      data-formula={name}
      style={{fontSize, color, opacity, lineHeight: 1, transform: dy ? `translateY(${dy}px)` : undefined, filter: glow, ...style}}
      // SVG 自包含 + currentColor，直接内联即可（无外部资源）
      dangerouslySetInnerHTML={{__html: e.svg}}
    />
  );
};

/**
 * 公式揭示：整条公式按进度 `p` **从左向右**显出来（视觉上等价于"逐项写出来"）。
 * 做法是横向裁剪（clip-path inset），确定性纯函数——比按 token 拆多条 SVG 更稳。
 * 需要严格"每 3 帧出一个 token"时，把 TeX 拆成多段分别生成、按顺序逐个 SoftIn。
 */
export const MathFormulaReveal: React.FC<MathFormulaProps & {
  N: number; f0: number; len?: number;
  /** 'wipe' 左→右写出（默认）｜'fade' 整体淡入 + 轻微上浮 */
  mode?: 'wipe' | 'fade';
}> = ({N, f0, len = 24, mode = 'wipe', ...rest}) => {
  const n = N - f0;
  if (n < 0) return null;
  const p = easeOutCubic(clamp01(n / len));
  if (mode === 'fade') {
    return <MathFormula {...rest} opacity={(rest.opacity ?? 1) * p} dy={(rest.dy ?? 0) + 10 * (1 - p)} />;
  }
  return (
    <div style={{clipPath: `inset(0 ${((1 - p) * 100).toFixed(2)}% 0 0)`, WebkitClipPath: `inset(0 ${((1 - p) * 100).toFixed(2)}% 0 0)`}}>
      <MathFormula {...rest} opacity={(rest.opacity ?? 1) * clamp01(p * 4)} />
    </div>
  );
};

/** 已生成的公式名单（写分镜/派单时用它核对键名；也可用于文档与自检） */
export const FORMULA_NAMES: string[] = Object.keys(MATHJAX_SVG);
/** 取某条公式的 TeX 源码（出镜标注/事实核对用） */
export const formulaTex = (name: string): string => MATHJAX_SVG[name]?.tex ?? '';
