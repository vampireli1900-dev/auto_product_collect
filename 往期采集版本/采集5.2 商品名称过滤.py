import uiautomator2 as u2
import cv2
from ultralytics import YOLO
import time
import re
import requests
import easyocr

# ====================== 初始化 ======================
d = u2.connect()
model = YOLO("../runs/detect/pdd_logo_train-2/weights/best.pt")
subsidy_model = YOLO("../runs/detect/subsidy_train/weights/best.pt")
detail_model = YOLO("../runs/detect/product_detail_train/weights/best.pt")
reader = easyocr.Reader(['ch_sim'], gpu=False)

# ====================== 【商品搜索名单】 ======================
PRODUCT_LIST = [
    "倩碧水嫩保湿三件套裝",
    "娇韵诗 多元日晚面霜套装",
    "娇韵诗双萃眼霜紧致两件套",
    "赫莲娜 黑白绷带日晚面霜套装",
    "娇韵诗 弹簧两件套",
    "娇韵诗 美白三件套",
    "娇韵诗 弹簧三件套",
    "娇韵诗 孕妇两件套",
    "碧欧泉 男士水动力3件套",
    "兰蔻 菁纯臻颜三件套",
    "SK2多方位三件套",
    "后水妍两件套盒",
    "后天气丹华泫套盒",
    "雪花秀滋盈肌本舒活2件套 318ml",
    "雪花秀顺行三件套 575ml",
    "whoo后男士套装拱辰享君王套盒",
    "后Whoo拱辰享雪美白两件套",
    "后Whoo拱辰享美黄金气垫13G+替换装13G*2#21",
    "Kiehls科颜氏男士保湿三件套"
]

# ====================== 🔥 最终版：AI语义切割匹配（Qwen:4b） ======================
def is_same_product_by_llm(search_word, product_title):
    # ========== 统一提示词：语义切割 + 每个单元≤5字符 + 无标点 ==========
    cut_prompt = """
请把下面的文本，按中文语义切成独立词语单元。
规则：
1. 每个单元不超过5个字符
2. 只用空格分隔
3. 不要任何标点符号
4. 不要解释，只输出切割结果

文本：
"""

    def ai_cut(text):
        """内部函数：调用模型做语义切割"""
        try:
            resp = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "qwen:4b",
                    "prompt": cut_prompt + text,
                    "stream": False,
                    "temperature": 0.0,
                    "top_p": 0.1
                },
                timeout=20
            )
            raw = resp.json()["response"].strip()
            # 清洗：去标点 → 小写 → 切词
            clean = re.sub(r'[^\w\s]', ' ', raw).lower()
            return [w for w in clean.split() if w]
        except:
            return text.lower().split()

    # ========== 核心：两边都用 AI 语义切割 ==========
    title_units = ai_cut(product_title)
    search_units = ai_cut(search_word)

    print(f"[DEBUG] 标题语义单元: {title_units}")
    print(f"[DEBUG] 搜索词语义单元: {search_units}")

    # ========== 匹配：搜索词每个词都能在标题找到 ==========
    hit = 0
    for s in search_units:
        if any(s in t for t in title_units):
            hit += 1
    name_ok = hit > 0

    # ========== 规格判断 ==========
    search_has_digit = any(c.isdigit() for c in "".join(search_units))
    title_has_digit = any(c.isdigit() for c in "".join(title_units))
    spec_ok = not search_has_digit or title_has_digit

    final = name_ok and spec_ok
    print(f"[DEBUG] 核心词匹配: {name_ok} | 规格匹配: {spec_ok}")
    print(f"[DEBUG] 最终判定: {final}")
    return final


