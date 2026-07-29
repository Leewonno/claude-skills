---
name: pr-summary
description: 현재 브랜치와 기준 브랜치(main)의 diff를 바탕으로 PR title과 description(요약/상세)을 한국어로 정리한다. 사용자가 "PR 정리", "PR 제목/설명 뽑아줘", "PR 요약", "PR title desc 정리", "clean up PR title/description" 등을 요청할 때 사용.
---

# PR Summary — PR title / description 정리

현재 브랜치와 기준 브랜치를 비교해 작업 내용을 파악하고, PR의 **title**과 **description(요약 / 상세)**을 한국어로 정리해 대화창에 출력한다.

이 스킬은 **출력 전용**이다. `gh`로 PR을 생성하거나 수정하지 않는다. 사용자가 명시적으로 "PR에 반영해줘" 등을 요청하면 그때만 gh를 사용한다.

## 절차

### 1. 기준 브랜치(base) 자동 감지

항상 **현재 브랜치 vs 기준 브랜치**를 비교한다. 기준 브랜치는 다음 순서로 감지한다.

```bash
# 1) origin/HEAD가 가리키는 기본 브랜치
git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
# 2) 없으면 존재하는 브랜치 중 우선순위로 폴백
for b in main master develop; do
  git show-ref --verify --quiet "refs/heads/$b" && echo "$b" && break
done
```

- 위에서 base 이름을 얻는다. 원격 기준으로 비교할 수 있으면 `origin/<base>`를 우선 사용한다.
- 현재 브랜치가 base 자체이거나 감지가 애매하면 사용자에게 base를 확인한다.

### 2. 비교 대상 확정 및 diff 수집

merge-base(공통 조상)부터의 변경만 보도록 `...`(three-dot)을 사용한다.

```bash
git rev-parse --abbrev-ref HEAD                     # 현재 브랜치 확인
git log --oneline --no-merges <base>...HEAD         # 커밋 목록
git diff --stat <base>...HEAD                        # 변경 파일 요약
git diff <base>...HEAD                               # 실제 변경 내용 (필요 시 파일별로)
```

- diff가 크면 `--stat`으로 전체 그림을 먼저 잡고, 핵심 파일 위주로 `git diff <base>...HEAD -- <path>`를 읽는다.
- 커밋 메시지와 실제 코드 변경을 **모두** 근거로 삼는다. 커밋 메시지만 믿지 말 것.

### 3. 내용 분석

- 이 브랜치가 **무엇을**, **왜** 바꿨는지 파악한다.
- 변경을 성격별로 묶는다: 기능 추가 / 버그 수정 / 리팩터링 / 문서 / 설정·빌드 / 테스트 등.
- 사용자 관점에서 의미 있는 변화와 내부 구현 변화를 구분한다.

### 4. 출력 (한국어)

아래 형식으로 정리해 출력한다. title은 관례를 따르되, 저장소가 Conventional Commits(`feat:`, `fix:` 등)를 쓰면 그 스타일에 맞춘다.

```markdown
## Title
<한 줄 제목 — 무엇을 했는지 명확하고 간결하게>

## Description

### 요약
- 이 PR이 무엇을/왜 했는지 2~4개 불릿으로 핵심만.

### 상세
- 주요 변경 사항을 항목별로 설명 (파일·모듈 단위로 묶어서).
- 필요 시 배경, 구현 방식, 영향 범위, 주의점 포함.
```

## 원칙

- **근거 기반**: diff에 없는 내용을 지어내지 않는다. 불확실하면 추측이라고 명시하거나 사용자에게 묻는다.
- **간결함**: 요약은 훑어보면 핵심이 잡히게, 상세는 리뷰어가 맥락을 이해할 만큼만.
- **한국어**로 작성한다.
- 변경이 없으면(`git diff <base>...HEAD`가 비어 있으면) 그 사실을 알리고 base가 맞는지 확인한다.
