# Module 02 — Array & Hash Map

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">📐</span>
    <span class="chapter-back-text">BigTech Algorithm</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-two-sum-한-번-끝까지-따라가기">3. 작은 예 — Two Sum 추적</a>
  <a class="page-toc-link" href="#4-일반화-hash-map-3-가지-용법">4. 일반화 — Hash Map 3 용법</a>
  <a class="page-toc-link" href="#5-디테일-sv-syntax-패턴별-dry-run-코드">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Array 와 Hash Map 의 lookup / insert / delete 의 평균/최악 복잡도를 적을 수 있다.
    - **Explain** Hash collision 이 왜 발생하며 Java/Python/C++ 가 어떻게 다루는지 설명할 수 있다.
    - **Apply** Two-Sum / Has Duplicate / Group Anagrams 같은 전형 문제를 hash map 으로 O(N) 으로 해결할 수 있다.
    - **Analyze** "왜 array 만으론 O(N²) 인 문제가 hash map 으로 O(N) 이 되는가" 를 단계별로 trace 할 수 있다.
    - **Evaluate** Hash map 사용이 부적합한 경우(순서 의존, 메모리 제약, DoS 위험) 를 판단할 수 있다.

!!! info "사전 지식"
    - Module 01 — Big-O 와 패턴 사고법
    - Array indexing, mutability, Python dict / Java HashMap / SV associative array 한 가지 친숙성

---

## 1. Why care? — 이 모듈이 왜 필요한가

LeetCode Easy / Medium 문제의 **30~40 %** 는 hash map 단 하나로 O(N) 풀이가 가능합니다. "이전에 본 적 있는가?" 라는 질문이 등장하면 거의 항상 hash map 후보 — 면접 첫 풀이를 _시작하는 속도_ 가 hash map 신호 인지에 달려 있습니다.

이 모듈을 건너뛰면 이후 Two Pointers / Sliding Window / DFS+memo 같은 패턴이 등장할 때마다 "hash map 이랑 뭐가 다른가" 를 매번 처음부터 비교해야 합니다. 반대로 hash map 의 _key 설계_ 만 명확히 잡고 나면, 이후 모듈이 "hash map 의 _대안_ 또는 _보완_" 으로 자연스럽게 정렬됩니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Hash Map** ≈ **옷장 칸별 보관 — 이름표(key) 를 보고 정해진 칸으로 즉시 찾아감**.<br>
    Brute Force 의 "옷장 전체를 뒤져 찾기" (O(N)) 가, hash map 에서는 "이름표만 hash 해서 그 칸으로 직진" (평균 O(1)) 으로 줄어듭니다. 단, _같은 칸에 여러 옷이 걸리면_ (collision) 그 칸 안에서는 O(M) 까지 떨어질 수 있죠.

### 한 장 그림 — Brute Force vs Hash Map

```
              Brute Force O(n²)                   Hash Map O(n)
              ─────────────────────────           ──────────────────────────
   for i:     ┌─ i=0 ─────────────────┐           seen = {}                
                for j: 1..n            │           
                  검색하며 O(n)        │           for i:
                                       │             complement 계산        
              ┌─ i=1 ─────────────────┐             ┌──────────────────┐
                for j: 2..n            │             │  seen.exists(c)?  │ O(1)
                  검색하며 O(n)        │             │       │           │
                                       │             │   ┌───┴───┐       │
              ┌─ i=2 ... ─────────────┐             │   YES    NO       │
                                       │             │   │      │        │
              ⋮                                          답!   seen[v]=i  
                                                                         
   총 비용:   n × n = O(n²)                       총 비용: n × O(1) = O(n)
```

핵심 변환: **"내부 루프의 검색"** 을 **"hash map 의 O(1) lookup"** 으로 바꾼 것이 전부입니다.

### 왜 이렇게 설계됐는가 — Design rationale

