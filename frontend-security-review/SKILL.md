---
name: frontend-security-review
description: Detect the project's frontend framework, then audit the code for frontend security issues and fix them. Use when the user asks to check, audit, or review frontend/web security — e.g. "프론트 보안 검사해줘", "보안 점검", "security review", "웹 보안 확인", "XSS 취약점 봐줘", "보안 취약점 검토". Auto-detects React, Vue, and Next.js (incl. App Router / RSC / Server Actions) and applies framework-specific checks.
---

# 프론트엔드 보안 검사 & 수정 스킬

프로젝트의 프레임워크를 먼저 자동 감지한 뒤, 프론트엔드 코드의 보안 취약점을 검토하고 확실한 문제는 코드까지 직접 수정한다.

전제: **프론트엔드는 사용자(공격자)가 완전히 통제하는 환경에서 실행된다.** 클라이언트 검증·숨김·난독화는 보안 경계가 아니다. 실제 신뢰 경계는 항상 서버다.

## 언제 이 스킬을 쓰나

사용자가 다음을 요청할 때:
- 프론트엔드 코드/컴포넌트/페이지의 보안 검토·감사·개선
- "보안 검사", "보안 점검", "security review", "XSS 봐줘", "취약점 검토", "토큰 저장 안전한지" 등

## 작업 흐름

