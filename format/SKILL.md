---
name: format
description: 현재 프로젝트에서 저장(Ctrl+S / Cmd+S)할 때마다 ESLint 자동 수정(--fix)과 Prettier 포맷이 실행되도록 IDE를 설정한다. 실행할 때마다 IDE(WebStorm 등 JetBrains / VS Code 계열)를 자동 판단해 해당 IDE 설정 파일을 만든다. 사용자가 "저장할 때 eslint/prettier 실행", "format on save", "저장 시 자동 정리", "ctrl+s 누르면 포맷", "/format" 등을 요청할 때 사용.
---

# Format on Save — 저장 시 ESLint + Prettier 자동 실행

현재 프로젝트에서 파일을 저장하면 **ESLint `--fix` + Prettier**가 실행되도록 설정한다.
IDE는 실행할 때마다 감지하고, 감지된 IDE에 맞는 설정 파일을 만들거나 기존 파일에 병합한다.

## 절차

### 1. 프로젝트 상태 파악

```bash
ls -a                                   # .idea / .vscode / 설정 파일 존재 여부
cat package.json                        # eslint, prettier, eslint-config-prettier, eslint-plugin-prettier 설치 여부
ls -a | grep -iE 'eslint|prettier'      # eslint.config.* / .eslintrc* / .prettierrc* / prettier.config.*
ls package-lock.json yarn.lock pnpm-lock.yaml bun.lockb 2>/dev/null   # 패키지 매니저 판단
cat .gitignore                          # .idea / .vscode 커밋 여부 확인용
```

- `package.json`의 `"prettier"` 키도 Prettier 설정으로 간주한다.
- 모노레포라면 실제 프론트 패키지 루트(가장 가까운 `package.json`)를 기준으로 한다. 애매하면 사용자에게 묻는다.

### 2. IDE 감지

아래 신호를 모아 판단한다.

| 신호 | WebStorm (JetBrains) | VS Code 계열 (Cursor 포함) |
|---|---|---|
| 환경변수 | `TERMINAL_EMULATOR=JetBrains-JediTerm` | `TERM_PROGRAM=vscode` |
| 프로젝트 폴더 | `.idea/` 존재 | `.vscode/` 존재 |

```bash
echo "TERM_PROGRAM=$TERM_PROGRAM TERMINAL_EMULATOR=$TERMINAL_EMULATOR"
ls -d .idea .vscode 2>/dev/null
```

- **환경변수가 가장 확실한 신호**다 (Claude Code를 그 IDE의 터미널에서 실행 중이라는 뜻). 환경변수가 있으면 그 IDE를 쓴다.
- 환경변수가 없으면 폴더로 판단한다. 한쪽만 있으면 그 IDE.
- 둘 다 있거나 아무 신호도 없으면 `AskUserQuestion`으로 묻는다 (선택지: WebStorm / VS Code / 둘 다).
- 사용자가 인자로 IDE를 지정하면 (`/format vscode`, `/format webstorm`) 감지보다 우선한다.

### 3. 의존성 확인

필요한 패키지: `eslint`, `prettier`, `eslint-config-prettier` (ESLint의 포맷 규칙과 Prettier 충돌 방지).

- 빠진 패키지가 있으면 **설치 전에 사용자에게 확인**받고, 감지한 패키지 매니저로 devDependency 설치한다 (`npm i -D` / `yarn add -D` / `pnpm add -D` / `bun add -d`).
- ESLint 설정 파일 자체가 없으면 여기서 멈추고 사용자에게 알린다 (ESLint 초기 설정은 이 스킬 범위가 아니다).
- `eslint-plugin-prettier`는 필수가 아니다. 이미 쓰고 있으면 유지하고, 새로 추가하지는 않는다.

### 4. Prettier 설정 파일 정리 (단일 출처로 만들기)

IDE의 Prettier는 **Prettier 설정 파일이 있어야** 자동으로 동작하고, ESLint와 IDE가 같은 옵션을 써야 저장할 때 결과가 충돌하지 않는다.

1. **Prettier 설정 파일이 이미 있으면** 그대로 쓴다.
2. **없는데 ESLint 설정의 `prettier/prettier` 규칙에 옵션 객체가 인라인으로 있으면**:
   - 그 옵션을 그대로 `.prettierrc`(JSON)로 옮긴다.
   - ESLint 규칙은 `"prettier/prettier": "error"`처럼 옵션 없이 바꾸고, 옵션은 `.prettierrc`에서 관리한다는 주석을 프로젝트 주석 스타일에 맞게 남긴다.
   - 이유: 규칙 옵션은 `.prettierrc`보다 우선하므로, 그대로 두면 ESLint와 IDE의 Prettier가 서로 다른 설정을 쓸 수 있다.
