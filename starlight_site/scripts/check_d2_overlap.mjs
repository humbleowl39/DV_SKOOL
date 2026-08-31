#!/usr/bin/env node
/**
 * 생성된 d2 SVG에서 라벨끼리 겹쳐 읽을 수 없게 된 곳을 찾는다.
 *
 * d2/elk는 도형 배치는 충돌 없이 잘 풀지만, **연결선(edge) 라벨**은
 * 서로의 폭을 고려하지 않고 선 중앙에 그냥 놓는다. 그래서 평행한 두 간선에
 * 긴 라벨이 달리면 같은 높이에서 좌우로 겹친다.
 *
 * 폰트 메트릭이 없으므로 문자 종류별 평균 폭으로 텍스트 폭을 추정한다.
 * 겹침 판정은 보수적으로 — 실제로 읽기 어려운 수준(겹침 폭이 좁은 쪽의
 * MIN_OVERLAP_FRAC 이상)만 보고한다.
 *
 * 사용법 (starlight_site/ 에서):
 *   node scripts/check_d2_overlap.mjs --all
 *   node scripts/check_d2_overlap.mjs public/d2/docs/hbm4_jedec_dd
 */
import fs from 'node:fs/promises'
import path from 'node:path'

const SITE = path.resolve(process.argv[1], '../..')
const D2_ROOT = path.join(SITE, 'public/d2/docs')
const MIN_OVERLAP_FRAC = 0.15 // 좁은 쪽 폭의 15% 이상 겹치면 보고
const BASELINE_TOL = 0.7 // 같은 줄로 볼 y 차이 (font-size 배수)

const args = process.argv.slice(2)

/** 문자 종류별 폭 계수 (em 단위). CJK·기호는 전각, 라틴은 반각 취급 */
function textWidth(s, fontSize) {
  let em = 0
  for (const ch of s) {
    const c = ch.codePointAt(0)
    if (c >= 0x1100 && c <= 0x11ff) em += 1.0          // 한글 자모
    else if (c >= 0x2e80 && c <= 0xa4cf) em += 1.0      // CJK 부수·한자
    else if (c >= 0xac00 && c <= 0xd7a3) em += 1.0      // 한글 음절
    else if (c >= 0xf900 && c <= 0xfaff) em += 1.0
    else if (c >= 0xfe30 && c <= 0xfe4f) em += 1.0
    else if (c >= 0xff00 && c <= 0xff60) em += 1.0      // 전각 라틴
    else if (c === 0x2014 || c === 0x2013) em += 1.0    // em/en dash
    else if (ch === ' ') em += 0.30
    else if (/[iljI.,:;'`|!]/.test(ch)) em += 0.28
    else if (/[A-Z0-9]/.test(ch)) em += 0.62
    else em += 0.53
  }
  return em * fontSize
}

async function* walk(dir) {
  for (const e of await fs.readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) yield* walk(p)
    else if (e.name.endsWith('.svg')) yield p
  }
}

let targets = []
if (args.includes('--all') || args.length === 0) {
  for await (const f of walk(D2_ROOT)) targets.push(f)
} else {
  for (const a of args) {
    const p = path.resolve(a)
    const st = await fs.stat(p).catch(() => null)
    if (!st) continue
    if (st.isDirectory()) { for await (const f of walk(p)) targets.push(f) }
    else targets.push(p)
  }
}
targets.sort()

const TEXT = /<text\b([^>]*)>([\s\S]*?)<\/text>/g
const TSPAN = /<tspan\b([^>]*)>([^<]*)<\/tspan>/g
function attr(tag, name) {
  const m = new RegExp(`${name}="([^"]*)"`).exec(tag)
  return m ? m[1] : null
}

let checked = 0
let failures = 0
const hitFiles = new Set()

for (const file of targets) {
  const svg = await fs.readFile(file, 'utf8')
  const items = []
  for (const m of svg.matchAll(TEXT)) {
    const tag = m[1]
    const body = m[2]
    const x = parseFloat(attr(tag, 'x'))
    const y = parseFloat(attr(tag, 'y'))
    if (!Number.isFinite(y)) continue
    const style = attr(tag, 'style') || ''
    const fs_ = parseFloat((/font-size:\s*([\d.]+)px/.exec(style) || [])[1] || '16')
    const anchor = (/text-anchor:\s*(\w+)/.exec(style) || [])[1] || 'start'

    // 여러 줄 라벨은 <tspan> 으로 쪼개진다. 각 tspan 이 한 줄이며
    // 자체 x 와 이전 줄 대비 dy 를 갖는다.
    const spans = [...body.matchAll(TSPAN)]
    const lines = []
    if (spans.length) {
      let cy = y
      for (const sp of spans) {
        const stag = sp[1]
        const dy = parseFloat(attr(stag, 'dy'))
        if (Number.isFinite(dy)) cy += dy
        const sx = parseFloat(attr(stag, 'x'))
        lines.push({ text: sp[2].trim(), x: Number.isFinite(sx) ? sx : x, y: cy })
      }
    } else {
      lines.push({ text: body.trim(), x, y })
    }

    for (const ln of lines) {
      if (!ln.text || !Number.isFinite(ln.x)) continue
      const w = textWidth(ln.text, fs_)
      const x0 = anchor === 'middle' ? ln.x - w / 2 : anchor === 'end' ? ln.x - w : ln.x
      items.push({ label: ln.text, x0, x1: x0 + w, y: ln.y, fs: fs_, w })
    }
  }

  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i], b = items[j]
      const tol = Math.max(a.fs, b.fs) * BASELINE_TOL
      if (Math.abs(a.y - b.y) > tol) continue
      checked++
      const ov = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0)
      if (ov <= 0) continue
      const frac = ov / Math.min(a.w, b.w)
      if (frac < MIN_OVERLAP_FRAC) continue
      failures++
      hitFiles.add(file)
      const rel = path.relative(D2_ROOT, file)
      console.log(
        `  ✗ ${rel}  y=${a.y.toFixed(0)} 겹침 ${ov.toFixed(0)}px (${(frac * 100).toFixed(0)}%)\n` +
        `      "${a.label.slice(0, 38)}"  ×  "${b.label.slice(0, 38)}"`,
      )
    }
  }
}
console.log(`\n같은 줄 쌍 ${checked}건 검사 · 겹침 ${failures}건 · 해당 파일 ${hitFiles.size}개`)
process.exit(failures ? 1 : 0)
