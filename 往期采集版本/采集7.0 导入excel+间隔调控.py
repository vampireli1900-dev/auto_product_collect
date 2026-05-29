import uiautomator2 as u2
import cv2
from ultralytics import YOLO
import time
import re
import requests
import easyocr
import pandas as pd
import os
import logging
logging.disable(logging.WARNING)  # 关闭警告
YOLO().verbose = False            # 关闭 YOLO 检测打印

# ====================== 初始化 ======================
d = u2.connect()
model = YOLO("../runs/detect/pdd_logo_train-2/weights/best.pt")
subsidy_model = YOLO("../runs/detect/subsidy_train/weights/best.pt")
detail_model = YOLO("../runs/detect/product_detail_train/weights/best.pt")
reader = easyocr.Reader(['ch_sim'], gpu=False)

# ====================== 【新增配置项】 ======================
PRODUCT_LIST_FILE = "../模块开发/测试用例.xlsx"  # 商品名单Excel
SEARCH_INTERVAL_SECONDS = 5           # 每个商品采集完等待秒数

# ====================== 全局存储所有商品记录 ======================
record_list = []
# 自定义表头
EXCEL_HEADER = [
    "货品名称（详情页采集的）",
    "关键词（搜索的）",
    "规格",
    "原价",
    "现价",
    "是否百亿补贴产品",
    "生产日期"
]

# ====================== 保存Excel 追加写入 ======================
def save_all_to_excel():
    if not record_list:
        print("⚠️ 暂无采集数据，跳过保存")
        return
    df = pd.DataFrame(record_list, columns=EXCEL_HEADER)
    file = "../商品采集汇总.xlsx"
    if os.path.exists(file):
        old_df = pd.read_excel(file)
        df = pd.concat([old_df, df], ignore_index=True)
    df.to_excel(file, index=False)
    print(f"\n📁 已批量保存全部记录至：{file}，当前总行数：{len(df)}")

# ====================== 【新增】读取带续采状态的商品名单 ======================
def load_product_list_with_status():
    if not os.path.exists(PRODUCT_LIST_FILE):
        print(f"❌ 未找到名单文件：{PRODUCT_LIST_FILE}")
        return []

    df = pd.read_excel(PRODUCT_LIST_FILE)

    if "货品名称" not in df.columns:
        print("❌ Excel必须包含列：货品名称")
        return []

    if "状态" not in df.columns:
        df["状态"] = "未采集"

    todo = df[df["状态"] == "未采集"]["货品名称"].dropna().astype(str).tolist()
    total = len(df)
    done = len(df[df["状态"] == "已采集"])

    print(f"✅ 总商品数：{total} | 已采集：{done} | 待采集：{len(todo)}")
    return todo

# ====================== 【新增】标记商品为已采集 ======================
def mark_product_as_done(product_name):
    df = pd.read_excel(PRODUCT_LIST_FILE)
    df.loc[df["货品名称"] == product_name, "状态"] = "已采集"
    df.to_excel(PRODUCT_LIST_FILE, index=False)
    print(f"✅ 已标记完成：{product_name}")

# ====================== 🔥 AI语义切割匹配（Qwen:4b）—— 你原版，完全不动 ======================
def is_same_product_by_llm(search_word, product_title):
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
        try:
            resp = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "qwen:4b",
                    "prompt": cut_prompt + text,
                    "stream": False,
                    "temperature": 0.0,
                    "top_p": 0.1,
                    "context": []
                },
                timeout=20
            )
            raw = resp.json()["response"].strip()
            clean = re.sub(r'[^\w\s]', ' ', raw).lower()
            return [w for w in clean.split() if w]
        except Exception as e:
            print('❌ AI对话异常：', str(e))
            clean_text = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', text.lower())
            return [c for c in clean_text]

    title_units = ai_cut(product_title)
    search_units = ai_cut(search_word)

    print(f"[DEBUG] 标题语义单元: {title_units}")
    print(f"[DEBUG] 搜索词语义单元: {search_units}")

    hit = 0
    for s in search_units:
        if any(s in t for t in title_units):
            hit += 1
    name_ok = hit > 0

    search_has_digit = any(c.isdigit() for c in "".join(search_units))
    title_has_digit = any(c.isdigit() for c in "".join(title_units))
    spec_ok = not search_has_digit or title_has_digit

    final = name_ok and spec_ok
    print(f"[DEBUG] 核心词匹配: {name_ok} | 规格匹配: {spec_ok}")
    print(f"[DEBUG] 最终判定: {final}")
    return final