# ====================== 1. 搜索功能 ======================
def search_product(keyword):
    print(f"\n🔍 开始搜索商品：{keyword}")
    width, height = d.window_size()
    search_y = int(height * 200 / 2400)
    d.swipe(width // 2, height // 2, width // 2, height // 2 + 400)
    time.sleep(1)
    d.click(width // 2, search_y)
    time.sleep(0.8)
    d(className="android.widget.EditText").clear_text()
    d(className="android.widget.EditText").set_text(keyword)
    time.sleep(0.8)
    d(text="搜索", className="android.widget.TextView").click()
    print("✅ 搜索完成，等待列表加载")
    time.sleep(3)


# ====================== 2. 列表页商品标签识别 ======================
def scan_list_products():
    d.screenshot("list_screen.jpg")
    img = cv2.imread("../list_screen.jpg")
    results = model(img, conf=0.25)
    debug_img = results[0].plot()  # 画出检测框
    cv2.imwrite("../debug_detection.jpg", debug_img)

    # ====================== 🔥 展示调试窗口 ======================
    cv2.imshow("YOLO 列表商品检测", debug_img)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()

    products = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            conf = box.conf[0].item()
            if conf < 0.5:
                continue
            cls = int(box.cls)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            if cls == 0:
                products.append({"type": "baiyi", "cx": cx, "cy": cy})
            elif cls == 1:
                products.append({"type": "brand", "cx": cx, "cy": cy})
            elif cls == 2:
                products.append({"type": "global", "cx": cx, "cy": cy})
    return products


def get_products_with_tags():
    products = scan_list_products()
    grouped = {}
    for p in products:
        cx, cy = p["cx"], p["cy"]
        matched = False
        for key in list(grouped.keys()):
            existing_cx, existing_cy = key
            same_column = abs(cx - existing_cx) < 200
            same_row = abs(cy - existing_cy) < 180
            if same_column and same_row:
                grouped[key]["tags"].add(p["type"])
                matched = True
                break
        if not matched:
            grouped[(cx, cy)] = {"tags": {p["type"]}, "cx": cx, "cy": cy}
    return list(grouped.values())


# ====================== 3. 排序 ======================
def get_priority(tags):
    if "baiyi" in tags and "brand" in tags:
        return 4
    elif "brand" in tags:
        return 3
    elif "baiyi" in tags:
        return 2
    elif "global" in tags:
        return 1
    else:
        return 0

def sort_products_by_priority(products):
    return sorted(products, key=lambda p: get_priority(p["tags"]), reverse=True)


# ====================== 4. 补贴判断 ======================
def is_subsidy_product():
    xml = d.dump_hierarchy()
    return "百亿补贴" in xml or "官方补贴" in xml



# ====================== 5. 商品信息提取 ======================
def extract_product_info(xml_content, search_word):
    import re

    # 生成二元连续分割
    def get_ngram_pairs(text, n=2):
        text = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', text.lower())
        return [text[i:i+n] for i in range(len(text)-n+1)] if len(text) >= n else [text]

    # 生成单字分割（兜底）
    def get_single_chars(text):
        text = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', text.lower())
        return [c for c in text]

    # 统计中文字符数量
    def count_chinese(text):
        return len(re.findall(r'[\u4e00-\u9fff]', text))

    search_cn_count = count_chinese(search_word)
    desc_list = re.findall(r'content-desc="([^"]+)"', xml_content)

    best_title = ""
    best_count = 0

    # ============= 先使用二元组匹配 =============
    search_pairs = get_ngram_pairs(search_word)

    for desc in desc_list:
        desc = desc.strip()

        blacklist = [
            "电池", "状态栏", "电量", "百分之", "WLAN", "手机信号", "5G", "4G",
            "通知", "天气", "高德", "淘宝", "浏览器", "手机管家", "振铃器", "静音",
            "返回", "分享", "店铺", "收藏", "客服", "工具栏", "顶部", "拼小圈",
            "¥", "￥", "大促价", "已抢", "假一赔十", "正品", "100%正品", "拼单价",
            "狂降", "直接成团", "买过", "次", "图片", "该店", "tronplayer_view"
        ]
        if any(kw in desc for kw in blacklist):
            continue

        if count_chinese(desc) < search_cn_count:
            continue

        desc_clean = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', desc.lower())
        match_count = sum(1 for p in search_pairs if p in desc_clean)

        if match_count > best_count:
            best_count = match_count
            best_title = desc
        elif match_count == best_count and match_count > 0:
            if len(desc) > len(best_title):
                best_title = desc

    # ============= 兜底：如果为空，切换单字匹配 =============
    if not best_title:
        search_chars = get_single_chars(search_word)
        best_count = 0
        for desc in desc_list:
            desc = desc.strip()

            blacklist = [
                "电池", "状态栏", "电量", "百分之", "WLAN", "手机信号", "5G", "4G",
                "通知", "天气", "高德", "淘宝", "浏览器", "手机管家", "振铃器", "静音",
                "返回", "分享", "店铺", "收藏", "客服", "工具栏", "顶部", "拼小圈",
                "¥", "￥", "大促价", "已抢", "假一赔十", "100%正品", "拼单价",
                "狂降", "直接成团", "买过", "次", "图片", "该店", "tronplayer_view"
            ]
            if any(kw in desc for kw in blacklist):
                continue

            if count_chinese(desc) < search_cn_count:
                continue

            desc_clean = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', desc.lower())
            match_count = sum(1 for c in search_chars if c in desc_clean)

            if match_count > best_count:
                best_count = match_count
                best_title = desc
            elif match_count == best_count and match_count > 0:
                if len(desc) > len(best_title):
                    best_title = desc

    # 价格逻辑：最大原价，最小现价
    price_pattern = r'[¥￥]\s*(\d+(?:\.\d+)?)'
    all_prices = re.findall(price_pattern, xml_content)
    price_nums = [float(p) for p in all_prices]

    original_price = None
    current_price = None
    if len(price_nums) > 0:
        current_price = str(min(price_nums))
        original_price = str(max(price_nums))

    return {
        "title": best_title.strip() if best_title else "",
        "original_price": original_price,
        "current_price": current_price
    }


# ====================== 6. 详情模块 ======================
def find_and_click_detail(max_scroll=6):
    for _ in range(max_scroll):
        img = d.screenshot(format="opencv")
        results = detail_model(img, conf=0.75)

        target_box = None
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    target_box = (x1, y1, x2, y2)
                    break
            if target_box:
                break

        if target_box:
            x1, y1, x2, y2 = target_box

            img_show = img.copy()
            cv2.rectangle(img_show, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_show, "DETECT", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

            cv2.imshow("YOLO 检测区域", img_show)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()

            crop = img[y1:y2, x1:x2]
            cv2.imshow("裁剪区域 OCR", crop)
            cv2.waitKey(800)
            cv2.destroyAllWindows()

            ocr_text = reader.readtext(crop, detail=0)
            full_text = ''.join(ocr_text).replace(' ', '')
            print("OCR 识别结果：", full_text)

            if any(kw in full_text for kw in ["商品详情", "详情"]):
                cx, cy = (x1+x2)//2, (y1+y2)//2
                print("✅ 校验通过，点击")
                d.click(cx, cy)
                time.sleep(1.2)

                for _ in range(4):
                    xml = d.dump_hierarchy()
                    if any(k in xml for k in ["生产日期", "保质期"]):
                        print("✅ 找到生产日期")
                        return True
                    d.swipe(500, 1700, 500, 700, 0.2)
                    time.sleep(0.8)
                return False
            else:
                print("❌ 校验不通过，不是目标")

        d.swipe(500, 1800, 500, 600, 0.25)
        time.sleep(0.7)

    print("未找到商品详情")
    return False

# ====================== 7. 生产日期 ======================
def get_production_date_from_xml(xml_content):
    match = re.search(r'text="(\d{4}-\d{1,2}-\d{1,2})"', xml_content)
    return match.group(1) if match else None

def get_date_with_retry():
    for i in range(3):
        xml = d.dump_hierarchy(pretty=True)
        production_date = get_production_date_from_xml(xml)
        if production_date:
            print(f"✅ 生产日期提取成功：{production_date}")
            return production_date
        d.swipe(500, 1600, 500, 800)
        time.sleep(1)
    print("❌ 未找到生产日期")
    return None


# ====================== 8. 单个商品采集 ======================
def collect_single_product(search_word):
    xml = d.dump_hierarchy(pretty=True)
    product_info = extract_product_info(xml, search_word)
    is_subsidy = is_subsidy_product()

    title = product_info["title"]
    original_price = product_info["original_price"]
    current_price = product_info["current_price"]

    print("📌 是否百亿补贴：", is_subsidy)
    print("📦 商品名称：", title)
    print("💰 原价：", original_price)
    print("💰 现价：", current_price)

    # ======================
    # 🔥 AI语义匹配（已启用）
    # ======================
    print(f"🔍 正在 AI 校验商品是否匹配：{search_word}")
    if not is_same_product_by_llm(search_word, title):
        print("❌ AI 判定：商品不匹配，直接跳过")
        return "NOT_MATCH"

    found_detail = find_and_click_detail()
    production_date = None
    if found_detail:
        production_date = get_date_with_retry()

    print("📅 生产日期：", production_date)

    return {
        "subsidy": is_subsidy,
        "title": title,
        "original_price": original_price,
        "current_price": current_price,
        "produce_date": production_date,
        "found_detail": found_detail
    }


# ====================== 9. 批量采集 ======================
def select_and_collect_best_product(search_word):
    print("🔍 开始扫描列表页商品标签...")
    products = get_products_with_tags()
    if not products:
        print("❌ 未识别到任何标签商品")
        return None

    sorted_products = sort_products_by_priority(products)
    highest_priority = get_priority(sorted_products[0]["tags"])
    candidates = [p for p in sorted_products if get_priority(p["tags"]) == highest_priority]
    print(f"✅ 识别到 {len(candidates)} 个最高优先级商品")

    best_date = None
    best_product = None
    best_info = None
    time.sleep(1)

    for idx, p in enumerate(candidates):
        print(f"\n--- 进入商品 {idx + 1}/{len(candidates)} ---")
        click_x, click_y = p["cx"], p["cy"]
        d.click(click_x, click_y)
        time.sleep(1)

        info = collect_single_product(search_word)

        if info == "NOT_MATCH":
            print("🔙 商品不匹配，返回列表")
            d.press("back")
            time.sleep(1.5)
            continue

        production_date = info["produce_date"]
        found_detail = info["found_detail"]

        if production_date:
            if not best_date or production_date > best_date:
                best_date = production_date
                best_product = p
                best_info = info

        if found_detail:
            print("🔙 找到详情，返回2次回到列表")
            d.press("back")
            time.sleep(0.5)
            d.press("back")
            time.sleep(1.5)
        else:
            print("🔙 未找到详情，返回1次回到列表")
            d.press("back")
            time.sleep(1.5)

    if best_product:
        print(f"\n🏆 当前商品最优结果：{best_info}")
        return best_info
    else:
        return None


# ====================== 10. 主循环 ======================
def main():
    print("🚀 启动自动搜索 + 商品采集程序")
    for product in PRODUCT_LIST:
        search_product(product)
        select_and_collect_best_product(product)

        time.sleep(1)
        print(f"\n================================")
        print(f"✅ {product} 全部采集完成")
        print(f"================================")
    print("\n🎉 所有商品名单全部采集完毕！")


if __name__ == "__main__":
    main()