// 生成 MathJax TeX → SVG（自包含，fontCache:'local'），输出 src/common/mathjax_svg.ts 供 Remotion 内联渲染。
//
// 用法：
//   npm i                     （首次；需要 devDependency mathjax-full）
//   node scripts/gen_mathjax_svg.mjs
//
// 加新公式：把一条 `键名: String.raw`...`` 加进下面的 FORMULAS，重跑本脚本，提交生成物。
// 为什么在构建期生成而不是运行期：MathJax 有 40MB，运行期只用生成好的 SVG 字符串 →
// 片子 bundle 里不带 MathJax、不需要 LaTeX、不需要字体文件、渲染逐字节可复现。
import {mathjax} from 'mathjax-full/js/mathjax.js';
import {TeX} from 'mathjax-full/js/input/tex.js';
import {SVG} from 'mathjax-full/js/output/svg.js';
import {liteAdaptor} from 'mathjax-full/js/adaptors/liteAdaptor.js';
import {RegisterHTMLHandler} from 'mathjax-full/js/handlers/html.js';
import {AllPackages} from 'mathjax-full/js/input/tex/AllPackages.js';
import fs from 'node:fs';

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({packages: AllPackages});
// fontCache:'local' → 每个 SVG 自带 <defs>，不依赖外部字体文件、不依赖页面级共享缓存
const svg = new SVG({fontCache: 'local'});
const doc = mathjax.document('', {InputJax: tex, OutputJax: svg});

const FORMULAS = {
  // ── 代数 / 基础 ────────────────────────────────────────────
  quadratic: String.raw`\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}`,
  pythagoras: String.raw`a^{2}+b^{2}=c^{2}`,
  logProduct: String.raw`\log(xy)=\log x+\log y`,
  binomial: String.raw`(a+b)^{2}=a^{2}+2ab+b^{2}`,

  // ── 微积分 ─────────────────────────────────────────────────
  limit: String.raw`\lim_{x\to0}\frac{\sin x}{x}=1`,
  derivDef: String.raw`f'(x)=\lim_{\Delta x\to0}\frac{f(x+\Delta x)-f(x)}{\Delta x}`,
  chainRule: String.raw`\frac{d}{dx}f(g(x))=f'(g(x))\cdot g'(x)`,
  integralDef: String.raw`\int_{a}^{b}f(x)\,dx=\lim_{n\to\infty}\sum_{i=1}^{n}f(x_{i})\,\Delta x`,
  ftc: String.raw`\int_{a}^{b}f'(x)\,dx=f(b)-f(a)`,
  gaussInt: String.raw`\int_{0}^{\infty} e^{-x^{2}}\,dx=\frac{\sqrt{\pi}}{2}`,
  basel: String.raw`\sum_{n=1}^{\infty}\frac{1}{n^{2}}=\frac{\pi^{2}}{6}`,
  taylor: String.raw`f(x)=\sum_{n=0}^{\infty}\frac{f^{(n)}(a)}{n!}(x-a)^{n}`,
  eulerIdentity: String.raw`e^{i\pi}+1=0`,

  // ── 三角 / 复数 ────────────────────────────────────────────
  eulerFormula: String.raw`e^{i\theta}=\cos\theta+i\sin\theta`,
  sinSum: String.raw`\sin(\alpha+\beta)=\sin\alpha\cos\beta+\cos\alpha\sin\beta`,
  phasor: String.raw`A\cos(\omega t+\varphi)=\operatorname{Re}\!\left(Ae^{i(\omega t+\varphi)}\right)`,

  // ── 傅里叶（样片主题）──────────────────────────────────────
  fourierSeries: String.raw`f(t)=a_{0}+\sum_{n=1}^{\infty}\left(a_{n}\cos n\omega t+b_{n}\sin n\omega t\right)`,
  fourierCoeffA: String.raw`a_{n}=\frac{2}{T}\int_{0}^{T}f(t)\cos n\omega t\,dt`,
  fourierCoeffB: String.raw`b_{n}=\frac{2}{T}\int_{0}^{T}f(t)\sin n\omega t\,dt`,
  fourierTransform: String.raw`\hat{f}(\xi)=\int_{-\infty}^{\infty}f(t)\,e^{-2\pi i\xi t}\,dt`,
  fourierInverse: String.raw`f(t)=\int_{-\infty}^{\infty}\hat{f}(\xi)\,e^{2\pi i\xi t}\,d\xi`,
  convolution: String.raw`\widehat{f*g}=\hat{f}\cdot\hat{g}`,
  parseval: String.raw`\int_{-\infty}^{\infty}|f(t)|^{2}dt=\int_{-\infty}^{\infty}|\hat{f}(\xi)|^{2}d\xi`,
  squareWave: String.raw`\frac{4}{\pi}\sum_{k=1,3,5,\dots}\frac{1}{k}\sin(k\omega t)`,

  // ── 物理：电磁 ─────────────────────────────────────────────
  maxwellGaussE: String.raw`\nabla\cdot\vec{E}=\frac{\rho}{\varepsilon_{0}}`,
  maxwellFaraday: String.raw`\nabla\times\vec{E}=-\frac{\partial\vec{B}}{\partial t}`,
  maxwellAmpere: String.raw`\nabla\times\vec{B}=\mu_{0}\vec{J}+\mu_{0}\varepsilon_{0}\frac{\partial\vec{E}}{\partial t}`,
  maxwellGaussB: String.raw`\nabla\cdot\vec{B}=0`,
  coulomb: String.raw`\vec{F}=\frac{1}{4\pi\varepsilon_{0}}\frac{q_{1}q_{2}}{r^{2}}\hat{r}`,
  lorentz: String.raw`\vec{F}=q\left(\vec{E}+\vec{v}\times\vec{B}\right)`,
  faradayIntegral: String.raw`\oint_{\partial S}\vec{E}\cdot d\vec{l}=-\frac{d\Phi_{B}}{dt}`,
  capacitance: String.raw`C=\frac{Q}{V},\qquad U=\frac{1}{2}CV^{2}`,
  rcCharge: String.raw`q(t)=Q\left(1-e^{-t/RC}\right)`,

  // ── 物理：波 / 量子 / 其它 ─────────────────────────────────
  waveEquation: String.raw`\frac{\partial^{2}u}{\partial t^{2}}=c^{2}\nabla^{2}u`,
  schrodinger: String.raw`i\hbar\frac{\partial}{\partial t}\Psi=\hat{H}\Psi`,
  planck: String.raw`E=h\nu=\frac{hc}{\lambda}`,
  ohmsLaw: String.raw`V=IR`,
  sci: String.raw`m=9.11\times10^{-31}\,\mathrm{kg}`,

  // ── 线性代数 ───────────────────────────────────────────────
  matrix2x2: String.raw`\begin{pmatrix} a & b \\ c & d \end{pmatrix}`,
  determinant: String.raw`\det\begin{pmatrix} a & b \\ c & d \end{pmatrix}=ad-bc`,
  eigen: String.raw`A\vec{v}=\lambda\vec{v}`,
  rotation: String.raw`R(\theta)=\begin{pmatrix}\cos\theta & -\sin\theta\\ \sin\theta & \cos\theta\end{pmatrix}`,

  // ── 排版疑难样式（回归检查用）──────────────────────────────
  casesAbs: String.raw`|x|=\begin{cases} x & x\ge 0 \\ -x & x<0 \end{cases}`,
  nestedFrac: String.raw`\frac{\sqrt{\pi}}{2}+\frac{\frac{a}{b}}{\frac{c}{d}}`,
  bigO: String.raw`T(n)=O(n\log n)`,
  gaborLimit: String.raw`\sigma_{t}\,\sigma_{f}\;\ge\;\frac{1}{4\pi}`,          // 时频精度不能同时要好
  dct: String.raw`X_{k}=\sum_{n=0}^{N-1}x_{n}\cos\!\left[\frac{\pi}{N}\left(n+\tfrac{1}{2}\right)k\right]`,  // JPEG 用的余弦变换
  nSquared: String.raw`O(n^{2})`,
  nLogN: String.raw`O(n\log n)`,
  sumLimit: String.raw`\lim_{n\to\infty}\frac{1}{n}\sum_{k=1}^{n}f\!\left(\frac{k}{n}\right)=\int_{0}^{1}f(x)\,dx`,
};