1. **프레임워크 감지 (필수 첫 단계)** — 아래 "프레임워크 감지" 절차대로 `package.json` 등을 읽어 React / Vue / Next.js와 주요 버전을 확정한다. 감지 결과를 사용자에게 한 줄로 알린 뒤 진행한다.
2. **대상 파악** — 사용자가 지정한 파일/디렉터리가 있으면 그 범위를, 없으면 소스 루트(`src/`, `app/`, `pages/`, `components/` 등)를 대상으로 한다. 범위가 너무 크면 우선순위(인증/폼/외부입력 처리부터)를 잡거나 사용자에게 범위를 확인한다.
3. **공통 검토** — "공통 체크리스트"로 모든 프로젝트를 훑는다. grep으로 위험 패턴(`innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `localStorage`, `eval`, `href={`, `target="_blank"` 등)을 먼저 잡고 해당 파일을 읽는다.
4. **프레임워크별 검토** — 감지된 프레임워크의 전용 체크리스트를 추가로 적용한다. Next.js는 서버/클라이언트 경계 문제가 핵심이라 특히 꼼꼼히.
5. **문제 정리** — 발견 항목을 `파일:라인` + 취약점 유형 + 이유 + 공격 시나리오로 요약해 보여준다. 심각도(🔴 치명적 / 🟠 권장 / 🟡 개선)로 묶는다.
6. **수정** — 확실한 취약점은 바로 Edit로 고친다. 판단이 갈리거나 동작에 영향을 주는 항목(예: 인증 방식 변경, 쿠키 전환)은 의도를 확인한 뒤 고친다.
7. **검증** — 프로젝트에 `eslint-plugin-security`, `eslint-plugin-react`, `npm audit`가 가능하면 돌려 확인한다. 없으면 도입을 제안(강요는 하지 않음).

수정 원칙: **서버에서 재검증 가능한 것을 프론트 검증으로 대체하지 않는다.** 그리고 라이브러리(예: DOMPurify)로 해결되는 문제를 직접 정규식 필터로 만들지 않는다.

---

## 프레임워크 감지

우선순위대로 확인한다. 최신 버전 여부는 확신하지 말고 **감지된 버전에 맞춰** 조언한다. 라이브러리별 최신 API/컨벤션이 필요하면 **context7 MCP로 해당 버전 문서를 확인**한다.

1. `package.json`의 `dependencies` / `devDependencies`를 읽는다.
   - `next` 존재 → **Next.js** (버전 확인. 라우터 방식은 아래로 판별)
   - `next` 없고 `react` 존재 → **React (SPA/CRA/Vite 등)**
   - `vue` 존재 → **Vue** (2 vs 3: `vue` 버전, `nuxt` 존재 여부 확인)
   - `nuxt` 존재 → **Nuxt** (Vue 계열 + SSR 관점 병행)
2. **Next.js 라우터/버전 판별** (보안 체크가 크게 달라짐):
   - `app/` 디렉터리 존재 → **App Router** (RSC, Server Actions, DAL 관점 적용)
   - `pages/` 만 존재 → **Pages Router** (API Routes, `getServerSideProps` 관점)
   - **Next.js 16+ 여부**: 파일 컨벤션이 `proxy.ts`/`proxy.js`면 16+, `middleware.ts`/`middleware.js`면 15 이하(또는 미마이그레이션). ⚠️ **`middleware` → `proxy` 네이밍 변경은 Next.js 16에서 일어났다.** 프로젝트에 있는 실제 파일명을 grep으로 확인하고 그 이름으로 지칭한다.
3. 감지가 애매하면(모노레포 등) 사용자에게 어느 앱/패키지를 볼지 확인한다.

감지 후 한 줄 보고 예: `감지: Next.js 16 (App Router), proxy.ts 사용 중 — App Router 보안 체크를 적용합니다.`

---

## 공통 체크리스트 (모든 프레임워크)

### 🧨 1. XSS (Cross-Site Scripting)

- [ ] `innerHTML` / `outerHTML` / `insertAdjacentHTML`에 사용자·외부 데이터 주입 → **DOMPurify로 sanitize** 후 사용하거나 `textContent`로 대체.
- [ ] `dangerouslySetInnerHTML`(React) / `v-html`(Vue) 사용처 전수 확인 → 값의 출처가 신뢰 가능한지, sanitize 됐는지 검증.
- [ ] `eval`, `new Function`, `setTimeout("문자열")`, `setInterval("문자열")` → 문자열 실행 제거.
- [ ] `<a href={userInput}>`, `location.href = userInput`, `window.open(userInput)` → `javascript:`/`data:` 스킴 차단. `http(s):`만 허용하는 검증.
- [ ] 마크다운 렌더러(marked, markdown-it 등)에 raw HTML 허용 옵션이 켜져 있는지 → sanitize 파이프라인 확인.

### 🔑 2. 민감 정보 노출

- [ ] API 키·시크릿·토큰이 소스/번들에 하드코딩 → **제거하고 서버로 이동**. 프론트에 남아야 하는 공개 키만 남긴다.
- [ ] 클라이언트 노출 환경변수 접두사 오남용 — `NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`, `VUE_APP_`, `NUXT_PUBLIC_` 가 붙은 값에 **진짜 시크릿이 들어있지 않은지** 확인. 이 접두사는 번들에 그대로 노출된다.
- [ ] 상태 관리 store(Redux/Zustand/Pinia/Vuex)에 비밀번호·주민번호·전체 토큰 등 저장 → devtools로 노출됨. 최소화.
- [ ] 프로덕션 빌드에 **source map** 노출 여부 확인.
- [ ] `console.log`로 토큰/개인정보 출력이 프로덕션에 남아있는지.

### 🪪 3. 인증 토큰 / 세션 저장

- [ ] `localStorage` / `sessionStorage`에 액세스 토큰·리프레시 토큰 저장 → **XSS로 탈취 가능.** 가능하면 `HttpOnly` + `Secure` + `SameSite` 쿠키로 전환 권고.
- [ ] 쿠키 설정 확인: `HttpOnly`, `Secure`, `SameSite=Lax/Strict`.
- [ ] 로그아웃 시 토큰·세션이 실제로 무효화/삭제되는지.
- [ ] JWT를 프론트에서 신뢰해 인가 판단 → 서명 검증은 서버 몫. 프론트 디코딩은 UI 표시용으로만.

### 🌐 4. 요청 / CORS / CSRF

- [ ] 쿠키 기반 인증인데 CSRF 방어(토큰 또는 `SameSite`)가 없는지.
- [ ] CORS를 프론트에서 우회하려 `*` 와일드카드 프록시를 열어두지 않았는지(설정 파일 확인).
- [ ] URL/쿼리 파라미터를 그대로 리다이렉트에 사용 → **오픈 리다이렉트**. 허용 목록(allowlist) 검증.

### 🧩 5. 의존성 / 서드파티

- [ ] `npm audit` 고위험 취약점 확인. Dependabot/Snyk 미도입 시 제안.
- [ ] 외부 `<script src>` 로드 시 **SRI(integrity)** 적용 여부.
- [ ] 신뢰 불가한 서드파티 위젯/태그가 민감 페이지(결제/로그인)에 삽입돼 있는지.

### 🛡️ 6. 보안 헤더 / 전송

- [ ] **CSP(Content-Security-Policy)** 설정 여부 — XSS 최후 방어선. 인라인 스크립트/외부 소스 제한.
- [ ] `Strict-Transport-Security`(HSTS), `X-Content-Type-Options: nosniff`, `X-Frame-Options`/`frame-ancestors`(클릭재킹), `Referrer-Policy`, `Permissions-Policy` 설정.
- [ ] `target="_blank"` 링크에 `rel="noopener noreferrer"` — 탭내빙(tabnabbing) 방지.

### 🚧 7. 클라이언트 검증 맹신 금지

- [ ] 폼 유효성/권한 체크가 **프론트에만** 있고 서버 재검증이 없는지 → 프론트 검증은 UX용임을 명시하고 서버 검증 필요성 지적.
- [ ] 숨긴 UI(`display:none`, 조건부 렌더)로 권한 제어를 대체하고 있지 않은지 → 데이터/엔드포인트는 여전히 접근 가능.

---

## 프레임워크별 체크리스트

### ⚛️ React (SPA)

- [ ] `dangerouslySetInnerHTML` 전수 검토 (위 XSS 항목 강화).
- [ ] `ref`를 통한 직접 DOM 조작에서 XSS 우회 경로.
- [ ] `href`/`src`에 상태값 바인딩 시 스킴 검증.
- [ ] 클라이언트 라우팅 가드가 **UI 숨김일 뿐** 실제 API 보호가 아님을 확인 — 보호는 서버 API에서.

### 🟩 Vue

- [ ] `v-html` 전수 검토 — Vue의 기본 이스케이프가 여기서만 무력화됨.
- [ ] 동적 컴포넌트 `<component :is="...">`에 신뢰 불가 값 주입 금지.
- [ ] `:href` / `:src` 바인딩 스킴 검증.
- [ ] Vue 2라면 EOL(지원 종료) 상태 — 업그레이드 권고 검토. 버전은 감지 결과 기준.

### ▲ Next.js (공통)

- [ ] 클라이언트 노출 환경변수(`NEXT_PUBLIC_`)에 시크릿 없는지 재확인.
- [ ] `next.config.js`(또는 `.ts`)의 `headers()`로 보안 헤더(CSP 등) 설정 여부.
- [ ] 이미지/외부 도메인 `remotePatterns` 설정이 과도하게 열려있지 않은지.

### ▲ Next.js — App Router / RSC / Server Actions (16 포함)

핵심: **서버 코드와 클라이언트 코드가 섞이며 데이터가 경계를 넘는다.**

- [ ] **서버→클라이언트 데이터 유출**: Server Component에서 DB 객체/레코드를 통째로 클라이언트 컴포넌트에 props로 넘기면 직렬화되어 노출된다(`password_hash`, 내부 플래그 등). → **DTO 패턴**으로 필요한 필드만 반환.
- [ ] **`server-only` 격리**: DB 접근·시크릿을 다루는 모듈에 `import 'server-only'`가 있는지. 없으면 클라이언트 번들에 딸려갈 위험 → 추가 권고.
- [ ] **React Taint API**: 민감값에 `experimental_taintUniqueValue` / `experimental_taintObjectReference` 적용 여부(안전망). 버전이 지원하는지 context7로 확인.
- [ ] **Server Action = 공개 엔드포인트**: `'use server'` 함수는 자동으로 공개 POST 엔드포인트가 된다. 누구나 직접 호출 가능 → **함수 진입부에서 매번 인증·인가 재검증**(`verifySession()` → `forbidden()` 등)이 있는지 확인. UI에서 버튼을 숨긴 것만으로는 보호가 아니다.
- [ ] **Server Action 반환값 최소화**: `db.user.update()` 결과를 그대로 return하지 말고 `{ success: true }` 등 필요한 것만.
- [ ] **인가 중앙화(DAL)**: 인가 로직이 컴포넌트 곳곳에 흩어져 있지 않고 Data Access Layer 한 곳에 모여 있는지.
- [ ] **`proxy`(구 `middleware`)는 최종 방어선이 아니다**: ⚠️ Server Function은 해당 라우트로의 POST 요청으로 처리되어 **proxy matcher를 우회할 수 있다.** matcher 변경/리팩터링으로 보호가 소리 없이 사라질 수 있으므로, **proxy에만 의존하지 말고 각 Server Action·Route Handler·페이지 안에서 인가를 재검증**하는지 확인한다. (파일명이 `proxy.*`인지 `middleware.*`인지 감지 결과대로 지칭)

### ▲ Next.js — Pages Router

- [ ] `getServerSideProps`/`getStaticProps`에서 반환하는 props에 서버 시크릿·내부 필드가 섞여 클라이언트로 넘어가지 않는지.
- [ ] `pages/api/*` 라우트 핸들러 각각에서 인증·인가·입력 검증을 하는지(클라이언트 가드와 별개).

---

## 검증 도구 (있으면 활용)

- `npm audit` / `pnpm audit` / `yarn audit` — 의존성 취약점.
- `eslint-plugin-security`, `eslint-plugin-react`, `eslint-plugin-no-unsanitized` — 정적 분석. 없으면 도입 제안.
- 최신 프레임워크 보안 API(taint, server-only, proxy 등)의 정확한 사용법이 필요하면 **context7 MCP**로 감지된 버전의 공식 문서를 확인해 근거를 댄다.

## 보고 형식 예시

```
감지: Next.js 16 (App Router)

🔴 치명적
- app/actions/updateRole.ts:5 — Server Action에 인가 검증 없음.
  누구나 POST로 직접 호출해 role을 변경할 수 있음. verifySession + forbidden 필요.

🟠 권장
- lib/auth.ts:12 — 액세스 토큰을 localStorage에 저장. XSS 시 탈취 가능.
  HttpOnly 쿠키 전환 권고.

🟡 개선
- next.config.js — CSP 헤더 미설정. XSS 방어선 추가 권장.
```
