import time
import uiautomator2 as u2
import re
from typing import Dict, Optional, Set

# 连接手机
d = u2.connect()
print("=== 设备信息 ===")
print(d.info)
print("=" * 50)

# ====================== 品牌字典 ======================
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
    "纳斯": ["NARS", "纳斯"],
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

def fuzzy_contains_no_stop(core, target):
    filtered = ''.join(ch for ch in core if ch not in STOP_CHARS)
    if not filtered:
        return False
    pattern = '.*?'.join(re.escape(ch) for ch in filtered)
    return re.search(pattern, target) is not None

_brand_aliases_lower = None
def _get_brand_aliases_lower():
    global _brand_aliases_lower
    if _brand_aliases_lower is None:
        _brand_aliases_lower = set()
        for aliases in brand_lib.values():
            for a in aliases:
                _brand_aliases_lower.add(a.lower())
    return _brand_aliases_lower

def extract_specs(text: str):
    """从文本中提取容量数字集合和色号集合（已过滤容量误识别）"""
    text = str(text).lower()
    cap_nums: Set[str] = set()
    color_codes: Set[str] = set()
    pack_set: Set[str] = set()

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
        if not code.isdigit():
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
    # 纯数字色号（2~4位），排除容量、包装、年份、有效期
    for m in re.finditer(r'(?<!\d)(\d{2,4})(?!\d)', text):
        code = m.group(1)
        start = m.start()
        prefix = text[max(0, start-10):start]
        if re.search(r'(效期|到期|限用日期|保质期|\d\s*年|年)', prefix):
            continue
        if code not in cap_nums and code not in pack_set and not re.fullmatch(r'20\d{2}', code):
            color_codes.add(code)

    # ---------- 后置过滤：剔除被误识别为色号的容量单位 ----------
    unit_abbr = {'ml', 'g', 'l', 'oz', '毫升', '克', '升', '片', '粒', '枚', '支', '个', '盒', '瓶', '块'}
    filtered_colors = set()
    for code in color_codes:
        # 匹配数字+单位模式
        m = re.match(r'^(\d+\.?\d*)([a-z]+)$', code)
        if m:
            num_str = m.group(1)
            unit = m.group(2)
            if unit in unit_abbr:
                try:
                    val = float(num_str)
                    if val.is_integer():
                        num_str_int = str(int(val))
                    else:
                        num_str_int = num_str
                    # 数字属于容量集合则忽略
                    if num_str_int in cap_nums:
                        continue
                except ValueError:
                    pass
        filtered_colors.add(code)
    color_codes = filtered_colors

    return cap_nums, color_codes

def match_brand(text):
    """品牌匹配，返回标准品牌名"""
    txt = str(text).lower()
    for name, aliases in brand_lib.items():
        for a in aliases:
            if a.lower() in txt:
                return name
    return "未匹配"

