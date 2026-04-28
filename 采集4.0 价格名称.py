import uiautomator2 as u2
import cv2
from ultralytics import YOLO
import time
import re

# ====================== 初始化 ======================
d = u2.connect()
model = YOLO("runs/detect/pdd_logo_train-2/weights/best.pt")
subsidy_model = YOLO("runs/detect/subsidy_train/weights/best.pt")
detail_model = YOLO("runs/detect/product_detail_train/weights/best.pt")

# ====================== 【商品搜索名单】 ======================
PRODUCT_LIST = [
    "SK-II前男友面膜",
    "雅诗兰黛小棕瓶",
    "兰蔻小黑瓶",
    "海蓝之谜面霜"
]

# 优先级定义
PRIORITY_MAP = {
    ("baiyi", "brand"): 4,
    ("brand",): 3,
    ("baiyi",): 2,
    ("global"): 1
}


# ====================== 1. 搜索功能（从搜索页开始） ======================
def search_product(keyword):
    print(f"\n🔍 开始搜索商品：{keyword}")
    # 1. 从屏幕中间 向下滑动（下拉露出搜索框）—— 这才是对的！
    width, height = d.window_size()
    # 👇 核心：严格按 height * 200 / 2400 计算搜索框 Y 坐标
    search_y = int(height * 200 / 2400)
    # 从屏幕中间向下滑动
    d.swipe(width // 2, height // 2, width // 2, height // 2 + 400)
    time.sleep(1)
    # 点击搜索框（按比例计算）
    d.click(width // 2, search_y)
    time.sleep(0.8)
    # 清空输入 + 输入新关键词
    d(className="android.widget.EditText").clear_text()
    d(className="android.widget.EditText").set_text(keyword)
    time.sleep(0.8)
    # 点击搜索
    d(text="搜索", className="android.widget.TextView").click()
    print("✅ 搜索完成，等待列表加载")


# ====================== 2. 列表页商品标签识别 ======================
def scan_list_products():
    d.screenshot("list_screen.jpg")
    img = cv2.imread("list_screen.jpg")
    results = model(img, conf=0.25)
    debug_img = results[0].plot()
    cv2.imwrite("debug_detection.jpg", debug_img)

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
    # 按优先级从高到低判断：存在即生效
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


# ====================== 4. 补贴判断（XML） ======================
def is_subsidy_product():
    xml = d.dump_hierarchy()
    return "百亿补贴" in xml or "官方补贴" in xml


# ====================== 5. 商品信息提取（XML） ======================
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
def find_and_click_detail(max_scroll=5):
    # ======================
    # 第一步：YOLO 识别 商品详情模块
    # ======================
    for i in range(max_scroll):
        # 截图 + YOLO 推理
        img = d.screenshot(format="opencv")
        results = detail_model(img, conf=0.8)

        detail_found = False
        click_x, click_y = 0, 0

        # 解析识别结果
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if cls == 0:
                    # 找到商品详情模块 → 获取中心坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    click_x = (x1 + x2) // 2
                    click_y = (y1 + y2) // 2
                    detail_found = True
                    break

        if detail_found:
            # ======================
            # 找到 → 点击进入
            # ======================
            print("✅ YOLO 找到商品详情模块，点击进入")
            d.click(click_x, click_y)
            time.sleep(1.5)

            # ======================
            # 第二步：进入后滑动找 生产日期/保质期
            # ======================
            for j in range(max_scroll):
                xml = d.dump_hierarchy()
                if "生产日期" in xml or "保质期" in xml:
                    print("✅ 找到生产日期/保质期")
                    return True
                d.swipe(500, 1800, 500, 600)
                time.sleep(1)

            # 点进去了但没找到日期
            return False

        # 没找到 → 上滑一次
        d.swipe(500, 1800, 500, 600)
        time.sleep(1)

    # 滑了5次都没找到详情模块
    print("❌ 未找到商品详情模块")
    return False


# ====================== 7. 生产日期（纯正则） ======================
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
def collect_single_product():
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


# ====================== 9. 列表商品批量采集 ======================
def select_and_collect_best_product():
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

        info = collect_single_product()
        production_date = info["produce_date"]
        found_detail = info["found_detail"]

        if production_date:
            if not best_date or production_date > best_date:
                best_date = production_date
                best_product = p
                best_info = info

        # ======================
        # 【核心逻辑：动态返回】
        # ======================
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
        select_and_collect_best_product()

        time.sleep(1)

        print(f"\n================================")
        print(f"✅ {product} 全部采集完成")
        print(f"================================")
    print("\n🎉 所有商品名单全部采集完毕！")


# ====================== 入口 ======================
if __name__ == "__main__":
    main()