Hash map 은 **"공간을 사 시간을 얻는다"** 는 trade-off 의 가장 직접적인 도구입니다. O(N) 의 추가 메모리를 허용하면, "이 값을 본 적 있는가?" 라는 모든 질문이 평균 O(1) 로 떨어집니다. 면접에서 N=10⁵, 10⁶ 가 주어지면 O(N²) 은 사형선고. 그래서 _첫 30 초_ 에 "이 문제, hash map 으로 lookup 을 O(1) 로 만들 수 있나?" 를 자문하는 것이 표준 절차입니다.

---

## 3. 작은 예 — Two Sum 한 번 끝까지 따라가기

가장 단순한 시나리오. **`nums = [2, 7, 11, 15]`, `target = 9`** 에서 합이 9 인 두 인덱스를 찾기.

### 단계별 추적

```
   index:   0    1    2    3
   value:   2    7   11   15
            ▲    ▲
         정답 [0, 1]  (2 + 7 = 9)

   ┌─ i=0: nums[0]=2 ──────────────────────────────────────┐
   │  complement = 9 - 2 = 7                                │
   │  seen.exists(7) ?  →  NO   (seen 비어 있음)            │
   │  seen[2] = 0                                           │
   │  seen 상태: {2: 0}                                     │
   └────────────────────────────────────────────────────────┘

   ┌─ i=1: nums[1]=7 ──────────────────────────────────────┐
   │  complement = 9 - 7 = 2                                │
   │  seen.exists(2) ?  →  YES  (i=0 에서 저장됨!)          │
   │  답 = [seen[2], 1] = [0, 1]    ⭐                      │
   │  return                                                │
   └────────────────────────────────────────────────────────┘

   → 단 2 번의 iteration 으로 답 도출. n=4 라도 n=10⁶ 라도 동일 패턴.
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|------|------|--------|-----|
| ① | iterator | `i=0` 에서 `nums[0]=2` 읽음 | 단일 루프 (O(n) work) |
| ② | computation | `complement = target - 2 = 7` 계산 | 찾으려는 _짝_ 의 값 |
| ③ | hash lookup | `seen.exists(7)` → NO | O(1) 검색 |
| ④ | hash insert | `seen[2] = 0` (key=값, value=인덱스) | _미래 lookup 을 위해_ 자기를 저장 |
| ⑤ | iterator | `i=1` 에서 `nums[1]=7` 읽음 | 다음 원소 |
| ⑥ | computation | `complement = 9 - 7 = 2` | 짝 |
| ⑦ | hash lookup | `seen.exists(2)` → YES | O(1) hit! |
| ⑧ | answer | `[seen[2], 1] = [0, 1]` 반환 | _이전 인덱스_ 와 _현재 인덱스_ 의 쌍 |

```python
# 위 trace 의 실제 코드. Key = 값, Value = 인덱스 가 핵심.
def two_sum(nums, target):
    seen = {}                       # {value: index}
    for i, v in enumerate(nums):
        complement = target - v
        if complement in seen:      # O(1) lookup
            return [seen[complement], i]
        seen[v] = i                 # 미래 lookup 을 위해 저장
    return []
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Key 가 무엇인가가 풀이의 절반** — 여기서는 _찾고 싶은 값_ (= 배열 원소) 이 key, _부가 정보_ (= 인덱스) 가 value. "이전에 본 적 있는가?" 라는 질문이 곧 `key in map` 으로 1:1 변환됩니다.<br>
    **(2) "자기를 먼저 보지 않는다"** — `seen.exists(complement)` 가 먼저, `seen[v] = i` 가 나중. 순서가 바뀌면 `target = 2*v` 같은 케이스에서 자기 자신과 짝을 이루어 false positive 가 됩니다.

---

## 4. 일반화 — Hash Map 3 가지 용법

### 4.1 신호 → Hash Map 결정 트리

```
   문제를 보고 자문:
   ┌──────────────────────────────────────────────────────┐
   │ "이 값을 이전에 본 적 있는가?" 라는 lookup 이 있나?     │
   └──────┬───────────────────────────────────────────────┘
          │
       ┌──┴──┐
       YES   NO  →  Hash Map 후보 아님 (Two Pointers / DP / 다른 패턴)
       │
       ▼
   ┌────────────────────────────────────────────────────┐
   │ 무엇을 추적하나?                                     │
   │   ① 존재 여부            → Key=값,    Value=index/1 │
   │   ② 빈도(count)         → Key=값,    Value=count   │
   │   ③ 그룹                → Key=불변식, Value=목록    │
   └────────────────────────────────────────────────────┘
```

