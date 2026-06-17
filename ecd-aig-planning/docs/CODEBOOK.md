# ECD-AIG Planning 코드북 및 사용 매뉴얼

## 1. 목적

ECD-AIG Planning은 자동 생성 문항 또는 외부에서 가져온 후보 문항을 응답자료 수집 전에 정리하고 점검하는 도구다.

이 도구의 목적은 문항 타당도를 확정하는 것이 아니다. 문항의 설계 근거를 추적 가능하게 만들고, 구조적 오류와 문항 품질 위험을 조기에 찾고, 전문가 검토와 파일럿 조사를 준비하는 것이 목적이다.

## 2. 해석 원칙

가장 중요한 원칙은 다음과 같다.

```text
사전 점검 통과 != 경험적 타당도 확보
```

`PASS`는 선언된 설계 구조 안에서 자동 점검 규칙을 통과했다는 뜻이다. 문항이 실제 응답자 집단에서 신뢰롭고 타당하며 공정하게 작동한다는 뜻이 아니다.

### 응답 전 단계에서 가능한 주장

- 문항의 ECD 계보가 선언되어 있는지 확인했다.
- 점수화 메타데이터와 척도 연결을 확인했다.
- 결정론적으로 탐지 가능한 중복과 감시 대상 표현을 점검했다.
- 전문가가 우선 검토할 문항을 선별했다.
- 파일럿 조사에 넘길 후보 문항 묶음을 준비했다.

### 응답자료 없이 할 수 없는 주장

- 신뢰도 또는 Cronbach alpha가 확보되었다.
- 문항-총점 상관이 적절하다.
- 요인구조 또는 단일차원성이 확인되었다.
- IRT 문항모수가 보정되었다.
- DIF가 없으며 경험적으로 공정하다.
- 운영 타당도가 확보되었다.

## 3. 전체 워크플로우

```text
1. 이론 근거 정의
   construct → KSA → evidence claim

2. 과제모형 정의
   task model → parent template → variables → response scale

3. 후보 문항 준비
   generate 또는 import-items

4. 구조 점검
   traceability → scoring readiness → redundancy → sensitivity

5. 문항 품질 점검
   문장 길이 → 이중질문 → 모호 표현 → 다중 부정
   → 민감 표현 → 단일 상황 → 단일 반응

6. 전문가 검토
   approve / revise / reject

7. 응답 전 준비 보고서
   pre-response → CAF → Toulmin → dossier → export-items

8. 별도 후속 단계
   파일럿 응답자료 수집 이후 reliability / CTT / IRT / DIF
```

## 4. 폴더 구조

```text
ecd
├─ examples/                 예시 프로젝트와 응답자료
├─ outputs/                  내보낸 파일
├─ src/ecd_aig/              파이썬 코드
├─ tests/                    자동 테스트
└─ docs/CODEBOOK.md          이 문서
```

## 5. 프로젝트 JSON 코드북

프로젝트 JSON은 하나의 문항 설계 기록이다.

| 필드 | 의미 | 필수 여부 |
|---|---|---|
| `id` | 프로젝트 식별자 | 필수 |
| `title` | 프로젝트 이름 | 필수 |
| `constructs` | 측정하려는 상위 구인 | 필수 |
| `ksas` | 구인의 하위 지식, 기술, 태도 또는 속성 | 필수 |
| `evidence_claims` | 응답으로 뒷받침하려는 주장 | 필수 |
| `task_models` | 응답자가 수행할 과제 형식 | 필수 |
| `parent_templates` | 문항 생성 규칙과 변수 도메인 | 생성 시 필수 |
| `response_scale` | 응답 척도와 점수 앵커 | 필수 |
| `items` | 생성 또는 반입된 후보 문항 | 필수 |
| `reviews` | 전문가 검토 결정 | 파일럿 준비 전 필수 |
| `metadata` | 추가 기록 | 선택 |

### 문항 계보

모든 문항은 다음 연결을 가져야 한다.

```text
item.construct_id
item.ksa_id
item.evidence_claim_id
item.task_model_id
item.parent_template_id
```

연결값이 없으면 도구가 임의로 측정 의미를 만들어 내지 않는다. 특히 `import-items`는 외부 문항의 `construct_id`, `ksa_id`, `evidence_claim_id`를 추측하지 않는다.

### 최소 문항 예시

```json
{
  "id": "ITEM-001",
  "construct_id": "construct_work_stress",
  "ksa_id": "ksa_deadline_pressure",
  "evidence_claim_id": "claim_deadline_pressure",
  "task_model_id": "task_self_report_likert",
  "parent_template_id": "tpl_deadline_001",
  "variables": {
    "work_situation": "마감 기한이 가까워질 때",
    "negative_response": "압박감"
  },
  "stem": "나는 마감 기한이 가까워질 때 압박감을 느낀다.",
  "scoring": {
    "direction": "positive",
    "valid_scores": [1, 2, 3, 4, 5]
  },
  "status": "generated"
}
```

