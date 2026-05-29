# sku_matcher.py
import re
import time
from typing import Dict, Optional, Set, List

# ---------- 品牌字典 ----------
brand_lib = {
    "赫莲娜": ["HR", "HelenaRubinstein", "Helena Rubinstein", "赫莲娜"],
    "海蓝之谜": ["LM", "LaMer", "La Mer", "腊梅", "海蓝之谜"],
    "莱珀妮": ["LaPrairie", "Prairie", "莱珀妮"],
    "希思黎": ["Sisley", "希思黎"],
    "法尔曼": ["Valmont", "法尔曼"],
    "兰蔻": ["Lancome", "Lancôme", "兰蔻"],
    "娇兰": ["Guerlain", "娇兰"],
    "倩碧": ["Clinique", "倩碧"],
    "娇韵诗": ["Clarins", "娇韵诗"],
    "科颜氏": ["Kiehls", "Kiehl's", "科颜氏"],
    "碧欧泉": ["Biotherm", "碧欧泉"],
    "薇姿": ["Vichy", "薇姿"],
    "德美乐嘉": ["Dermalogica", "德美乐嘉"],
    "雅诗兰黛": ["EsteeLauder", "Estée Lauder", "ESTEE LAUDER", "雅诗兰黛", "红石榴"],
    "大宝": ["Embryolisse", "大宝"],
    "薇迪薇奇": ["VidiVici", "Vidi Vici", "薇迪薇奇"],
    "肌肤之钥": ["CPB", "CleDePeauBeaute", "Cle de Peau Beauté", "肌肤之钥", "cledepece"],
    "SK-II": ["SK2", "SKII", "SK-II"],
    "资生堂": ["Shiseido", "资生堂"],
    "安耐晒": ["安耐晒"],
    "黛珂": ["Decorte", "Decorté", "黛珂"],
    "城野医生": ["DrCiLabo", "Dr.Ci:Labo", "城野医生"],
    "茵芙莎": ["IPSA", "茵芙莎", "茵芙纱"],
    "宝丽": ["POLA", "宝丽"],
    "兰芝": ["Laneige", "兰芝"],
    "植村秀": ["ShuUemura", "Shu Uemura", "植村秀"],
    "汤姆福特": ["TF", "TomFord", "Tom Ford", "汤姆福特"],
    "圣罗兰": ["YSL", "YvesSaintLaurent", "Yves Saint Laurent", "圣罗兰"],
    "魅可": ["MAC", "M.A.C", "魅可"],
    "纳斯": ["NARS", "纳斯", '娜斯'],
    "芭比布朗": ["BobbiBrown", "Bobbi Brown", "BB", "芭比布朗", "芭比波朗"],
    "纪梵希": ["Givenchy", "纪梵希"],
    "苏秘": ["Sum37", "Su:m37", "苏秘", "苏秘37"],
    "衰败城市": ["UrbanDecay", "Urban Decay", "衰败城市"],
    "罗拉": ["LauraMercier", "Laura Mercier", "罗拉"],
    "后": ["WHOO", "TheHistoryOfWhoo", "The History Of Whoo", "后"],
    "雪花秀": ["Sulwhasoo", "雪花", "后雪", "雪花秀"],
    "祖玛珑": ["JM", "JoMalone", "Jo Malone", "祖马龙", "祖玛珑"],
    "芦丹氏": ["SL", "SergeLutens", "Serge Lutens", "芦丹氏"],
    "百瑞德": ["Byredo", "百瑞德"],
    "爱马仕": ["Hermes", "Hermès", "爱马仕"],
    "古驰": ["Gucci", "古驰"],
    "范思哲": ["Versace", "范思哲"],
    "阿玛尼": ["Armani", "阿玛尼"],
    "巴宝莉": ["Burberry", "巴宝莉", "博柏利"],
    "蔻依": ["Chloe", "Chloé", "克洛伊", "蔻依"],
    "莫杰": ["MarcJacobs", "Marc Jacobs", "MJ", "莫杰"],
    "纳西索": ["Narciso", "纳西索"],
    "帕尔玛之水": ["AcquaDiParma", "Acqua di Parma", "帕尔玛之水"],
    "梅森马吉拉": ["MaisonMargiela", "Maison Margiela", "MM", "梅森马吉拉", "马丁马吉拉"],
    "欧珑": ["AtelierCologne", "Atelier Cologne", "欧珑"],
    "宝格丽": ["Bvlgari", "宝格丽"],
    "杜鲁萨迪": ["Trussardi", "杜鲁萨迪"],
    "卡尔文克雷恩": ["CK", "CalvinKlein", "Calvin Klein", "卡尔文克雷恩"],
    "缪缪": ["MiuMiu", "miumiu", "Miu Miu", "缪缪"],
    "香奈儿": ["Chanel", "香奈儿"],
    "卡诗": ["Kerastase", "Kérastase", "卡诗"],
    "欧舒丹": ["Loccitane", "L'Occitane", "欧舒丹"],
    "欧莱雅": ["Loreal", "L'Oréal", "欧莱雅"],
    "潘婷": ["Pantene", "潘婷"],
    "大卫杜夫": ["Davidoff", "大卫杜夫"],
    "拉夫劳伦": ["RalphLauren", "Ralph Lauren", "拉夫劳伦"],
    "馥蕾诗": ["Fresh", "馥蕾诗"],
    "伟博": ["Webber", "伟博"],
    "慕拉得": ["Murad", "慕拉得"],
    "未来驱蚊": ["VAPE", "未來", "未来驅蚊"],
    "澳洲NatureBOBO": ["NatureBOBO", "Nature BOBO", "澳洲"],
    "旧街场": ["OldTown", "Old Town", "旧街场"],
    "费列罗": ["Ferrero", "费列", "费列罗"],
    "伊丽莎白雅顿": ["ElizabethArden", "Elizabeth Arden", "伊丽莎白雅顿"],
    "迪奥": ["Dior", "迪奥"],
}