### 4.2 세 가지 용법 요약

| 용법 | Key 설계 | Value | 대표 문제 |
|---|---|---|---|
| **① 존재 확인** | 찾을 값 | 인덱스 또는 1 | Two Sum, Has Duplicate, Contains Nearby Duplicate |
| **② 빈도 카운트** | 값/문자 | 출현 횟수 | Is Anagram, Most Frequent, Top-K |
| **③ 그룹핑** | 그룹 불변식 (sorted str, char count tuple) | 원본 목록 | Group Anagrams, Subdomain Visit Count |

### 4.3 SV / Python / C++ 의 lookup 시간

| 언어 | 자료구조 | Avg lookup | Worst lookup | Collision 처리 |
|------|---------|-----------|-------------|--------------|
| SystemVerilog | `int seen[int];` (associative array) | O(1) (구현 의존) | O(N) | 시뮬레이터 내부 |
| Python | `dict` (3.7+) | O(1) | O(N) | open addressing + randomized seed |
| Java | `HashMap` | O(1) | O(log N) (Java 8+) | chaining → tree at threshold |
| C++ | `std::unordered_map` | O(1) | O(N) | chaining (보통) |

→ Java 8+ 의 worst-case O(log N) 은 **bucket 이 일정 이상 커지면 linked list → red-black tree** 로 바꾸기 때문 (DoS 방어 목적).

---

## 5. 디테일 — SV Syntax, 패턴별 Dry Run, 코드

### 5.1 SystemVerilog 연관 배열 (Associative Array)

```systemverilog
int seen[int];          // 선언: Key=int, Value=int
seen[key] = val;        // 삽입: O(1)
seen.exists(key);       // 검색: O(1) — KEY를 검색
seen.delete(key);       // 삭제: O(1)
seen.num();             // 크기
foreach (seen[k]) ...   // 순회

주의: exists() 는 KEY 를 검색한다, VALUE 가 아니다!
   seen[7] = 0;
   seen.exists(7);   // 1 (true) — Key 7이 존재
   seen.exists(0);   // 0 (false) — Key 0은 없음 (0 은 Value!)
```

### 5.2 왜 Hash Map 인가 — 비용 비교

```
핵심 질문: "이 값을 이전에 본 적 있는가?"
   → YES → Hash Map 사용

Brute Force:  매번 배열 전체를 검색 → O(n) × n번 = O(n²)
Hash Map:     exists()로 O(1) 검색  → O(1) × n번 = O(n)

핵심: Hash Map 의 Key = 나중에 찾고 싶은 값
```

### 5.3 Key 설계 가이드

```
"이전에 본 적 있는가?" → Key = 값 자체
   예: Two Sum → Key = 배열 값, Value = 인덱스
   예: Has Duplicate → Key = 배열 값, Value = 아무거나 (1)

"빈도를 세야 하는가?" → Key = 값, Value = 카운트
   예: Anagram → Key = 문자, Value = 출현 횟수
   예: Most Frequent → Key = 값, Value = 카운트

"그룹으로 묶어야 하는가?" → Key = 그룹 기준, Value = 목록
   예: Group Anagrams → Key = 정렬된 문자열, Value = 원본 목록
```

### 5.4 Has Duplicate — Dry Run

```
문제: nums 에 중복 값이 있으면 1, 없으면 0

nums = [1, 2, 3, 1]:
   i=0: nums[0]=1, seen.exists(1)? NO → seen[1]=1
   i=1: nums[1]=2, seen.exists(2)? NO → seen[2]=1
   i=2: nums[2]=3, seen.exists(3)? NO → seen[3]=1
   i=3: nums[3]=1, seen.exists(1)? YES! → return 1

nums = [1, 2, 3, 4]:
   모든 원소가 최초 → return 0
```

