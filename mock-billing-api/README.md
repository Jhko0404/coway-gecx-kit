# 코웨이 모의 렌탈 요금 API (Mock API)

이 모의 API 서버는 두 개의 샘플 렌탈 청구서 데이터를 `/coway/v1/rental-invoice` 경로를 통해 제공합니다. 

쿼리 매개변수는 GECX OpenAPI 툴셋이 정상적으로 인식하고 바인딩할 수 있도록 파이썬 식별자 안전 이름(`customer_id`, `bill_id`)을 사용하도록 설계되었습니다.

---

## 💻 1. 로컬 실행 방법
```bash
# mock-billing-api 디렉터리로 이동
cd mock-billing-api

# 모의 API 서버 구동
uvicorn app:app --reload --port 8080

# curl 명령어로 요금 조회 테스트
curl 'http://localhost:8080/coway/v1/rental-invoice?customer_id=urn:coway:rental:product:ban:115720204&fields=id,amountDue'
```

---

## 🚀 2. Cloud Run 배포 방법 (프로젝트: gemeni-workshop)
```bash
# GCP Cloud Run에 무인증 접근 허용으로 배포
gcloud run deploy coway-bill-mock \
  --source . \
  --region us-central1 \
  --project gemeni-workshop \
  --allow-unauthenticated
```
*   *(배포 완료 후 반환되는 Service URL을 OpenAPI 스펙 `open_api_schema.yaml` 파일의 `servers.url` 부분에 업데이트해 주십시오.)*
