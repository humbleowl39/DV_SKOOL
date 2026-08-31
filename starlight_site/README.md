# DV SKOOL — 사이트 빌드 가이드

Astro + Starlight 기반 정적 사이트. 콘텐츠는 `src/content/docs/<topic>/`,
배포는 `.github/workflows/deploy.yml`(Node 22)가 `main` 푸시마다 수행한다.

## 구조

```
src/content/docs/<topic>/       # 토픽별 챕터 (.md / .mdx)
  ├── index.mdx                 # 토픽 표지
  ├── NN_<slug>.md              # 본문 챕터
  └── quiz/NN_<slug>_quiz.md    # 짝 퀴즈
public/d2/docs/<topic>/         # d2 다이어그램 SVG (커밋 대상)
scripts/                        # d2 생성·검사 도구
astro.config.mjs                # 사이드바 등록 · astro-d2 설정
```

## 명령

| 명령 | 설명 |
| :-- | :-- |
| `npm run dev` | 로컬 개발 서버 (`localhost:4321`) |
| **`CI=true npx astro build`** | **빌드는 반드시 이 형태로** (아래 참조) |
| `node scripts/gen_d2.mjs --all` | d2 SVG 전체 생성 (`--topic <name>` / 파일 경로도 가능) |
| `node scripts/check_d2_overlap.mjs --all` | 라벨 겹침 검사 |
| `node scripts/check_d2_contrast.mjs --all` | 라이트/다크 대비 검사 |

Node는 v22가 필요하다: `export PATH="$HOME/.nvm/versions/node/v22.22.3/bin:$PATH"`

---

## ⚠️ 로컬 빌드는 반드시 `CI=true`

```bash
CI=true npx astro build      # ✅
npx astro build              # ❌ public/d2 의 SVG 를 전부 파괴한다
```

`astro.config.mjs` 의 `skipGeneration: !!process.env.CI` 때문이다. 로컬에는 `CI` 가
없으므로 astro-d2 가 **직접 재생성 모드**로 동작하며 출력 디렉터리를 먼저 비운다.
그런데 astro-d2 내부 경로는 다이어그램 1개에 7분 이상 걸려 650여 개는 완주가 불가능하다.

실수로 돌렸다면: 빌드를 중단하고 `git checkout -- starlight_site/public/d2/` 로 복구한 뒤,
그 작업에서 새로 만든 SVG 만 `scripts/gen_d2.mjs`(d2 바이너리, 0.7초/개)로 다시 생성한다.

`CI=true` 는 GitHub Actions 가 실제로 쓰는 경로이기도 하므로, 로컬 검증과 CI 가 일치한다.

---

## d2 다이어그램 규칙

SVG 는 `scripts/gen_d2.mjs`(d2 바이너리)로 생성해 **커밋한다**. CI 는 생성하지 않는다.
`.md` 의 d2 블록을 고쳤으면 해당 파일을 재생성하고 두 검사기를 통과시킨 뒤 커밋한다.

### 1. 라벨에 마크다운·HTML 을 쓰지 않는다

d2 는 일반 라벨에서 마크다운을 처리하지 **않는다**(`|md |` 블록에서만 처리).
아래는 전부 화면에 글자 그대로 나온다.

| 쓰면 안 되는 것 | 화면 출력 |
| :-- | :-- |
| `"**Bold**"` | `**Bold**` |
| `"*강조*"` · `"_강조_"` | `*강조*` · `_강조_` |
| `` "`code`" `` | `` `code` `` |
| `"&nbsp;&nbsp;들여쓰기"` | `&nbsp;&nbsp;들여쓰기` |

강조가 필요하면 `style.bold: true` 나 색을 쓰고, 들여쓰기는 **실제 U+00A0 문자**를 넣는다.
SVG 는 XML 이라 HTML 엔티티가 정의되어 있지 않다.

단, `*` 가 마크다운이 아닌 경우는 건드리지 말 것 —
`m_qp_tracker[*][*]`(SV 연관배열), `'*.env.agent.*'`(config_db 경로 글롭).

### 2. 흐름도에 `grid-*` 를 쓰지 않는다

`grid-rows` / `grid-columns` 는 **간선을 고려하지 않고 노드를 배치**한다. 결과적으로
화살표가 전부 교차하고 간선 라벨이 노드 박스 위에 찍힌다. 선언 순서와 채우기 방향이
어긋나 논리적 그룹이 뒤섞이기도 한다.

흐름이 있는 그림은 **컨테이너 + elk** 로 표현한다. 그리드는 흐름 없는 격자 표에만 쓴다.

### 3. 간선 라벨은 짧게, 길면 접는다

d2/elk 는 도형은 충돌 없이 배치하지만 **간선 라벨은 서로의 폭을 고려하지 않고** 선 중앙에
놓는다. 평행·역평행 간선에 긴 라벨이 달리면 겹친다.

- 긴 라벨은 `\n` 으로 접어 폭을 줄인다
- 같은 라벨을 두 간선에 반복하지 말고 구분되는 짧은 값을 쓴다 (`PC = 0` / `PC = 1`)
- 접기로 해결되지 않으면 라벨이 **다른 노드 위로 옮겨간 것**일 수 있다 — 이때는 접기가 아니라
  레이아웃(대개 `grid-*`)을 고쳐야 한다

### 4. 컨테이너 중첩은 3단까지

d2 바이너리는 **4단 중첩 컨테이너에서 조용히 실패한다** — `exit 0` 을 반환하면서 파일을
아예 쓰지 않아 옛 SVG 가 그대로 남는다. `scripts/gen_d2.mjs` 가 이를 검출해
`⚠ 실패 N개` 를 출력하고 `exit 1` 로 끝내므로, **생성 결과의 종료 코드를 확인할 것.**

깊어지면 최상위 컨테이너를 형제 노드로 빼고 화살표로 연결한다.

### 5. 커스텀 배경에는 글자색을 함께 지정한다

`style.fill` 은 인라인 고정 색이 되지만 라벨 색은 테마 클래스라 다크 모드에서 뒤집힌다.
`style.fill` 을 주면 `style.font-color` 도 같이 준다.

간선 라벨은 **채워진 컨테이너 안에 있을 때만** `style.font-color` 를 고정한다.
캔버스 위의 간선 라벨에 고정하면 다크 모드에서 배경과 같은 색이 되어 사라진다.

---

## 콘텐츠 규칙

- 상대 링크: 챕터→챕터 `../NN_slug/`, 챕터→퀴즈 `../quiz/NN_slug_quiz/`,
  챕터→타 토픽 `../../topic/`, `index.mdx` 에서는 `./NN/` · `../topic/`
- 새 토픽은 `astro.config.mjs` 사이드바와 루트 `index.mdx` 카드에 등록한다
- SystemVerilog 예제에 `$display` / `$finish` / `$stop` 금지 — `uvm_info` / `uvm_error` 사용
- 규격 원문(JEDEC 등) PDF 는 **커밋하지 않는다**. 표·그림을 복제하지 말고 절 번호로 인용한다