### 5.5 Is Anagram (LeetCode #242) — Dry Run

```
문제: 두 문자열이 아나그램인지 판별 (같은 문자를 같은 횟수로 사용)

s = "anagram", t = "nagaram"

사고 과정:
   1. 아나그램 = 문자 빈도가 동일
   2. s 의 각 문자 빈도를 +1, t 의 각 문자 빈도를 -1 → 모두 0 이어야 함

Dry Run:
   s 순회 (빈도 +1):
     'a':3, 'n':1, 'g':1, 'r':1, 'm':1

   t 순회 (빈도 -1):
     'n'-1→0, 'a'-1→2, 'g'-1→0, 'a'-1→1, 'r'-1→0, 'a'-1→0, 'm'-1→0

   모든 값이 0 → return 1 (아나그램!)

반례: s = "rat", t = "car"
   s 순회: 'r':1, 'a':1, 't':1
   t 순회: 'c'-1→-1 ← 0 이 아님! → return 0

시간 O(n), 공간 O(1) — 문자 종류 고정(26) 이므로 공간은 상수
```

### 5.6 Group Anagrams (LeetCode #49) — 사고 과정

```
문제: 문자열 배열에서 아나그램끼리 그룹으로 묶기
입력: ["eat", "tea", "tan", "ate", "nat", "bat"]
출력: [["eat","tea","ate"], ["tan","nat"], ["bat"]]

사고 과정:
   1. 아나그램 = 문자를 정렬하면 같은 문자열
      "eat" → "aet", "tea" → "aet", "tan" → "ant"
   2. Key = 정렬된 문자열, Value = 원본 문자열 목록

Dry Run:
   "eat" → sort → "aet" → groups["aet"] = ["eat"]
   "tea" → sort → "aet" → groups["aet"] = ["eat", "tea"]
   "tan" → sort → "ant" → groups["ant"] = ["tan"]
   "ate" → sort → "aet" → groups["aet"] = ["eat", "tea", "ate"]
   "nat" → sort → "ant" → groups["ant"] = ["tan", "nat"]
   "bat" → sort → "abt" → groups["abt"] = ["bat"]

결과: groups 의 values → 3 개 그룹

시간 O(n × k log k) — n=문자열 수, k=최대 문자열 길이
공간 O(n × k)
```

### 5.7 면접 답안 템플릿

**Q: "Two Sum 을 풀어보세요"**

> "Brute Force 는 모든 쌍을 확인하는 O(n²) 입니다. 내부 루프가 'complement 가 존재하는가?' 를 검색하고 있으므로, Hash Map 의 O(1) 검색으로 대체하면 O(n) 이 됩니다. Key 는 배열의 값, Value 는 인덱스로 저장합니다."

→ 항상 "Brute Force → 비효율 분석 → 최적화" 순서로 설명.

### 5.8 SystemVerilog 예제 코드

원본 파일: `02_array_hashmap.sv`

