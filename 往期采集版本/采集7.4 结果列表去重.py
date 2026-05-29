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
import subprocess  # 用于adb命令

logging.disable(logging.WARNING)
YOLO().verbose = False

# ====================== 初始化 ======================
d = u2.connect()
model = YOLO("../runs/detect/pdd_logo_train-2/weights/best.pt")
subsidy_model = YOLO("../runs/detect/subsidy_train/weights/best.pt")
detail_model = YOLO("../runs/detect/product_detail_train/weights/best.pt")
reader = easyocr.Reader(['ch_sim'], gpu=False)

# ====================== 【新增配置项】 ======================
PRODUCT_LIST_FILE = "../模块开发/测试用例.xlsx"
SEARCH_INTERVAL_SECONDS = 40
PACKAGE_NAME = "com.xunmeng.pinduoduo"  # 拼多多包名

# ====================== 全局存储所有商品记录 ======================
record_list = []

# ====================== 最新表头 ======================
EXCEL_HEADER = [
    "序号",
    "货品名称",
    "关键词",
    "原价",
    "现价",
    "是否百亿补贴产品",
    "生产日期"
]


# ====================== 保存Excel + 自动去重 ======================
def save_all_to_excel():
    if not record_list:
        print("⚠️ 暂无采集数据，跳过保存")
        return

    df = pd.DataFrame(record_list, columns=EXCEL_HEADER)
    file = "../商品采集汇总.xlsx"

    if os.path.exists(file):
        old_df = pd.read_excel(file)
        df = pd.concat([old_df, df], ignore_index=True)

    # ========== 去重核心：同序号 + 同货品名称 + 同现价 = 唯一 ==========
    df = df.drop_duplicates(
        subset=["序号", "货品名称", "现价"],
        keep="last"
    )

    df.to_excel(file, index=False)
    print(f"\n📁 已批量保存全部记录至：{file}，当前总行数：{len(df)}")


# ====================== 【终极稳定版：应用内强制回到首页】 ======================
def go_to_pinduoduo_home():
    print("\n🔴 检测到异常，正在强制跳回拼多多首页...")
    try:
        subprocess.run([
            "adb", "shell", "am", "start", "-S", "-n",
            "com.xunmeng.pinduoduo/com.xunmeng.pinduoduo.ui.activity.MainFrameActivity"
        ], check=True, timeout=15)
        time.sleep(6)
        print("🟢 已回到拼多多首页，准备重新采集")
    except Exception as e:
        print(f"❌ 跳转失败: {e}，尝试重启APP")
        subprocess.run(["adb", "shell", "am", "force-stop", "com.xunmeng.pinduoduo"])
        time.sleep(2)
        subprocess.run(["adb", "shell", "am", "start", "-n",
                        "com.xunmeng.pinduoduo/com.xunmeng.pinduoduo.ui.activity.MainFrameActivity"])
        time.sleep(8)


# ====================== 读取带续采状态的名单 ======================
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
    todo = df[df["状态"] == "未采集"].copy()
    total = len(df)
    done = len(df[df["状态"] == "已采集"])
    print(f"✅ 总商品数：{total} | 已采集：{done} | 待采集：{len(todo)}")
    return todo


# ====================== 标记商品为已采集 ======================
def mark_product_as_done(product_name):
    df = pd.read_excel(PRODUCT_LIST_FILE)
    df.loc[df["货品名称"] == product_name, "状态"] = "已采集"
    df.to_excel(PRODUCT_LIST_FILE, index=False)
    print(f"✅ 已标记完成：{product_name}")


# ====================== 🔥 AI语义切割匹配（你原版，完全不动） ======================
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
    img = cv2.imread("list_screen.jpg")
    results = model(img, conf=0.2)
    debug_img = results[0].plot()
    cv2.imwrite("debug_detection.jpg", debug_img)

    # cv2.imshow("YOLO 列表商品检测", debug_img)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()

    products = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
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


# ====================== 3. 优先级排序 + 全局GLOBAL翻页逻辑 ======================
def get_priority(tags):
    if "baiyi" in tags and "brand" in tags:
        return 4
    elif "baiyi" in tags:
        return 3
    elif "brand" in tags:
        return 2
    elif "global" in tags:
        return 1
    else:
        return 0


def is_all_global(item_list):
    """判断当前识别到的商品是否全部为global"""
    for item in item_list:
        if "baiyi" in item["tags"] or "brand" in item["tags"]:
            return False
    return True


def scroll_down_once():
    """单次向下翻页"""
    d.swipe(500, 1800, 500, 600, 0.3)
    time.sleep(2.5)


def scroll_to_top():
    """滑动返回列表顶部"""
    for _ in range(2):
        d.swipe(500, 600, 500, 1800, 0.3)
        time.sleep(0.8)


def sort_products_by_priority():
    raw_products = get_products_with_tags()

    # =============================================
    # ✅ 正确逻辑：逐页翻页，一旦发现非 global 就停止
    # =============================================
    if is_all_global(raw_products):
        print("⚠️ 当前页面全部为global标签，开始逐次翻页检测...")

        # 翻第1次
        scroll_down_once()
        raw_products = get_products_with_tags()
        if not is_all_global(raw_products):
            print("✅ 第1次翻页找到优质商品，停止翻页")

        else:
            # 第1次还是全 global → 翻第2次
            scroll_down_once()
            raw_products = get_products_with_tags()
            if not is_all_global(raw_products):
                print("✅ 第2次翻页找到优质商品，停止翻页")
            else:
                print("⚠️ 2次翻页仍全是global，返回顶部")
                scroll_to_top()
                time.sleep(2)
                raw_products = get_products_with_tags()

    # 排序
    sorted_products = sorted(raw_products, key=lambda p: get_priority(p["tags"]), reverse=True)

    # 如果还是全 global，只取前2个
    if is_all_global(sorted_products):
        sorted_products = sorted_products[:2]

    return sorted_products