# ====================== 1. 搜索功能（不动） ======================
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

# ====================== 2. 列表页商品标签识别（不动） ======================
def scan_list_products():
    d.screenshot("list_screen.jpg")
    img = cv2.imread("../list_screen.jpg")
    results = model(img, conf=0.25)
    debug_img = results[0].plot()
    cv2.imwrite("../debug_detection.jpg", debug_img)

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

# ====================== 3. 优先级排序（不动） ======================
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

# ====================== 4. 补贴判断（不动） ======================
def is_subsidy_product():
    xml = d.dump_hierarchy()
    return "百亿补贴" in xml or "官方补贴" in xml

# ====================== 5. 商品名称+价格提取（不动） ======================
def extract_product_info(xml_content, search_word):
    import re
    def get_ngram_pairs(text, n=2):
        text = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', text.lower())
        return [text[i:i+n] for i in range(len(text)-n+1)] if len(text) >= n else [text]

    def get_single_chars(text):
        text = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', text.lower())
        return [c for c in text]

    def count_chinese(text):
        return len(re.findall(r'[\u4e00-\u9fff]', text))

    search_cn_count = count_chinese(search_word)
    desc_list = re.findall(r'content-desc="([^"]+)"', xml_content)

    best_title = ""
    best_count = 0

    blacklist = [
        "电池", "状态栏", "电量", "百分之", "WLAN", "手机信号", "5G", "4G",
        "通知", "高德", "淘宝", "浏览器", "手机管家", "振铃器", "静音",
        "返回", "分享", "店铺", "收藏", "客服", "工具栏", "顶部", "拼小圈",
        "¥", "￥", "大促价", "已抢", "假一赔十", "100%正品", "拼单价",
        "狂降", "直接成团", "买过", "次", "图片", "该店", "tronplayer_view", "查看全部"
    ]

    search_pairs = get_ngram_pairs(search_word)
    for desc in desc_list:
        desc = desc.strip()
        if any(kw in desc for kw in blacklist):
            continue
        if count_chinese(desc) < search_cn_count:
            continue
        desc_clean = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', desc.lower())
        match_count = sum(1 for p in search_pairs if p in desc_clean)
        if match_count > best_count and match_count > 0:
            best_count = match_count
            best_title = desc
        elif match_count == best_count and match_count > 0:
            if len(desc) > len(best_title):
                best_title = desc

    if not best_title:
        search_chars = get_single_chars(search_word)
        best_count = 0
        for desc in desc_list:
            desc = desc.strip()
            if any(kw in desc for kw in blacklist):
                continue
            if count_chinese(desc) < search_cn_count:
                continue
            desc_clean = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', desc.lower())
            match_count = sum(1 for c in search_chars if c in desc_clean)
            if match_count > best_count and match_count > 0:
                best_count = match_count
                best_title = desc
            elif match_count == best_count and match_count > 0:
                if len(desc) > len(best_title):
                    best_title = desc

    price_pattern = r'[¥￥]\s*(\d+(?:\.\d+)?)'
    all_prices = re.findall(price_pattern, xml_content)
    price_nums = [float(p) for p in all_prices]

    original_price = None
    current_price = None

    if len(price_nums) > 0:
        prices = sorted(list(set(price_nums)))
        valid = []
        for i in prices:
            keep = True
            for j in prices:
                if i == j:
                    continue
                if max(i, j) >= min(i, j) * 10:
                    s_i = str(int(round(i)))
                    s_j = str(int(round(j)))
                    if len(s_i) >= 3 and len(s_j) >= 3 and s_i[:3] == s_j[:3]:
                        if i > j:
                            keep = False
                        break
            if keep:
                valid.append(i)
        if valid:
            current_price = str(min(valid))
            original_price = str(max(valid))

    return {
        "title": best_title.strip() if best_title else "",
        "original_price": original_price,
        "current_price": current_price
    }

