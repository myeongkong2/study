# ECD-AIG Planning

Gemini 2.5 Flash를 이용해 ECD 계보를 유지하면서 전문가 검토 전 후보 문항을 생성하는 연구용 프로토타입입니다.

## 핵심 원칙

```text
LLM 후보 문항 생성
→ ECD 계보 자동 연결
→ 구조 게이트 검사
→ 중복 문항 제거 및 부족분 재요청
→ 규칙 기반 문항 품질 검사
→ 전문가 검토
→ 파일럿 조사 준비
```

이 프로그램은 자동 생성 문항의 경험적 타당도를 입증하지 않습니다. 신뢰도, 문항-총점 상관, IRT, DIF 분석은 실제 응답자료 수집 이후 단계입니다.

## 코드와 릴리즈

- [GitHub 저장소](https://github.com/myeongkong2/study)
- [최신 릴리즈](https://github.com/myeongkong2/study/releases/latest)

## 로컬 실행

```powershell
cd C:\dev\ecd
$env:PYTHONPATH='src'
$env:GEMINI_API_KEY='YOUR_GOOGLE_AI_STUDIO_KEY'

py -m ecd_aig llm-generate outputs\my_llm_project.json `
  --template tpl_worry_001 `
  --count 20 `
  --brief '업무 걱정을 측정하되, 서로 다른 구체적 업무 상황과 단일 감정 반응을 사용해 중복 없이 다양하게 생성' `
  --markdown
```

API 키는 코드, JSON, GitHub 저장소에 올리지 않습니다.

## 사용 범위

생성 결과는 전문가 검토가 필요한 사전 후보입니다.

- construct alignment와 construct drift 검토
- 단일 신호 해석 가능성 검토
- 임상적 또는 낙인 표현 검토
- 응답척도 적합성 검토
- 내용 관련성, 명료성, 공정성 검토
