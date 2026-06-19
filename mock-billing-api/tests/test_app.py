# mock-billing-api/tests/test_app.py
"""FastAPI 웹 애플리케이션 엔드포인트 작동 테스트 모듈

이 모듈은 TestClient를 사용하여 실제 HTTP 요청 없이 FastAPI의 라우팅,
필수 쿼리 매개변수 유효성 검사, 필드 필터링(Projection)이 올바르게 
작동하는지 모의 검증(E2E)을 수행합니다.
"""
import os
import sys

# 상위 폴더(mock-billing-api)를 path에 삽입하여 app 모듈을 가져올 수 있도록 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient  # noqa: E402
from app import app  # noqa: E402

# 테스트를 위한 FastAPI 클라이언트 초기화
client = TestClient(app)

# 테스트에 사용될 가상 계정 ID(BAN) 및 특정 청구서 고유 ID(MAR_ID) 정의
BAN = "urn:coway:rental:product:ban:115720204"
MAR_ID = "urn:coway:rental:product:ban-billdoc:115720204-229428890-0121341447484"


def test_list_requires_customer_id():
    """요청 시 필수 값인 customer_id 누락 시 422 에러(유효성 검사 실패)가 발생하는지 검증합니다."""
    # 필수 파라미터가 없으므로 422 Unprocessable Entity 에러 반환 확인
    assert client.get("/coway/v1/rental-invoice").status_code == 422


def test_list_returns_array_of_two():
    """정상적인 고객 ID로 조회했을 때 총 2개의 고지서 데이터 목록이 반환되는지 확인합니다."""
    # 정상 파라미터 전달
    r = client.get("/coway/v1/rental-invoice", params={"customer_id": BAN})
    assert r.status_code == 200
    # 등록된 샘플 데이터 개수인 2개 확인
    assert len(r.json()) == 2


def test_fields_narrowing():
    """fields 파라미터를 사용해 요청한 필드(id, billDate 등)만 결과 키에 한정되어 출력되는지 검증합니다."""
    fields_query = "id,billDate,billingPeriod,amountDue,paymentDueDate"
    r = client.get("/coway/v1/rental-invoice",
                   params={"customer_id": BAN, "fields": fields_query})
    
    assert r.status_code == 200
    # 반환받은 첫 번째 고지서의 JSON 키 셋이 요청한 필드 셋과 완벽히 일치하는지 대조
    assert set(r.json()[0].keys()) == {
        "id", "billDate", "billingPeriod", "amountDue", "paymentDueDate"}


def test_bill_id_filter_returns_one_full():
    """bill_id 필터를 지정해 요청했을 때, 일치하는 고지서 딱 1개만 세부 내역까지 정상 로드되는지 확인합니다."""
    r = client.get("/coway/v1/rental-invoice", params={"customer_id": BAN, "bill_id": MAR_ID})
    body = r.json()
    
    assert r.status_code == 200
    # 결과가 1개이고, 해당 ID가 매칭되는지 확인. 상세 정보인 'billSummary' 필드가 존재하는지도 대조.
    assert len(body) == 1 and body[0]["id"] == MAR_ID and "billSummary" in body[0]
