# 🏠 GECX Coway Rental Billing POC Kit 
본 저장소는 Google Cloud의 **GECX (CX Agent Studio)** 플랫폼 상에서 코웨이의 스마트 가전 렌탈 요금 분석 생성형 AI 에이전트를 구성하고 배포하기 위한 **독립 실행형 패키지**이자 배포 설명서입니다.

이 패키지는 플랫폼 이관에 필수적인 핵심 파이썬 커스텀 도구 및 프롬프트 인스트럭션, 모의 요금 API 서버 소스 코드를 포함하고 있으며, 누구든지 복제(Clone)하여 손쉽게 콘솔 구축 테스트를 수행할 수 있도록 완전히 상대적인 구조로 설계되었습니다.

---

## 📂 저장소 주요 구성 요소

*   **요금 분석 시나리오 흐름도 ([FLOW_DIAGRAM.md](./FLOW_DIAGRAM.md))**: 고객이 요금을 질문했을 때 에이전트 간의 전환 동작 및 백엔드 API와의 시퀀스를 도식화한 아키텍처 흐름도입니다.
*   **표준 가이드 준수 보고서 ([BEST_PRACTICES.md](./BEST_PRACTICES.md))**: Google Cloud 공식 GECX 에이전트 설계 및 도구 정의 모범 사례(Best Practices & Patterns)에 맞춘 설계 준수 내역 해설서입니다.
*   **[tools/](./tools/)**: GECX 커스텀 파이썬 환경에 그대로 주입할 단일 파일 형태의 파이썬 비즈니스 로직(6개)
    *   [lookup_customer.py](./tools/lookup_customer.py): 고객 정보 조회
    *   [list_invoices.py](./tools/list_invoices.py): 청구서 목록 조회
    *   [get_invoice_breakdown.py](./tools/get_invoice_breakdown.py): 기기별/계정 요금 세부 내역 조회
    *   [compare_invoices.py](./tools/compare_invoices.py): 전월 대비 요금 변동 요인 비교분석
    *   [update_language.py](./tools/update_language.py): 다국어 세션 변수(English/Korean) 전환
    *   [set_session_state.py](./tools/set_session_state.py): 세션 상태 변수 강제 설정 (상담사 연결용)
*   **[agent_configs/](./agent_configs/)**: 메인 상담 에이전트(`root_agent`) 및 요금 전문 에이전트(`billing_agent`)의 프롬프트 지침서
    *   [root_agent_instruction.txt](./agent_configs/root_agent_instruction.txt): 메인 상담원 지침서
    *   [billing_agent_instruction.txt](./agent_configs/billing_agent_instruction.txt): 요금 전문 상담원 지침서
*   **[toolsets/](./toolsets/)**: OpenAPI 스키마 정의
    *   [open_api_schema.yaml](./toolsets/open_api_schema.yaml): 코웨이 모의 API 연동 규격 스키마
*   **[mock-billing-api/](./mock-billing-api/)**: GCP Cloud Run에 배포할 모의 API 서버 소스 코드 (Python FastAPI)
*   **[mock_data/](./mock_data/)**: 시뮬레이터 검증 시나리오에 활용되는 2026년 2월 및 3월분 JSON 모의 고지서 원본 및 집계표
    *   [Bill-Feb-2026.json](./mock_data/Bill-Feb-2026.json): 2026년 2월분 고지서 원본
    *   [Bill-Mar-2026.json](./mock_data/Bill-Mar-2026.json): 2026년 3월분 고지서 원본
    *   [BILL_DATA_SUMMARY.md](./mock_data/BILL_DATA_SUMMARY.md): 샘플 고지서 주요 수치 요약집

---

## 🛠️ 사전 준비 사항 (Prerequisites)

1.  **Google Cloud Platform (GCP) 계정**: Cloud Run 서비스 배포 권한이 포함된 GCP 프로젝트 ID가 필요합니다.
2.  **GECX Agent Studio 콘솔 접근 권한**: GECX 애플리케이션 및 에이전트를 생성할 권한이 주어져야 합니다.
3.  **Google Cloud SDK (`gcloud` CLI)**: 로컬 터미널에 설치되어 있고 권한 인증이 완료되어 있어야 합니다. (로컬 설치 없이 GCP 웹 콘솔 내의 **Cloud Shell**을 활용하는 것도 가능합니다.)

---

## ⚙️ 단계별 배포 및 설정 절차

### 1단계: 모의 API 배포 (GCP Cloud Run)

에이전트가 호출할 백엔드 모의 API를 GCP에 컨테이너 형태로 배포합니다. 

