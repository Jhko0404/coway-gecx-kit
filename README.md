# 🏠 GECX Coway Rental Billing POC Kit

본 저장소는 Google Cloud의 **GECX (CX Agent Studio)** 플랫폼 상에서 코웨이의 스마트 가전 렌탈 요금 분석 생성형 AI 에이전트를 구성하고 배포하기 위한 **독립 실행형 패키지**입니다.

이 패키지는 플랫폼 이관에 필수적인 핵심 파이썬 커스텀 도구 및 프롬프트 인스트럭션, 모의 요금 API 서버 소스 코드를 포함하고 있으며, 누구든지 복제(Clone)하여 손쉽게 콘솔 구축 테스트를 수행할 수 있도록 완전히 상대적인 구조로 설계되었습니다.

---

## 📂 저장소 주요 구성 요소

*   **배포 가이드 ([DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md))**: GCP Cloud Run 모의 API 배포부터 GECX 웹 콘솔상의 에이전트, 툴셋, 6대 도구 설정까지 전체 과정을 해설하는 단계별 설명서입니다.
*   **요금 분석 시나리오 흐름도 ([FLOW_DIAGRAM.md](./FLOW_DIAGRAM.md))**: 고객이 요금을 질문했을 때 에이전트 간의 전환 동작 및 백엔드 API와의 시퀀스를 도식화한 아키텍처 흐름도입니다.
*   **표준 가이드 준수 보고서 ([BEST_PRACTICES.md](./BEST_PRACTICES.md))**: Google Cloud 공식 GECX 에이전트 설계 및 도구 정의 모범 사례(Best Practices & Patterns)에 맞춘 설계 준수 내역 해설서입니다.
*   **[tools/](./tools/)**: GECX 커스텀 파이썬 환경에 그대로 주입할 단일 파일 형태의 파이썬 비즈니스 로직(6개)
*   **[agent_configs/](./agent_configs/)**: 메인 상담 에이전트(`root_agent`) 및 요금 전문 에이전트(`billing_agent`)의 프롬프트 지침서
*   **[mock-billing-api/](./mock-billing-api/)**: 원클릭으로 구글 클라우드에 배포할 수 있는 FastAPI 기반의 모의 수납 청구 API 서버
*   **[mock_data/](./mock_data/)**: 시뮬레이터 검증 시나리오에 활용되는 2026년 2월 및 3월분 JSON 모의 고지서 원본 및 집계표

---

## 🚀 빠른 시작 (Quick Start)

본 패키지를 활용한 에이전트 구축 및 시연 검증은 다음의 흐름으로 진행됩니다.

1.  **모의 API 배포**: `./mock-billing-api` 소스코드를 Google Cloud Run에 배포하고 서비스 URL을 획득합니다.
2.  **스키마 반영**: `./toolsets/open_api_schema.yaml` 파일 내 `servers.url`에 해당 Cloud Run URL을 기재합니다.
3.  **GECX 콘솔 설정**: GECX 웹 콘솔에 로그인한 뒤, `./tools/` 경로의 파이썬 코드 및 `./agent_configs/` 의 지침서를 수동으로 복사-붙여넣기하여 에이전트 환경을 빌드합니다.
4.  **시뮬레이터 검증**: 제공되는 검증용 한국어 대화 시나리오 및 시뮬레이터 트레이스(Trace) 분석 가이드를 따라 연동 성공 여부를 디버깅합니다.

상세한 구축 명령어와 GECX 설정 캡처 가이드는 **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** 문서를 열어 참조하십시오!
