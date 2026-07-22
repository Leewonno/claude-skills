---
name: a11y-review
description: Review frontend code for web accessibility (a11y / WCAG) compliance and fix the issues. Use when the user asks to check, audit, review, or improve accessibility of components, pages, or UI code — e.g. "접근성 확인해줘", "a11y 검토", "check accessibility", "웹 접근성 지켰는지 봐줘", "WCAG 검사". Works on React/JSX, Vue, Svelte, and plain HTML.
---

# 웹 접근성(a11y) 검토 & 수정 스킬

프론트엔드 코드가 웹 접근성을 잘 지켰는지 검토하고, 문제를 발견하면 코드까지 직접 수정한다.

기준은 두 가지다.
1. **frontend-fundamentals.com/a11y** 의 4대 원칙 (아래 체크리스트로 내재화됨)
2. **WCAG 2.2 Level AA** 핵심 성공 기준

## 언제 이 스킬을 쓰나

사용자가 다음을 요청할 때:
- 컴포넌트/페이지/UI 코드의 접근성 검토·감사·개선
- "접근성 확인", "a11y 검토", "WCAG 검사", "스크린리더 대응", "키보드 접근성" 등

## 작업 흐름

1. **대상 파악** — 사용자가 지정한 파일/디렉터리/컴포넌트를 읽는다. 지정이 없으면 어떤 범위를 볼지 물어본다. JSX/TSX, Vue, Svelte, HTML 모두 대상.
2. **검토** — 아래 체크리스트로 코드를 훑는다. `role`, `aria-*`, `alt`, `htmlFor`/`for`, `tabIndex`, 키보드 핸들러, 시맨틱 태그 사용 여부를 중점적으로 grep/read 한다.
3. **문제 정리** — 발견 항목을 `파일:라인` + 위반 원칙 + 이유로 요약해 사용자에게 보여준다. 심각도(치명적/권장/개선)로 묶으면 좋다.
4. **수정** — 확실한 위반은 바로 Edit로 고친다. 판단이 갈리는 항목(예: 장식용 vs 의미있는 이미지, aria-label 문구)은 사용자에게 의도를 확인한 뒤 고친다.
5. **검증** — 프로젝트에 `eslint-plugin-jsx-a11y`가 있으면 lint를 돌려 확인한다. 없으면 도입을 제안(강요는 하지 않음).

수정할 때 원칙: **네이티브 HTML 요소로 해결 가능하면 ARIA보다 우선**한다. "No ARIA is better than bad ARIA."

---

## 검토 체크리스트 (frontend-fundamentals 4대 원칙 기준)

### 🧱 1. 올바른 구조 만들기 (시맨틱 HTML)

- [ ] `<div onClick>` / `<span onClick>` 로 만든 가짜 버튼·링크 → 실제 `<button>`, `<a>` 로 교체. 불가피하면 `role`, `tabIndex={0}`, 키보드 핸들러 모두 부여.
- [ ] 상호작용 요소 중첩 금지 — 버튼 안에 버튼, `<a>` 안에 `<button>`, `<a>` 안에 `<a>` 등.
- [ ] 목록은 `<ul>/<ol>/<li>`, 표는 `<table>/<thead>/<th scope>`, 제목은 `<h1>~<h6>` 로 계층 유지(레벨 건너뛰기 금지, h1은 페이지당 하나 권장).
- [ ] 랜드마크 사용: `<header> <nav> <main> <footer>`, 폼 입력은 `<form>` 으로 감싸기.
- [ ] 페이지에 스킵 링크(`Skip to main content`) 제공 검토.

### 🗣️ 2. 의미를 정확하게 전달하기 (role & label)

- [ ] **role**: 네이티브 요소는 role이 내장(`<button>`,`<input>`,`<nav>`…). `<div>` 기반 커스텀 위젯(tab, switch, dialog 등)은 `role` 명시.
  - 단, 네이티브 상호작용 요소에 상호작용 role을 덮어씌우지 말 것 (예: `<a role="button">` 지양).
- [ ] **아이콘 전용 버튼/링크**: 보이는 텍스트가 없으면 `aria-label` 필수.
  ```jsx
  // ❌ <button><SearchIcon /></button>
  // ✅ <button aria-label="검색"><SearchIcon /></button>
  ```
- [ ] **입력 필드**: 모든 input은 이름을 가진다. `<label htmlFor="id">` + `<input id="id">` 가 표준. 시각적 라벨이 없으면 `aria-label`.
  ```jsx
  // ❌ <span>주소</span><input />
  // ✅ <label htmlFor="addr">주소</label><input id="addr" />
  ```
- [ ] **연관 입력 그룹**: 카드번호·생년월일 등은 `<fieldset><legend>` 로 묶고 각 칸에 개별 `aria-label`.
- [ ] **이미지 `alt`**:
  - 의미 있는 이미지 → 내용을 서술 (`alt="스타벅스 아이스아메리카노 4,700원"`).
  - 장식용 이미지 → `alt=""` (빈 값, 스크린리더가 무시).
  - 차트/그래프 → 핵심 수치·축 정보를 `alt`/`aria-label`로.
- [ ] **동일 이름 반복 요소**: 같은 "수정" 버튼이 여러 개면 맥락 추가(`aria-label="주소 수정"`).
- [ ] `aria-labelledby` / `aria-describedby` 로 제목·설명·에러메시지를 요소와 프로그래밍적으로 연결.