#### 옵션 A: 로컬 터미널에서 `gcloud` CLI로 배포
1.  로컬 터미널을 열고 본 패키지의 모의 API 폴더로 이동합니다.
    ```bash
    cd mock-billing-api
    ```
2.  gcloud CLI가 대상 GCP 프로젝트로 설정되어 있는지 확인하고 로그인합니다.
    ```bash
    gcloud auth login
    gcloud config set project [GCP_PROJECT_ID]
    ```
3.  Cloud Run에 서비스를 빌드 및 배포합니다. (인증 없이 호출 가능하도록 설정)
    ```bash
    gcloud run deploy coway-bill-mock \
      --source . \
      --region us-central1 \
      --allow-unauthenticated
    ```
4.  배포가 완료되면 출력되는 **Service URL**을 복사해 둡니다.

#### 옵션 B: GCP 콘솔에서 GitHub 저장소를 직접 연결하여 배포 (GUI 방식)
1.  **GCP Cloud Run 콘솔**에 접속 후 **`서비스 만들기 (Create Service)`** 클릭.
2.  **`소스 저장소에서 배포 (Deploy from a source repository)`** 선택 후 **`클라우드 빌드 설정`** 클릭.
3.  GitHub 계정을 연동하고 본 코웨이 Repository를 선택합니다.
4.  **빌드 설정(Build Configuration)** 단계:
    *   **Branch**: `main`
    *   **Build Type**: `Dockerfile` 선택
    *   **Source directory**: `/mock-billing-api`
    *   **Dockerfile path**: `Dockerfile`
5.  **인증(Authentication)**에서 **`미인증 호출 허용`**을 선택하고 **`만들기 (Create)`**를 누릅니다.

---

### 2단계: OpenAPI 스키마에 서비스 주소 반영

