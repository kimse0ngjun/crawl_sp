import json

# 파일 불러오기
with open("ssd-product-2025-09-15-0009.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 중복 제거 기준: name
seen = set()
unique = []
duplicates = []

for item in data:
    key = item["name"]  # 필요에 따라 (item["name"], item["manufacturer"]) 등으로 확장 가능
    if key not in seen:
        unique.append(item)   # 첫 번째만 저장
        seen.add(key)
    else:
        duplicates.append(item)  # 이후 중복은 따로 모음

# 중복 제거된 데이터 저장
with open("ssd-product-2025-09-30-1439.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=4)

# 로그 출력
print(f"총 데이터 개수: {len(data)}")
print(f"중복 제거 후: {len(unique)}")
print(f"중복 발견: {len(duplicates)} 개")

print("\n중복 데이터 목록:")
for d in duplicates:
    print(d["name"], d["lowest_price"]["pcode"])