# ====================== 6. 详情模块（不动） ======================
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
            ocr_text = reader.readtext(crop, detail=0)
            full_text = ''.join(ocr_text).replace(' ', '')
            if any(kw in full_text for kw in ["商品详情", "详情"]):
                cx, cy = (x1+x2)//2, (y1+y2)//2
                d.click(cx, cy)
                time.sleep(1.2)
                for _ in range(4):
                    xml = d.dump_hierarchy()
                    if any(k in xml for k in ["生产日期", "保质期"]):
                        return True
                    d.swipe(500, 1700, 500, 700, 0.2)
                    time.sleep(0.8)
                return False
        d.swipe(500, 1800, 500, 600, 0.25)
        time.sleep(0.7)
    return False

# ====================== 7. 生产日期（不动） ======================
def get_production_date_from_xml(xml_content):
    match = re.search(r'text="(\d{4}-\d{1,2}-\d{1,2})"', xml_content)
    return match.group(1) if match else None

def get_date_with_retry():
    for i in range(3):
        xml = d.dump_hierarchy(pretty=True)
        pd = get_production_date_from_xml(xml)
        if pd:
            return pd
        d.swipe(500, 1600, 500, 800)
        time.sleep(1)
    return None

# ====================== 8. 单个商品采集（不动） ======================
def collect_single_product(search_word):
    xml = d.dump_hierarchy(pretty=True)
    product_info = extract_product_info(xml, search_word)
    is_subsidy = is_subsidy_product()

    title = product_info["title"]
    original_price = product_info["original_price"]
    current_price = product_info["current_price"]

    subsidy_str = "是" if is_subsidy else "否"

    found_detail = find_and_click_detail()
    produce_date = get_date_with_retry() if found_detail else ""
    spec_str = ""

    row_data = [
        title,
        search_word,
        spec_str,
        original_price,
        current_price,
        subsidy_str,
        produce_date
    ]

    record_list.append(row_data)

    print("\n" + "="*80)
    print("📋 本条采集记录：")
    print(f"货品名称：{title}")
    print(f"搜索关键词：{search_word}")
    print(f"规格：{spec_str}")
    print(f"原价：{original_price}")
    print(f"现价：{current_price}")
    print(f"是否百亿补贴：{subsidy_str}")
    print(f"生产日期：{produce_date}")
    print("="*80)

    if not is_same_product_by_llm(search_word, title):
        print("❌ AI 判定：商品不匹配")
        return "NOT_MATCH"

    return {
        "title": title,
        "subsidy": is_subsidy,
        "produce_date": produce_date,
        "found_detail": found_detail
    }

# ====================== 9. 遍历同优先级全部商品（不动） ======================
def select_and_collect_best_product(search_word):
    print("🔍 开始扫描列表页商品标签...")
    products = get_products_with_tags()
    if not products:
        print("❌ 未识别到任何标签商品")
        return None

    sorted_products = sort_products_by_priority(products)
    highest_priority = get_priority(sorted_products[0]["tags"])
    candidates = [p for p in sorted_products if get_priority(p["tags"]) == highest_priority]
    print(f"✅ 识别到 {len(candidates)} 个最高优先级商品，全部采集")

    for idx, p in enumerate(candidates):
        print(f"\n--- 进入商品【{idx + 1}/{len(candidates)}】---")
        d.click(p["cx"], p["cy"])
        time.sleep(1)
        res = collect_single_product(search_word)
        if res == "NOT_MATCH":
            d.press("back")
            time.sleep(1.5)
        else:
            if res["found_detail"]:
                d.press("back")
                time.sleep(0.5)
                d.press("back")
                time.sleep(1.5)
            else:
                d.press("back")
                time.sleep(1.5)
    return True

# ====================== 10. 主循环（已改造：续采 + 间隔 + 标记） ======================
def main():
    print("🚀 启动自动搜索 + 全商品采集 + Excel导出 + 中断续采")

    # 读取待采集列表
    PRODUCT_LIST = load_product_list_with_status()
    if not PRODUCT_LIST:
        print("🎉 所有商品已全部采集完成！")
        return

    for keyword in PRODUCT_LIST:
        search_product(keyword)
        select_and_collect_best_product(keyword)

        # 标记已完成并保存
        mark_product_as_done(keyword)
        save_all_to_excel()

        # 商品间等待
        print(f"\n⏳ 等待 {SEARCH_INTERVAL_SECONDS} 秒后继续...")
        time.sleep(SEARCH_INTERVAL_SECONDS)

        print(f"\n=====================================")
        print(f"✅ 【{keyword}】全部商品采集完成")
        print(f"=====================================")

    print("\n🎉 全部商品采集任务结束！")

if __name__ == "__main__":
    main()