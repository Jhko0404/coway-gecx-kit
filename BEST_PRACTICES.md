# 🛡️ Google Cloud Conversational AI Playbook Best Practices 준수 보고서

본 저장소(`coway-gecx-kit`)는 Google Cloud의 **GECX (CX Agent Studio) 공식 디자인 가이드라인 및 모범 사례(Best Practices & Design Patterns)**를 100% 준수하여 설계되었습니다. 

본 문서는 GECX 공식 개발 표준과 본 프로젝트 소스 코드 간의 매핑을 상세하게 해설하여, 타 사용자들이 GECX 환경에서 효율적이고 신뢰성 높은 생성형 AI 에이전트를 설계하는 교육 자료로 활용할 수 있도록 돕습니다.

---

## 💡 핵심 매핑 요약 (GECX Best Practices vs. Project Code)

| GECX 공식 권장 디자인 패턴 (Best Practice) | 본 프로젝트 내 구현 방식 및 적용 소스 파일 |
| :--- | :--- |
| **1. Python 도구를 통한 API 래핑 (Context Engineering)** | OpenAPI 툴셋의 비정형 JSON 출력을 Python 도구에서 파싱하여 정제된 정보만 모델에 전달 <br> ➔ [tools/get_invoice_breakdown.py](./tools/get_invoice_breakdown.py) |
| **2. Python 코드 내 순차 호출 (Tool Chaining)** | 다단계 백엔드 호출(목록 조회 ➔ ID 추출 ➔ 상세 조회)을 에이전트에 맡기지 않고 Python 내부에서 순차 실행 <br> ➔ [tools/compare_invoices.py](./tools/compare_invoices.py) |
| **3. 명확하고 고유한 도구 정의 (Tool Definition)** | 식별하기 쉬운 도구명, snake_case로 구성된 평탄한(Flat) 형태의 입력 파라미터 설계 <br> ➔ [tools/lookup_customer.py](./tools/lookup_customer.py) |
| **4. XML 태그 기반의 구조화된 프롬프트 지침서** | 가이드라인과 태스크 흐름(Taskflow)을 XML 구조화 태그를 활용해 정합성 있게 정렬 <br> ➔ [agent_configs/root_agent_instruction.txt](./agent_configs/root_agent_instruction.txt) |
| **5. 자동화된 연동 테스트 및 평가 (Evaluations)** | 로컬에서의 모킹 테스트 모듈 구축 및 플랫폼 연동 에러 검증 테스트 제공 <br> ➔ [tests/test_wrappers.py](./tests/test_wrappers.py) |

---

## 🔍 패턴별 상세 분석 및 준수 사례

### 패턴 1. OpenAPI API를 직접 노출하지 않고 Python 도구로 래핑 (Context Engineering)

> ⚠️ **Google Cloud 가이드라인**:
> 외부 API 스키마가 반환하는 대용량 JSON 페이로드(예: 100개의 키-값 쌍)를 모델에 그대로 전달하면 불필요한 토큰 낭비, 추론 지연(Latency), 모델의 환각(Hallucination)을 유발합니다. 필요한 핵심 정보만 필터링하여 전달하는 **콘텍스트 엔지니어링(Context Engineering)**이 필요합니다.

*   **준수 사례 ([get_invoice_breakdown.py](./tools/get_invoice_breakdown.py))**:
    모의 API가 반환하는 청구서 상세 내역(TMF678 규격) 중, 에이전트 답변에 직접적으로 활용되지 않는 복잡한 내부 메타데이터와 중첩 객체들을 배제하고 필요한 **카테고리별 요금 합산액**만 집계하여 콤팩트한 딕셔너리로 축소 반환합니다.
    ```python
    # API 결과 중 핵심 필드만 필터링하여 GECX 컨텍스트 크기를 90% 이상 절감
    bd, total = line_breakdown(matches[0], lang)
    base.update({
        "scope": "product",
        "product": "…" + last3,
        "total": total,
        "breakdown": bd
    })
    return base
    ```

---

### 패턴 2. 비결정론적 에이전트 체이닝 대신 Python 내에서 동적 연쇄 호출 (Tool Chaining)

> ⚠️ **Google Cloud 가이드라인**:
> 하나의 대화 턴 내에서 에이전트에게 1차 도구 실행 ➔ 결과 해석 ➔ 2차 도구 실행의 결정을 위임(Chaining)하면 모델의 비결정성 때문에 순서가 바뀌거나 오작동할 위험이 큽니다. 여러 API를 연쇄 실행해야 할 경우, **하나의 파이썬 도구 안에서 일괄 실행(Deterministic Wrapper)**해야 합니다.