def clean_title(text, brand):
    """深度清洗标题（去除品牌、容量、色号、营销噪声）"""
    s = str(text).lower()
    if brand != "未匹配" and brand in brand_lib:
        for alias in brand_lib[brand]:
            s = re.sub(re.escape(alias.lower()), '', s, flags=re.I)
    s = re.sub(r'(?:\d+[\-\/\s]*)*\d+\.?\d*\s*(ml|g|l|oz|片|粒|枚|对|支|个|盒|瓶|块|毫升|克|升)', '', s, flags=re.I)
    noise_phrases = [
        r'/\s*(支|个|件|瓶|盒|对|组)',
        r'(新\s*)?条码',
        r'效期\d{2,4}年',
        r'(效期|到期|限用日期|保质期)\s*\d{2,4}\s*年?',
        r'百补品牌.*?件',
        r'热销\d+\.?\d*万件',
        r'热销\d+件',
        r'\d+\.?\d*万件',
        r'法国直发|进口|原装|专柜|正品|保税仓|直邮|发货',
        r'【.*?】|\[.*?\]|\(.*?\)',
        r'女士|男士',
        r'浓香|淡香|edp|edt|edc|香水|香氛',
        r'水光|绚色|光感|自然色?\b|自然',
        r'奶桃|西柚|烟粉|豆沙|粉金|小粉金',
        r'磨皮|持妆|服帖|亲妈',
        r'精华|修护|滋润|保湿|遮瑕|持久|焕亮|柔滑|控油|清爽|温和|清透',
        r'版|款|型',
        r'馥郁|浓情|淡雅|清新',
        r'新品|新款|新版|旧版|经典款|升级版',
        r'柑橘调|花香调|木质调|果香调|东方调|西普调|皮革调|馥奇调',
        r'\b单品\b',
        r'留香|芳香|芬芳|芬芳馥郁',
        r'\b水\b',
        r'\b新\b',
        r'20\d{2}年|\d{2}年',
        r'油皮|干皮|混油|无泵头|有泵头',
        r'\b20\d{2}\b',
        r'丝柔|柔雾|冷萃|玫瑰|sweet\s?deal',
        r'大宠粉|大辣椒|宠粉',
    ]
    for pat in noise_phrases:
        s = re.sub(pat, '', s, flags=re.I)
    s = re.sub(r'[\*xX×]\s*\d+', '', s)
    s = re.sub(r'\d+\s*(支|个|件|瓶|盒|对|组)\s*装?', '', s)
    s = re.sub(r'(两|双|三|四|五|六)\s*(支|个|瓶|盒|对|组)\s*装?', '', s)
    s = re.sub(r'#[a-zA-Z0-9]+', '', s)
    s = re.sub(r'[a-zA-Z0-9]+#', '', s)
    s = re.sub(r'\b[A-Za-z]?\d+[A-Za-z]*\s*(色|号)\b', '', s)
    s = re.sub(r'\b[a-z]?\d+[a-z]\d*\b', '', s)
    s = re.sub(r'\b[A-Za-z]\d+\b', '', s)
    s = re.sub(r'(?<!\d)\d{2,4}(?!\d)', '', s)
    EN_STOP_WORDS = {'a', 'an', 'of', 'in', 'on', 'to', 'for', 'the', 'is', 'at', 'by', 'or', 'no', 'if', 'we', 'it'}
    def remove_en_stopwords(txt):
        return re.sub(r'\b[a-z]{1,2}\b', lambda m: '' if m.group() in EN_STOP_WORDS else m.group(), txt)
    s = remove_en_stopwords(s)
    s = re.sub(r'[^\u4e00-\u9fff\w]', '', s)
    return s.strip()

def get_sku_identifier(search_word: str) -> Optional[str]:
    """提取规格标识：色号 > 英文产品名(去品牌) > 容量+单位"""
    # 1. 色号
    _, color_codes = extract_specs(search_word)
    if color_codes:
        return max(color_codes, key=len)

    # 2. 英文产品名（去掉容量数字+单位，然后提取≥2的字母序列，过滤品牌别名）
    cleaned = re.sub(r'\d+(?:\.\d+)?\s*(ml|g|l|oz|毫升|克|升)\b', '', search_word, flags=re.I)
    words = re.findall(r'[a-zA-Z]{2,}', cleaned)
    if words:
        brand_set = _get_brand_aliases_lower()
        # 过滤品牌词
        meaningful = [w for w in words if w.lower() not in brand_set]
        if meaningful:
            return ' '.join(meaningful).lower()
        # 全是品牌词？用原词（极少情况）
        return ' '.join(words).lower()

    # 3. 容量+单位
    m = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g|l|oz|毫升|克|升)', search_word, re.I)
    if m:
        num = m.group(1)
        unit = m.group(2).lower()
        unit_map = {'毫升': 'ml', '克': 'g', '升': 'l'}
        unit = unit_map.get(unit, unit)
        return f"{num}{unit}"
    return None

import re, time
from typing import Dict, Optional, Set

# ---------- 辅助：容量出现次数统计 ----------
def _count_capacity_occurrences(xml_content: str, capacity_id: str) -> int:
    """返回 text 或 content-desc 中包含该容量标识的节点数量（忽略大小写）"""
    pattern = rf'<(?:node|android\.widget\.\w+)[^>]*?(?:text|content-desc)="[^"]*{re.escape(capacity_id)}[^"]*"'
    return len(re.findall(pattern, xml_content, re.IGNORECASE))