### 🎯 3. 예측 가능한 인터랙션 만들기 (state & keyboard)

- [ ] **키보드 조작 가능**: 마우스로 되는 모든 동작은 키보드로도 가능해야. `onClick`만 있고 `onKeyDown`이 없는 커스텀 상호작용 요소 점검(Enter/Space).
- [ ] **포커스 표시**: `outline: none` 만 있고 대체 포커스 스타일이 없으면 안 됨. `:focus-visible` 로 명확한 포커스 링 제공(WCAG 2.2 Focus Appearance).
- [ ] **상태 속성으로 동작 반영**:
  - 펼침/접힘 → `aria-expanded`
  - 탭/리스트 선택 → `aria-selected`
  - 체크/스위치 → `aria-checked` (또는 네이티브 `checked`)
  - 비활성 → `disabled` / `aria-disabled`
  - 현재 위치(현재 페이지, 오늘 날짜) → `aria-current`
- [ ] **모달/다이얼로그**:
  - `role="dialog"` + `aria-modal="true"`, 제목은 `aria-labelledby`.
  - 열릴 때 내부로 초기 포커스 이동, 닫힐 때 열었던 요소로 포커스 복원.
  - 포커스 트랩(Tab이 모달 밖으로 안 나감), `Esc`로 닫기.
  - 배경 콘텐츠에 `inert` 부여.
  - **가장 간단한 정답: 네이티브 `<dialog>` + `showModal()`** — 위 대부분을 브라우저가 처리.
- [ ] **동적 업데이트 알림**: 토스트·폼 검증·에러는 `aria-live`(`polite`/`assertive`) 또는 `role="status"`/`role="alert"`.
  - ⚠️ 흔한 실수: 조건부로 alert를 마운트/언마운트하면 스크린리더가 못 읽는다. **컨테이너는 항상 마운트해 두고 내용만 갱신**.
- [ ] **SPA 라우팅**: 페이지 전환 시 포커스가 사라진 요소에 남지 않도록, 새 페이지의 제목/메인으로 포커스 이동.
- [ ] `tabindex` 양수 사용 금지(`tabindex="1"` 등) — DOM 순서를 따르게. 필요 시 `0` 또는 `-1`만.

### 🌈 4. 시각 정보에만 의존하지 않기

- [ ] **색상 대비**: 본문 텍스트 4.5:1, 큰 텍스트/UI 요소 3:1 이상(WCAG AA).
- [ ] **색상만으로 정보 전달 금지**: 에러를 빨간색으로만 표시하지 말고 아이콘/텍스트 병행. 필수 항목을 색으로만 구분하지 말 것.
- [ ] **아이콘/이미지**는 텍스트나 `aria-label`로 보완(원칙 2와 연결).
- [ ] **타깃 크기**: 터치 타깃 최소 24×24 CSS px(WCAG 2.2), 가능하면 44×44 권장.
- [ ] **모션/자동재생**: 자동 재생 미디어는 정지 수단 제공, `prefers-reduced-motion` 존중, 3회/초 초과 깜빡임 금지.

---

## WCAG 2.2 신규 기준 (놓치기 쉬움)

- **Target Size (Minimum)** — 상호작용 타깃 24×24px 이상.
- **Focus Appearance** — 포커스 표시는 충분히 두껍고 대비되게.
- **Dragging Movements** — 드래그로만 되는 기능은 클릭/키보드 대안 제공.
- **Accessible Authentication** — 인증에 인지 테스트(캡차 등)만 강제하지 않기, 대안 제공.
- **Consistent Help / Redundant Entry** — 도움 요소 위치 일관, 이미 입력한 정보 재입력 강요 금지.

---

## 도구로 검증하기

- **ESLint**: `eslint-plugin-jsx-a11y` (React/JSX). 핵심 규칙:
  - `alt-text` — 이미지 대체 텍스트 필수
  - `control-has-associated-label` — 상호작용 요소에 접근 가능한 이름
  - `no-noninteractive-element-interactions` — 비상호작용 요소에 핸들러 달 때 role 명시
  - `no-noninteractive-element-to-interactive-role` — 컨테이너 요소에 button/link role 부여 금지
  - `no-noninteractive-tabindex` — 비상호작용 요소에 tabIndex 금지
  - `tabindex-no-positive` — 양수 tabIndex 금지
  - Vue는 `eslint-plugin-vuejs-accessibility`, Svelte는 컴파일러 a11y 경고 활용.
- **자동 스캔**: axe DevTools, WAVE, Lighthouse (초기 스캔용). 단, 자동 도구는 이슈의 일부만 잡으므로 위 체크리스트로 수동 검토 병행.
- **접근성 프리미티브 추천**: 복잡한 위젯(메뉴, 콤보박스, 중첩 모달)은 직접 구현보다 Radix UI, React Aria, Ariakit, Base UI 같은 검증된 헤드리스 라이브러리 사용을 제안.

## 보고 형식 예시

```
## 접근성 검토 결과

### 🔴 치명적 (스크린리더/키보드 사용 불가)
- Header.tsx:42 — 아이콘 버튼에 접근 가능한 이름 없음 → aria-label 추가 필요
- Modal.tsx:15 — role="dialog"·포커스 트랩·Esc 닫기 없음

### 🟡 권장
- Nav.tsx:20 — <div onClick>로 만든 링크 → <a>/<button>로 교체

### 🟢 개선
- Button.css:3 — outline:none, 대체 포커스 스타일 없음 → :focus-visible 추가
```
