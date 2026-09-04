import re
from typing import List, Optional

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
    "雅诗兰黛": ["EsteeLauder", "Estée Lauder", "ESTEE LAUDER", "雅诗兰黛"],
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
    "伊丽莎白雅顿": ["ElizabethArden", "Elizabeth Arden", "伊丽莎白雅顿", '雅顿'],
    "迪奥": ["Dior", "迪奥"],
    "克雷德": ["Creed", "克雷德"],
    "罗意威": ["Loewe", "罗意威"],
    "香缇卡": ["Chantecaille", "香缇卡"],
    "伊索": ["Aesop", "伊索"],
    "CNP": ["CNP", "CNP"],
}

def extract_concentration(text):
    """
    从文本中提取香精浓度类型，返回标准化标识。
    返回值: 'heavy' (浓香/EDP/香精), 'light' (淡香/EDT/古龙水), 或 '' (未识别)
    """
    t = text.lower()
    # 浓组
    heavy_patterns = [
        r'\bedp\b', r'parfum', r'浓香', r'浓香水', r'香精',
        r'eaudeparfum', r'edp', r'浓香型'
    ]
    # 淡组
    light_patterns = [
        r'\bedt\b', r'\bedc\b', r'淡香', r'淡香水', r'古龙水',
        r'eaudetoilette', r'eaudecologne', r'淡香型'
    ]
    for pat in heavy_patterns:
        if re.search(pat, t):
            return '浓香'
    for pat in light_patterns:
        if re.search(pat, t):
            return '淡香'
    return ''


def extract_simple_pack(text):
    """检测简装标识，返回'简装'或空字符串"""
    t = text.lower()
    if re.search(r'简装', t):
        return '简装'
    return ''


def concentration_match(conc_a, conc_b):
    """
    浓度匹配规则：
    - 如果任一为空，认为通过（无约束）
    - 否则必须同组（heavy-heavy 或 light-light）才匹配
    """
    if not conc_a or not conc_b:
        return True
    return conc_a == conc_b

def extract_specs(text):
    text = str(text).lower()
    cap_nums = set()
    color_codes = set()
    pack_set = set()

    # ---------- 容量 ----------
    cap_pattern = r'(\d+(?:\.\d+)?(?:\s*[-/]\s*\d+(?:\.\d+)?)*)\s*(ml|g|l|oz|片|粒|枚|对|支|个|盒|瓶|块|毫升|克|升|条)'
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
    # 字母+字母+数字（如 LC1, NC20, BR20）
    for m in re.finditer(r'(?<![a-z0-9])([a-z]{2}\d{1,2})(?![a-z0-9])', text):
        color_codes.add(m.group(1))
    # 单字母/数字色号（如 L1, N2）
    for m in re.finditer(r'(?<![a-z0-9])([A-Za-z]\d+)(?![a-z0-9])', text):
        code = m.group(1).lower()
        if code not in cap_nums:
            color_codes.add(code)
    # 数字+单字母色号（如 8B, 02N）
    for m in re.finditer(r'(?<!\d)(\d+[a-zA-Z])(?![a-zA-Z0-9])', text):
        code = m.group(1).lower()
        if code not in cap_nums:
            color_codes.add(code)
    # 纯数字色号（2~4位），排除容量、包装、年份、有效期、日期，以及营销数字（如“106.3万”）
    for m in re.finditer(r'(?<!\d)(\d{2,4})(?!\d)', text):
        code = m.group(1)
        start = m.start()
        end = m.end()
        # 如果数字后紧跟“万”或“w”（含小数点情况已在前面匹配时分离，但这里直接检查后续字符）
        after = text[end:end+2]
        if after.startswith('万') or after.startswith('w'):
            continue
        # 如果数字前有“万”（如“106.3万”中的“.3”部分不会匹配到纯数字，但“106”前面可能是小数点，需要更精细）
        # 检查数字前面是否有小数点（表示是小数部分），如果有，跳过
        if start > 0 and text[start-1] == '.':
            continue
        # 如果数字后紧跟“+”或“条”等，也跳过
        if after.startswith('+') or after.startswith('条'):
            continue
        # 检查前面是否有“热销”“好评”“销量”等营销词
        prefix = text[max(0, start-10):start]
        if re.search(r'(热销|好评|销量|评分|万\+?)', prefix):
            continue
        # 原有其他检查...
        if end < len(text) and (text[end] == '年' or text[end] == '款'):
            continue
        before = text[max(0, start-3):start]
        after2 = text[end:min(len(text), end+3)]
        if re.search(r'月|日', before) or re.search(r'月|日', after2):
            continue
        prefix2 = text[max(0, start-10):start]
        if re.search(r'(效期|到期|限用日期|保质期|\d\s*年|年)', prefix2):
            continue
        if code not in cap_nums and code not in pack_set and not re.fullmatch(r'20\d{2}', code):
            color_codes.add(code)

    color_codes = {c for c in color_codes if not re.search(r'(ml|g|oz|升|毫升)$', c.lower())}
    cap_nums.update(pack_set)
    # ========== 新增：过滤品牌别名 ==========
    # 构建品牌别名集合（小写）
    brand_aliases_lower = set()
    for aliases in brand_lib.values():
        for a in aliases:
            brand_aliases_lower.add(a.lower())
    # 过滤色号：剔除属于品牌别名的
    filtered_color_codes = {c for c in color_codes if c.lower() not in brand_aliases_lower}

    return cap_nums, filtered_color_codes