# ---------- 标识提取 ----------
def get_sku_identifiers(search_word: str) -> list:
    identifiers = []
    seen = set()

    # 1. 完整色号（如 NC12）
    full_colors = re.findall(r'\b([a-zA-Z]{1,4}\d{1,3}[a-zA-Z]?)\b', search_word)
    for c in full_colors:
        cl = c.lower()
        if cl not in seen:
            seen.add(cl)
            identifiers.append(cl)

    # 2. 拆分色号，过滤长度<3的纯数字
    _, color_codes = extract_specs(search_word)
    for c in color_codes:
        cl = c.lower()
        if cl in seen:
            continue
        if re.fullmatch(r'\d+', cl) and len(cl) < 3:
            continue
        seen.add(cl)
        identifiers.append(cl)

    # 3. 英文产品名（过滤品牌词，如果全是品牌词则跳过）
    cleaned = re.sub(r'\d+(?:\.\d+)?\s*(ml|g|l|oz|毫升|克|升)\b', '', search_word, flags=re.I)
    words = re.findall(r'[a-zA-Z]{2,}', cleaned)
    if words:
        brand_set = _get_brand_aliases_lower()
        meaningful = [w for w in words if w.lower() not in brand_set]
        if meaningful:
            eng_id = ' '.join(meaningful).lower()
            if eng_id not in seen:
                seen.add(eng_id)
                identifiers.append(eng_id)
        # 如果全是品牌词，则跳过（不添加英文名标识）

    # 4. 容量+单位
    m = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g|l|oz|毫升|克|升)', search_word, re.I)
    if m:
        num = m.group(1)
        unit = m.group(2).lower()
        unit_map = {'毫升': 'ml', '克': 'g', '升': 'l'}
        unit = unit_map.get(unit, unit)
        cap_id = f"{num}{unit}"
        if cap_id not in seen:
            identifiers.append(cap_id)

    return identifiers

# ---------- 带校验的价格提取 ----------
def extract_sku_price_with_id(xml_content: str, identifier: str, search_word: str = "") -> Dict[str, Optional[str]]:
    if not identifier:
        return {"title": "", "current_price": None}
    print(f"尝试匹配标识: {identifier}")

    # 已选节点
    selected = re.search(r'<node[^>]*?(?:text|content-desc)="([^"]*已选(?:择)?[^"]*)"', xml_content)
    if not selected:
        print("未找到已选节点")
        return {"title": "", "current_price": None}
    selected_text = selected.group(1).strip()
    print(f"已选节点: {selected_text}")

    sel = selected_text.lower()
    id_norm = identifier.lower()
    is_capacity = bool(re.match(r'\d+[a-z]+$', id_norm))

    matched = False
    if is_capacity:
        # 容量匹配：数字和单位均出现
        num = re.search(r'\d+', id_norm).group()
        unit = id_norm.replace(num, '')
        if num in sel and unit in sel:
            # 唯一性检查
            occ = _count_capacity_occurrences(xml_content, id_norm)
            if occ > 2:
                print(f"容量 {id_norm} 出现 {occ} 次（>2），忽略")
                return {"title": "", "current_price": None}
            # 色号/英文名校验
            all_ids = get_sku_identifiers(search_word)
            non_cap_ids = [cid for cid in all_ids if not re.match(r'\d+[a-z]+$', cid)]
            if non_cap_ids and not any(cid in sel for cid in non_cap_ids):
                print(f"容量匹配但已选缺少标识 {non_cap_ids}，无效")
                return {"title": "", "current_price": None}
            matched = True
            print("容量匹配+唯一性+色号校验通过")
    else:
        # 非容量匹配
        if id_norm in sel:
            matched = True
        else:
            id_words = id_norm.split()
            if len(id_words) > 1 and any(w in sel for w in id_words):
                matched = True

    if not matched:
        print("标识不匹配")
        return {"title": "", "current_price": None}

    print("标识匹配成功")

    # 提取价格
    price_m = re.search(r'<node[^>]*?(?:text|content-desc)="([^"]*?[¥￥]\s*\d+\.?\d*[^"]*)"', xml_content)
    if price_m:
        num_m = re.search(r'[¥￥]\s*(\d+\.?\d*)', price_m.group(1))
        if num_m:
            price = num_m.group(1)
            try:
                if float(price) >= 10:
                    return {"title": selected_text, "current_price": price}
            except ValueError:
                pass
    print("未找到有效价格")
    return {"title": selected_text, "current_price": None}