1.  [toolsets/open_api_schema.yaml](./toolsets/open_api_schema.yaml#L6) 파일을 엽니다.
2.  `servers.url` 부분의 주소를 1단계에서 획득한 **Cloud Run 서비스 URL**로 대체하고 저장합니다.
    ```yaml
    servers:
      - url: https://coway-bill-mock-xxxxxxxx-uc.a.run.app   # 여기에 붙여넣기
    ```

---

### 3단계: GECX 콘솔에서 에이전트 설정

#### ① 새 GECX 애플리케이션 생성
1.  GECX Agent Studio 콘솔 메인 화면에서 **Create App**을 클릭합니다.
2.  설정을 기입합니다:
    *   **App Name**: `coway-gecx-agent`
    *   **Language controls**: `English (US)`로 유지합니다. (GECX UI의 한글 지원 한계로 인해 영어 기본 세션 상태에서 프롬프트 강제를 통해 한글을 구현합니다.)

#### ② OpenAPI 툴셋(Toolset) 등록
1.  좌측 메뉴 **Toolsets** ➔ **Create Toolset** 클릭.
2.  설정을 기입합니다:
    *   **Toolset Name**: `coway_billing`
    *   **Description**: `코웨이 고객 렌탈 청구서 조회 API`
    *   **Schema**: [open_api_schema.yaml](./toolsets/open_api_schema.yaml) 내용 전문 복사 후 붙여넣기.
    *   **Authentication (인증)**: 하단의 **Authentication** 섹션에서 **Service Agent ID Token**을 선택합니다. 
      *(참고: 1단계에서 모의 API를 `--allow-unauthenticated`로 배포했기 때문에 인증 없이도 호출되나, GECX 플랫폼의 표준 보안 연동 규격을 따르기 위해 ID Token 주입을 활성화합니다. 향후 Cloud Run에 비공개 액세스 권한을 강화할 경우 이 토큰이 활용됩니다.)*
3.  **Save**를 클릭하여 저장합니다.

#### ③ Custom Python 도구 6개 생성
좌측 메뉴의 **Tools** ➔ **Create Tool**을 누른 뒤, 각 툴 이름과 설명을 적고 지정된 파이썬 파일의 내용 전체를 복사하여 에디터에 붙여넣습니다. (도구 이름은 Python 함수명과 대소문자까지 완전히 일치해야 합니다.)

| 도구 이름 (Tool Name) | 설명 (Description) | 소스코드 파일 위치 (복사 대상) |
| :--- | :--- | :--- |
| **`lookup_customer`** | Looks up customer rental account details. | [lookup_customer.py](./tools/lookup_customer.py) |
| **`list_invoices`** | Lists available rental invoices. | [list_invoices.py](./tools/list_invoices.py) |
| **`get_invoice_breakdown`** | Breaks an invoice into charge categories. | [get_invoice_breakdown.py](./tools/get_invoice_breakdown.py) |
| **`compare_invoices`** | Compares two invoices and explains difference. | [compare_invoices.py](./tools/compare_invoices.py) |
| **`update_language`** | Sets active language explicitly. | [update_language.py](./tools/update_language.py) |
| **`set_session_state`** | Writes trigger variables to session state. | [set_session_state.py](./tools/set_session_state.py) |

> [!WARNING]
> 파이썬 도구 내부에는 컴파일 오류 및 문자 깨짐 방지를 위해 한글 주석이 배제되고 유니코드 이스케이프 기법이 적용되어 있으니, 반드시 지정된 `.py` 파일의 텍스트를 그대로 복사하여 입력해 주십시오.

#### ④ 신규 에이전트 생성 및 설정
좌측 메뉴 **Agents** ➔ **Create Agent**를 각각 실행하여 다음 두 개의 에이전트를 설정합니다. 
*(참고: 연결해야 하는 도구 중 `end_session`은 GECX가 기본 제공하는 시스템 내장 도구(System Tool)이므로, 따로 커스텀 생성할 필요 없이 체크박스만 선택하면 됩니다.)*

##### 1. `billing_agent`
*   **Agent Name**: `billing_agent`
*   **Instructions**: [billing_agent_instruction.txt](./agent_configs/billing_agent_instruction.txt) 내용 전체 복사-붙여넣기
*   **Linked Tools**: `set_session_state`, `lookup_customer`, `list_invoices`, `get_invoice_breakdown`, `compare_invoices`, `update_language`, `end_session` 체크
*   **Linked Toolsets**: `coway_billing` (호출 가능 오퍼레이션 `getInvoices` 체크)

##### 2. `root_agent`
*   **Agent Name**: `root_agent`
*   **Instructions**: [root_agent_instruction.txt](./agent_configs/root_agent_instruction.txt) 내용 전체 복사-붙여넣기
*   **Linked Tools**: `set_session_state`, `lookup_customer`, `update_language`, `end_session` 체크
*   **Child Agents**: `billing_agent` 연결 체크

#### ⑤ 애플리케이션 전역 설정 및 로그 활성화
1.  우측 상단의 **Settings (설정⚙️)** 아이콘 클릭.
2.  **Behavior**: **Allow user interruptions** 활성화 (On)
3.  **Logging**: **Enable Cloud Logging** 활성화 (On)
4.  **Tools**: **Execution mode**를 `Parallel` (병렬 호출)로 설정
5.  **Global instructions**: 아래 한글 대화 우회 강제 지침을 그대로 복사하여 입력:
    ```text
    Always reply to the user in the same language they used for their query. If the user speaks in Korean, you must output your response in Korean. If the user speaks in English, output in English. Never translate the user's conversation language to English unless explicitly requested.
    ```
6.  하단의 **Save** 클릭하여 저장.
7.  대시보드로 돌아와 메인 루트 에이전트 항목에 `root_agent`가 지정되어 있는지 재확인합니다.

---

## 🗣️ 4단계: E2E 시뮬레이터 검증 시나리오

GECX 콘솔 우측 상단의 **Test agent** 시뮬레이터를 켭니다. 
대화를 시작하기 전에, 시뮬레이터 패널 우측 상단의 톱니바퀴 옆 **Parameters** 버튼을 누르고 아래 세션 파라미터를 키-값(Key-Value) 쌍으로 수동 등록(Add Parameter)한 뒤 테스트를 시작해야 로그인 및 세션이 활성화됩니다.

*   **주입할 세션 파라미터 (Session Parameters)**:
    *   `auth_status` = `authenticated`
    *   `customer_name` = `홍길동`
    *   `account_id` = `urn:coway:rental:product:ban:115720204`
    *   `active_language` = `Korean`

### 대화 테스트 스크립트

1.  **시작 인사**:
    *   **에이전트**: *"안녕하세요, 홍길동 고객님. 코웨이 대표 고객센터 상담원입니다. 오늘 어떤 도움이 필요하신가요?"*
2.  **렌탈 요금 상세 조회 요청**:
    *   **사용자**: *"이번 달 고지서 요금 명세 좀 보여줘"*
    *   *(에이전트가 `billing_agent`로 세션 이동 후 `get_invoice_breakdown(month="latest")` 실행)*
    *   **에이전트**: 
        > 홍길동 고객님의 **2026년 3월 총 청구 금액은 5,370원**입니다.
        > 
        > **[요금 세부 내역]**
        > *   **기본 렌탈료**: 167,837원
        > *   **방문 케어 서비스료**: 6,689원
        > *   **소모품 및 필터 추가 구매 비용**: 3,008원
        > *   **제휴카드 및 패키지 결합 할인액**: -173,025원 (차감 완료)
        > 
        > 제품별 세부 요금 명세도 안내해 드릴까요?
3.  **지난달 대비 비교분석 요청**:
    *   **사용자**: *"이번 달 요금이 왜 지난달보다 더 나왔어?"*
    *   *(에이전트가 `compare_invoices(month="latest", compare_to="previous")` 실행)*
    *   **에이전트**: 
        > **2026년 3월 요금은 지난달(2월: -1,790원) 대비 총 7,160원 인상**되었습니다.
        > 
        > **[주요 변동 원인]**
        > *   **소모품 및 필터 추가 구매 비용 (기타 수수료)**: +3,580원 발생
        > *   **기본 렌탈료**: 비데(룰루) 제품의 일부 결합 할인 혜택 종료로 인해 +3,001원 인상
        > 
        > 추가적으로 궁금하신 점이 있으신가요?
4.  **다국어 영어 전환 테스트**:
    *   **사용자**: *"Can you explain that in English?"*
    *   *(에이전트가 `update_language(new_language="English")` 실행 후 즉시 전환)*
    *   **에이전트**: 
        > Sure, I can explain that in English.
        > 
        > **Your March bill is 5,370 KRW, which is 7,160 KRW higher** than your February bill (-1,790 KRW).
        > 
        > **[Key Drivers]**
        > *   **Other Fees**: +3,580 KRW
        > *   **Rental Fees**: +3,001 KRW (due to partial discount expiration on your bidet)

---

## 🔍 5단계: 시뮬레이터 내 실시간 OpenAPI 연동/도구 호출 디버깅 방법

Python 툴이 실제 백엔드 Mock API를 조회하는 두 차례의 REST API 호출 경로(`getInvoices`)가 제대로 연동되었는지 GECX 웹 콘솔에서 직접 확인하는 방법입니다.

1.  **시뮬레이터 추적창 활성화**:
    *   Test Agent 시뮬레이터 우측 패널에서 대화를 입력한 후, 하단의 **`Trace` (추적)** 탭을 엽니다.
2.  **도구 파라미터 로깅 확인**:
    *   도구 호출이 발생한 대화 턴의 로그 트리에서 `get_invoice_breakdown` 또는 `compare_invoices` 노드를 펼칩니다.
    *   **`Input` (입력)** 필드에 `month: "latest"` 또는 `compare_to: "previous"` 매개변수가 LLM에 의해 정상 추출되어 입력되었는지 검사합니다.
3.  **HTTP API 요청/응답 페이로드 추적 (콘솔 직접 검증)**:
    *   도구 로그 내부의 OpenAPI 연동 오퍼레이션(`coway_billing_getInvoices`) 로그 노드를 클릭합니다.
    *   여기서 **실제 HTTP Request URL**이 Cloud Run 주소(`https://coway-bill-mock-xxxxxxxx-uc.a.run.app/getInvoices?...`)로 정상 전송되었는지 조회할 수 있습니다.
    *   **`Response` (출력)** JSON 바디를 열어 TMF678 규격 고지서 원본 데이터(`{"id": "...", "amountDue": {"value": 5370.0}}`)가 Mock API 서버로부터 올바르게 반환되었는지 실시간으로 들여다볼 수 있습니다.
4.  **에러 유형 분석**:
    *   `Method not found`: 2단계에서 `open_api_schema.yaml` 내 `servers.url`에 Cloud Run 주소를 올바르게 반영했는지 점검하십시오.
    *   `401 Unauthorized` 또는 `403 Forbidden`: GECX 툴셋의 **인증 설정**에서 `Service Agent ID Token`을 올바르게 세팅했는지 확인하십시오.

---

## 🧪 6단계 (선택 사항) 로컬 환경에서 도구 작동 및 계산 정합성 테스트

본 키트에는 GECX 샌드박스에 업로드하기 전에, 파이썬 코드 내부의 요금 분석 계산 및 날짜 처리 로직이 제대로 작동하는지 검증할 수 있는 단위 테스트가 동봉되어 있습니다.

1.  패키지 루트 디렉토리에서 Python 가상 환경을 활성화하고 필요한 종속성 패키지를 설치합니다.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install pytest
    ```
2.  `pytest` 명령어를 실행하여 툴킷 비즈니스 로직과 API 모킹(Mocking) 테스트를 통과하는지 검사합니다.
    ```bash
    pytest
    ```