```systemverilog
// =============================================================
// Unit 2: Array & Hash Map (Associative Array)
// =============================================================
// Key Insight: Associative array exists() turns O(n^2) -> O(n)
//   - Key = what you want to SEARCH FOR
//   - Value = auxiliary info (index, count, etc.)
//   - Pattern: "Have I seen this value before?" -> use hash map
//
// SV Associative Array Cheat Sheet:
//   int seen[int];          // declare
//   seen[key] = val;        // insert   O(1)
//   seen.exists(key);       // lookup   O(1)  <-- searches KEY
//   seen.delete(key);       // delete   O(1)
//   seen.num();             // size
// =============================================================

module unit2_array_hashmap;

  // ---------------------------------------------------------
  // Two Sum: find two indices whose values sum to target
  // Brute force O(n^2) -> Hash Map O(n)
  // ---------------------------------------------------------
  function automatic void two_sum(int nums[], int target);
    int seen[int]; // {value: index}

    for (int i = 0; i < nums.size(); i++) begin
      int complement = target - nums[i];
      if (seen.exists(complement)) begin     // O(1) lookup
        $display("Found: [%0d, %0d]", seen[complement], i);
        return;
      end
      seen[nums[i]] = i; // KEY = value, VALUE = index
    end
    $display("Not found");
  endfunction

  // ---------------------------------------------------------
  // Has Duplicate: return 1 if any duplicate exists
  // Pattern: "seen this before?" -> hash map
  // ---------------------------------------------------------
  function automatic bit has_duplicate(int nums[]);
    int seen[int];

    foreach (nums[i]) begin
      if (seen.exists(nums[i]))
        return 1;
      seen[nums[i]] = 1; // KEY = the value we want to find later
    end
    return 0;
  endfunction

  // ---------------------------------------------------------
  // Is Anagram: frequency counting pattern
  // Key = character (byte), Value = count
  // Increment for s, decrement for t -> all zeros = anagram
  // ---------------------------------------------------------
  function automatic bit is_anagram(string s, string t);
    int freq[byte];

    if (s.len() != t.len()) return 0;

    for (int i = 0; i < s.len(); i++) begin
      freq[s[i]]++;         // count up for s
      freq[t[i]]--;         // count down for t
    end

    foreach (freq[k])
      if (freq[k] != 0) return 0;  // mismatch -> not anagram

    return 1;
  endfunction

  // ---------------------------------------------------------
  // Most Frequent Element: find the value that appears most
  // Key = value, Value = count
  // ---------------------------------------------------------
  function automatic int most_frequent(int nums[]);
    int freq[int];
    int best_val = nums[0];
    int best_cnt = 0;

    foreach (nums[i]) begin
      freq[nums[i]]++;
      if (freq[nums[i]] > best_cnt) begin
        best_cnt = freq[nums[i]];
        best_val = nums[i];
      end
    end
    return best_val;
  endfunction

  // ---------------------------------------------------------
  // Test
  // ---------------------------------------------------------
  initial begin
    int arr1[] = '{2, 7, 11, 15};
    two_sum(arr1, 9);          // Expected: Found: [0, 1]

    int arr2[] = '{1, 2, 3, 1};
    $display("has_dup: %0b", has_duplicate(arr2)); // Expected: 1

    int arr3[] = '{1, 2, 3, 4};
    $display("has_dup: %0b", has_duplicate(arr3)); // Expected: 0

    $display("anagram(anagram,nagaram): %0b", is_anagram("anagram", "nagaram")); // 1
    $display("anagram(rat,car): %0b", is_anagram("rat", "car"));                 // 0

    int arr4[] = '{1, 3, 2, 3, 3, 1};
    $display("most_frequent: %0d", most_frequent(arr4)); // 3
  end

endmodule
```

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Hash Map average O(1) 이 항상 보장된다'"
    **실제**: Hash collision (의도적 attack 또는 unfortunate distribution) 시 worst-case O(N). 외부 입력 key 에는 randomized seed (Python `PYTHONHASHSEED`) 또는 SipHash 류를 쓰지 않으면 **Hash-Flooding DoS** 가능. Java 8+ 가 bucket 을 tree 로 변환하는 이유가 이것입니다.<br>
    **왜 헷갈리는가**: 교과서가 average 만 강조 + worst 는 "드물다" 로 처리해 attack scenario 를 못 봄.

!!! danger "❓ 오해 2 — 'Hash Map 은 항상 정렬된 dict'"
    **실제**: Python 3.7+ `dict` 는 _삽입 순서_ 보존, Java `LinkedHashMap` 은 _접근 순서_ 옵션 있음. 그러나 일반 `HashMap` / `unordered_map` / SV associative array 는 **순서 무관**. 정렬된 순회가 필요하면 별도 자료구조 (TreeMap, sorted-by-key).<br>
    **왜 헷갈리는가**: Python 의 dict 가 순서를 보존하는 게 _기본_ 이라 다른 언어도 그럴 거라 가정.