# ---------- 自动流程（先匹配，后点击） ----------
def get_sku_price_auto(d, search_word: str, click_timeout: float = 2.0) -> Dict[str, Optional[str]]:
    identifiers = get_sku_identifiers(search_word)
    if not identifiers:
        print("未提取到任何规格标识")
        return {"title": "", "current_price": None}
    print(f"候选标识: {identifiers}")

    # 第一轮：当前页面匹配
    xml = d.dump_hierarchy()
    for ident in identifiers:
        res = extract_sku_price_with_id(xml, ident, search_word)
        if res["current_price"]:
            return res

    # 第二轮：按顺序点击（先非容量，后容量）
    non_cap = [i for i in identifiers if not re.match(r'\d+[a-z]+$', i)]
    cap = [i for i in identifiers if re.match(r'\d+[a-z]+$', i)]
    for ident in non_cap + cap:
        print(f"尝试点击标识: {ident}")
        if _click_sku_by_identifier(d, ident, click_timeout):
            time.sleep(0.5)
            xml = d.dump_hierarchy()
            res = extract_sku_price_with_id(xml, ident, search_word)
            if res["current_price"]:
                return res

    print("所有标识尝试完毕")
    return {"title": "", "current_price": None}


# 保留原函数名兼容（内部使用 get_sku_identifiers 的第一个标识）
def extract_sku_price(xml_content: str, search_word: str) -> Dict[str, Optional[str]]:
    ids = get_sku_identifiers(search_word)
    ident = ids[0] if ids else None
    return extract_sku_price_with_id(xml_content, ident)


def _click_sku_by_identifier(d: u2.Device, identifier: str, timeout: float = 2.0) -> bool:
    """
    使用 XPath contains + translate 忽略大小写点击控件
    若 identifier 含多个单词，优先用第一个非品牌词点击
    """
    # 确定用于点击的关键词（单个单词）
    brand_set = _get_brand_aliases_lower()
    words = identifier.split()
    click_word = words[0].lower()
    for w in words:
        if w.lower() not in brand_set:
            click_word = w.lower()
            break

    # 构造 XPath：忽略大小写匹配 text 属性
    xpath = (
        f'//*[contains(translate(@text, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
        f'"abcdefghijklmnopqrstuvwxyz"), "{click_word}")]'
    )
    elem = d.xpath(xpath)
    if elem.exists:
        print(f"点击匹配文本: {elem.get().attrib.get('text', '')}")
        elem.click()
        time.sleep(timeout)
        return True

    # 降级：尝试 content-desc 属性
    xpath_desc = (
        f'//*[contains(translate(@content-desc, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
        f'"abcdefghijklmnopqrstuvwxyz"), "{click_word}")]'
    )
    elem_desc = d.xpath(xpath_desc)
    if elem_desc.exists:
        print(f"点击匹配描述: {elem_desc.get().attrib.get('content-desc', '')}")
        elem_desc.click()
        time.sleep(timeout)
        return True

    return False

# ====================== 原有商品名称+价格提取 ======================
def extract_product_info(xml_content: str, search_word: str) -> Dict[str, Optional[str]]:
    # 原函数保留，内容略（按你之前提供的完整实现）
    pass



# ====================== 调试运行 ======================
if __name__ == '__main__':
    # 示例1：当前已选择色号匹配时
    # result1 = get_sku_price_auto(d, 'YSL粉气垫替换芯B10')
    # print("\n===== 结果1 =====")
    # print("匹配文本:", result1["title"])
    # print("价格:", result1["current_price"])

    # 示例2：当前已选择色号不匹配，会自动点击 BR20 再提取
    result2 = get_sku_price_auto(d, 'NARS 水光绚色液体腮红 Secret Lover 7ml')
    print("\n===== 结果2 =====")
    print("匹配文本:", result2["title"])
    print("价格:", result2["current_price"])