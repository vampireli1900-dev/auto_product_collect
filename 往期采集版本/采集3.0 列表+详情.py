import uiautomator2 as u2
import cv2
from ultralytics import YOLO
import time
import re
import easyocr

# ====================== 初始化 ======================
d = u2.connect()
model = YOLO("../runs/detect/pdd_logo_train-2/weights/best.pt")
subsidy_model = YOLO("../runs/detect/subsidy_train/weights/best.pt")  # 来自代码二
detail_model = YOLO("../runs/detect/product_detail_train/weights/best.pt")
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)

# 优先级定义
PRIORITY_MAP = {
    ("baiyi", "brand"): 4,   # 品牌+百亿补贴（最高）
    ("brand",): 3,           # 品牌标
    ("baiyi",): 2,           # 百亿补贴
    ("global"): 1            # 全球购（最低）
}

# ====================== 价格识别配置（来自代码二，完全不动） ======================
SCREEN_FULL_HEIGHT = 1094
SCREEN_FULL_WIDTH = 488
PRICE_X1, PRICE_Y1 = 0, 470
PRICE_X2, PRICE_Y2 = 440, 580

# ====================== 1. 列表页商品标签识别（你原版，完全保留） ======================
def scan_list_products():
    d.screenshot("list_screen.jpg")
    img = cv2.imread("../list_screen.jpg")
    results = model(img, conf=0.25)
    # ====================== 调试：保存带检测框的图片 ======================
    debug_img = results[0].plot()  # 画出框、标签、置信度
    cv2.imwrite("../debug_detection.jpg", debug_img)  # 保存到本地

    products = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # 【置信度 > 50% 才保留】
            conf = box.conf[0].item()
            if conf < 0.5:
                continue  # 低于50%直接跳过
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
    """把标签按商品合并（适配2列布局，左右列分开判断）"""
    products = scan_list_products()
    grouped = {}

    for p in products:
        cx, cy = p["cx"], p["cy"]
        matched = False

        for key in list(grouped.keys()):
            existing_cx, existing_cy = key
            # 核心修复：先判断是否在同一列，再判断y轴误差
            # 两列布局，左右标签的x轴差通常>200，同一列的差很小
            same_column = abs(cx - existing_cx) < 200
            same_row = abs(cy - existing_cy) < 180  # 放宽一点y轴误差，适配不同手机

            if same_column and same_row:
                grouped[key]["tags"].add(p["type"])
                matched = True
                break

        if not matched:
            grouped[(cx, cy)] = {
                "tags": {p["type"]},
                "cx": cx,
                "cy": cy
            }

    return list(grouped.values())

# ====================== 2. 按优先级排序（你原版） ======================
def get_priority(tags):
    tags_tuple = tuple(sorted(tags))
    return PRIORITY_MAP.get(tags_tuple, 0)

def sort_products_by_priority(products):
    return sorted(products, key=lambda p: get_priority(p["tags"]), reverse=True)

# ====================== 3. 百亿补贴检测（来自代码二） ======================
def is_subsidy_product(img_path):
    img = cv2.imread(img_path)
    results = subsidy_model(img, conf=0.25)
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0:
                return True
    return False

# ====================== 4. 价格识别 + 修复（来自代码二，完全不动） ======================
def auto_fix_by_compare(price_list):
    if len(price_list) != 2:
        return price_list
    a, b = price_list
    try:
        val_a, val_b = float(a), float(b)
    except:
        return price_list
    fix_a, fix_b = a, b
    if a.isdigit() and "." in b and val_a > val_b * 2.5:
        fix_a = f"{a[:-1]}.{a[-1]}"
    if b.isdigit() and "." in a and val_b > val_a * 2.5:
        fix_b = f"{b[:-1]}.{b[-1]}"
    return [fix_a, fix_b]

def get_final_price(img_path, is_subsidy):
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    x_ratio = w / SCREEN_FULL_WIDTH
    y_ratio = h / SCREEN_FULL_HEIGHT
    cx1 = int(PRICE_X1 * x_ratio)
    cy1 = int(PRICE_Y1 * y_ratio)
    cx2 = int(PRICE_X2 * x_ratio)
    cy2 = int(PRICE_Y2 * y_ratio)
    crop = img[cy1:cy2, cx1:cx2]
    results = reader.readtext(crop)
    raw_text = " ".join([t[1] for t in results]).replace("半", "¥")
    price_list = re.findall(r'\d+\.?\d*', raw_text)
    price_list = [p for p in price_list if len(p) > 1]
    price_list = auto_fix_by_compare(price_list)
    if len(price_list) >= 2:
        final = price_list[0] if is_subsidy else price_list[1]
    else:
        final = price_list[0] if price_list else "未识别"
    return final, price_list, raw_text