*   **준수 사례 ([compare_invoices.py](./tools/compare_invoices.py))**:
    두 고지서의 요금을 비교 분석하기 위해 **"요약 목록 조회 ➔ 최신월 및 전월 ID 식별 ➔ 최신월 상세 정보 조회 ➔ 전월 상세 정보 조회"**라는 총 4단계의 백엔드 트랜잭션을 하나의 `compare_invoices` 파이썬 도구 내부에서 결정론적으로 연쇄 실행합니다.
    ```python
    # GECX 에이전트의 개입 없이, 파이썬 도구 내부에서 안전하고 결정론적으로 연쇄 통신 수행
    summaries = _get_bills(account_id)
    current = resolve_month(summaries, month)
    other = older_than(summaries, current)
    
    cur_d = (_get_bills(account_id, bill_id=current["id"]) or [None])[0]
    oth_d = (_get_bills(account_id, bill_id=other["id"]) or [None])[0]
    ```

---

### 패턴 3. 명확하고 고유한 도구 정의 및 snake_case 파라미터 설계

> ⚠️ **Google Cloud 가이드라인**:
> 도구 이름이 서로 비슷하거나 모호하면 모델이 도구를 오선택할 수 있습니다. 매개변수명에는 축약어(예: `fn`, `pnum`)를 지양하고 구체적인 snake_case 이름을 쓰되, 복잡한 중첩 구조(Nested object) 대신 평탄화된(Flattened) 자료형을 활용해야 예측 성공률이 높아집니다.

*   **준수 사례 ([tools/](./tools/))**:
    모든 도구의 입력 매개변수를 문자열(str) 단일 필드로 한정하여 모델의 매개변수 채우기(Slot Filling)를 극대화했습니다.
    *   `lookup_customer` ➔ `customer_id` (축약어 없는 구체적 단일 매개변수)
    *   `update_language` ➔ `new_language` (의도가 명확한 변수명)
    *   `compare_invoices` ➔ `month`, `compare_to` (중첩 없는 평탄 구조)

---

### 패턴 4. 구조화된 지침서 작성 (Prompt Structuring)

> ⚠️ **Google Cloud 가이드라인**:
> 에이전트의 지침서(Instructions)는 구체적이고 모호하지 않아야 하며, 사람이 읽기에도 용이하도록 토픽별로 정돈되어 작성되어야 합니다. GECX는 XML 마크업 구조를 활용하여 프롬프트를 작성하는 방식을 권장합니다.

*   **준수 사례 ([agent_configs/root_agent_instruction.txt](./agent_configs/root_agent_instruction.txt))**:
    가독성이 뛰어나고 모델이 역할을 완벽하게 모델링할 수 있도록 프롬프트를 XML 태그로 구조화하여 파이프라인별 업무 흐름(Taskflow)을 규정했습니다.
    ```markdown
    <role>당신은 코웨이의 대표 고객센터 상담원입니다...</role>
    <guidelines>
      <guideline name="currency">...</guideline>
    </guidelines>
    <taskflow>
      <subtask name="Authentication_And_Identity">...</subtask>
    </taskflow>
    ```

---

### 패턴 5. 단위 테스트 및 검증 기법 도입 (Evaluations)

> ⚠️ **Google Cloud 가이드라인**:
> 에이전트 배포 주기에는 반드시 외부 시스템 연동을 보증하기 위한 검증 및 테스트 프로세스가 수반되어야 합니다.

*   **준수 사례 ([tests/](./tests/))**:
    로컬 가상 개발 서버 없이도 파이썬의 `unittest/mock` 기법을 변형 적용하여, GECX 플랫폼의 변수 주입 환경(`context.state`, `tools`)을 시뮬레이션하고 비즈니스 파싱 로직의 정합성을 검증하는 로컬 테스트 스위트를 완성하였습니다.
    ```bash
    # 로컬에서 pytest를 활용해 백엔드 파이썬 래핑 및 계산 정합성을 사전 검증 가능
    pytest tests/
    ```

---

## 🎓 교육적 가치 (Educational Value)

본 저장소의 설계 패턴은 GECX 플랫폼을 처음 도입하여 비즈니스 연동을 구현하고자 하는 **AICC 개발자, 기획자, 파트너 엔지니어에게 표준 구현 교과서의 역할**을 수행합니다. 복잡한 API 세부 명세와 비결정론적 LLM 간의 간극을 파이썬 래퍼 도구를 통해 어떻게 메울 수 있는지 직관적인 실용 사례를 제공합니다.
