import re
from typing import List, Optional

# ====================== 品牌字典 ======================
brand_lib = {
    "赫莲娜": ["HR", "HelenaRubinstein", "Helena Rubinstein", "赫莲娜"],
    "海蓝之谜": ["LM", "LaMer", "La Mer", "腊梅", "海蓝之谜"],
    "莱珀妮": [ "LaPrairie", "Prairie", "莱珀妮"],
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
    "后": ["WHOO", "TheHistoryOfWhoo", "The History Of Whoo", "后" ],
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

# ====================== 工具函数 ======================
STOP_CHARS = set("的之了·・-— ")

def fuzzy_contains_no_stop(core, target):
    """去除 core 中的虚词后再做模糊子序列包含"""
    filtered = ''.join(ch for ch in core if ch not in STOP_CHARS)
    if not filtered:
        return False
    pattern = '.*?'.join(re.escape(ch) for ch in filtered)
    return re.search(pattern, target) is not None

def extract_specs(text):
    text = str(text).lower()
    cap_nums = set()
    color_codes = set()
    pack_set = set()   # 包装数字，防止被当成色号

    # ---------- 容量（不变）----------
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

    # ---------- 包装数量（新加入，必须在纯数字色号之前）----------
    # 1. *2, x2, ×2 等
    for m in re.finditer(r'[\*xX×]\s*(\d+)', text):
        pack_set.add(m.group(1))
    # 2. 2支, 2支装, 2个, 2瓶 等
    for m in re.finditer(r'(\d+)\s*(支|个|件|瓶|盒|对|组)\s*装?', text):
        pack_set.add(m.group(1))
    # 3. 中文数量词：两支装、三瓶等
    chinese_num_map = {'两':'2','三':'3','四':'4','五':'5','六':'6'}
    for m in re.finditer(r'(两|三|四|五|六)\s*(支|个|瓶|盒|对|组)\s*装?', text):
        pack_set.add(chinese_num_map[m.group(1)])

    # ---------- 色号（调整纯数字部分）----------
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
        # 如果数字后紧跟“年”，跳过（年份信息）
        if end < len(text) and text[end] == '年':
            continue
        prefix = text[max(0, start - 10):start]
        if re.search(r'(效期|到期|限用日期|保质期|\d\s*年|年)', prefix):
            continue
        if code not in cap_nums and code not in pack_set and not re.fullmatch(r'20\d{2}', code):
            color_codes.add(code)

    return cap_nums, color_codes   # 返回值不变，内部已处理 pack_set

def match_brand(text):
    """品牌匹配，返回标准品牌名，未匹配返回"未匹配" """
    txt = str(text).lower()
    for name, aliases in brand_lib.items():
        for a in aliases:
            if a.lower() in txt:
                return name
    return "未匹配"

def clean_title(text, brand):
    """
    深度清洗标题：
    - 移除已识别品牌别名
    - 移除容量、色号片段
    - 移除常见营销噪声和无意义修饰词
    - 保留有意义的中文、英文、数字序列
    """
    s = str(text).lower()

    # 1. 去掉品牌别名
    if brand != "未匹配" and brand in brand_lib:
        for alias in brand_lib[brand]:
            s = re.sub(re.escape(alias.lower()), '', s, flags=re.I)

    # 2. 去掉容量相关字符串
    s = re.sub(r'(?:\d+[\-\/\s]*)*\d+\.?\d*\s*(ml|g|l|oz|片|粒|枚|对|支|个|盒|瓶|块|毫升|克|升)', '', s, flags=re.I)

    # 4. 移除营销/噪声短语（持续可扩充）
    noise_phrases = [
        r'/\s*(支|个|件|瓶|盒|对|组)',  # 移除 /支、/个 等包装单位
        r'(新\s*)?条码',  # 移除“新条码”、“条码”
        r'效期\d{2,4}年',  # 保质期信息
        r'(效期|到期|限用日期|保质期)\s*\d{2,4}\s*年?',
        r'百补品牌.*?件',        # 百补品牌热销225.2万件
        r'热销\d+\.?\d*万件',
        r'热销\d+件',
        r'\d+\.?\d*万件',
        r'法国直发|进口|原装|专柜|正品|保税仓|直邮|发货',
        r'【.*?】|\[.*?\]|\(.*?\)',
        r'女士|男士',
        r'浓香|淡香|edp|edt|edc|香水|香氛',
        r'水光|绚色|光感|自然色?\b|自然',   # “自然”可能有“自然色”，我们删除“自然色”优先
        r'奶桃|西柚|烟粉|豆沙|粉金|小粉金',
        r'磨皮|持妆|服帖|亲妈',          # 已有部分可能重复，无妨
        r'精华|修护|滋润|保湿|遮瑕|持久|焕亮|柔滑|控油|清爽|温和|清透',
        r'版|款|型',
        r'馥郁|浓情|淡雅|清新',
        r'新品|新款|新版|旧版|经典款|升级版',
        r'柑橘调|花香调|木质调|果香调|东方调|西普调|皮革调|馥奇调',
        r'\b单品\b',  # 加入 noise_phrases
        r'留香|芳香|芬芳|芬芳馥郁',
        r'\b水\b',               # 孤立“水”字
        r'\b新\b',               # 孤立“新”字
        r'20\d{2}年|\d{2}年',    # 2026年、26年
        r'油皮|干皮|混油|无泵头|有泵头',
        r'\b20\d{2}\b',  # 2026（无年）
        r'丝柔|柔雾|冷萃|玫瑰|sweet\s?deal',  # 颜色/气味/质地修饰词
        r'大宠粉|大辣椒|宠粉',  # 色号别名/营销词

    ]
    for pat in noise_phrases:
        s = re.sub(pat, '', s, flags=re.I)

    # 4. 移除数量表达式（*2, x2, 2支装 等）——在纯数字删除之前
    s = re.sub(r'[\*xX×]\s*\d+', '', s)  # *2
    s = re.sub(r'\d+\s*(支|个|件|瓶|盒|对|组)\s*装?', '', s)  # 2支, 2支装
    s = re.sub(r'(两|双|三|四|五|六)\s*(支|个|瓶|盒|对|组)\s*装?', '', s) # 中文数量
    # 5. 去掉色号/型号
    s = re.sub(r'#[a-zA-Z0-9]+', '', s)  # #1C1
    s = re.sub(r'[a-zA-Z0-9]+#', '', s)  # 1N2#
    s = re.sub(r'\b[A-Za-z]?\d+[A-Za-z]*\s*(色|号)\b', '', s)
    s = re.sub(r'\b[a-z]?\d+[a-z]\d*\b', '', s)  # 独立色号，如 1C1、NC20
    s = re.sub(r'\b[A-Za-z]\d+\b', '', s)  # 删除 L1、N2 等
    # 5.5 删除独立纯数字（2~4位），不依赖单词边界
    s = re.sub(r'(?<!\d)\d{2,4}(?!\d)', '', s)


    # 5. 只删除英文虚词（常见介词/冠词），保留产品代号
    EN_STOP_WORDS = {'a', 'an', 'of', 'in', 'on', 'to', 'for', 'the', 'is', 'at', 'by', 'or', 'no', 'if', 'we', 'it'}

    def remove_en_stopwords(txt):
        return re.sub(r'\b[a-z]{1,2}\b', lambda m: '' if m.group() in EN_STOP_WORDS else m.group(), txt)

    s = remove_en_stopwords(s)

    # 6. 只保留中文、英文、数字
    s = re.sub(r'[^\u4e00-\u9fff\w]', '', s)
    return s.strip()

def fuzzy_contains(core, text):
    """模糊子序列包含（不忽略虚词）"""
    pattern = '.*?'.join(re.escape(ch) for ch in core)
    return re.search(pattern, text) is not None

def tokenize(text):
    """分词：英文单词｜连续2-4字的中文短语（重叠提取，去重）"""
    # 英文单词
    eng_words = re.findall(r'[a-zA-Z]{2,}', text.lower())   # 至少2个字母，避免无意义单字
    # 中文短语：利用正向预扫描，提取所有长度2-4的子串，后面会去重
    chinese = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
    # 合并去重，保留顺序
    seen = set()
    tokens = []
    for t in eng_words + chinese:
        if t not in seen:
            seen.add(t)
            tokens.append(t)
    return tokens

def normalize_token(tk):
    """美妆常用同义词归一化"""
    mapping = {
        '洗面奶': '洁面',
        '洁面泡沫': '洁面',
        '洁面乳': '洁面',
        '洁面膏': '洁面',
        '洁面啫喱': '洁面',
        '泡沫洁面': '洁面',
        '防晒乳': '防晒',
        '防晒霜': '防晒',
        '防晒露': '防晒',
        '子弹头': '子弹',
        # 可继续补充
    }
    return mapping.get(tk, tk)

def word_bag_ratio(search_tokens, product_tokens):
    """
    搜索词中的每个 token，只要在商品 tokens 的任意一个中出现（子串包含），
    即视为匹配。
    """
    if not search_tokens:
        return 0.0
    found = 0
    for tk in search_tokens:
        if any(tk in pt for pt in product_tokens):
            found += 1
    return found / len(search_tokens)

def lcs_sequence_length(a, b):
    """最长公共子序列长度（不要求连续）"""
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]