!!! danger "❓ 오해 3 — 'exists(value) 로 값을 검색할 수 있다'"
    **실제**: SV `assoc.exists(k)` 는 _KEY_ 를 검색합니다. value 로 검색하려면 O(N) 순회 필요. 그래서 _자주 검색할 것을 key 로 잡는 게_ 설계의 핵심.<br>
    **왜 헷갈리는가**: SQL 의 SELECT 처럼 임의 컬럼 검색이 가능하다고 오해.

!!! danger "❓ 오해 4 — '메모리 무한 가정'"
    **실제**: Hash map 은 _공간을 사 시간을 얻는_ 도구. N=10⁹ 의 입력에 hash map 을 쓰면 메모리가 폭발합니다. 메모리 제약 빡빡하면 Two Pointers / Sort 기반 풀이 (Module 03) 검토.<br>
    **왜 헷갈리는가**: 면접 입력 (~10⁶) 만 보면 메모리 한계가 안 보이고, 실서비스에서 처음 발견.

### 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Two Sum 이 자기 자신과 짝지음 (`[i, i]`) | `seen[v]=i` 가 `exists(complement)` 보다 _먼저_ 실행 | 두 줄의 순서 — exists 가 먼저, insert 가 나중 |
| 빈도 카운트가 음수로 떨어짐 | `freq[k]--` 만 있고 사전 `++` 없음 | s/t 길이 비교 누락? 또는 한쪽 루프가 다른 키 |
| Group Anagrams 가 같은 그룹을 두 곳에 분리 | Key 로 `sorted(str)` 대신 `set(str)` 사용 (중복 문자 정보 손실) | "aab" 와 "ab" 가 같은 set 으로 충돌 |
| Hash Map 풀이가 production 에서 느려짐 (avg) | Collision 누적 / load factor 폭증 | rehash 임계, hash function 의 distribution 측정 |
| 외부 입력에서 latency spike | DoS-style collision attack 가능성 | randomized hash seed 사용 여부 |
| Python `dict` 순서 의존 코드가 Java port 후 깨짐 | `HashMap` 은 순서 무관 | `LinkedHashMap` 또는 별도 list 로 순서 유지 |
| `assoc.exists(0)` 가 false 인데 `assoc[0]` 접근 | SV 의 default value 와 exists 혼동 | _값_ 의 default 과 _key_ 존재 여부는 별개 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Array** : index-by-position 이 강점, 순서 보존, lookup-by-value 는 O(N).
- **Hash Map** : key 기반 평균 O(1) lookup. 순서 보존이 필요하면 LinkedHashMap / dict (Python 3.7+).
- **신호 → hash map** : "두 원소의 합 / 짝 / 이전 등장 위치" 처럼 lookup 이 핵심이면 hash map 후보.
- **Collision** 처리는 Java(체이닝→트리) / Python(open addressing) / C++(체이닝) 가 다르다.
- **메모리 trade-off** — hash map 은 시간을 사기 위해 공간을 쓴다. 메모리 제약이 빡빡하면 다른 패턴 검토.

!!! warning "실무 주의점"
    - **Hash-Flooding DoS**: 외부 입력 key 는 randomized hash 또는 입력 검증으로 collision 차단.
    - **Order assumption**: `dict`/`HashMap` 의 순서는 언어별로 다르다. 순서가 필요하면 명시적 자료구조.
    - **메모리 폭발**: N 이 매우 클 때 hash map 은 OOM 의 주범. 정렬 기반 풀이를 _대안_ 으로 항상 떠올려라.

---

## 다음 모듈

→ [Module 03 — Two Pointers & Sliding Window](03_two_pointers_sliding_window_explained.md): hash map 으로 풀리는 문제를 _O(1) 공간_ 으로 풀어내는 기법. 정렬 가정이 더해질 때 뭐가 좋아지는지.

[퀴즈 풀어보기 →](quiz/02_array_hashmap_explained_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_big_o_explained/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Big-O 복잡도 & 패턴 사고법</div>
  </a>
  <a class="nav-next" href="../03_two_pointers_sliding_window_explained/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Two Pointers & Sliding Window</div>
  </a>
</div>


--8<-- "abbreviations.md"
