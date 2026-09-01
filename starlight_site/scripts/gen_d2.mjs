#!/usr/bin/env node
/**
 * 대상 파일의 d2 블록만 SVG로 생성한다.
 *
 * `npm run build`는 astro-d2가 전 토픽의 d2를 한 번에 렌더링하므로 메모리 압박으로
 * 중단되기 쉽고, 중단되면 다른 토픽의 SVG까지 삭제·훼손된다. 이 스크립트는 지정한
 * 파일만 처리해 그 위험을 없앤다.
 *
 * 기본 엔진은 d2 **바이너리**다. astro.config.mjs는 experimental.useD2js(WASM)를 쓰지만
 * WASM은 다이어그램 1개에 수 분이 걸린다. 두 엔진의 출력이 동일한지는
 * `--verify`로 확인할 수 있다(도형/텍스트 수 비교). HBM 토픽 15개 기준 전부 일치했다.
 *
 * 출력 경로·파일명은 astro-d2(libs/remark.ts getOutputPaths)와 동일하다:
 *   src/content/docs/<topic>/<name>.md  ->  public/d2/docs/<topic>/<name>-<i>.svg
 *
 * 사용법 (starlight_site/ 에서):
 *   node scripts/gen_d2.mjs --topic hbm --topic hbm_dv
 *   node scripts/gen_d2.mjs src/content/docs/hbm/03_stack_architecture.md
 *   node scripts/gen_d2.mjs --all
 *   node scripts/gen_d2.mjs --check --topic hbm     # 생성 없이 대상만 출력
 */
import fs from 'node:fs/promises'
import path from 'node:path'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import os from 'node:os'

const execFileAsync = promisify(execFile)

const SITE = path.resolve(process.argv[1], '../..') // starlight_site/
const CONTENT = path.join(SITE, 'src/content')
const OUT_ROOT = path.join(SITE, 'public/d2')

// astro.config.mjs의 d2({...})와 반드시 일치시킬 것
const OPTS = { layout: 'elk', theme: '0', darkTheme: '200', sketch: 'false', pad: '20' }

const args = process.argv.slice(2)
const checkOnly = args.includes('--check')
const wantAll = args.includes('--all')
const topics = args.filter((a, i) => args[i - 1] === '--topic')
const explicit = args.filter((a, i) => !a.startsWith('--') && args[i - 1] !== '--topic')

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
  const docs = path.join(CONTENT, 'docs')
  if (explicit.length) return explicit.map((p) => path.resolve(p))
  if (wantAll) return walk(docs)
  if (topics.length) {
    const out = []
    for (const t of topics) out.push(...(await walk(path.join(docs, t))))
    return out
  }
  console.error('대상이 없습니다. 파일 경로 / --topic <name> / --all 중 하나를 주세요.')
  process.exit(1)
}

/** ```d2 펜스 블록 본문을 등장 순서대로 반환 */
function extractD2Blocks(src) {
  const blocks = []
  let open = false
  let buf = []
  for (const line of src.split('\n')) {
    if (!open && /^```d2(\s|$)/.test(line)) { open = true; buf = []; continue }
    if (open && /^```\s*$/.test(line)) { open = false; blocks.push(buf.join('\n')); continue }
    if (open) buf.push(line)
  }
  return blocks
}

function outPathFor(file, index) {
  const rel = path.relative(CONTENT, file)
  const p = path.parse(rel)
  return path.join(OUT_ROOT, p.dir, `${p.name}-${index}.svg`)
}

const files = await targets()
// d2 예약어를 노드 키로 쓰면 **조용히 깨진다** — exit 0, 경고 없음.
// 리프 노드면 라벨이 사라지고 키워드가 소문자로 표시되며,
// 컨테이너면 자식 노드가 통째로 없어진다.
// 실측으로 확인된 위험 키워드만 담았다 (bottom/right/center/style/shape/grid 는 안전).
const D2_RESERVED_KEYS = new Set(['top', 'left', 'near', 'label', 'class', 'link'])

