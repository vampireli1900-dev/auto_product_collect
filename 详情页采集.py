import uiautomator2 as u2
import time
import cv2
from ultralytics import YOLO
import easyocr
import re

# ==============================================
# 【全局初始化】只执行一次
# ==============================================
# 1. 连接手机
d = u2.connect()

# 2. 加载模型
subsidy_model = YOLO("runs/detect/subsidy_train/weights/best.pt")
detail_model = YOLO("runs/detect/product_detail_train/weights/best.pt")

# 3. 初始化OCR
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)

# 价格区域固定配置
SCREEN_FULL_HEIGHT = 1094
SCREEN_FULL_WIDTH = 488
PRICE_X1, PRICE_Y1 = 0, 490
PRICE_X2, PRICE_Y2 = 370, 533

# ==============================================
# 【功能1】百亿补贴检测
# ==============================================
def is_subsidy_product(img_path):
    img = cv2.imread(img_path)
    results = subsidy_model(img, conf=0.25)
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0:
                return True
    return False

# ==============================================
# 【功能2】价格识别 + 2.5倍自动修复小数点
# ==============================================
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

# ==============================================
# 【功能3】寻找并点击商品详情模块（最多滑动5次）
# ==============================================
def find_and_click_detail(max_scroll=5):
    for i in range(max_scroll):
        d.screenshot("screen.jpg")
        img = cv2.imread("screen.jpg")
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

# ==============================================
# 【功能4】生产日期识别（全图、不裁切、找关键字）
# ==============================================
def get_production_date(img_path):
    result = reader.readtext(img_path)
    all_text = " ".join([line[1] for line in result])
    if "生产日期" not in all_text:
        return False
    match = re.search(r"\d{4}-\d{1,2}-\d{1,2}", all_text)
    return match.group() if match else False

# ==============================================
# 【功能5】重试识别生产日期（滑动2次）
# ==============================================
def get_date_with_retry():
    for i in range(3):
        d.screenshot("screen_date.jpg")
        date = get_production_date("screen_date.jpg")
        if date:
            return date
        if i < 2:
            print(f"未找到生产日期，从下往上滑动 ({i+1}/2)")
            d.swipe(500, 1600, 500, 800)
            time.sleep(1)
    return False

# ==============================================
# 【主流程：完整商品采集】
# ==============================================
def collect_product():
    print("\n" + "=" * 60)
    print("           开始自动化商品信息采集")
    print("=" * 60)

    # 1. 截图当前详情页
    d.screenshot("screen.jpg")
    print("✅ 已截图")

    # 2. 检测百亿补贴
    is_subsidy = is_subsidy_product("screen.jpg")
    print("📌 是否百亿补贴：", is_subsidy)

    # 3. 采集价格
    final_price, prices, raw_text = get_final_price("screen.jpg", is_subsidy)
    print("💰 最终价格：", final_price)
    print("📝 价格原文：", raw_text)

    # 4. 寻找并点击商品详情
    find_and_click_detail(max_scroll=5)

    # 5. 识别生产日期（重试2次）
    production_date = get_date_with_retry()
    print("📅 生产日期：", production_date)

    # 6. 最终结果
    print("\n" + "=" * 60)
    print("              采集完成")
    print(f"百亿补贴：{is_subsidy}")
    print(f"最终价格：{final_price}")
    print(f"生产日期：{production_date}")
    print("=" * 60)

    return {
        "subsidy": is_subsidy,
        "price": final_price,
        "produce_date": production_date
    }

# ==============================================
# 启动采集
# ==============================================
if __name__ == "__main__":
    collect_product()