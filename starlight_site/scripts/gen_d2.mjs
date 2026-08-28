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
const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'gend2-'))
let made = 0
let scanned = 0

for (const file of files) {
  const blocks = extractD2Blocks(await fs.readFile(file, 'utf8'))
  if (!blocks.length) continue
  scanned++
  for (const [i, input] of blocks.entries()) {
    const outputPath = outPathFor(file, i)
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
    const { size } = await fs.stat(outputPath)
    console.log('  wrote', path.relative(SITE, outputPath), `(${size} bytes)`)
  }
}

console.log(`\n파일 ${scanned}개 · ${checkOnly ? '(check only)' : `다이어그램 ${made}개 생성`}`)
