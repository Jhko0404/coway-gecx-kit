"""정수기 모의 렌탈 요금 API용 데이터 로드 및 필터링 모듈

본 모듈은 웹 프레임워크(FastAPI)와 무관하게 순수하게 청구서 JSON 파일을 로드하고,
ID 필터링 및 필드 선택(Projection/Field Narrowing) 연산을 수행하는 비즈니스 로직을 담고 있습니다.

주요 기능:
1. data/ 디렉터리 내 모든 청구서 JSON 데이터 자동 로드
2. 특정 고지서 ID(bill_id) 기준 데이터 필터링
3. 수신 데이터의 오버헤드를 줄이기 위한 특정 필드 선택 기능 (TMF 표준 Field Narrowing 기법 지원)
"""
import json
import os

# 고지서 JSON 데이터 파일들이 저장된 디렉터리 경로 설정
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_bills():
    """data/ 폴더 내의 모든 JSON 파일을 읽어 리스트로 반환합니다.
    
    Returns:
        list: 로드된 모든 고지서 객체(dict)들의 리스트
    """
    bills = []
    # 데이터 폴더 내 파일을 정렬하여 읽기
    for name in sorted(os.listdir(DATA_DIR)):
        if name.endswith(".json"):
            file_path = os.path.join(DATA_DIR, name)
            with open(file_path, "r", encoding="utf-8") as f:
                bills.append(json.load(f))
    return bills


def _project(bill, fields):
    """지정된 필드만 남기고 고지서 데이터 객체의 키를 필터링(축소)합니다.
    (API 응답 페이로드를 줄여주는 최적화 역할)

    Args:
        bill (dict): 단일 고지서 데이터 객체
        fields (str): 반환받고자 하는 필드명 목록 (쉼표 구분자 형식, 예: "id,billDate,amountDue")

    Returns:
        dict: 요청된 필드들만 포함된 축소된 고지서 객체
    """
    if not fields:
        return bill
    # 쉼표 기준 파싱 및 양끝 공백 제거
    keys = [k.strip() for k in fields.split(",") if k.strip()]
    # 고지서 객체에서 존재하는 키만 복사하여 반환
    return {k: bill[k] for k in keys if k in bill}


def query_bills(bills, bill_id="", fields=""):
    """청구서 목록에서 ID 조건으로 필터링하고 필드 제약 사항을 반영하여 반환합니다.

    Args:
        bills (list): 전체 고지서 리스트
        bill_id (str): 찾고자 하는 특정 고지서 ID (비어있을 시 전체 검색)
        fields (str): 축소 반환할 필드명 목록

    Returns:
        list: 조건에 맞게 가공된 고지서 목록 리스트
    """
    # bill_id가 지정된 경우 해당 ID가 일치하는 고지서만 필터링
    result = [b for b in bills if (not bill_id or b.get("id") == bill_id)]
    # 필터링된 결과 각각에 필드 축소(Projection) 적용 후 반환
    return [_project(b, fields) for b in result]