# ====================== 5. 寻找详情模块（你原版，完全保留） ======================
def find_and_click_detail(max_scroll=5):
    for i in range(max_scroll):
        d.screenshot("screen.jpg")
        img = cv2.imread("../screen.jpg")
        results = detail_model(img, conf=0.1)
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    print(f"✅ 找到详情模块，点击坐标 ({cx}, {cy})")
                    d.click(cx, cy)
                    time.sleep(1.5)
                    return True
        print(f"未找到详情，向下滑动 ({i+1}/{max_scroll})")
        d.swipe(500, 1800, 500, 600)
        time.sleep(1)
    print("❌ 滑动5次未找到详情模块")
    return False

# ====================== 6. 生产日期识别（你原版） ======================
def get_production_date(img_path):
    result = reader.readtext(img_path)
    all_text = " ".join([line[1] for line in result])
    if "生产日期" not in all_text:
        return False
    match = re.search(r"\d{4}-\d{1,2}-\d{1,2}", all_text)
    return match.group() if match else False

def get_date_with_retry():
    for i in range(3):
        d.screenshot("screen_date.jpg")
        date = get_production_date("../screen_date.jpg")
        if date:
            return date
        if i < 2:
            print(f"未找到生产日期，从下往上滑动 ({i+1}/2)")
            d.swipe(500, 1600, 500, 800)
            time.sleep(1)
    return False

# ====================== 7. 单个商品完整采集流程（核心整合） ======================
def collect_single_product():
    # 1. 截图识别补贴
    d.screenshot("screen.jpg")
    is_subsidy = is_subsidy_product("../screen.jpg")
    print("📌 是否百亿补贴：", is_subsidy)

    # 2. 识别价格
    final_price, prices, raw_text = get_final_price("../screen.jpg", is_subsidy)
    print("💰 最终价格：", final_price)

    # 3. 找详情模块 + 识别日期
    find_and_click_detail()
    production_date = get_date_with_retry()
    print("📅 生产日期：", production_date)

    return {
        "subsidy": is_subsidy,
        "price": final_price,
        "produce_date": production_date
    }

# ====================== 8. 主流程：遍历商品 + 选择最优（你原版逻辑） ======================
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

    for idx, p in enumerate(candidates):
        print(f"\n--- 进入商品 {idx+1}/{len(candidates)} ---")
        # 点击位置：你原版，完全不动
        click_x, click_y = p["cx"], p["cy"]
        d.click(click_x, click_y)
        time.sleep(2)

        # 采集：价格 + 补贴 + 日期
        info = collect_single_product()
        production_date = info["produce_date"]
        print(f"✅ 商品采集完成：日期={production_date}")

        # 选择最新日期
        if production_date:
            if not best_date or production_date > best_date:
                best_date = production_date
                best_product = p
                best_info = info

        # ======================
        # 后退两次 → 回到列表页（你要的逻辑）
        # ======================
        print("🔙 返回列表页...")
        d.press("back")
        time.sleep(0.5)
        d.press("back")
        time.sleep(1.5)

    if best_product:
        print(f"\n🏆 最优商品：日期={best_date}")
        # 已删除：点击最终商品逻辑
        return {**best_info, "tags": list(best_product["tags"])}
    else:
        print("❌ 未找到有效生产日期")
        return None


# ====================== 9. 仅全球购逻辑（你原版） ======================
def handle_only_global_purchase():
    print("⚠️  当前页面只有全球购商品，下滑3次...")
    for i in range(3):
        d.swipe(500, 1800, 500, 600)
        time.sleep(1.5)
    for _ in range(3):
        d.swipe(500, 600, 500, 1800)
        time.sleep(0.8)

    products = get_products_with_tags()
    global_products = [p for p in products if "global" in p["tags"]]
    if global_products:
        p = global_products[0]
        d.click(p["cx"], p["cy"] + 200)
        time.sleep(2)
        collect_single_product()
        return True
    return False

# ====================== 入口 ======================
if __name__ == "__main__":
    products = get_products_with_tags()
    if not products:
        print("❌ 未识别到商品")
        exit()

    all_tags = [p["tags"] for p in products]
    only_global = all("global" in tags and len(tags) == 1 for tags in all_tags)

    if only_global:
        handle_only_global_purchase()
    else:
        select_and_collect_best_product()