# sku_matcher.py
import re
import time
from typing import Dict, Optional, Set, List
import uiautomator2 as u2
from spec_utils import  extract_specs, brand_lib


STOP_CHARS = set("的之了·・-— ")


_brand_aliases_lower = None


def _get_brand_aliases_lower():
    global _brand_aliases_lower
    if _brand_aliases_lower is None:
        _brand_aliases_lower = set()
        for aliases in brand_lib.values():
            for a in aliases:
                _brand_aliases_lower.add(a.lower())
    return _brand_aliases_lower


def get_sku_identifiers(search_word: str) -> list:
    """提取规格标识列表：色号、英文名、容量，并额外拆分单词"""
    identifiers = []
    seen = set()

    # 1. 提取 #数字 色号
    hash_digits = re.findall(r'#(\d+)', search_word)
    for d in hash_digits:
        if d not in seen:
            seen.add(d)
            identifiers.append(d)

    # 2. 完整色号（字母+数字 或 数字+字母）
    full_colors = re.findall(r'\b([a-zA-Z]{1,4}\d{1,3}[a-zA-Z]?)\b', search_word)
    for c in full_colors:
        cl = c.lower()
        if cl not in seen:
            seen.add(cl)
            identifiers.append(cl)

    # 3. 拆分色号（从 extract_specs 获取）
    _, color_codes = extract_specs(search_word)
    brand_set = _get_brand_aliases_lower()
    filtered_colors = []

    for c in color_codes:
        cl = c.lower()
        if cl in brand_set:
            continue  # 跳过品牌别名
        # 额外排除像 "sk2" 这种纯品牌简写
        filtered_colors.append(cl)
        if cl in seen:
            continue
        if re.fullmatch(r'\d+', cl) and len(cl) == 4 and 1900 < int(cl) < 2100:
            continue
        seen.add(cl)
        identifiers.append(cl)

    # 4. 英文产品名（过滤品牌词），并额外添加每个独立单词
    # 先移除所有容量数字+单位
    cleaned = re.sub(r'\d+(?:\.\d+)?\s*(ml|g|l|oz|毫升|克|升)\b', '', search_word, flags=re.I)
    words = re.findall(r'[a-zA-Z]{2,}', cleaned)
    # 在函数开头或文件顶部定义黑名单（避免重复，可以在函数内定义）
    concentration_blacklist = {'edp', 'edt', 'edc', 'parfum', 'toilette', '浓香', '淡香', '古龙'}


    # 常见单位黑名单（不应当作为标识）
    unit_blacklist = {'ml', 'g', 'l', 'oz', '毫升', '克', '升', 'mg', 'kg'}

    if words:
        brand_set = _get_brand_aliases_lower()
        brand_parts = set()
        for alias in brand_set:
            parts = re.split(r'[^a-z]+', alias)
            for p in parts:
                if len(p) >= 2:
                    brand_parts.add(p)
        meaningful = []
        for w in words:
            w_lower = w.lower()
            if w_lower in brand_set or w_lower in brand_parts:
                continue
            if w_lower in unit_blacklist:
                continue
            if w_lower in concentration_blacklist:
                continue  # 跳过浓度词
            meaningful.append(w_lower)
        if meaningful:
            # 添加完整短语
            eng_phrase = ' '.join(meaningful).lower()
            if eng_phrase not in seen:
                seen.add(eng_phrase)
                identifiers.append(eng_phrase)
            # 额外添加每个独立单词（长度≥3）
            for w in meaningful:
                if len(w) >= 3 and w not in seen:
                    seen.add(w)
                    identifiers.append(w)

    # 5. 容量（只添加带数字的单位，如 50ml）
    m = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g|l|oz|毫升|克|升)', search_word, re.I)
    if m:
        num = m.group(1)
        unit = m.group(2).lower()
        unit_map = {'毫升': 'ml', '克': 'g', '升': 'l'}
        unit = unit_map.get(unit, unit)
        cap_id = f"{num}{unit}"
        if cap_id not in seen:
            identifiers.append(cap_id)


    print(f"[DEBUG][get_sku_identifiers] 提取标识: {identifiers}")
    return identifiers


