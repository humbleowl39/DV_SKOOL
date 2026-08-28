#!/usr/bin/env node
/**
 * 생성된 d2 SVG의 라벨 대비를 라이트/다크 양쪽에서 검사한다.
 *
 * 각 <text>가 기하학적으로 어느 도형 안에 있는지 찾아 그 도형의 배경색을 구하고,
 * 텍스트 색과의 WCAG 대비비를 계산한다. 도형 색과 글자 색이 각각
 * inline 속성(테마 무관 고정)일 수도, 테마 클래스(모드에 따라 변함)일 수도 있으므로
 * 두 팔레트를 SVG의 <style>에서 직접 파싱해 각각 적용한다.
 *
 * 사용법 (starlight_site/ 에서):
 *   node scripts/check_d2_contrast.mjs public/d2/docs/hbm public/d2/docs/hbm_dv
 *   node scripts/check_d2_contrast.mjs --all
 */
import fs from 'node:fs/promises'
import path from 'node:path'

const SITE = path.resolve(process.argv[1], '../..')
const D2_ROOT = path.join(SITE, 'public/d2/docs')
const MIN_RATIO = 3.0 // WCAG AA (large text). 다이어그램 라벨은 대체로 굵고 크다.

const args = process.argv.slice(2)

function lin(v) { return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4) }
function lum(hex) {
  let h = String(hex).replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null
  const [r, g, b] = [0, 2, 4].map((i) => lin(parseInt(h.slice(i, i + 2), 16) / 255))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
function ratio(a, b) {
  const [x, y] = [lum(a), lum(b)]
  if (x === null || y === null) return null
  const [hi, lo] = x > y ? [x, y] : [y, x]
  return (hi + 0.05) / (lo + 0.05)
}

/** <style>에서 라이트/다크 팔레트(class -> color)를 뽑는다 */
function palettes(svg) {
  const styles = [...svg.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]).join('\n')
  const cut = styles.indexOf('@media screen and (prefers-color-scheme:dark)')
  const build = (chunk) => {
    const map = {}
    for (const m of chunk.matchAll(/\.(fill-[A-Z0-9]+)\s*\{\s*fill\s*:\s*(#[0-9A-Fa-f]{3,6})/g)) map[m[1]] = m[2]
    return map
  }
  return cut === -1
    ? { light: build(styles), dark: build(styles) }
    : { light: build(styles.slice(0, cut)), dark: build(styles.slice(cut)) }
}

function attr(tag, name) {
  const m = new RegExp(`\\s${name}="([^"]*)"`).exec(tag)
  return m ? m[1] : null
}
function colorOf(tag, pal, fallback) {
  const inline = attr(tag, 'fill')
  if (inline && inline.startsWith('#')) return inline
  if (inline === 'white') return '#FFFFFF'
  if (inline === 'black') return '#000000'
  const cls = (attr(tag, 'class') || '').split(/\s+/).find((c) => c.startsWith('fill-'))
  return (cls && pal[cls]) || fallback
}

async function svgFiles() {
  if (args.includes('--all')) {
    const out = []
    const walk = async (d) => {
      for (const e of await fs.readdir(d, { withFileTypes: true })) {
        const p = path.join(d, e.name)
        if (e.isDirectory()) await walk(p)
        else if (e.name.endsWith('.svg')) out.push(p)
      }
    }
    await walk(D2_ROOT)
    return out
  }
  const out = []
  for (const a of args.filter((x) => !x.startsWith('--'))) {
    const p = path.resolve(a)
    const st = await fs.stat(p)
    if (st.isDirectory()) {
      for (const f of await fs.readdir(p)) if (f.endsWith('.svg')) out.push(path.join(p, f))
    } else out.push(p)
  }
  return out
}

let checked = 0
let failures = 0
for (const file of (await svgFiles()).sort()) {
  const svg = await fs.readFile(file, 'utf8')
  const pal = palettes(svg)
  const body = svg.replace(/<style[\s\S]*?<\/style>/g, '')

  // 배경 도형: 좌표가 있는 rect (마스크용 흑백 rect는 클래스/스타일이 없어 제외하기 어려우므로
  // 캔버스 rect와 동일 크기인 것만 걸러낸다)
  const rects = []
  for (const m of body.matchAll(/<rect[^>]*>/g)) {
    const t = m[0]
    const [x, y, w, h] = ['x', 'y', 'width', 'height'].map((k) => parseFloat(attr(t, k)))
    if ([x, y, w, h].some(Number.isNaN)) continue
    rects.push({ x, y, w, h, tag: t, area: w * h })
  }
  // 원/타원도 배경이 된다 (예: FSM의 INITIAL 노드). 경계 상자로 환산해 함께 다룬다.
  for (const m of body.matchAll(/<(?:ellipse|circle)[^>]*>/g)) {
    const t = m[0]
    const cx = parseFloat(attr(t, 'cx'))
    const cy = parseFloat(attr(t, 'cy'))
    const rx = parseFloat(attr(t, 'rx') ?? attr(t, 'r'))
    const ry = parseFloat(attr(t, 'ry') ?? attr(t, 'r'))
    if ([cx, cy, rx, ry].some(Number.isNaN)) continue
    rects.push({ x: cx - rx, y: cy - ry, w: rx * 2, h: ry * 2, tag: t, area: rx * ry * Math.PI })
  }
  const canvasArea = rects.length ? Math.max(...rects.map((r) => r.area)) : 0

  for (const m of body.matchAll(/<text[^>]*>([\s\S]*?)<\/text>/g)) {
    const tag = m[0].slice(0, m[0].indexOf('>') + 1)
    const label = m[1].replace(/<[^>]*>/g, '').trim()
    if (!label) continue
    const tx = parseFloat(attr(tag, 'x'))
    const ty = parseFloat(attr(tag, 'y'))
    if (Number.isNaN(tx) || Number.isNaN(ty)) continue

    // 텍스트를 포함하는 가장 작은 rect = 실제 배경 (마스크용 black rect는 제외)
    const holders = rects
      .filter((r) => r.area < canvasArea && attr(r.tag, 'fill') !== 'black')
      .filter((r) => tx >= r.x && tx <= r.x + r.w && ty >= r.y - 4 && ty <= r.y + r.h + 4)
      .sort((a, b) => a.area - b.area)
    const holder = holders[0]

    for (const mode of ['light', 'dark']) {
      const p = pal[mode]
      const canvas = p['fill-N7'] || (mode === 'dark' ? '#1E1E2E' : '#FFFFFF')
      const bg = holder ? colorOf(holder.tag, p, canvas) : canvas
      const fg = colorOf(tag, p, p['fill-N1'] || '#000000')
      const r = ratio(fg, bg)
      checked++
      if (r !== null && r < MIN_RATIO) {
        failures++
        const rel = path.relative(D2_ROOT, file)
        console.log(
          `  ✗ ${rel} [${mode}] ratio=${r.toFixed(2)}  fg=${fg} bg=${bg}  "${label.slice(0, 42)}"`,
        )
      }
    }
  }
}
console.log(`\n검사 ${checked}건 · 대비 미달(<${MIN_RATIO}:1) ${failures}건`)
process.exit(failures ? 1 : 0)