def lcs_substring_length(a, b):
    """最长公共连续子串长度"""
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    max_len = 0
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                max_len = max(max_len, dp[i][j])
            else:
                dp[i][j] = 0
    return max_len

# ====================== 核心校验函数 ======================
def validate_product(
    search_word,
    product_title,
    trace_lines: Optional[List[str]] = None,
):
    # 1. 品牌
    s_brand = match_brand(search_word)
    p_brand = match_brand(product_title)
    brand_ok = (s_brand == p_brand) if s_brand != "未匹配" else True

    # 2. 规格（分离容量与色号）
    s_cap, s_color = extract_specs(search_word)
    p_cap, p_color = extract_specs(product_title)

    # 容量检查：搜索有容量时，要求是商品容量的子集
    if s_cap:
        spec_ok = s_cap.issubset(p_cap)
    else:
        spec_ok = True

    # 色号检查：搜索中的每一个色号必须整体出现在商品文本中（忽略大小写）
    product_lower = product_title.lower()
    for code in s_color:
        if code not in product_lower:
            spec_ok = False
            break

    # 3. 品名清洗
    s_clean = clean_title(search_word, s_brand)
    p_clean = clean_title(product_title, p_brand)

    # 4. 品名匹配（词袋优先）
    # --- 原始 tokens ---
    s_tokens_raw = [normalize_token(t) for t in tokenize(s_clean)]
    p_tokens_raw = [normalize_token(t) for t in tokenize(p_clean)]

    # 纯中文 token 过滤（至少包含一个汉字）
    def is_chinese_token(tk):
        return bool(re.search(r'[\u4e00-\u9fff]', tk))

    s_cn_tokens = [t for t in s_tokens_raw if is_chinese_token(t)]
    p_cn_tokens = [t for t in p_tokens_raw if is_chinese_token(t)]

    # 若双方都有中文 token，则用中文 token 计算；否则回退到原始 token
    if s_cn_tokens and p_cn_tokens:
        s_tokens = s_cn_tokens
        p_tokens = p_cn_tokens
    else:
        s_tokens = s_tokens_raw
        p_tokens = p_tokens_raw

    bag_ratio = word_bag_ratio(s_tokens, p_tokens)

    # 调试输出（可选保留）
    print(f"[DEBUG] 搜索词 tokens (过滤后): {s_tokens}")
    print(f"[DEBUG] 商品 tokens  (过滤后): {p_tokens}")
    print(f"[DEBUG] bag_ratio = {bag_ratio:.2f}")

    # 色号辅助动态阈值
    if s_color:
        threshold = 0.3
    else:
        threshold = 0.5
    bag_ok = bag_ratio >= threshold

    if bag_ok:
        name_ok = True
        ratio = bag_ratio
        method = f'词袋({bag_ratio:.1%})'
    elif fuzzy_contains_no_stop(s_clean, p_clean):
        name_ok = True
        ratio = 1.0
        method = '模糊包含(去虚词)'
    elif fuzzy_contains(s_clean, p_clean):
        name_ok = True
        ratio = 1.0
        method = '模糊包含'
    else:
        common = lcs_sequence_length(s_clean, p_clean)
        if len(s_clean) > 0:
            ratio = common / len(s_clean)
        else:
            ratio = 1.0
        name_ok = (ratio >= 0.50) and (common >= 2)
        method = f'LCS子序列({ratio:.1%})'
    final = brand_ok and spec_ok and name_ok

    if final:
        reason_tail = "所有检查通过"
    else:
        reasons_dbg = []
        if not brand_ok:
            reasons_dbg.append("品牌不一致")
        if not spec_ok:
            reasons_dbg.append("规格不匹配")
        if not name_ok:
            reasons_dbg.append(f"品名相似不足(ratio={ratio:.1%})")
        reason_tail = "；".join(reasons_dbg)

    lines_out = [
        "=" * 60,
        f"搜索词 ：{search_word}",
        f"商品名 ：{product_title}",
        f"品牌    ：{s_brand} → {p_brand} | {'✅' if brand_ok else '❌'}",
        f"容量规格：{s_cap} → {p_cap} | {'✅' if spec_ok else '❌'}",
        f"色号    ：{s_color} → {p_color}",
        f"清洗后  ：{s_clean} → {p_clean}",
        f"品名匹配：{method} | {'✅' if name_ok else '❌'}",
        f"结果    ：{'✅ PASS' if final else '❌ FAIL'} | 原因：{reason_tail}",
        "=" * 60,
    ]
    if trace_lines is not None:
        trace_lines.extend(lines_out)
    for ln in lines_out:
        print(ln)
    reasons = []
    if not brand_ok: reasons.append('品牌不一致')
    if not spec_ok: reasons.append('规格不匹配')
    if not name_ok: reasons.append(f'品名相似不足(ratio={ratio:.1%})')
    remark = '；'.join(reasons) if reasons else '通过'

    return {
        'final': final,
        's_brand': s_brand,
        'p_brand': p_brand,
        'brand_ok': brand_ok,
        'spec_ok': spec_ok,
        'name_ok': name_ok,
        's_cap': s_cap,
        'p_cap': p_cap,
        's_color': s_color,
        'p_color': p_color,
        's_clean': s_clean,
        'p_clean': p_clean,
        'method': method,
        'ratio': ratio,
        'remark': remark,
    }