def is_identifier_match(identifier: str, selected_text: str) -> bool:
    """判断标识是否与已选文本匹配（字母数字需同时匹配）"""
    id_lower = identifier.lower()
    sel_lower = selected_text.lower()

    # 1. 直接包含
    if id_lower in sel_lower:
        return True

    # 2. 对于字母+数字组合 (如 nc11)，要求字母部分和数字部分都出现在 sel 中，且字母部分作为一个整体
    alpha_part = re.match(r'^([a-z]+)(\d+)$', id_lower)
    if alpha_part:
        letters = alpha_part.group(1)  # 'nc'
        digits = alpha_part.group(2)  # '11'
        # 字母整体出现在 sel 中（作为单词边界更好）
        if letters in sel_lower and digits in sel_lower:
            # 避免类似 'nw11' 包含 'n' 和 '11' 的误判，检查字母连续出现
            # 简单检查：letters 作为一个独立子串（前后非字母或边界）
            if re.search(r'(?<![a-z])' + re.escape(letters) + r'(?![a-z])', sel_lower):
                return True
    return False

def _count_capacity_occurrences(xml_content: str, capacity_id: str) -> int:
    pattern = rf'<(?:node|android\.widget\.\w+)[^>]*?(?:text|content-desc)="[^"]*{re.escape(capacity_id)}[^"]*"'
    count = len(re.findall(pattern, xml_content, re.IGNORECASE))
    print(f"[DEBUG][_count_capacity_occurrences] '{capacity_id}' 出现 {count} 次")
    return count


def extract_sku_price_with_id(xml_content: str, identifier: str, search_word: str = "") -> Dict[str, Optional[str]]:
    """根据标识匹配已选规格并提取价格"""
    print(f"[DEBUG][extract_sku_price_with_id] 尝试匹配标识: '{identifier}'")
    if not identifier:
        return {"title": "", "current_price": None}

    selected = re.search(r'<node[^>]*?(?:text|content-desc)="([^"]*已选(?:择)?[^"]*)"', xml_content)
    if not selected:
        print("[DEBUG][extract_sku_price_with_id] 未找到已选节点")
        # print(xml_content)
        return {"title": "", "current_price": None}

    selected_text = selected.group(1).strip()
    sel = selected_text.lower()
    id_norm = identifier.lower()
    # 容量单位白名单
    capacity_units = {'ml', 'g', 'l', 'oz', '毫升', '克', '升'}
    cap_match = re.match(r'(\d+)([a-z]+)$', id_norm)
    is_capacity = cap_match and cap_match.group(2) in capacity_units
    print(f"[DEBUG][extract_sku_price_with_id] 已选文本: '{selected_text}'")
    print(f"[DEBUG][extract_sku_price_with_id] 是否为容量标识: {is_capacity}")

    matched = False
    if is_capacity:
        num = re.search(r'\d+', id_norm).group()
        unit = id_norm.replace(num, '')
        print(f"[DEBUG][extract_sku_price_with_id] 容量数字: '{num}', 单位: '{unit}'")
        if num in sel and unit in sel:
            occ = _count_capacity_occurrences(xml_content, id_norm)
            if occ > 2:
                print(f"[DEBUG][extract_sku_price_with_id] 容量出现次数 >2，忽略")
                return {"title": "", "current_price": None}
            all_ids = get_sku_identifiers(search_word)
            non_cap_ids = [cid for cid in all_ids if not re.match(r'\d+[a-z]+$', cid)]
            if non_cap_ids and not any(cid in sel for cid in non_cap_ids):
                print(f"[DEBUG][extract_sku_price_with_id] 容量匹配但缺少色号/英文名标识 {non_cap_ids}，无效")
                return {"title": "", "current_price": None}
            matched = True
            print("[DEBUG][extract_sku_price_with_id] 容量匹配成功")
    else:
        if id_norm in sel:
            matched = True
            print(f"[DEBUG][extract_sku_price_with_id] 直接包含匹配")
        else:
            id_words = id_norm.split()
            if len(id_words) > 1 and any(w in sel for w in id_words):
                matched = True
                print(f"[DEBUG][extract_sku_price_with_id] 部分词匹配: {id_words}")
            else:
                print(f"[DEBUG][extract_sku_price_with_id] 标识不匹配")
    if not matched:
        return {"title": "", "current_price": None}

    # 提取价格
    price_m = re.search(r'<node[^>]*?(?:text|content-desc)="([^"]*?[¥￥]\s*\d+\.?\d*[^"]*)"', xml_content)
    if price_m:
        num_m = re.search(r'[¥￥]\s*(\d+\.?\d*)', price_m.group(1))
        if num_m:
            price = num_m.group(1)
            try:
                if float(price) >= 10:
                    print(f"[DEBUG][extract_sku_price_with_id] 提取到价格: {price}")
                    return {"title": selected_text, "current_price": price}
            except ValueError:
                pass
    print("[DEBUG][extract_sku_price_with_id] 未找到有效价格")
    return {"title": selected_text, "current_price": None}


