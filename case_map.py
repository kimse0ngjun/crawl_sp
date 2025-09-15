import json

# 한글 키 → 영어 키 매핑
key_map = {
    "상단": "top",
    "하단": "bottom"
}

# JSON 파일 읽기
with open("case-product-2025-09-14-2045.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 키 변환 함수 (중첩 dict도 처리)
def convert_keys(obj):
    if isinstance(obj, dict):
        return {key_map.get(k, k): convert_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys(i) for i in obj]
    else:
        return obj

converted = convert_keys(data)

# 변환된 JSON 저장
with open("case-product-2025-09-14-2045-converted.json", "w", encoding="utf-8") as f:
    json.dump(converted, f, ensure_ascii=False, indent=4)