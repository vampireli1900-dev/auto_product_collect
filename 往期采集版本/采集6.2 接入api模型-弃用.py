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
from zhipuai import ZhipuAI
logging.disable(logging.WARNING)  # 关闭警告
YOLO().verbose = False            # 关闭 YOLO 检测打印

# ====================== 初始化 ======================
d = u2.connect()
model = YOLO("../runs/detect/pdd_logo_train-2/weights/best.pt")
subsidy_model = YOLO("../runs/detect/subsidy_train/weights/best.pt")
detail_model = YOLO("../runs/detect/product_detail_train/weights/best.pt")
reader = easyocr.Reader(['ch_sim'], gpu=False)
API_KEY = "f95ee93c19db4b9c935d2815211ef146.8yjbjcS2vM6auXbR"

# ====================== 【商品搜索名单】 ======================
PRODUCT_LIST = [

    "雪花秀顺行三件套",
    "后男士两件套",
    "后拱辰享美白两件套",
    "Whoo后拱辰享美黄金气垫粉底液#21正装+带双替换",
    "科颜氏男士保湿三件套"
]

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


# ====================== 🔥 GLM-4.7-Flash 语义切割匹配 ======================
def is_same_product_by_llm(search_word, product_title):
    # 提示词：一次请求同时拆分两个文本
    cut_prompt = """
请严格按要求执行，不要分析、不要解释、不要步骤、不要思考过程。
将下面【文本1】和【文本2】分别拆分为词语单元。
规则：
1. 每个词语单元不超过5个汉字
2. 多个词语只用空格隔开
3. 删除所有标点、符号、特殊字符
4. 输出格式：只返回两行，第一行是文本1的结果，第二行是文本2的结果

文本1：{search}
文本2：{title}
"""

    try:
        client = ZhipuAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[
                {"role": "user", "content": cut_prompt.format(search=search_word, title=product_title)}
            ],
            thinking={
                "type": "enabled",    # 你指定的，我不动
            },
            temperature=0.0,
            max_tokens=65536,
            stream=False,
            timeout=30
        )

        # 一次请求拿到结果，按行拆分
        content = response.choices[0].message.content.strip()
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        search_result = lines[0] if len(lines) >= 1 else ""
        title_result = lines[1] if len(lines) >= 2 else ""

        # 转成列表格式（兼容你原有逻辑）
        search_units = re.sub(r'[^\w\s]', ' ', search_result).lower().split()
        title_units = re.sub(r'[^\w\s]', ' ', title_result).lower().split()

    except Exception as e:
        print('❌ GLM 调用异常：', str(e))
        # 兜底本地分词
        search_units = list(re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', search_word.lower()))
        title_units = list(re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', product_title.lower()))

    # ======================
    # 你原有逻辑 完全不动
    # ======================
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

# ====================== 3. 优先级排序 ======================
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

# ====================== 5. 商品名称+价格提取（二元+单字兜底+中文数量规则） ======================
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

    # ========================== 【强力修复：价格过滤】 ==========================
    price_pattern = r'[¥￥]\s*(\d+(?:\.\d+)?)'
    all_prices = re.findall(price_pattern, xml_content)
    price_nums = [float(p) for p in all_prices]

    original_price = None
    current_price = None

    if len(price_nums) > 0:
        # 去重
        prices = sorted(list(set(price_nums)))
        valid = []

        # 你定的规则：前3位相同，并且大10倍 → 删掉大的
        for i in prices:
            keep = True
            for j in prices:
                if i == j:
                    continue
                # 10倍关系
                if max(i, j) >= min(i, j) * 10:
                    # 转整数，判断前3位
                    s_i = str(int(round(i)))
                    s_j = str(int(round(j)))
                    if len(s_i) >= 3 and len(s_j) >= 3 and s_i[:3] == s_j[:3]:
                        # 大的那个丢掉
                        if i > j:
                            keep = False
                        break
            if keep:
                valid.append(i)

        # 最终有效价格
        if valid:
            current_price = str(min(valid))
            original_price = str(max(valid))
    # ==========================================================================

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

# ====================== 7. 生产日期 ======================
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

# ====================== 8. 单个商品采集 + 即时存入记录 ======================
def collect_single_product(search_word):
    xml = d.dump_hierarchy(pretty=True)
    product_info = extract_product_info(xml, search_word)
    is_subsidy = is_subsidy_product()

    title = product_info["title"]
    original_price = product_info["original_price"]
    current_price = product_info["current_price"]

    subsidy_str = "是" if is_subsidy else "否"

    # 进入详情拿生产日期
    found_detail = find_and_click_detail()
    produce_date = get_date_with_retry() if found_detail else ""

    # 规格暂时空置
    spec_str = ""

    # 🔥 拆分：原价、现价 独立两列
    row_data = [
        title,
        search_word,
        spec_str,
        original_price,
        current_price,
        subsidy_str,
        produce_date
    ]

    # 存入全局列表
    record_list.append(row_data)

    # 控制台打印
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

    # AI匹配校验
    if not is_same_product_by_llm(search_word, title):
        print("❌ AI 判定：商品不匹配")
        return "NOT_MATCH"

    return {
        "title": title,
        "subsidy": is_subsidy,
        "produce_date": produce_date,
        "found_detail": found_detail
    }

# ====================== 9. 遍历同优先级全部商品，全部采集 ======================
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
        # 返回列表
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

# ====================== 10. 主循环 ======================
def main():
    print("🚀 启动自动搜索 + 全商品采集 + Excel导出")
    for keyword in PRODUCT_LIST:
        search_product(keyword)
        select_and_collect_best_product(keyword)
        time.sleep(1)
        print(f"\n=====================================")
        print(f"✅ 【{keyword}】全部商品采集完成")
        print(f"=====================================")
    # 全部跑完统一保存Excel
    save_all_to_excel()
    print("\n🎉 全部商品采集任务结束！")

if __name__ == "__main__":
    main()