def _click_sku_by_identifier(d, identifier: str, timeout: float = 2.0) -> bool:
    """点击包含指定文本（忽略大小写）的控件"""
    print(f"[DEBUG][_click_sku_by_identifier] 尝试点击标识: '{identifier}'")

    # 容量格式特殊处理
    capacity_match = re.match(r'(\d+)(ml|g|l|oz|毫升|克|升)', identifier.lower())
    if capacity_match:
        full_id = identifier.lower()
        elems = d(textContains=full_id)
        if elems.count > 0:
            elems[0].click()
            print(f"[DEBUG][_click_sku_by_identifier] 点击容量标识完整匹配成功: {full_id}")
            time.sleep(timeout)
            return True
        num = capacity_match.group(1)
        unit = capacity_match.group(2)
        xpath = f'//*[contains(translate(@text, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{num}") and contains(translate(@text, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{unit}")]'
        elem = d.xpath(xpath)
        if elem.exists:
            elem.click()
            print(f"[DEBUG][_click_sku_by_identifier] 点击容量标识拆分匹配成功: {num}{unit}")
            time.sleep(timeout)
            return True
        print(f"[DEBUG][_click_sku_by_identifier] 容量标识 {identifier} 未找到匹配控件")
        return False

    # --- 纯数字标识特殊处理（避免 textContains 漏匹配）---
    if identifier.isdigit():
        # 1. XPath 直接匹配 text 包含该数字且可点击的节点
        xpath_clickable = f'//*[contains(@text, "{identifier}") and @clickable="true"]'
        elem = d.xpath(xpath_clickable)
        if elem.exists:
            print(f"[DEBUG][_click_sku_by_identifier] XPath 可点击匹配成功: {elem.get().attrib.get('text', '')}")
            elem.click()
            time.sleep(timeout)
            return True

        # 2. 兜底：任意 text 包含该数字的节点
        xpath_any = f'//*[contains(@text, "{identifier}")]'
        elem_any = d.xpath(xpath_any)
        if elem_any.exists:
            print(f"[DEBUG][_click_sku_by_identifier] XPath 任意节点匹配成功: {elem_any.get().attrib.get('text', '')}")
            elem_any.click()
            time.sleep(timeout)
            return True

        # 3. 最后尝试原有的 ignoreCase 匹配（针对特殊场景）
        try:
            elems = d(textContains=identifier, ignoreCase=True)
            if elems.count > 0:
                elems[0].click()
                time.sleep(timeout)
                return True
        except:
            pass
        return False

    # 非容量标识：原有逻辑
    brand_set = _get_brand_aliases_lower()
    words = identifier.split()
    click_word = words[0].lower()
    for w in words:
        if w.lower() not in brand_set:
            click_word = w.lower()
            break

    try:
        elems = d(textContains=click_word, ignoreCase=True)
        if elems.count > 0:
            elems[0].click()
            print(f"[DEBUG][_click_sku_by_identifier] 点击文本匹配成功 (ignoreCase)")
            time.sleep(timeout)
            return True
        elems_desc = d(descriptionContains=click_word, ignoreCase=True)
        if elems_desc.count > 0:
            elems_desc[0].click()
            print(f"[DEBUG][_click_sku_by_identifier] 点击 description 匹配成功")
            time.sleep(timeout)
            return True
    except Exception as e:
        pass

    xpath_text = f'//*[contains(translate(@text, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{click_word}")]'
    elem = d.xpath(xpath_text)
    if elem.exists:
        elem.click()
        time.sleep(timeout)
        return True
    xpath_desc = f'//*[contains(translate(@content-desc, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{click_word}")]'
    elem_desc = d.xpath(xpath_desc)
    if elem_desc.exists:
        elem_desc.click()
        time.sleep(timeout)
        return True

    return False