const out = {};
for (const [k, v] of Object.entries(FORMULAS)) {
  const node = doc.convert(v, {display: true, em: 16, ex: 8, containerWidth: 1200});
  let s = adaptor.outerHTML(node);
  // 去掉固定 style，尺寸交给外层 CSS（fontSize 缩放 ex）
  s = s.replace(/\sstyle="[^"]*"/, '');
  out[k] = {tex: v, svg: s};
}

fs.mkdirSync('src/common', {recursive: true});
fs.writeFileSync(
  'src/common/mathjax_svg.ts',
  '// 由 scripts/gen_mathjax_svg.mjs 生成，请勿手改；加公式改脚本的 FORMULAS 后重跑\n' +
    'export type MathJaxEntry = {tex: string; svg: string};\n' +
    'export const MATHJAX_SVG: Record<string, MathJaxEntry> = ' +
    JSON.stringify(out, null, 2) +
    ' as const;\n'
);

let bad = 0;
for (const [k, v] of Object.entries(out)) {
  const urls = (v.svg.match(/url\(/g) || []).length;
  const external = v.svg.replace(/xmlns(:\w+)?="[^"]*"/g, '').includes('http');
  if (urls || external) { bad++; console.log(`  ✗ ${k}: url()=${urls} external=${external}`); }
}
console.log(`${Object.keys(out).length} 条公式已写入 src/common/mathjax_svg.ts`);
console.log(bad ? `✗ ${bad} 条含外部引用（不合格）` : `✓ 全部自包含（0 个 url() 引用、0 处外链）`);
