from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import re


def extract_pcode(url: str) -> str:
    """URL에서 pcode 추출"""
    if not url or url == "N/A":
        return "N/A"
    m = re.search(r"pcode=(\d+)", url)
    return m.group(1) if m else "N/A"


def get_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 브라우저 창 안 띄우고 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)


def get_detail_image(driver, url):
    """상품 상세 페이지 대표 이미지"""
    try:
        driver.get(url)
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img#baseImage"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        img_tag = soup.select_one("img#baseImage")
        if not img_tag:
            return "N/A"

        if img_tag.has_attr("data-original"):
            return img_tag["data-original"]
        elif img_tag.has_attr("src"):
            src = img_tag["src"]
            return "http:" + src if src.startswith("//") else src
        return "N/A"
    except Exception:
        return "N/A"


def get_price_info(prod):
    """리스트에서 가격 추출"""
    try:
        pricelist = prod.select_one("div.prod_pricelist")
        if not pricelist:
            return []

        options = []
        li_tags = pricelist.select("ul > li")
        for li in li_tags:

            price_tag = li.select_one("p.price_sect a strong")
            price = price_tag.get_text(strip=True) + "원" if price_tag else "N/A"

            unit_price_tag = li.select_one("p.memory_sect span.memory_price_sect")
            unit_price = unit_price_tag.get_text(strip=True) if unit_price_tag else "N/A"

            capacity_text = None
            cap_tag = li.select_one("p.memory_sect span.text")
            if cap_tag:
                capacity_text = cap_tag.get_text(strip=True)

            pcode = None
            pcode_tag = li.select_one("input[name=compareValue]")
            if pcode_tag:
                pcode = pcode_tag.get("value")

            options.append({
                "pcode": pcode,
                "capacity": capacity_text,
                "price": price,
                "unit_price": unit_price
            })

        return options

    except Exception as e:
        print("get_price_info error:", e)
        return []


def get_detail_buy_link(driver, url):
    """개별 상품 상세 페이지에서 '구매하기' 버튼의 bridge URL 추출"""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.d_buy a.btn_buy.priceCompareBuyLink")
            )
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        buy_tag = soup.select_one("div.d_buy a.btn_buy.priceCompareBuyLink")
        if buy_tag and buy_tag.has_attr("href"):
            href = buy_tag["href"].strip()
            return "https:" + href if href.startswith("//") else href
        return "N/A"
    except Exception as e:
        print("get_detail_buy_link error:", e)
        return "N/A"


def resolve_final_url_with_selenium(driver, url):
    """다나와 bridge 링크를 Selenium으로 열어서 최종 쇼핑몰 URL 추출"""
    try:
        if not url or url == "N/A":
            return "N/A"
        driver.get(url)
        WebDriverWait(driver, 10).until(
            lambda d: "danawa.com/bridge" not in d.current_url
        )
        return driver.current_url
    except Exception as e:
        print("resolve_final_url_with_selenium error:", e)
        return url