## 6. 핵심 명령어

먼저 실행 환경을 설정한다.

```powershell
$env:PYTHONPATH='src'
```

### 기본 보고서

```powershell
py -m ecd_aig pre-response examples\job_stress_workload_12item_user_project.json --markdown
```

이 명령은 사전점검 상태를 한 번에 보여 준다.

| 상태 | 의미 |
|---|---|
| `revision_required` | 구조 또는 품질 게이트에서 수정 필요 |
| `ready_for_expert_review` | 자동 점검은 통과했지만 전문가 결정 미완료 |
| `ready_for_pilot_administration` | 사전점검과 전문가 검토 완료. 파일럿 조사 후보로 이동 가능 |

`ready_for_pilot_administration`도 경험적 타당도 확보를 뜻하지 않는다.

### 세부 명령어

| 명령어 | 역할 |
|---|---|
| `validate` | ECD 계보, 점수화, 중복, 민감 표현 구조 점검 |
| `audit-items --strict` | 문항 품질 위험 점검 |
| `generate --template ID --count N` | 부모 템플릿에서 후보 문항 생성 |
| `llm-generate --template ID --count N` | Gemini로 부모 템플릿 범위 안의 후보 문항 생성 |
| `import-items INPUT --out OUTPUT` | 외부 후보 문항 가져오기 |
| `blueprint` | KSA와 템플릿별 문항 분포 확인 |
| `review-status` | 전문가 검토 상태 확인 |
| `caf` | CAF 설계 지도 출력 |
| `toulmin --item ID` | 문항별 측정 논증 출력 |
| `dossier --item ID` | 사전점검 근거 묶음 출력 |
| `export-items --format FORMAT --out PATH` | 후보 문항 내보내기 |
| `webapp` | 로컬 확인 화면 실행 |

`webapp` 화면에서는 `examples` 폴더에서 `items` 목록을 가진 JSON 프로젝트를 선택할 수 있다. `examples` 밖의 경로는 로딩하지 않는다.

### 응답자료 이후에만 사용하는 명령어

| 명령어 | 역할 |
|---|---|
| `responses PROJECT CSV` | 파일럿 응답 파일 형식과 점수화 확인 |
| `psychometrics PROJECT CSV` | 기초 CTT 통계와 Cronbach alpha 계산 |

현재 프로토타입은 완전한 IRT 또는 DIF 분석 도구가 아니다.

`psychometrics`는 결측 응답이 있을 때 문항 통계와 수정 문항-총점 상관에 사용 가능한 응답을 사용하고, Cronbach alpha는 complete case만 사용한다. 출력의 `alpha_respondents`, `missing_summary`, `warnings`를 함께 확인해야 한다.

## 7. 구조 게이트

`validate`는 네 가지 게이트를 실행한다.

| 게이트 | 확인 내용 |
|---|---|
| `traceability` | construct, KSA, evidence claim, task model, parent template 연결 |
| `scoring_readiness` | 응답척도와 문항 점수화 메타데이터 연결 |
| `redundancy` | 동일 문항 문구의 결정론적 중복 |
| `sensitivity` | 감시 대상 민감 표현 포함 여부 |

이 검사는 자동 규칙 기반이다. 의미 판단이 필요한 항목은 전문가 검토가 필요하다.

`audit-items`의 결과는 `automated_rule_based` screening이다. construct alignment, construct drift, 맥락상 임상어의 적절성, 응답척도 적합성은 전문가 검토 영역으로 남는다.

## 8. 파일별 역할

| 파일 | 역할 |
|---|---|
| `models.py` | 프로젝트 JSON 로딩과 저장 |
| `generation.py` | 부모 템플릿 기반 후보 문항 생성 |
| `import_items.py` | 외부 후보 문항 반입 |
| `validation.py` | 구조 게이트 |
| `item_quality.py` | 문항 품질 게이트 |
| `pre_response.py` | 응답 전 준비 상태 통합 보고서 |
| `blueprint.py` | 문항 배분과 변수 커버리지 |
| `review.py` | 전문가 결정 상태 |
| `caf.py` | CAF 설계 지도 |
| `toulmin.py` | 문항별 측정 논증 |
| `dossier.py` | 사전점검 근거 묶음 |
| `export.py` | CSV, JSON, LMS JSON, QTI-lite 출력 |
| `response_data.py` | 후속 단계 응답자료 점검 |
| `psychometrics.py` | 후속 단계 기초 CTT 분석 |

`qti-lite`는 정식 IMS QTI 운영 패키지가 아니다. 실제 LMS 연동 전에는 대상 LMS 규격과 정식 QTI 패키징 요구사항을 별도로 검토한다.

## 9. 권장 운영 절차

