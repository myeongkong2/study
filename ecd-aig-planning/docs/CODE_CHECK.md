# ECD-AIG 코드 점검 기록

## 점검 일자

2026-06-08

## 점검 범위

- `src/ecd_aig/*.py`
- `tests/test_ecd_aig.py`
- `pages/index.html`
- `docs/CODEBOOK.md`
- `docs/SRC_CODE_GUIDE.md`

## 점검 기준

현재 프로젝트의 기준은 다음과 같다.

```text
응답자료 전 단계에서는 후보 문항의 설계 계보와 구조적 위험만 점검한다.
자동 생성 문항의 경험적 타당도, 신뢰도, IRT, DIF는 응답자료가 들어온 뒤에만 주장할 수 있다.
```

## 자동 테스트

PowerShell에서 다음 명령으로 실행했다.

```powershell
$env:PYTHONPATH='src'
py -m unittest discover -s tests -v
```

결과:

```text
Ran 34 tests
OK
```

첫 실행에서 `PYTHONPATH` 없이 테스트를 실행했을 때 `ModuleNotFoundError: No module named 'ecd_aig'`가 발생했다. 이는 코드 오류가 아니라 실행 환경 설정 누락이었다. 코드북과 소스 해설서에는 `PYTHONPATH='src'` 설정을 먼저 하도록 안내되어 있다.

## 주요 점검 결과

| 영역 | 점검 결과 |
|---|---|
| 구조 게이트 | `validation.py`가 계보 ID 존재 여부와 관계 일관성을 확인한다 |
| 문항 품질 | `item_quality.py`가 규칙 기반 스크리닝과 전문가 판단 영역을 분리한다 |
| LLM 생성 | `llm_generation.py`가 부모 템플릿 계보를 유지하고 중복 stem/변수 조합을 제거한다 |
| 심리측정 | `psychometrics.py`가 상관계수를 -1에서 1 사이로 제한하고 결측 경고를 제공한다 |
| 로컬 웹앱 | `webapp.py`가 examples 내부 프로젝트만 읽고 DOM `textContent` 렌더링을 사용한다 |
| 공유 웹 화면 | `pages/index.html`이 기본 API 키 입력과 접힌 고급 연결 설정을 분리한다 |

## 이번 점검에서 수정한 사항

### 1. 공유 웹 화면의 모델/주소 동기화

문제:

`pages/index.html`의 고급 연결 설정에서 `모델 이름`을 바꿔도 Gemini API 주소에 포함된 모델 경로가 그대로 남을 수 있었다.

수정:

`apiConfig()`에서 Gemini 형식 주소를 감지하면 `모델 이름` 값을 사용해 `/models/...:generateContent` 경로를 함께 갱신하도록 했다.

의미:

사용자가 고급 설정에서 Gemini 모델명을 바꿨을 때 실제 API 호출도 같은 모델을 향한다.

### 2. 코드북 보강

`docs/CODEBOOK.md`에 GitHub Pages 후보 문항 생성 화면 코드북을 추가했다.

추가한 내용:

- 기본 화면 입력값
- 고급 연결 설정의 의미
- 생성 결과 저장 방식
- 저장 JSON의 핵심 필드
- 응답자료 전 후보 문항이라는 해석 경계

### 3. 소스 코드 해설서 보강

`docs/SRC_CODE_GUIDE.md`에 `pages/index.html` 해설을 추가했다.

추가한 내용:

- Python `webapp.py`와 GitHub Pages 화면의 차이
- 핵심 UI 구조
- 핵심 JavaScript 함수
- 코드 점검 포인트

## 남아 있는 주의점

1. GitHub Pages 화면은 서버 프록시가 없는 정적 앱이다. 사용자의 API 키가 브라우저에서 직접 사용된다.
2. 다른 API 주소를 고급 설정에 넣는 경우, 해당 API가 브라우저 직접 호출과 CORS를 허용해야 한다.
3. `pages/index.html`의 후보 문항 생성은 연구자 검토 전 후보를 만드는 기능이다. 이 결과를 실증 타당도 증거로 해석하면 안 된다.
4. 실제 운영 서비스로 확장하려면 API 키 보호를 위한 서버 프록시, 인증, 권한관리, 프로젝트 저장소가 필요하다.