STOP_CHARS = set("的之了·・-— ")


def extract_specs(text: str):
    """提取容量数字集合和色号集合（与 product_validator 保持一致）"""
    text = str(text).lower()
    cap_nums = set()
    color_codes = set()
    pack_set = set()   # 包装数字，防止被当成色号

    # ---------- 容量 ----------
    cap_pattern = r'(\d+(?:\.\d+)?(?:\s*[-/]\s*\d+(?:\.\d+)?)*)\s*(ml|g|l|oz|片|粒|枚|对|支|个|盒|瓶|块|毫升|克|升)'
    for match in re.finditer(cap_pattern, text):
        num_part = match.group(1)
        nums = re.findall(r'\d+\.?\d*', num_part)
        for n in nums:
            try:
                val = float(n)
                if val.is_integer():
                    cap_nums.add(str(int(val)))
                else:
                    cap_nums.add(n)
            except:
                cap_nums.add(n)

    # ---------- 包装数量 ----------
    for m in re.finditer(r'[\*xX×]\s*(\d+)', text):
        pack_set.add(m.group(1))
    for m in re.finditer(r'(\d+)\s*(支|个|件|瓶|盒|对|组)\s*装?', text):
        pack_set.add(m.group(1))
    chinese_num_map = {'两':'2','三':'3','四':'4','五':'5','六':'6'}
    for m in re.finditer(r'(两|三|四|五|六)\s*(支|个|瓶|盒|对|组)\s*装?', text):
        pack_set.add(chinese_num_map[m.group(1)])

    # ---------- 色号 ----------
    # 带 # 号
    for m in re.finditer(r'#([A-Za-z0-9]+)', text):
        color_codes.add(m.group(1).lower())
    # 后置 # 号
    for m in re.finditer(r'([A-Za-z0-9]+)#', text):
        code = m.group(1).lower()
        # 移除纯数字限制，但过滤掉常见容量单位（如 30ml#）
        if not re.search(r'(ml|g|oz|升|毫升)$', code):
            color_codes.add(code)
    # 紧贴“色”或“号”
    for m in re.finditer(r'\b([A-Za-z]?\d+[A-Za-z]*)\s*(色|号)\b', text):
        color_codes.add(m.group(1).lower())
    # 独立色号（含字母）
    for m in re.finditer(r'\b([a-z]?\d+[a-z]\d*)\b', text):
        code = m.group(1)
        if not re.fullmatch(r'\d{4}', code) and code not in cap_nums:
            color_codes.add(code)
    # 单字母/数字色号（如 L1, N2），长度 2-4，排除容量数字
    for m in re.finditer(r'(?<![a-z0-9])([A-Za-z]\d+)(?![a-z0-9])', text):
        code = m.group(1).lower()
        if code not in cap_nums:
            color_codes.add(code)
    # 数字+单字母色号（如 8B, 02N）
    for m in re.finditer(r'(?<!\d)(\d+[a-zA-Z])(?![a-zA-Z0-9])', text):
        code = m.group(1).lower()
        if code not in cap_nums:
            color_codes.add(code)
    # 纯数字色号（2~4位），排除容量、包装、年份、有效期
    for m in re.finditer(r'(?<!\d)(\d{2,4})(?!\d)', text):
        code = m.group(1)
        start = m.start()
        end = m.end()
        # 如果数字后紧跟“年”或“款”，跳过（年份信息）
        if end < len(text) and (text[end] == '年' or text[end] == '款'):
            continue
        prefix = text[max(0, start-10):start]
        if re.search(r'(效期|到期|限用日期|保质期|\d\s*年|年)', prefix):
            continue
        if code not in cap_nums and code not in pack_set and not re.fullmatch(r'20\d{2}', code):
            color_codes.add(code)

    # 最终过滤：去掉带容量单位的误识别
    color_codes = {c for c in color_codes if not re.search(r'(ml|g|oz|升|毫升)$', c.lower())}
    return cap_nums, color_codes


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
    for c in color_codes:
        cl = c.lower()
        if cl in seen:
            continue
        if re.fullmatch(r'\d+', cl) and len(cl) == 4 and 1900 < int(cl) < 2100:
            continue
        seen.add(cl)
        identifiers.append(cl)

    # 4. 英文产品名（过滤品牌词），并额外添加每个独立单词
    cleaned = re.sub(r'\d+(?:\.\d+)?\s*(ml|g|l|oz|毫升|克|升)\b', '', search_word, flags=re.I)
    words = re.findall(r'[a-zA-Z]{2,}', cleaned)
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

    # 5. 容量
    m = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g|l|oz|毫升|克|升)', search_word, re.I)
    if m:
        num = m.group(1)
        unit = m.group(2).lower()
        unit_map = {'毫升': 'ml', '克': 'g', '升': 'l'}
        unit = unit_map.get(unit, unit)
        cap_id = f"{num}{unit}"
        if cap_id not in seen:
            identifiers.append(cap_id)

    print(f"[DEBUG][get_sku_identifiers] 输入: '{search_word}'")
    print(f"[DEBUG][get_sku_identifiers] 提取标识: {identifiers}")
    return identifiers


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
        return {"title": "", "current_price": None}

    selected_text = selected.group(1).strip()
    sel = selected_text.lower()
    id_norm = identifier.lower()
    is_capacity = bool(re.match(r'\d+[a-z]+$', id_norm))
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
    brand_set = _get_brand_aliases_lower()
    words = identifier.split()
    click_word = words[0].lower()
    for w in words:
        if w.lower() not in brand_set:
            click_word = w.lower()
            break
    print(f"[DEBUG][_click_sku_by_identifier] 用于点击的关键词: '{click_word}'")

    xpath = (
        f'//*[contains(translate(@text, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
        f'"abcdefghijklmnopqrstuvwxyz"), "{click_word}")]'
    )
    elem = d.xpath(xpath)
    if elem.exists:
        elem.click()
        print(f"[DEBUG][_click_sku_by_identifier] 点击文本匹配成功")
        time.sleep(timeout)
        return True

    xpath_desc = (
        f'//*[contains(translate(@content-desc, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
        f'"abcdefghijklmnopqrstuvwxyz"), "{click_word}")]'
    )
    elem_desc = d.xpath(xpath_desc)
    if elem_desc.exists:
        elem_desc.click()
        print(f"[DEBUG][_click_sku_by_identifier] 点击 content-desc 匹配成功")
        time.sleep(timeout)
        return True

    print(f"[DEBUG][_click_sku_by_identifier] 未找到可点击控件")
    return False