/** d2 소스에서 예약어를 노드 키로 쓴 줄을 찾는다. 없으면 빈 배열. */
function findReservedKeys(src) {
  const found = []
  src.split('\n').forEach((raw, idx) => {
    const line = raw.trim()
    if (!line || line.startsWith('#')) return
    const decl = line.match(/^([A-Za-z_][\w-]*)\s*:\s*"/) || line.match(/^([A-Za-z_][\w-]*)\s*:?\s*\{/)
    if (decl && D2_RESERVED_KEYS.has(decl[1].toLowerCase())) {
      // 컨테이너 안의 `label: "..."` 는 정당한 속성이므로 들여쓰기가 있으면 통과
      const indented = /^\s/.test(raw)
      if (!(indented && decl[1].toLowerCase() === 'label')) {
        found.push({ line: idx + 1, key: decl[1], text: line.slice(0, 60) })
        return
      }
    }
    for (const m of line.matchAll(/(?:^|\s)([A-Za-z_][\w.-]*)\s*(?:->|--|<->)\s*([A-Za-z_][\w.-]*)/g)) {
      for (const g of [m[1], m[2]]) {
        if (D2_RESERVED_KEYS.has(g.split('.')[0].toLowerCase())) {
          found.push({ line: idx + 1, key: g, text: line.slice(0, 60) })
          return
        }
      }
    }
  })
  return found
}

const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'gend2-'))
let made = 0
let scanned = 0
let broken = 0
const mtimes = new Map()

for (const file of files) {
  const blocks = extractD2Blocks(await fs.readFile(file, 'utf8'))
  if (!blocks.length) continue
  scanned++
  for (const [i, input] of blocks.entries()) {
    const outputPath = outPathFor(file, i)
    const reserved = findReservedKeys(input)
    if (reserved.length) {
      for (const r of reserved) {
        console.log(`  \u2717 d2 예약어를 노드 키로 사용: '${r.key}' \u2014 ${path.relative(SITE, file)} 블록 ${i} 줄 ${r.line}`)
        console.log(`      ${r.text}`)
      }
      console.log('      \u2192 키 이름을 바꾸세요. 예약어는 조용히 노드를 삼킵니다 (top/left/near/label/class/link)')
      broken++
      continue
    }
    try { mtimes.set(outputPath, (await fs.stat(outputPath)).mtimeMs) } catch {}
    if (checkOnly) { console.log('  would write', path.relative(SITE, outputPath)); continue }
    const src = path.join(tmp, `d-${made}.d2`)
    await fs.writeFile(src, input)
    await fs.mkdir(path.dirname(outputPath), { recursive: true })
    await execFileAsync('d2', [
      `--layout=${OPTS.layout}`,
      `--theme=${OPTS.theme}`,
      `--dark-theme=${OPTS.darkTheme}`,
      `--sketch=${OPTS.sketch}`,
      `--pad=${OPTS.pad}`,
      src,
      outputPath,
    ])
    made++
    // d2 바이너리는 깊게 중첩된 라벨 컨테이너에서 **조용히 실패**한다 —
    // exit 0 을 반환하면서 파일을 아예 쓰지 않거나, 도형/글자가 없는 빈 SVG 를 남긴다.
    // 그대로 두면 옛 파일이 살아남아 "생성됨"으로 오인되므로 여기서 잡는다.
    const before = mtimes.get(outputPath)
    let stat = null
    try { stat = await fs.stat(outputPath) } catch {}
    if (!stat) {
      console.log('  ✗ 실패(파일 미생성)', path.relative(SITE, outputPath))
      broken++
      continue
    }
    if (before !== undefined && stat.mtimeMs === before) {
      console.log('  ✗ 실패(파일 갱신 안 됨 — d2 가 조용히 no-op)', path.relative(SITE, outputPath))
      broken++
      continue
    }
    const out = await fs.readFile(outputPath, 'utf8')
    const nText = (out.match(/<text\b/g) || []).length
    if (nText === 0) {
      console.log('  ✗ 실패(글자 없는 빈 SVG)', path.relative(SITE, outputPath))
      broken++
      continue
    }
    console.log('  wrote', path.relative(SITE, outputPath), `(${stat.size} bytes)`)
  }
}

console.log(`\n파일 ${scanned}개 · ${checkOnly ? '(check only)' : `다이어그램 ${made}개 생성`}${broken ? ` · ⚠ 실패 ${broken}개` : ''}`)
if (broken) process.exit(1)
