#!/usr/bin/env node
/**
 * d2 블록의 텍스트 대비를 고친다.
 *
 * 문제: d2 도형에 `style.fill`을 하드코딩하면 그 값은 SVG에 inline `fill=` 속성으로
 * 박히지만, 라벨 텍스트는 테마 클래스(`fill-N1`/`fill-N2`)를 쓴다. astro-d2는
 * `@media (prefers-color-scheme: dark)`에서 그 클래스를 밝은 색으로 바꾸므로,
 * 다크 모드에서 **밝은 텍스트 + 밝은 고정 배경**이 되어 라벨이 보이지 않는다.
 * (`#333` 같은 어두운 fill은 반대로 라이트 모드에서 안 보인다.)
 *
 * 해결: `style.fill`이 있는 도형에 `style.font-color`를 함께 지정해 배경과 대비되는
 * 값으로 고정한다. 라이트 모드 색상(#0A0F25 = d2 theme-0의 N1)을 그대로 쓰므로
 * 라이트 모드 렌더링은 바뀌지 않는다.
 *
 * fill이 없는 도형(테마 기본 배경)과 연결선 라벨(캔버스 위)은 배경도 테마를 따르므로
 * 손대지 않는다.
 *
 * 사용법 (starlight_site/ 에서):
 *   node scripts/fix_d2_contrast.mjs --dry-run --topic hbm
 *   node scripts/fix_d2_contrast.mjs --topic hbm --topic hbm_dv
 *   node scripts/fix_d2_contrast.mjs --all
 */
import fs from 'node:fs/promises'
import path from 'node:path'

const SITE = path.resolve(process.argv[1], '../..')
const DOCS = path.join(SITE, 'src/content/docs')

const DARK_TEXT = '#0A0F25' // d2 theme 0 (Neutral default) N1 — 라이트 모드와 동일
const LIGHT_TEXT = '#FFFFFF'

const args = process.argv.slice(2)
const dryRun = args.includes('--dry-run')
const wantAll = args.includes('--all')
const topics = args.filter((a, i) => args[i - 1] === '--topic')
const explicit = args.filter((a, i) => !a.startsWith('--') && args[i - 1] !== '--topic')

/** sRGB 상대 휘도 — 밝으면 어두운 글자, 어두우면 흰 글자 */
function textColorFor(hex) {
  let h = hex.replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  if (h.length !== 6) return DARK_TEXT
  const ch = [0, 2, 4].map((i) => {
    const v = parseInt(h.slice(i, i + 2), 16) / 255
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
  })
  const L = 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
  return L > 0.5 ? DARK_TEXT : LIGHT_TEXT
}

async function walk(dir) {
  const out = []
  for (const e of await fs.readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) out.push(...(await walk(p)))
    else if (/\.mdx?$/.test(e.name)) out.push(p)
  }
  return out
}

async function targets() {
  if (explicit.length) return explicit.map((p) => path.resolve(p))
  if (wantAll) return walk(DOCS)
  if (topics.length) {
    const out = []
    for (const t of topics) out.push(...(await walk(path.join(DOCS, t))))
    return out
  }
  console.error('대상이 없습니다. 파일 경로 / --topic <name> / --all 중 하나를 주세요.')
  process.exit(1)
}

const FILL = /style\.fill:\s*"(#[0-9A-Fa-f]{3,6})"/

/**
 * 멱등: 같은 줄이나 바로 다음 줄에 이미 font-color가 있으면 건드리지 않는다.
 * (블록 형태에서는 다음 줄에 삽입하므로 같은 줄만 보면 재실행 시 중복된다.)
 */
function patchLine(line, nextLine) {
  if (line.includes('style.font-color')) return { line, n: 0 }
  const m = FILL.exec(line)
  if (!m) return { line, n: 0 }
  if (nextLine && nextLine.includes('style.font-color')) return { line, n: 0 }
  const color = textColorFor(m[1])
  const decl = `style.font-color: "${color}"`
  // fill 선언이 그 줄에 홀로 있으면 같은 들여쓰기로 다음 줄에 추가
  if (line.trim() === m[0]) {
    const indent = line.slice(0, line.length - line.trimStart().length)
    return { line: `${line}\n${indent}${decl}`, n: 1 }
  }
  // 한 줄 안에 다른 선언과 같이 있으면 세미콜론으로 이어 붙인다
  return { line: line.replace(m[0], `${m[0]}; ${decl}`), n: 1 }
}

let totalFiles = 0
let totalDecls = 0

for (const file of await targets()) {
  const src = await fs.readFile(file, 'utf8')
  if (!src.includes('```d2')) continue
  const lines = src.split('\n')
  let inD2 = false
  let changed = 0
  const out = lines.map((line, i) => {
    if (!inD2 && /^```d2(\s|$)/.test(line)) { inD2 = true; return line }
    if (inD2 && /^```\s*$/.test(line)) { inD2 = false; return line }
    if (!inD2) return line
    const r = patchLine(line, lines[i + 1])
    changed += r.n
    return r.line
  })
  if (!changed) continue
  totalFiles++
  totalDecls += changed
  console.log(`  ${path.relative(DOCS, file)}  +${changed}`)
  if (!dryRun) await fs.writeFile(file, out.join('\n'))
}

console.log(`\n${dryRun ? '[dry-run] ' : ''}파일 ${totalFiles}개 · font-color ${totalDecls}개 추가`)