def get_sku_price_auto(d, search_word: str, click_timeout: float = 2.0) -> Dict[str, Optional[str]]:
    """自动匹配规格并返回已选规格文本和价格"""
    print(f"\n[DEBUG][get_sku_price_auto] 开始匹配，搜索词: '{search_word}'")
    identifiers = get_sku_identifiers(search_word)
    if not identifiers:
        print("[DEBUG][get_sku_price_auto] 未提取到任何规格标识，退出")
        return {"title": "", "current_price": None}

    # 第一轮：当前页面匹配
    print("[DEBUG][get_sku_price_auto] === 第一轮：当前页面匹配 ===")
    xml = d.dump_hierarchy()
    for ident in identifiers:
        res = extract_sku_price_with_id(xml, ident, search_word)
        if res["current_price"]:
            print(f"[DEBUG][get_sku_price_auto] 匹配成功，价格: {res['current_price']}")
            return res

    # 第二轮：按优先级点击后匹配
    print("[DEBUG][get_sku_price_auto] === 第二轮：点击后匹配 ===")
    non_cap = [i for i in identifiers if not re.match(r'\d+[a-z]+$', i)]
    cap = [i for i in identifiers if re.match(r'\d+[a-z]+$', i)]
    print(f"[DEBUG][get_sku_price_auto] 非容量标识: {non_cap}")
    print(f"[DEBUG][get_sku_price_auto] 容量标识: {cap}")
    for ident in non_cap + cap:
        print(f"[DEBUG][get_sku_price_auto] 尝试标识: {ident}")
        if _click_sku_by_identifier(d, ident, click_timeout):
            time.sleep(0.5)
            xml = d.dump_hierarchy()
            res = extract_sku_price_with_id(xml, ident, search_word)
            if res["current_price"]:
                print(f"[DEBUG][get_sku_price_auto] 点击后匹配成功，价格: {res['current_price']}")
                return res

    print("[DEBUG][get_sku_price_auto] 所有尝试均失败")
    return {"title": "", "current_price": None}