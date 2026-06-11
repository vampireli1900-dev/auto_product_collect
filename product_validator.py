import re
from typing import List, Optional
from spec_utils import extract_concentration, extract_simple_pack, concentration_match, extract_specs, brand_lib
# ====================== 品牌字典 ======================


# ====================== 工具函数 ======================
STOP_CHARS = set("的之了·・-— ")

def fuzzy_contains_no_stop(core, target):
    """去除 core 中的虚词后再做模糊子序列包含"""
    filtered = ''.join(ch for ch in core if ch not in STOP_CHARS)
    if not filtered:
        return False
    pattern = '.*?'.join(re.escape(ch) for ch in filtered)
    return re.search(pattern, target) is not None

def match_brand(text):
    """品牌匹配，返回标准品牌名，未匹配返回'未匹配'。优先匹配最长的别名。"""
    txt = str(text).lower()
    best_brand = "未匹配"
    best_len = 0
    for name, aliases in brand_lib.items():
        for a in aliases:
            a_lower = a.lower()
            if a_lower in txt:
                if len(a_lower) > best_len:
                    best_len = len(a_lower)
                    best_brand = name
    return best_brand

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
    s = re.sub(r'(?:\d+[\-\/\s]*)*\d+\.?\d*\s*(ml|g|l|oz|片|粒|枚|对|支|个|盒|瓶|块|毫升|克|升|条)', '', s, flags=re.I)
    # 4. 移除营销/噪声短语（持续可扩充）
    noise_phrases = [
        r'绮梦',   # 删除系列名/营销词
        r'栀',  # 删除系列名/营销词
        r'轻垫',
        r'/\s*(支|个|件|瓶|盒|对|组)',  # 移除 /支、/个 等包装单位
        r'(新\s*)?条码',  # 移除“新条码”、“条码”
        r'效期\d{2,4}年',  # 保质期信息
        r'(效期|到期|限用日期|保质期)\s*\d{2,4}\s*年?',
        r'百补品牌.*?件',        # 百补品牌热销225.2万件
        r'热销\d+\.?\d*万件',
        r'热销\d+件',
        r'\d+\.?\d*万件',
        r'\d+\.?\d*\s*万\+?',  # 106.3万+
        r'品牌好评[\d\.]+万\+?条',  # 品牌好评106.3万+条
        r'法国直发|进口|原装|专柜|正品|保税仓|直邮|发货',
        r'【.*?】|\[.*?\]|\(.*?\)',
        r'浓香|淡香|edp|edt|edc|香水|香氛',
        r'水光|绚色|光感|自然色?\b|自然',   # “自然”可能有“自然色”，我们删除“自然色”优先
        r'奶桃|西柚|烟粉|豆沙|粉金|小粉金',
        r'磨皮|服帖|亲妈',          # 已有部分可能重复，无妨
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
        '透亮': '提亮',
        '焕白': '美白',
        '亮白': '美白',
        '提亮': '提亮',
        '减黄': '去黄',
        '去黄': '去黄',
        '乳液': '乳',
        '奶乳': '乳',
        '乳美': '乳',
        '白淡': '淡斑',
        '斑乳': '乳',
        '乳白': '乳',
        '肌底液': '精华',
        '第二代': '二代',
        '润肤乳': '黄油',
        '有油润肤': '黄油',    # 新增：解决本案例
        '黄油': '黄油',
        '能量水': '水',
        '鲜活亮采': '水',
        '亮采水': '水',
        '红石榴': '红石榴',
        '口红': '唇膏',
        '唇膏': '唇膏',
        '金管': '金',
        '金色': '金',
        '短管': '管',
        '哑光': '哑光',  # 可选
        # 遮瑕类
        '遮瑕膏': '遮瑕',
        '遮瑕蜜': '遮瑕',
        '遮瑕': '遮瑕',
        # 香草与vanilla
        '香草': 'vanilla',
        'vanilla': 'vanilla',
        # 色号词（可忽略）
        '色号': '',
        '男生': '男士',
        '男士': '男士',
        '爽肤水': '爽肤水',
        '均衡水': '爽肤水',
        '活力均衡水': '爽肤水',
        '酒渍樱桃色': 'insatiable',
        '液体腮红': '腮红',
        '流体腮红': '腮红',
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

def apply_manual_overrides(search_word, product_title, result):
    """
    手动覆盖校验结果，处理通用逻辑无法正确判断的特例。
    参数：
        search_word: 搜索词
        product_title: 商品标题
        result: 包含 final, remark, name_ok, spec_ok 等字段的字典
    返回：
        修改后的 result 字典（会直接修改原字典，并返回）
    """
    # 规则1：兰蔻养肤水粉底液 vs 持妆粉底液 → 不通过
    if "养肤" in search_word and "持妆" in product_title:
        result['remark'] = "单例规则：'养肤'与'持妆'不符，品名不匹配"
        result['name_ok'] = False
        print("⚠️ 单例规则命中：兰蔻养肤水 vs 持妆")
        return result

    if "MAC 丝柔哑光唇膏" in search_word and "子弹头" in product_title:

        result['remark'] = "单例规则：子弹头强制通过"
        result['name_ok'] = True
        print("⚠️ 单例规则命中：子弹头强制通过")
        return result
    # 可以继续添加其他规则...
    if "小黑瓶眼霜" in search_word and "黑金臻宠眼霜" in product_title:
        result['name_ok'] = False
        extra = "单例规则：小黑瓶与黑金臻宠不符，品名不匹配"
        original = result.get('remark', '')
        if original and original != "通过":
            result['remark'] = f"{original}（{extra}）"
        else:
            result['remark'] = extra
        print("⚠️ 单例规则命中：兰蔻小黑瓶眼霜 vs 黑金臻宠，强制不通过")
        return result

    return result

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
    s_conc = extract_concentration(search_word)
    p_conc = extract_concentration(product_title)
    conc_ok = concentration_match(s_conc, p_conc)
    s_simple = extract_simple_pack(search_word)
    p_simple = extract_simple_pack(product_title)
    simple_ok = (s_simple == p_simple) if s_simple and p_simple else True

    # 容量检查
    if s_cap:
        cap_ok = s_cap.issubset(p_cap)
    else:
        cap_ok = True

    # 色号检查
    product_lower = product_title.lower()
    color_ok = all(code in product_lower for code in s_color)

    # 规格综合判断
    if s_color and p_color and color_ok:
        spec_ok = True
    else:
        spec_ok = cap_ok and color_ok

    # 3. 品名清洗
    s_clean = clean_title(search_word, s_brand)
    p_clean = clean_title(product_title, p_brand)

    # 4. 品名匹配（词袋优先）
    s_tokens_raw = [normalize_token(t) for t in tokenize(s_clean)]
    p_tokens_raw = [normalize_token(t) for t in tokenize(p_clean)]

    def is_chinese_token(tk):
        return bool(re.search(r'[\u4e00-\u9fff]', tk))

    s_cn_tokens = [t for t in s_tokens_raw if is_chinese_token(t)]
    p_cn_tokens = [t for t in p_tokens_raw if is_chinese_token(t)]

    if s_cn_tokens and p_cn_tokens:
        s_tokens = s_cn_tokens
        p_tokens = p_cn_tokens
    else:
        s_tokens = s_tokens_raw
        p_tokens = p_tokens_raw

    bag_ratio = word_bag_ratio(s_tokens, p_tokens)
    threshold = 0.3
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
        name_ok = ratio >= 0.3
        method = f'LCS子序列({ratio:.1%})'

    # ------------------- 单例规则（仅修改 name_ok 和追加 remark）-------------------
    # 构造原始 remark（不含单例）
    reasons = []
    if not brand_ok: reasons.append("品牌不一致")
    if not spec_ok: reasons.append("规格不匹配")
    if not conc_ok: reasons.append("浓度不匹配")
    if not simple_ok: reasons.append("简装不匹配")
    if not name_ok: reasons.append(f"品名相似不足(ratio={ratio:.1%})")
    original_remark = '；'.join(reasons) if reasons else "通过"

    temp = {'name_ok': name_ok, 'remark': original_remark}
    temp = apply_manual_overrides(search_word, product_title, temp)
    name_ok = temp['name_ok']
    remark = temp['remark']
    # ---------------------------------------------------------------------

    # 最终校验
    final = brand_ok and spec_ok and conc_ok and simple_ok and name_ok

    # 构造输出原因
    if final:
        if remark and remark != "通过":
            reason_tail = remark
        else:
            reason_tail = "所有检查通过"
    else:
        reasons_dbg = []
        if not brand_ok: reasons_dbg.append("品牌不一致")
        if not spec_ok: reasons_dbg.append("规格不匹配")
        if not conc_ok: reasons_dbg.append("浓度不匹配")
        if not simple_ok: reasons_dbg.append("简装不匹配")
        if not name_ok: reasons_dbg.append(f"品名相似不足(ratio={ratio:.1%})")
        reason_tail = "；".join(reasons_dbg)
        # 附加单例说明（如果有）
        if remark and remark != "通过" and remark != original_remark:
            reason_tail += f"（{remark}）"

    # 输出
    lines_out = [
        "=" * 60,
        f"搜索词 ：{search_word}",
        f"商品名 ：{product_title}",
        f"品牌    ：{s_brand} → {p_brand} | {'✅' if brand_ok else '❌'}",
        f"容量规格：{s_cap} → {p_cap} | {'✅' if spec_ok else '❌'}",
        f"色号    ：{s_color} → {p_color}",
        f"浓度    ：{s_conc} → {p_conc} | {'✅' if conc_ok else '❌'}",
        f"简装    ：{s_simple} → {p_simple} | {'✅' if simple_ok else '❌'}",
        f"清洗后  ：{s_clean} → {p_clean}",
        f"品名匹配：{method} | {'✅' if name_ok else '❌'}",
        f"结果    ：{'✅ PASS' if final else '❌ FAIL'} | 原因：{reason_tail}",
        "=" * 60,
    ]
    if trace_lines is not None:
        trace_lines.extend(lines_out)
    for ln in lines_out:
        print(ln)

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
        's_conc': s_conc,
        'p_conc': p_conc,
        'conc_ok': conc_ok,
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
    validate_product("后拱辰享水妍洁面180ml",
                     "韩国Whoo水妍洗面奶180ml控油深层清洁保湿滋润")
    print()
    validate_product("娇韵诗双萃精华50ml九代新版",
                     "【娇韵诗】九代双萃精华50ml/瓶滋润补水")
    print()
    validate_product("娇韵诗透亮焕白淡斑乳液75mL",
                     "【正品行货】Clarins/娇韵诗牛奶乳75ml美白淡斑减黄提亮保湿滋润")
    print()
    validate_product("科颜氏白泥面膜125ml 24款",
                     "Kiehls 科颜氏 亚马逊二代白泥面膜 125ml")
    print()
    validate_product("科颜氏 美白淡斑精华100ml",
                     "Kiehl’s/科颜氏VC淡斑精华液 面部提亮焕白肤色均衡亮肤50/100ml【5天内发货】")
    print()
    validate_product("拉夫劳伦地球淡香氛 100ml",
                     "【平潭保税】Ralph Lauren拉夫劳伦 地球淡香水EDT男女100ml简装")
    print()
    validate_product("拉夫劳伦俱乐部香水淡香型 100ML",
                     "RALPH LAUREN拉夫劳伦俱乐部男士浓香水100ml木质调EDP送男友礼物")
    print()
    validate_product("资生堂男士乳液100ml",
                     "【正品行货】资生堂男士焕能肌活滋润乳 100ml")
    print()
    validate_product("阿玛尼权力PR0粉底30ml#3",
                     "【阿玛尼】权力粉底液 3 号新款 30ml 持妆控油遮瑕油皮亲妈持久")
    print()
    validate_product("倩碧有油润肤乳125ml",
                     "【Clinique】倩碧黄油滋润(有油)125ml")
    print()
    validate_product("雅诗兰黛 红石榴洁面125ml",
                     "【ESTEE LAUDER】雅诗兰黛新款红石榴洗面奶125ml")
    print()
    validate_product("MAC魅可 轻尤雾弹 哑光唇釉973 5ml 新版",
                     "【MAC】魅可尤雾弹唇釉新色裸色系列哑光秋冬显色口红952/996/997/973【5天内发货】")
    print()
    validate_product("阿玛尼红气垫替换芯2#-24年",
                     "【品牌好评106.3万+条】GIORGIO ARMANI/阿玛尼红气垫替换芯15g#2号色单双个控油持妆新款")
    print()
    validate_product("古驰倾色绒雾唇膏505（金色短管）",
                     "【正品行货】Gucci古驰口红505金管绒雾哑光口红礼盒装 生日礼物")
    print()
    validate_product("蔻依北国雪松浓香水50ml",
                     "【蔻依】仙境花园系列北国雪松香水150ml浓香持久留香")
    print()
    validate_product("资生堂男生爽肤水150ml",
                     "【正品行货】资生堂男士活力均衡水150ml   补水保湿")
    print()

    validate_product("古驰绮梦栀子花香水50ml浓香型",
                     "Gucci古驰绮梦馥栀女士EDP浓香水50ml 25年新品")
    print()
    validate_product("马来西亚进口OldTown旧街场白咖啡特浓浓醇三合一速溶白咖啡15条",
                     "【旗舰店】旧街场马来西亚进浓醇三合一白咖啡速溶咖啡粉40条盒装")
    print()
    validate_product("大卫杜夫 冷水男士香水 75ml EDP 加强版",
                     "【大卫杜夫】冷水男士香水海洋调男士淡香水男生节日礼物75ml")
    print()
    validate_product("圣罗兰 明彩粉光轻垫粉底液 粉气垫 #B20 CN",
                     "【正品行货】YSL圣罗兰粉气垫12g  B10 B20 BR20遮瑕保湿持久养肤")
    print()
    validate_product("圣罗兰 明彩粉光轻垫粉底液 粉气垫 #B20 CN",
                     "【正品行货】圣罗兰新明彩轻垫粉底液 20 SPF35 遮瑕轻薄透气正装")
    print()
    validate_product("圣罗兰 明彩粉光轻垫粉底液 粉气垫 #B20 CN",
                     "【YSL】圣罗兰粉皮革气垫 明彩粉光轻垫粉底液气 垫 保湿持久遮瑕")
    print()
    validate_product("YSL圣罗兰恒久粉底液25年新款粉盖LC1",
                     "【YSL】圣罗兰25年新款贴肤衣粉底液 混干持妆服帖遮瑕粉盖LC1/LC2【5天内发货】")
    print()
    validate_product("SK-II前男友面膜10片装",
                     "【SK-II】前男友面膜贴片面膜单片*10组合保湿补水修复抗衰老美白【5天内发货】")
    print()
    validate_product("兰蔻养肤水粉底液 PO-01 30ml",
                     "【正品行货】兰蔻新款持妆粉底液30ml PO-01")
    print()
    validate_product("NARS液体腮红 INSATIABLE",
                     "【正品行货】NARS小粉金流体腮红水光绚色流体腮红酒渍樱桃色7ml")
    print()
    validate_product("NARS多用腮红棒欲焰HOT TAKE 8G",
                     "【NARS】娜斯新品柔滑多功能棒腮红棒眼颊唇三用swing,sex appeal 8g")
    print()
    validate_product("MAC 丝柔哑光唇膏 #669 WARM TEDDY 暖萌泰迪",
                     "【MAC】魅可大子弹头口红唇膏显色显白#602 大辣椒")
    print()
    validate_product("兰蔻小黑瓶眼霜15ml",
                     "Lancome 兰蔻 黑金臻宠眼霜 15ml")
    print()