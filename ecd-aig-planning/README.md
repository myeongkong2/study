# ECD-AIG Planning

ECD-AIG Planning은 자동 생성 또는 외부 반입 문항을 **응답자료 수집 전 단계**에서 점검하는 연구용 프로토타입입니다.

이 도구는 자동 생성 문항의 타당도를 확정하지 않습니다. 대신 문항이 어떤 `construct`, `KSA`, `evidence claim`, `task model`, `parent template`에서 왔는지 추적하고, 파일럿 조사 전에 수정이 필요한 후보를 선별합니다.

## 핵심 원칙

```text
자동 생성 문항
→ ECD 계보 연결
→ 구조 점검
→ 문항 품질 점검
→ 전문가 검토
→ 파일럿 조사 준비

Design-time screening != empirical validity
```

신뢰도, 요인구조, IRT, DIF, 경험적 공정성은 실제 응답자료가 들어온 뒤에만 분석할 수 있습니다.

## 빠른 시작

```powershell
$env:PYTHONPATH='src'
py -m unittest discover -s tests -v
py -m ecd_aig pre-response examples\job_stress_workload_12item_user_project.json --markdown
py -m ecd_aig validate examples\job_stress_workload_12item_user_project.json --json
py -m ecd_aig audit-items examples\job_stress_workload_12item_user_project.json --strict --markdown
py -m ecd_aig dossier examples\job_stress_workload_12item_user_project.json --item JS-WB-012 --markdown
py -m ecd_aig webapp
```

웹 화면: `http://127.0.0.1:8765`

## Gemini LLM 후보 문항 생성

```powershell
$env:GEMINI_API_KEY='YOUR_GOOGLE_AI_STUDIO_KEY'
Copy-Item examples\sample_project.json outputs\my_llm_project.json
py -m ecd_aig llm-generate outputs\my_llm_project.json --template tpl_worry_001 --count 2 --markdown
py -m ecd_aig llm-generate outputs\my_llm_project.json --template tpl_worry_001 --count 2 --write --json
```

부모 템플릿의 변수 목록은 예시와 설계 맥락으로 사용됩니다. LLM은 JSON을 손으로 수정하지 않아도 새로운 상황·반응 후보를 제안할 수 있습니다. 제안값은 `llm_proposed_for_expert_review`로 기록됩니다. 동일 조합과 동일 문장은 제외하고 부족한 수만 최대 4회까지 다시 요청합니다.

## 문서

상세한 데이터 구조, 명령어, 해석 원칙은 [docs/CODEBOOK.md](docs/CODEBOOK.md)를 참고하세요.

`src/ecd_aig`의 파이썬 파일별 역할과 주요 함수 설명은 [docs/SRC_CODE_GUIDE.md](docs/SRC_CODE_GUIDE.md)를 참고하세요.
