# Unit 2: Array & Hash Map (연관 배열)

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 8분</span>
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

## 왜 Hash Map인가?

```
핵심 질문: "이 값을 이전에 본 적 있는가?"
  → YES → Hash Map 사용

Brute Force:  매번 배열 전체를 검색 → O(n) × n번 = O(n²)
Hash Map:     exists()로 O(1) 검색 → O(1) × n번 = O(n)

핵심: Hash Map의 Key = 나중에 찾고 싶은 값
```

## SystemVerilog 연관 배열 (Associative Array)

```systemverilog
int seen[int];          // 선언: Key=int, Value=int
seen[key] = val;        // 삽입: O(1)
seen.exists(key);       // 검색: O(1) — KEY를 검색
seen.delete(key);       // 삭제: O(1)
seen.num();             // 크기
foreach (seen[k]) ...   // 순회

주의: exists()는 KEY를 검색한다, VALUE가 아니다!
  seen[7] = 0;
  seen.exists(7);   // 1 (true) — Key 7이 존재
  seen.exists(0);   // 0 (false) — Key 0은 없음 (0은 Value!)
```

## Two Sum — 대표 문제 Dry Run

```
문제: nums = [2, 7, 11, 15], target = 9
      합이 target인 두 인덱스를 찾아라.

Brute Force O(n²):
  i=0, j=1: 2+7=9 ✓ → [0,1]  (운 좋으면 빨리, 최악 O(n²))

Hash Map O(n):
  Key = 값, Value = 인덱스

  i=0: nums[0]=2, complement=9-2=7
       seen.exists(7)? NO → seen[2]=0  (seen: {2:0})

  i=1: nums[1]=7, complement=9-7=2
       seen.exists(2)? YES! → 답: [seen[2], 1] = [0, 1]

  → 2번만에 완료, O(n)
```

### Key 설계가 핵심

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

## Has Duplicate — Dry Run

```
문제: nums에 중복 값이 있으면 1, 없으면 0

nums = [1, 2, 3, 1]:
  i=0: nums[0]=1, seen.exists(1)? NO → seen[1]=1
  i=1: nums[1]=2, seen.exists(2)? NO → seen[2]=1
  i=2: nums[2]=3, seen.exists(3)? NO → seen[3]=1
  i=3: nums[3]=1, seen.exists(1)? YES! → return 1

nums = [1, 2, 3, 4]:
  모든 원소가 최초 → return 0
```

## 빈도 카운팅 패턴 — Dry Run

```
패턴: Key = 값, Value = 출현 횟수
용도: "가장 많이 나타나는 값", "아나그램 판별", "빈도 기반 필터링"
```

### Is Anagram (LeetCode #242) — Dry Run

```
문제: 두 문자열이 아나그램인지 판별 (같은 문자를 같은 횟수로 사용)

s = "anagram", t = "nagaram"

사고 과정:
  1. 아나그램 = 문자 빈도가 동일
  2. s의 각 문자 빈도를 세고, t의 각 문자 빈도를 빼면 → 모두 0이어야 함

Dry Run:
  s 순회 (빈도 +1):
    'a':3, 'n':1, 'g':1, 'r':1, 'm':1

  t 순회 (빈도 -1):
    'n'-1→0, 'a'-1→2, 'g'-1→0, 'a'-1→1, 'r'-1→0, 'a'-1→0, 'm'-1→0

  모든 값이 0 → return 1 (아나그램!)

반례: s = "rat", t = "car"
  s 순회: 'r':1, 'a':1, 't':1
  t 순회: 'c'-1→-1 ← 0이 아님! → return 0

시간 O(n), 공간 O(1) — 문자 종류가 고정(26개)이므로 공간은 상수
```

### Group Anagrams (LeetCode #49) — 사고 과정

```
문제: 문자열 배열에서 아나그램끼리 그룹으로 묶기
입력: ["eat", "tea", "tan", "ate", "nat", "bat"]
출력: [["eat","tea","ate"], ["tan","nat"], ["bat"]]

사고 과정:
  1. 아나그램 = 문자를 정렬하면 같은 문자열이 됨
     "eat" → "aet", "tea" → "aet", "tan" → "ant"
  2. Key = 정렬된 문자열, Value = 원본 문자열 목록

Dry Run:
  "eat" → sort → "aet" → groups["aet"] = ["eat"]
  "tea" → sort → "aet" → groups["aet"] = ["eat", "tea"]
  "tan" → sort → "ant" → groups["ant"] = ["tan"]
  "ate" → sort → "aet" → groups["aet"] = ["eat", "tea", "ate"]
  "nat" → sort → "ant" → groups["ant"] = ["tan", "nat"]
  "bat" → sort → "abt" → groups["abt"] = ["bat"]

결과: groups의 values → 3개 그룹

시간 O(n × k log k) — n=문자열 수, k=최대 문자열 길이
공간 O(n × k)
```

---

## 면접 팁

**Q: "Two Sum을 풀어보세요"**
> "Brute Force는 모든 쌍을 확인하는 O(n²)입니다. 내부 루프가 'complement가 존재하는가?'를 검색하고 있으므로, Hash Map의 O(1) 검색으로 대체하면 O(n)이 됩니다. Key는 배열의 값, Value는 인덱스로 저장합니다."

→ 항상 "Brute Force → 비효율 분석 → 최적화" 순서로 설명

### Hash Map 3가지 용법 요약

```
1. 존재 확인: Key = 찾을 값, Value = 인덱스/1
   → Two Sum, Has Duplicate

2. 빈도 카운팅: Key = 값, Value = 카운트
   → Is Anagram, Most Frequent Element

3. 그룹핑: Key = 그룹 기준, Value = 목록 (SV에서는 큐)
   → Group Anagrams
```


---

## 부록: SystemVerilog 예제 코드

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

<div class="chapter-nav">
  <a class="nav-prev" href="01_big_o_explained.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Big-O 복잡도 & 패턴 사고법</div>
  </a>
  <a class="nav-next" href="03_two_pointers_sliding_window_explained.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Two Pointers & Sliding Window</div>
  </a>
</div>