def _select_style_if_needed(d, timeout: float = 1.5) -> bool:
    """检查是否需要点击款式，使用 XPath 定位并点击；先下滑一次确保款式可见"""

    # 先向下滑动一次，让款式选项进入视野
    try:
        width, height = d.window_size()
        d.drag(width * 0.5, height * 0.8, width * 0.5, height * 0.4, duration=0.3)
        time.sleep(0.5)
    except Exception as e:
        # print(f"[DEBUG][_select_style_if_needed] 滑动异常: {e}")
        pass
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            # 获取所有包含“【”且不包含“已选”的 TextView
            xpath = '//android.widget.TextView[contains(@text, "【") and not(contains(@text, "已选"))]'
            elems = d.xpath(xpath)
            if elems.exists:
                nodes = elems.all()
                # 过滤掉色号（如【8B】、【5B】等）
                pattern = re.compile(r'【\d+[A-Za-z]*】')
                style_nodes = []
                for node in nodes:
                    text = node.attrib.get('text', '')
                    if pattern.search(text):
                        # print(f"[DEBUG][_select_style_if_needed] 跳过色号: {text}")
                        continue
                    style_nodes.append(node)
                if style_nodes:
                    # 按底部坐标降序排序，选择最靠下的款式
                    def get_bottom_y(node):
                        try:
                            bounds = node.attrib.get('bounds', '')
                            if '][' in bounds:
                                right_bottom = bounds.split('][')[1]
                                bottom = int(right_bottom.split(',')[1].rstrip(']'))
                                return bottom
                        except:
                            pass
                        return 0

                    style_nodes.sort(key=lambda n: get_bottom_y(n), reverse=True)
                    target = style_nodes[0]
                    target.click()
                    text = target.attrib.get('text', '')
                    # print(f"[DEBUG][_select_style_if_needed] XPath 点击款式: {text}")
                    time.sleep(timeout)
                    return True

            # 没有找到款式，且是第一次尝试，则再向下滑动
            if attempt == 0:
                # print("[DEBUG][_select_style_if_needed] 未找到款式，尝试再次向下滑动")
                width, height = d.window_size()
                d.drag(width * 0.5, height * 0.7, width * 0.5, height * 0.3, duration=0.3)
                time.sleep(1)
            else:
                # print("[DEBUG][_select_style_if_needed] 滑动后仍未找到款式")
                return False
        except Exception as e:
            print(f"[DEBUG][_select_style_if_needed] 异常: {e}")
            return False
    return False

