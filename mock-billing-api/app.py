"""코웨이 모의 렌탈 요금 API 서비스 — /coway/v1/rental-invoice 경로로 샘플 고지서 데이터 반환.

POC 환경 제약: 본 테스트용 API는 입력받은 customer_id에 관계없이 기등록된 샘플 계정 데이터로 간주하여 처리합니다.
반환되는 데이터 구조는 표준 렌탈 고지서 규격을 따르며, 에이전트 툴(Wrapper)이 실제 백엔드 연동 환경처럼 완벽히 동작하도록 돕습니다.

쿼리 매개변수는 GECX OpenAPI 툴셋이 파라미터를 파이썬의 kwargs로 정확하게 바인딩할 수 있도록,
점(`.`) 표기법이 배제된 파이썬 식별자 안전 이름(customer_id, bill_id, fields)을 적용했습니다.
"""
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from billstore import load_bills, query_bills

# FastAPI 애플리케이션 정의
app = FastAPI(title="Coway Rental Invoice API (mock)")

# 서버 메모리에 모의 청구 데이터 로딩
BILLS = load_bills()


@app.get("/coway/v1/rental-invoice")
def get_bills(
    customer_id: str = Query(..., description="고객 청구 계정 식별자 URN"),
    bill_id: Optional[str] = Query(None, description="특정 고지서 상세 조회를 위한 고지서 고유 ID"),
    fields: Optional[str] = Query(None, description="응답 최적화를 위해 필터링(축소)하여 받고자 하는 필드명 목록"),
):
    """고객 ID를 기준으로 고지서 목록 또는 특정 고지서의 상세 내역을 필터링하여 반환합니다."""
    return JSONResponse(query_bills(BILLS, bill_id=bill_id or "", fields=fields or ""))


@app.get("/healthz")
def healthz():
    """서버 작동 여부를 검증하기 위한 헬스 체크 엔드포인트입니다."""
    return {"status": "ok"}
