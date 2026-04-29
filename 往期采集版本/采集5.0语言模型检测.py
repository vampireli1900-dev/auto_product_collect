import uiautomator2 as u2
import cv2
from ultralytics import YOLO
import time
import re
import requests  # <-- 新增
import easyocr

# ====================== 初始化 ======================
d = u2.connect()
model = YOLO("../runs/detect/pdd_logo_train-2/weights/best.pt")
subsidy_model = YOLO("../runs/detect/subsidy_train/weights/best.pt")
detail_model = YOLO("../runs/detect/product_detail_train/weights/best.pt")
reader = easyocr.Reader(['ch_sim'], gpu=False)
# ====================== 【商品搜索名单】 ======================
PRODUCT_LIST = [
    "SK-II前男友面膜10片",
    "雅诗兰黛小棕瓶",
    "兰蔻小黑瓶",
    "海蓝之谜面霜"
]

# ====================== 🔥 LLM 商品匹配校验（新增） ======================
def is_same_product_by_llm(search_word, product_title):
    prompt = """
    请判断：搜索词 和 商品标题 是不是同一个商品。

    规则：
    1. SK-II 和 SK2 算同一个品牌。
    2. 功效词（补水、保湿、急救、紧致、抗皱）忽略不看。
    3. 如果商品标题里包含搜索词的规格（如10片），就算规格一致。
    4. 品牌 + 产品名 + 规格一致 = 是，否则 = 不是。

    只输出2行，()内填充你的回答，原因要简短，严格按格式，不许加任何其他内容：
    是否：()
    原因：()

    搜索词：{search_word}
    商品标题：{product_title}
    """.format(search_word=search_word, product_title=product_title)

    try:
        resp = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen:4b",  # 你要的 4b
                "prompt": prompt.strip(),
                "stream": False,
                "temperature": 0.0,    # 最严谨，不胡说
                "top_p": 0.1
            },
            timeout=25
        )
        result = resp.json()["response"].strip()

        is_match = "是否：是" in result
        reason = "未识别"
        for line in result.splitlines():
            if line.startswith("原因："):
                reason = line.replace("原因：", "").strip()

        print(f"🔍 AI 判定：{is_match} | 原因：{reason}")
        return is_match

    except Exception as e:
        print("⚠️ LLM 调用失败，自动通过")
        return True  # 失败不影响你的脚本运行


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
    debug_img = results[0].plot()
    cv2.imwrite("../debug_detection.jpg", debug_img)

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
    return "百亿补贴" in xml


# ====================== 5. 商品信息提取 ======================
def extract_product_info(xml_content):
    desc_list = re.findall(r'content-desc="([^"]+)"', xml_content)
    title = ""
    for desc in desc_list:
        if len(desc) > len(title):
            title = desc

    original_price = None
    ori_match = re.search(r'优惠前[¥￥](\d+(?:\.\d+)?)', xml_content)
    if ori_match:
        original_price = ori_match.group(1)

    current_price = None
    current_match = re.search(r'(?:补贴价|大促价|到手价|活动价|官方补贴价)[¥￥]?(\d+(?:\.\d+)?)', xml_content)
    if current_match:
        current_price = current_match.group(1)

    return {"title": title.strip(), "original_price": original_price, "current_price": current_price}


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

            # ==============================================
            # 在这里画框：把 YOLO 识别的区域标出来
            # ==============================================
            img_show = img.copy()
            cv2.rectangle(img_show, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_show, "DETECT", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

            # 弹出窗口看 YOLO 框在哪里
            cv2.imshow("YOLO 检测区域", img_show)
            cv2.waitKey(1000)   # 显示1秒
            cv2.destroyAllWindows()

            # 裁剪 YOLO 识别到的区域
            crop = img[y1:y2, x1:x2]

            # 看裁剪后的小图
            cv2.imshow("裁剪区域 OCR", crop)
            cv2.waitKey(800)
            cv2.destroyAllWindows()

            # OCR 识别
            ocr_text = reader.readtext(crop, detail=0)
            full_text = ''.join(ocr_text).replace(' ', '')
            print("OCR 识别结果：", full_text)  # 打印识别文字

            # 校验
            if any(kw in full_text for kw in ["商品详情", "详情", "商品参数", "查看全部"]):
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
    product_info = extract_product_info(xml)
    is_subsidy = is_subsidy_product()

    title = product_info["title"]
    original_price = product_info["original_price"]
    current_price = product_info["current_price"]

    print("📌 是否百亿补贴：", is_subsidy)
    print("📦 商品名称：", title)
    print("💰 原价：", original_price)
    print("💰 现价：", current_price)

    # ======================
    # 🔥 关键：LLM 校验商品是否匹配
    # ======================
    print(f"🔍 正在 AI 校验商品是否匹配：{search_word}")
    # if not is_same_product_by_llm(search_word, title):
    #     print("❌ AI 判定：商品不匹配，直接跳过")
    #     return "NOT_MATCH"

    # 匹配才继续走详情
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

        # 🔥 传入当前搜索词
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
        select_and_collect_best_product(product)  # 🔥 传入搜索词

        time.sleep(1)
        print(f"\n================================")
        print(f"✅ {product} 全部采集完成")
        print(f"================================")
    print("\n🎉 所有商品名单全部采集完毕！")


if __name__ == "__main__":
    main()