def get_sku_price_auto(d, search_word: str, click_timeout: float = 2.0) -> Dict[str, Optional[str]]:
    """自动匹配规格并返回已选规格文本和价格
    优先级：色号 > 容量（浓度辅助过滤）> 其他标识
    """
    print(f"\n[DEBUG][get_sku_price_auto] 开始匹配，搜索词: '{search_word}'")
    identifiers = get_sku_identifiers(search_word)
    if not identifiers:
        print("[DEBUG][get_sku_price_auto] 未提取到任何规格标识，退出")
        return {"title": "", "current_price": None}

    # 浓度词黑名单（用于识别搜索词中的浓度要求）
    concentration_blacklist = {'edp', 'edt', 'edc', 'parfum', 'toilette', '浓香', '淡香', '古龙', '香精'}

    # 辅助函数：从当前页面提取已选文本和价格
    def check_current_selection(xml_content):
        selected_match = re.search(r'<node[^>]*?(?:text|content-desc)="([^"]*已选(?:择)?[^"]*)"', xml_content)
        if not selected_match:
            return None, None
        selected_text = selected_match.group(1).strip()
        price_match = re.search(r'<node[^>]*?(?:text|content-desc)="([^"]*?[¥￥]\s*\d+\.?\d*[^"]*)"', xml_content)
        if price_match:
            num_match = re.search(r'[¥￥]\s*(\d+\.?\d*)', price_match.group(1))
            if num_match:
                price = num_match.group(1)
                try:
                    if float(price) >= 10:
                        return selected_text, price
                except:
                    pass
        return selected_text, None

    # 第一步：当前页面检查
    xml = d.dump_hierarchy()
    selected_text, price = check_current_selection(xml)
    if selected_text:
        matched = any(is_identifier_match(ident, selected_text) for ident in identifiers)
        if matched and price:
            print(f"[DEBUG][get_sku_price_auto] 当前已选规格匹配，价格: {price}")
            return {"title": selected_text, "current_price": price}
        elif matched and not price:
            print("[DEBUG][get_sku_price_auto] 当前已选规格匹配但无价格，尝试点击款式...")
            _select_style_if_needed(d, 0.5)
            xml2 = d.dump_hierarchy()
            _, price2 = check_current_selection(xml2)
            if price2:
                return {"title": selected_text, "current_price": price2}
            else:
                print("[DEBUG][get_sku_price_auto] 点击款式后仍无价格")
                return {"title": selected_text, "current_price": None}
        else:
            print("[DEBUG][get_sku_price_auto] 当前已选规格不匹配，尝试点击规格...")
    else:
        print("[DEBUG][get_sku_price_auto] 未找到已选节点，尝试点击规格...")

    # 分离标识：色号、容量、其他
    # 色号：非纯数字，且包含字母（由 extract_specs 提取的 color_codes 我们无法直接区分，用启发式）
    def is_color_code(ident):
        # 长度为 2~6，包含字母，不全是数字，不是容量格式（数字+ml/g等）
        if re.match(r'\d+[a-z]+$', ident):  # 如 90ml 是容量
            return False
        return bool(re.search(r'[a-z]', ident)) and len(ident) >= 2

    color_ids = [i for i in identifiers if is_color_code(i) and i not in concentration_blacklist]
    cap_ids = [i for i in identifiers if re.match(r'\d+[a-z]+$', i)]
    other_ids = [i for i in identifiers if i not in color_ids and i not in cap_ids]

    # 搜索词中的浓度要求（用于辅助容量过滤）
    search_concentration = [c for c in concentration_blacklist if c in search_word.lower()]

    # 辅助函数：点击容量并支持浓度筛选
    def try_click_capacity(cap_id):
        elems = d(textContains=cap_id)
        if elems.count == 0:
            return False
        print(f"[DEBUG] 容量 {cap_id} 找到 {elems.count} 个控件")
        if elems.count == 1:
            elems[0].click()
            print(f"[DEBUG] 点击唯一容量控件: {cap_id}")
            return True
        else:
            # 多个相同容量，如果有浓度要求则筛选
            if search_concentration:
                for elem in elems:
                    text = elem.info.get('text', '').lower()
                    if any(conc in text for conc in search_concentration):
                        elem.click()
                        print(f"[DEBUG] 点击符合浓度 {search_concentration} 的容量控件: {text}")
                        return True
                # 无匹配浓度，点击第一个
                elems[0].click()
                print(f"[DEBUG] 无匹配浓度，点击第一个容量控件: {cap_id}")
                return True
            else:
                # 无浓度要求，点击第一个
                elems[0].click()
                print(f"[DEBUG] 多个容量无浓度要求，点击第一个: {cap_id}")
                return True

    # 第二步：按优先级点击
    # 2.1 优先尝试色号
    for color_id in color_ids:
        if _click_sku_by_identifier(d, color_id, click_timeout):
            time.sleep(0.8)
            xml = d.dump_hierarchy()
            sel_text, price_val = check_current_selection(xml)
            if sel_text and price_val:
                # 验证点击后的已选包含该色号（或任意标识）
                if color_id in sel_text.lower():
                    print(f"[DEBUG] 色号 {color_id} 匹配成功，价格: {price_val}")
                    return {"title": sel_text, "current_price": price_val}
            # 如果有已选但无价格，尝试款式
            if sel_text and not price_val:
                _select_style_if_needed(d, 0.5)
                xml2 = d.dump_hierarchy()
                _, price2 = check_current_selection(xml2)
                if price2:
                    return {"title": sel_text, "current_price": price2}
            # 否则继续下一个色号
        time.sleep(0.3)

    # 2.2 色号失败，尝试容量（支持浓度辅助）
    for cap_id in cap_ids:
        if try_click_capacity(cap_id):
            time.sleep(click_timeout)
            xml = d.dump_hierarchy()
            sel_text, price_val = check_current_selection(xml)
            if sel_text and price_val:
                # 可选：验证已选文本包含容量
                if cap_id in sel_text.lower():
                    print(f"[DEBUG] 容量 {cap_id} 匹配成功，价格: {price_val}")
                    return {"title": sel_text, "current_price": price_val}
                else:
                    print(f"[DEBUG] 点击容量 {cap_id} 后已选文本为 {sel_text}，不包含目标容量，放弃")
                    continue  # 继续尝试下一个容量
            # 有已选无价格，尝试款式
            if sel_text and not price_val:
                _select_style_if_needed(d, 0.5)
                xml2 = d.dump_hierarchy()
                _, price2 = check_current_selection(xml2)
                if price2:
                    return {"title": sel_text, "current_price": price2}
        time.sleep(0.3)

    # 2.3 最后尝试其他标识（英文名等）
    for ident in other_ids:
        if _click_sku_by_identifier(d, ident, click_timeout):
            time.sleep(0.8)
            xml = d.dump_hierarchy()
            sel_text, price_val = check_current_selection(xml)
            if sel_text and price_val:
                if ident in sel_text.lower():
                    print(f"[DEBUG] 其他标识 {ident} 匹配成功，价格: {price_val}")
                    return {"title": sel_text, "current_price": price_val}
            if sel_text and not price_val:
                _select_style_if_needed(d, 0.5)
                xml2 = d.dump_hierarchy()
                _, price2 = check_current_selection(xml2)
                if price2:
                    return {"title": sel_text, "current_price": price2}
        time.sleep(0.3)

    print("[DEBUG][get_sku_price_auto] 所有标识尝试完毕，仍无价格")
    return {"title": "匹配失败", "current_price": None}



# 连接手机
d = u2.connect()
# ====================== 调试运行 ======================
if __name__ == '__main__':
    result2 = get_sku_price_auto(d, '黛珂散粉光肌00 24年新版')
    print("\n===== 结果2 =====")
    print("匹配文本:", result2["title"])
    print("价格:", result2["current_price"])