3. **둘 다 없으면** 사용자에게 원하는 스타일을 확인하거나, 기본값으로 `.prettierrc`에 `{}`를 만든다 (Prettier 기본값 사용).

ESLint 설정에 `eslint-config-prettier`가 적용되어 있지 않으면 마지막 extends/config 항목으로 추가한다 (flat config: `import eslintConfigPrettier from "eslint-config-prettier";` 후 배열 끝에 추가).

### 5. IDE 설정 파일 작성

기존 파일이 있으면 **먼저 읽고**, 다른 설정은 보존한 채 필요한 항목만 추가·수정한다.

#### WebStorm (JetBrains)

`.idea/jsLinters/eslint.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="EslintConfiguration">
    <files-pattern value="**/*.{js,jsx,ts,tsx}" />
    <option name="fix-on-save" value="true" />
  </component>
</project>
```
- Vue/Svelte 프로젝트면 패턴에 `vue`, `svelte`를 추가한다.
- 기존에 수동 설정(`custom-configuration-file`, `work-dir-patterns` 등)이 있으면 지우지 않는다.

`.idea/prettier.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="PrettierConfiguration">
    <option name="myConfigurationMode" value="AUTOMATIC" />
    <option name="myRunOnSave" value="true" />
    <option name="myFilesPattern" value="**/*.{js,jsx,ts,tsx,json,css,scss,html,md}" />
  </component>
</project>
```
- 프로젝트에서 쓰는 확장자(vue, svelte, less 등)에 맞게 패턴을 조정한다.

#### VS Code 계열

`.vscode/settings.json`
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "prettier.requireConfig": true
}
```

`.vscode/extensions.json` (팀원에게 확장 설치를 권장)
```json
{
  "recommendations": ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"]
}
```
- 두 파일은 JSONC(주석 허용)일 수 있다. 기존 파일은 주석을 보존하도록 `Edit`로 키만 추가·수정하고, 통째로 덮어쓰지 않는다.
- `recommendations`가 이미 있으면 빠진 항목만 추가한다.

### 6. 검증

```bash
npx eslint .                       # 설정이 깨지지 않았는지
npx prettier --check .             # Prettier 설정이 읽히는지
```
- 패키지 매니저에 맞게 `npx` / `yarn` / `pnpm exec` / `bunx`를 쓴다.
- 두 도구가 **같은 파일·같은 위치**를 지적하면 ESLint와 Prettier가 같은 설정을 공유하고 있다는 뜻이다. 다르면 4단계 설정이 어긋난 것이므로 다시 확인한다.
- 기존 코드의 포맷 위반은 **고치지 않는다** (사용자의 진행 중인 변경과 섞이지 않도록). 결과만 보고하고, 전체 정리(`eslint --fix .`, `prettier --write .`)를 원하는지 묻는다.
- IDE 안에서 실제로 저장이 동작하는지는 Claude가 확인할 수 없으므로, 확인하지 못했다고 명시한다.

### 7. 결과 보고 (한국어)

- 감지한 IDE와 판단 근거
- 만든/수정한 파일과 각각의 역할
- 검증 결과 (명령줄 실행 결과 그대로)
- 확인 방법:
  - WebStorm: IDE가 열려 있으면 설정이 바로 반영되지 않을 수 있으니 프로젝트를 다시 열 것. **Settings → Tools → Actions on Save**에서 "Run eslint --fix", "Run Prettier"가 체크되어 있는지 확인.
  - VS Code: ESLint / Prettier 확장이 설치되어 있어야 함. 필요하면 창 새로고침(Developer: Reload Window).
- `.gitignore`에 `.idea` / `.vscode`가 들어 있으면 IDE 설정은 이 컴퓨터에만 적용된다는 점. `.prettierrc`와 ESLint 설정 변경은 커밋해야 팀원도 같은 규칙을 쓴다는 점.

## 원칙

- **기존 설정 보존**: IDE 설정·ESLint 설정은 읽고 나서 필요한 부분만 바꾼다. 덮어쓰지 않는다.
- **단일 출처**: 포맷 옵션은 Prettier 설정 파일 한 곳에서만 관리한다.
- **설치·대량 수정은 확인 후**: 패키지 설치, 프로젝트 전체 포맷 적용은 사용자 동의를 받고 진행한다.
- **커밋하지 않는다**: 사용자가 요청할 때만 커밋한다.