# ====================== 4. 补贴判断 ======================
def is_subsidy_product():
    xml = d.dump_hierarchy()
    return "百亿补贴" in xml or "官方补贴" in xml


# ====================== 5. 商品名称+价格提取 ======================
def extract_product_info(xml_content, search_word):
    import re
    def get_ngram_pairs(text, n=2):
        text = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', text.lower())
        return [text[i:i + n] for i in range(len(text) - n + 1)] if len(text) >= n else [text]

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


# ====================== 6. 详情模块 ======================
def find_and_click_detail(max_scroll=7):
    for _ in range(max_scroll):
        img = d.screenshot(format="opencv")
        res = detail_model(img, conf=0.75)
        box = None

        for r in res:
            for b in r.boxes:
                if int(b.cls[0]) == 0:
                    box = tuple(map(int, b.xyxy[0]))
                    break
            if box:
                break

        if box:
            x1, y1, x2, y2 = box
            crop_img = img[y1:y2, x1:x2]

            ocr_result = reader.readtext(crop_img)
            full_text = ""
            for item in ocr_result:
                full_text += item[1]

            if "商品详情" in full_text:
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                d.click(cx, cy)
                time.sleep(1.5)

                page_xml = d.dump_hierarchy()
                if "生产日期" in page_xml:
                    return True
                else:
                    d.press("back")
                    return False

        d.swipe(500, 1600, 500, 900, 0.25)
        time.sleep(0.8)

    return False


# ====================== 7. 生产日期 ======================
def get_production_date_from_xml(xml_content):
    match = re.search(r'text="(\d{4}-\d{1,2}-\d{1,2})"', xml_content)
    return match.group(1) if match else None


def get_date_with_retry():
    xml = d.dump_hierarchy(pretty=True)
    pd = get_production_date_from_xml(xml)
    if pd:
        return pd
    else:
        return None


# ====================== 8. 单个商品采集 ======================
def collect_single_product(search_word, serial_num):
    xml = d.dump_hierarchy(pretty=True)
    product_info = extract_product_info(xml, search_word)
    is_subsidy = is_subsidy_product()

    title = product_info["title"]
    original_price = product_info["original_price"]
    current_price = product_info["current_price"]

    subsidy_str = "是" if is_subsidy else "否"

    found_detail = find_and_click_detail()
    produce_date = get_date_with_retry() if found_detail else ""

    # 最新结构（无规格）
    row_data = [
        serial_num,
        title,
        search_word,
        original_price,
        current_price,
        subsidy_str,
        produce_date
    ]

    record_list.append(row_data)

    # 原版打印完整保留
    print("\n" + "=" * 80)
    print("📋 本条采集记录：")
    print(f"货品名称：{title}")
    print(f"搜索关键词：{search_word}")
    print(f"原价：{original_price}")
    print(f"现价：{current_price}")
    print(f"是否百亿补贴：{subsidy_str}")
    print(f"生产日期：{produce_date}")
    print("=" * 80)

    # AI只做参考
    is_same_product_by_llm(search_word, title)

    return {
        "title": title,
        "subsidy": is_subsidy,
        "produce_date": produce_date,
        "found_detail": found_detail,
        "match": "MATCH"
    }


# ====================== 9. 遍历同优先级全部商品 ======================
def select_and_collect_best_product(search_word, serial_num):
    print("🔍 开始扫描列表页商品标签...")
    sorted_products = sort_products_by_priority()
    if not sorted_products:
        print("❌ 未识别到任何标签商品")
        return None

    highest_priority = get_priority(sorted_products[0]["tags"])
    candidates = [p for p in sorted_products if get_priority(p["tags"]) == highest_priority]
    print(f"✅ 识别到 {len(candidates)} 个最高优先级商品，全部采集")

    for idx, p in enumerate(candidates):
        print(f"\n--- 进入商品【{idx + 1}/{len(candidates)}】---")
        d.click(p["cx"], p["cy"])
        time.sleep(1)
        res = collect_single_product(search_word, serial_num)

        if res["found_detail"]:
            time.sleep(0.5)
            d.press("back")
            time.sleep(1.5)
            d.press("back")
        else:
            time.sleep(0.5)
            d.press("back")

    return True


# ====================== 【自动异常重启 + 断点续采】主循环 ======================
def main():
    print("🚀 启动自动搜索 + 全商品采集 + Excel导出 + 中断续采 + 异常自动重启")

    todo_df = load_product_list_with_status()
    if todo_df.empty:
        print("🎉 所有商品已全部采集完成！")
        return

    for _, row in todo_df.iterrows():
        keyword = str(row["货品名称"]).strip()
        serial_num = row["序号"]
        success = False

        while not success:
            try:
                print(f"\n===== 开始采集：{keyword} =====")
                search_product(keyword)
                select_and_collect_best_product(keyword, serial_num)

                mark_product_as_done(keyword)
                save_all_to_excel()

                print(f"\n⏳ 等待 {SEARCH_INTERVAL_SECONDS} 秒后继续...")
                time.sleep(SEARCH_INTERVAL_SECONDS)
                print(f"✅ 【{keyword}】采集完成！")
                success = True

            except Exception as e:
                print(f"\n❌ 采集发生异常：{str(e)}")
                go_to_pinduoduo_home()
                print(f"🔄 重启完成，重新采集：{keyword}")

    print("\n🎉 全部商品采集任务结束！")


if __name__ == "__main__":
    main()