def get_additional_info_case(driver, url):
    """케이스 상세 스펙 테이블 크롤링 (DB 저장용 전처리)"""
    try:
        driver.get(url + "#bookmark_product_information")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.prod_spec tbody tr"))
        )
        time.sleep(0.1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("div.prod_spec tbody tr")

        info_dict = {}
        key_map = {
            "제조회사": "manufacturer",
            "제품 분류": "case_type",
            "지원보드규격": "supported_board",
            "VGA 길이": "max_vga_length",
            "CPU쿨러 높이": "max_cpu_cooler_height",
            "케이스 크기": "case_size",
            "파워포함여부": "power_included",
            "지원파워규격": "supported_power",
            "8.9cm베이": "bay_8_9cm",
            "6.4cm베이": "bay_6_4cm",
            "저장장치 장착": "max_storage",
            "PCI 슬롯(수평)": "pci_slots",
            "프로젝트 제로": "project_zero",
            "스텔스": "stealth",
            "전면 패널 타입": "front_panel_type",
            "측면 패널 타입": "side_panel_type",
            "측면 개폐 방식": "side_opening",
            "먼지필터": "dust_filter",
            "쿨링팬": "total_fans",
            "LED팬": "led_fans",
            "전면": "led_front",
            "후면": "led_back",
            "내부 측면": "led_side",
            "내부 상단": "led_top",
            "미들타워": "middle_tower",
            "USB2.0": "usb2",
            "USB3.x 5Gbps": "usb3",
            "너비(W)": "width",
            "깊이(D)": "depth",
            "높이(H)": "height",
            "수직 PCI형태": "vertical_pci_type",
            "파워 장착 길이": "power_length",
            "파워 위치": "power_position",
            "수랭쿨러 규격": "max_watercooler_support",
            "라디에이터(상단)": "radiator_top",
            "라디에이터(후면)": "radiator_rear",
            "라디에이터(전면)": "radiator_front",
            "라디에이터(측면)": "radiator_side",
            "라디에이터(하단)": "radiator_bottom",
            "팬 컨트롤": "fan_control",
            "RGB 컨트롤": "rgb_control",
            "외부 LED": "outside_led"
        }

        skip_sections = ["등록년월", "적합성평가인증", "안전확인인증", "[부가기능]", "[추가기능]", "[변경사항]"]

        def parse_number(text):
            """숫자만 추출 (mm, 개수 등)"""
            if not text:
                return None
            nums = re.findall(r"\d+", text)
            return int(nums[0]) if nums else text
        
        number_keys = [
            "max_watercooler_support",
            "bay_8_9cm",
            "bay_6_4cm",
            "max_storage",
            "pci_slots",
            "total_fans",
            "led_fans"
        ]       

        for row in rows:
            ths = row.select("th")
            tds = row.select("td")

            for th, td in zip(ths, tds):
                key = th.get_text(strip=True)
                val = td.get_text(" ", strip=True)

                if not val and td.select_one("a"):
                    val = td.select_one("a").get_text(strip=True)

                if key in skip_sections or key == "":
                    continue

                eng_key = key_map.get(key, key)

                # 제조회사 처리
                if key == "제조회사":
                    first_link = td.select_one("a")
                    val = first_link.get_text(strip=True) if first_link else td.get_text(strip=True)

                # True/False 변환 (○ → True)
                if val in ["○", "지원", "있음", "포함", "파워포함"]:
                    info_dict[eng_key] = True
                elif val in ["-", "없음", "미지원", "미포함", "파워미포함"]:
                    info_dict[eng_key] = False
                elif val.strip() == "":
                    info_dict[eng_key] = None
                else:
                    if eng_key in number_keys:
                        info_dict[eng_key] = parse_number(val)
                    else:
                        info_dict[eng_key] = val

        return info_dict

    except Exception as e:
        print("get_additional_info_case error:", e)
        return {}


    
# 전처리 작업
def clean_number(text: str) -> int | None:
    """문자열에서 숫자만 추출 → int"""
    if not text or text == "N/A":
        return None
    nums = re.sub(r"[^0-9]", "", text)
    return int(nums) if nums else None

def preprocess_product(product: dict) -> dict:
    """크롤링된 상품 dict 전처리"""
    # modules 전처리
    if "modules" in product.get("options", {}):
        product["options"]["modules"] = clean_number(product["options"]["modules"])

    # price_info 전처리
    if "price_info" in product:
        price_info = product["price_info"]
        price_info["price"] = clean_number(price_info.get("price"))
        price_info["unit_price"] = clean_number(price_info.get("unit_price"))

    return product

def crawl_danawa_case():
    driver = get_driver()
    url = "https://prod.danawa.com/list/?cate=112775"
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    try:
        select_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "#danawa_content > div.product_list_wrap > div > div.prod_list_tab > div > div.view_opt > div > select.qnt_selector"))
        )
        Select(select_element).select_by_value("90")  # 90개 선택
        time.sleep(2)  # 목록 갱신 대기
    except Exception as e:
        print("[WARN] 목록 개수 90개 선택 실패:", e)

    results = []
    page = 1

    while True:
        # ✅ 상품 로딩 대기
        try:
            wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.prod_item"))
            )
        except:
            print(f"[END] {page}페이지 로딩 실패 → 종료")
            break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select("div.main_prodlist > ul.product_list > li.prod_item.prod_layer")

        if not products:
            print(f"[END] {page}페이지에 상품 없음 → 종료")
            break

        # ✅ 각 페이지 첫 번째 상품
        prod = products[0]

        name_tag = prod.select_one(".prod_info .prod_name a")
        date_tag = prod.select_one("dl.meta_item.mt_date dd")
        rank_tag = prod.select_one("strong.pop_rank")

        raw_rank = rank_tag.get_text(strip=True) if rank_tag else "N/A"
        match = re.search(r"\d+", raw_rank) if raw_rank != "N/A" else None
        pop_rank = int(match.group()) if match else "N/A"

        name = name_tag.text.strip() if name_tag else "N/A"
        link = name_tag["href"] if name_tag else "N/A"
        reg_date = date_tag.text.strip() if date_tag else "N/A"

        # 새 창 열기 (상세 페이지)
        main_window = driver.current_window_handle
        driver.execute_script("window.open(arguments[0]);", link)
        driver.switch_to.window(driver.window_handles[-1])

        try:
            # 상세 페이지 로딩
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img#baseImage"))
            )
            img = get_detail_image(driver, link)
            options = get_additional_info_case(driver, link) or {}
            manufacturer = options.pop("manufacturer", "N/A")

            # 가격 정보
            price_info_list = get_price_info(prod)

            product = {
                "page": page,
                "name": name,
                "image": img,
                "pop_rank": pop_rank,
                "reg_date": reg_date,
                "manufacturer": manufacturer,
                "type": "케이스",
                "options": options,
                "price_info": [],
            }

            for opt in price_info_list:
                pcode = opt.get("pcode")
                if not pcode or pcode == "N/A":
                    final_link = "N/A"
                else:
                    option_page = f"https://prod.danawa.com/info/?pcode={pcode}"

                    # ✅ 최저가 링크 새 창 열기
                    driver.execute_script("window.open(arguments[0]);", option_page)
                    driver.switch_to.window(driver.window_handles[-1])
                    try:
                        option_bridge_url = get_detail_buy_link(driver, option_page)
                        final_link = resolve_final_url_with_selenium(driver, option_bridge_url)
                    except:
                        final_link = "N/A"
                    driver.close()  # 최저가 창 닫기
                    driver.switch_to.window(driver.window_handles[-1])  # 상세 페이지로 복귀

                product["price_info"].append({
                    "option": opt.get("capacity", "N/A"),
                    "price": opt.get("price", "N/A").replace("원", "").strip(),
                    "pcode": pcode,
                    "link": final_link
                })

            # 최저가 계산
            valid_prices = []
            for p in product["price_info"]:
                digits = re.sub(r"[^\d]", "", p["price"])
                if digits:
                    valid_prices.append((int(digits), p))
            if valid_prices:
                _, lowest = min(valid_prices, key=lambda x: x[0])
                product["lowest_price"] = lowest
            else:
                product["lowest_price"] = {
                    "option": "N/A", "price": "N/A", "pcode": "N/A", "link": "N/A"
                }

            results.append(product)
            print(f"[INFO] {page}페이지 → {name}")

        finally:
            # 상세 페이지 닫고 리스트 페이지로 복귀
            driver.close()
            driver.switch_to.window(main_window)

        # ✅ 다음 페이지 이동
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            if page % 10 == 0:
                # 10, 20, 30... 페이지 → "다음 블록" 버튼
                next_block = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "#productListArea > div.prod_num_nav > div > a.edge_nav.nav_next")
                    )
                )
                driver.execute_script("arguments[0].click();", next_block)
            else:
                # 그 외→ 현재(now_on) 옆의 숫자 버튼
                next_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.num.now_on + a.num"))
                )
                driver.execute_script("arguments[0].click();", next_button)

            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.prod_item")))
            page += 1

        except Exception as e:
            print("[END] 더 이상 페이지 없음:", e)
            break

    driver.quit()
    save_to_json(results, "case_danawa.json")
    return results



def save_to_json(results, filename="case_danawa_test.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    results = crawl_danawa_case()
    save_to_json(results, "case_danawa_test.json")
    print("JSON 저장 완료")
