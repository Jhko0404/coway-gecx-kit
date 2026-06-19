# mock-billing-api/tests/test_billstore.py
"""데이터 저장소 로드 및 필터링 로직 유닛 테스트 모듈

이 모듈은 데이터 소스(JSON)를 파이썬 리스트 구조로 읽어온 뒤,
필터 조건(bill_id)에 부합하는지 여부와 반환 필드 제약 사항이 올바르게 
작업(Projection) 처리되는지를 검증하는 비즈니스 로직 유닛 테스트입니다.
"""
import os
import sys

# 상위 폴더(mock-billing-api)를 path에 삽입하여 billstore 모듈을 가져올 수 있도록 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from billstore import load_bills, query_bills  # noqa: E402

# 전체 청구서 리스트 로딩
BILLS = load_bills()
# 검증용 고지서 ID 정의
MAR_ID = "urn:purifier:rental:product:ban-billdoc:115720204-229428890-0121341447484"


def test_loads_two_bills():
    """데이터 폴더 내에서 정상적으로 2개의 고지서 JSON 파일을 로드했는지 확인합니다."""
    assert len(BILLS) == 2


def test_query_all_returns_full_bills():
    """ID 필터나 필드 제약 조건이 없을 때, 전체 2개 고지서가 상세 항목(billSummary)과 함께 전부 조회되는지 검증합니다."""
    out = query_bills(BILLS, bill_id="", fields="")
    assert len(out) == 2
    assert "billSummary" in out[0]


def test_query_by_bill_id_returns_one_full_bill():
    """특정 고지서 ID를 통해 조회 시 정확하게 일치하는 단 1개의 상세 고지서 객체가 반환되는지 확인합니다."""
    out = query_bills(BILLS, bill_id=MAR_ID, fields="")
    assert len(out) == 1
    assert out[0]["id"] == MAR_ID
    assert "billSummary" in out[0]


def test_query_unknown_id_returns_empty():
    """존재하지 않는 이상한 고지서 ID를 전달했을 때 빈 리스트([])를 반환하는지 대조합니다."""
    assert query_bills(BILLS, bill_id="nope", fields="") == []


def test_fields_narrowing():
    """요청한 fields 정보만 고지서 딕셔너리에서 선별적으로 가공(Projection)되어 반환되는지 확인합니다."""
    out = query_bills(BILLS, bill_id="",
                      fields="id,billDate,billingPeriod,amountDue,paymentDueDate")
    # 결과 객체의 키 세트가 요청한 파라미터 정보 셋과 완벽히 일치하는지 대조
    assert set(out[0].keys()) == {"id", "billDate", "billingPeriod", "amountDue", "paymentDueDate"}