1. 연구자가 construct, KSA, evidence claim을 먼저 작성한다.
2. task model과 parent template을 작성한다.
3. `generate` 또는 `import-items`로 후보 문항을 준비한다.
4. `pre-response` 보고서에서 `revision_required` 항목을 수정한다.
5. 전문가가 각 문항을 `approve`, `revise`, `reject`로 판정한다.
6. 승인 후보를 내보내 파일럿 조사를 실시한다.
7. 응답자료가 확보된 뒤 별도의 실증 분석 단계로 이동한다.

## 10. 보고서 작성 시 권장 문구

다음 표현을 사용한다.

> ECD-AIG 구조를 통해 자동 생성 후보 문항의 설계 계보와 응답 전 구조적 위험을 점검하였다. 이 결과는 경험적 타당도 확보를 의미하지 않으며, 신뢰도, 요인구조, IRT 및 DIF 분석은 파일럿 응답자료 수집 이후에 수행되어야 한다.

다음 표현은 사용하지 않는다.

> 자동 생성 문항의 타당도를 검증하였다.

## 11. GitHub Pages 후보 문항 생성 화면 코드북

공유 웹 화면은 `pages/index.html`과 저장소 최상단 `index.html`에 들어 있는 정적 HTML 앱이다. 별도 서버 없이 브라우저에서 직접 LLM API를 호출한다.

### 화면 입력값

| 화면 항목 | 의미 | 기본 동작 |
|---|---|---|
| `사용할 API` | `Gemini`, `OpenAI`, `Claude` 중 하나 | API 주소는 내부에서 고정 |
| `API 키` | 선택한 제공자의 API 키 | 기본 화면에서 바로 입력 |
| `이 브라우저에 키 저장` | 현재 브라우저 localStorage에 키 저장 | 공용 PC에서는 사용하지 않는 것을 권장 |
| `무엇을 측정할까요?` | 생성할 문항의 측정 초점 | 내부 부모 템플릿의 `measurement_focus`로 사용 |
| `어떤 맥락의 문항이 필요한가요?` | 문항 상황 도메인 | 문항마다 다른 구체적 상황을 요구하는 프롬프트로 사용 |
| `개수` | 생성할 후보 문항 수 | 1-30개 |
| `모델 설정` | 선택한 제공자의 모델 이름 | 기본은 접혀 있음 |

기본 사용자는 `사용할 API`, `API 키`, 측정 내용, 맥락, 개수만 입력하면 된다. API 주소는 사용자가 직접 입력하지 않는다.

### 지원 API

지원 범위는 다음 세 가지로 제한한다.

| 제공자 | 기본 모델 | 내부 호출 주소 | 인증 방식 |
|---|---|---|---|
| `Gemini` | `gemini-2.5-flash` | Google Generative Language `generateContent` | `x-goog-api-key` |
| `OpenAI` | `gpt-4.1-mini` | OpenAI Chat Completions | `Authorization: Bearer` |
| `Claude` | `claude-sonnet-4-6` | Anthropic Messages API | `x-api-key` |

`모델 설정`을 열면 모델 이름만 바꿀 수 있다. API 주소는 선택한 제공자에 따라 코드 내부에서 결정된다.

### 생성 결과 저장 방식

생성된 문항은 곧바로 최종 문항이 아니다. 화면 오른쪽에서 연구자가 저장할 문항만 `채택`으로 남기고, 필요하면 `검토 메모`를 적는다. 저장 버튼은 채택된 후보만 JSON으로 내려받는다.

저장 JSON에는 다음 정보가 포함된다.

| 필드 | 의미 |
|---|---|
| `parent_template` | 화면 입력값에서 자동 구성된 내부 부모 템플릿 |
| `generation_api` | 사용한 제공자, 모델, 내부 API 주소 |
| `status` | `expert_review_required` |
| `researcher_decision` | 저장 시 `accepted` |
| `researcher_note` | 연구자 검토 메모 |

이 화면에서 저장한 JSON 역시 응답자료 전 후보 문항 기록이다. 신뢰도, 요인구조, IRT, DIF 또는 운영 타당도 근거로 해석하지 않는다.

## Appendix: Gemini LLM candidate generation

Set the Google AI Studio API key in the environment and create a working copy.

```powershell
$env:GEMINI_API_KEY='YOUR_GOOGLE_AI_STUDIO_KEY'
Copy-Item examples\sample_project.json outputs\my_llm_project.json
```

Preview candidates without saving them.

```powershell
py -m ecd_aig llm-generate outputs\my_llm_project.json --template tpl_worry_001 --count 2 --markdown
```

Add `--write` only after reviewing the preview.

```powershell
py -m ecd_aig llm-generate outputs\my_llm_project.json --template tpl_worry_001 --count 2 --write --json
```

The parent-template variable values are examples and design context. The LLM may propose new context-appropriate task-feature values, so the user does not need to edit JSON before requesting a larger candidate set. Proposed values are recorded as `llm_proposed_for_expert_review`.

The generator removes repeated stems, repeated variable combinations within a batch, and combinations already saved for the same parent template. It requests only the missing number of candidates again, up to four attempts. Use `--brief` to describe the desired diversity in natural language.