# ====================== 测试用例 ======================
if __name__ == '__main__':
    # 案例1：之前失败的兰蔻是我
    validate_product("Lancome 兰蔻是我 浓情版 100ml",
                     "【百补品牌热销225.2万件】Lancome/兰蔻 IDOLE是我香水100ml 女士EDP持久花香调浓香")
    print()

    # 案例2：美丽人生范围容量
    validate_product("兰蔻 美丽人生香氛精华香水 50ml",
                     "兰蔻美丽人生馥郁版女士浓香EDP 30-50-100ml")
    print()

    # 案例3：李先生花园
    validate_product("李先生的花园(Le Jardin de Monsieur Li)，淡香水，100 ml",
                     "【Hermes】爱马仕香水李先生花园淡香水100mlEDT芳香柑橘调 持久留香")
    print()

    # 案例4：DW粉底液色号
    validate_product("ESTEE LAUDER /雅诗兰黛 DW持妆粉底液 #1C1 30ML 新版 2026年",
                     "【雅诗兰黛】DW持妆粉底液30ml油皮遮瑕控油无泵头1C1")
    print()

    # 案例4：DW粉底液色号
    validate_product("ESTEE LAUDER /雅诗兰黛 DW持妆粉底液 #1N2 30ML 新版 2026",
                     "【雅诗兰黛】DW持妆粉底液油皮亲妈持久遮瑕控油服帖防晒1N2#")
    print()

    # 案例4：DW粉底液色号
    validate_product("MAC魅可 丝柔哑光唇膏 大子弹口红#666 Sweet Deal 玫瑰冷萃",
                     "【正品行货】MAC/魅可大子弹头口红哑光柔雾666大宠粉602大辣椒")
    print()

    # 案例4：DW粉底液色号
    validate_product("NARS蜜粉饼5894 效期24年",
                     "【NARS】娜斯5894大白饼粉饼控油磨皮持妆蜜粉饼【5天内发货】")
    print()

    # 案例4：DW粉底液色号
    validate_product("WHOO/后拱辰享洁面泡沫180ml/支 （新条码）",
                     "韩国Whoo后拱辰享雪玉凝美白洁面洗面奶180ml*2")
    print()

    # 案例4：DW粉底液色号
    validate_product("马丁马吉拉-爵士酒廊淡香100ml",
                     "【Maison Margiela】 梅森马吉拉 爵士酒廊淡香水EDT 100毫升【5天内发货】")
    print()
    # 案例4：DW粉底液色号
    validate_product("NARS 水光绚色液体腮红 西柚奶桃 BRAZEN 7ml",
                     "Nars纳斯小粉金液体腮红7ml光感自然#BEHAVE烟粉豆沙")
    print()

    # 案例4：DW粉底液色号
    validate_product("古驰炼金师花园狮之心香水100ML",
                     "GUCCI/古驰炼金士花园系列香水100ML正品香氛送礼")
    print()
    # 案例4：DW粉底液色号
    validate_product("NARS 超方瓶粉底液#L1",
                     "【NARS】超方瓶流光美肌粉底液L1 30ml保湿滋润持久遮瑕")
    print()
    # 案例4：DW粉底液色号
    validate_product("NARS细管101 NO ANGEL",
                     "【NARS】NARS娜斯细管口红#102 #116  #135 #133 #1011.5g/支")
    print()
    # 案例4：DW粉底液色号
    validate_product("TF幻魅四色眼影盘#41 Peach Dawn桃色晨曦盘",
                     "正品TomFord/汤姆福特四色眼影41#PeachDawnTF桃色晨曦盘哑光显色【5天内发货】")
    print()
    # 案例4：DW粉底液色号
    validate_product("YSL口红8B",
                     "【正品行货】YSL圣罗兰粉管润唇膏 口红滋润保湿7b化妆品生日礼物")
    print()
    # 案例4：DW粉底液色号
    validate_product("黛珂散粉01 24年新版",
                     "【黛珂】心悦容光幻纱丝柔蜜粉#01细腻柔滑持久调光师定妆散粉")
    print()
    # 案例4：DW粉底液色号
    validate_product("黛珂散粉光肌00 24年新版",
                     "【黛珂】2024新版心悦容光幻纱丝柔蜜粉细腻柔滑持久定妆")
    print()
    validate_product("古驰花悦绽放女士浓香50ml",
                     "【原装正品】GUCCI/古驰花悦女士浓香水EDP30/50/100ml花香调")
    print()
    validate_product("古驰竹韵淡香50ml",
                     "【正品行货】GUCCI古驰竹韵女士浓香水持久花香木质调EDP 50ml")
    print()