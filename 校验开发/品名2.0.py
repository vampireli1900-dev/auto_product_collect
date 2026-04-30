import pandas as pd
import re

# ====================== 统一品牌字典 ======================
brand_lib = {
    # 奢护护肤
    "赫莲娜": ["HR", "HelenaRubinstein", "Helena Rubinstein", "赫莲娜"],
    "海蓝之谜": ["LM", "LaMer", "La Mer", "腊梅", "海蓝之谜"],
    "莱珀妮": ["LP", "LaPrairie", "La Prairie", "莱珀妮"],
    "希思黎": ["Sisley", "希思黎"],
    "法尔曼": ["Valmont", "法尔曼"],
    "兰蔻": ["Lancome", "Lancôme", "兰蔻"],
    "娇兰": ["Guerlain", "娇兰"],
    "倩碧": ["Clinique", "倩碧"],
    "娇韵诗": ["Clarins",  "娇韵诗"],
    "科颜氏": ["Kiehls", "Kiehl's",  "科颜氏"],
    "碧欧泉": ["Biotherm", "碧欧泉"],
    "薇姿": ["Vichy", "薇姿"],
    "德美乐嘉": ["Dermalogica",  "德美乐嘉"],
    "雅诗兰黛": ["EsteeLauder", "Estée Lauder", "ESTEE LAUDER", "雅诗兰黛", "红石榴"],
    "大宝": ["Embryolisse", "大宝"],
    "薇迪薇奇": ["VidiVici", "Vidi Vici", "薇迪薇奇"],

    # 日韩护肤
    "肌肤之钥": ["CPB", "CleDePeauBeaute", "Cle de Peau Beauté", "肌肤之钥", "cledepeau"],
    "SK-II": ["SK2", "SKII", "SK-II"],
    "资生堂": ["Shiseido",  "资生堂"],
    "安耐晒": ["安耐晒"],
    "黛珂": ["Decorte", "Decorté", "黛珂"],
    "城野医生": ["DrCiLabo", "Dr.Ci:Labo", "城野医生"],
    "茵芙莎": ["IPSA", "茵芙莎", "茵芙纱"],
    "宝丽": ["POLA", "宝丽"],
    "兰芝": ["Laneige", "兰芝"],
    "植村秀": ["ShuUemura", "Shu Uemura", "植村秀"],

    # 彩妆
    "汤姆福特": ["TF", "TomFord", "Tom Ford", "汤姆福特"],
    "圣罗兰": ["YSL", "YvesSaintLaurent", "Yves Saint Laurent",  "圣罗兰"],
    "魅可": ["MAC", "M.A.C", "魅可"],
    "纳斯": ["NARS", "纳斯"],
    "芭比布朗": ["BobbiBrown", "Bobbi Brown", "BB", "芭比布朗", "芭比波朗"],
    "纪梵希": ["Givenchy", "纪梵希"],
    "苏秘": ["Sum37", "Su:m37", "苏秘", "苏秘37"],
    "衰败城市": ["UrbanDecay", "Urban Decay", "衰败城市"],
    "罗拉": ["LauraMercier", "Laura Mercier", "罗拉"],

    # 韩系
    "后": ["WHOO", "TheHistoryOfWhoo", "The History Of Whoo", "后", "拱辰享"],
    "雪花秀": ["Sulwhasoo", "雪花", "后雪", "雪花秀"],

    # 香水 / 轻奢香氛
    "祖玛珑": ["JM", "JoMalone", "Jo Malone", "祖马龙", "祖玛珑"],
    "芦丹氏": ["SL", "SergeLutens", "Serge Lutens", "芦丹氏"],
    "百瑞德": ["Byredo",  "百瑞德"],
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

    # 洗护 / 身体 / 生活类
    "卡诗": ["Kerastase", "Kérastase", "卡诗"],
    "欧舒丹": ["Loccitane", "L'Occitane",  "欧舒丹"],
    "欧莱雅": ["Loreal", "L'Oréal", "欧莱雅"],
    "潘婷": ["Pantene", "潘婷"],
    "大卫杜夫": ["Davidoff", "大卫杜夫"],
    "拉夫劳伦": ["RalphLauren", "Ralph Lauren",  "拉夫劳伦"],
    "馥蕾诗": ["Fresh", "馥蕾诗"],

    # 补充定制品牌
    "伟博": ["Webber", "伟博"],
    "慕拉得": ["Murad", "慕拉得"],
    "未来驱蚊": ["VAPE", "未來", "未来驅蚊"],
    "澳洲NatureBOBO": ["NatureBOBO", "Nature BOBO", "澳洲"],
    "旧街场": ["OldTown", "Old Town", "旧街场"],
    "费列罗": ["Ferrero", "费列", "费列罗"]
}

# ====================== 品牌匹配函数 ======================
def match_brand(text):
    text_lower = str(text).lower()  # 转小写
    matched_brand = "未匹配"
    # 按品牌字典匹配，返回标准品牌名
    for standard_name, alias_list in brand_lib.items():
        for alias in alias_list:
            alias_lower = alias.lower()  # 别名也转小写
            if alias_lower in text_lower:
                matched_brand = standard_name
                return matched_brand, alias  # 找到立即返回，避免重复
    return matched_brand, ""

# ====================== 规格提取函数（全覆盖+优先级） ======================
def extract_specs(text):
    text = str(text).strip()
    temp_text = text
    result = []

    rules = [
        r'[A-Za-z0-9]+#', r'#[A-Za-z0-9]+',
        r'[0-9][A-Za-z][0-9]', r'[A-Za-z]+[0-9]+[A-Za-z]*', r'(?<!\.)\d+[A-Za-z]+', r'[A-Za-z]+-[0-9]+',
        r'\d+色', r'\d+号',
        r'\d+\.\d+\s*[mlgMLG]+', r'\d+\s*[mlgMLG]+', r'\d+\s*[条粒支瓶盒装片]',
        r'EDT|EDP|浓香|淡香',
        r'对装|两支装|三支装|两瓶装|双支装|\*2|x2|X2',
        r'新款|新版|旧版|经典款', r'\d+款|\d+年',
        r'(?<![A-Za-z])\d+\.?\d*(?![A-Za-z#])',
    ]

    for pattern in rules:
        matches = re.findall(pattern, temp_text, re.IGNORECASE)
        for val in matches:
            val = val.strip()
            if val and val not in result:
                result.append(val)
                temp_text = temp_text.replace(val, " ")

    return " | ".join(result) if result else "无规格"

# ====================== ✅ 修复版：删除【所有品牌别名】 ======================
def clean_final_name(original_name, brand_name, spec_text):
    name = str(original_name).strip()

    # ==============================================
    # 忽略大小写 删除所有品牌别名（解决 GUCCI / gucci 删不掉）
    # ==============================================
    if brand_name != "未匹配":
        for alias in brand_lib[brand_name]:
            # 不区分大小写 替换删除
            pattern = re.compile(re.escape(alias), re.IGNORECASE)
            name = pattern.sub("", name)

    # ==============================================
    # 不区分大小写 删除规格
    # ==============================================
    if spec_text != "无规格":
        for s in spec_text.split(" | "):
            pattern = re.compile(re.escape(s), re.IGNORECASE)
            name = pattern.sub("", name)

    # 清理多余符号
    name = re.sub(r'[ /\\\-_|()（）【】]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name if name else "纯品牌/纯规格"

# ====================== 主函数：整合输出 ======================
def process_full_export(file_path):
    # 读取文件
    df = pd.read_excel(file_path)
    required_cols = ["货品名称", "关键词", "序号"]
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ 表格缺少列：{col}")
            return

    # 存储结果
    result_data = []
    unmatched_list = []  # 用来存未匹配品牌

    # 控制台排版表头
    print("\n" + "="*140)
    print(f"{'序号':<6}{'原货品名称':<45}{'匹配品牌':<12}{'规格型号':<35}{'最终品名':<40}")
    print("="*140)

    # 逐行处理
    for _, row in df.iterrows():
        serial = row["序号"]
        original = str(row["货品名称"]).strip()
        keyword = str(row["关键词"]).strip()

        # 1 匹配品牌
        brand, _ = match_brand(f"{original} {keyword}")
        # 2 提取规格
        spec = extract_specs(original)
        # 3 清洗最终品名
        final_name = clean_final_name(original, brand, spec)

        # 记录未匹配
        if brand == "未匹配":
            unmatched_list.append({
                "序号": serial,
                "货品名称": original,
                "关键词": keyword
            })

        # 加入结果
        result_data.append({
            "序号": serial,
            "原货品名称": original,
            "关键词": keyword,
            "匹配品牌": brand,
            "规格型号": spec,
            "最终品名": final_name
        })

        # 控制台美观输出
        print(f"{serial:<6}{original[:42]+'...' if len(original)>42 else original:<45}{brand:<12}{spec[:32]+'...' if len(spec)>32 else spec:<35}{final_name[:37]+'...' if len(final_name)>37 else final_name:<40}")

    # 生成Excel
    out_df = pd.DataFrame(result_data)
    out_df.to_excel("品牌+规格+最终品名完整版.xlsx", index=False)

    # 统计
    total = len(result_data)
    unmatched = len(unmatched_list)
    print("="*140)
    print(f"✅ 处理完成 | 总计：{total} 条 | 品牌未匹配：{unmatched} 条")

    # ====================== 打印未匹配品牌清单 ======================
    if unmatched_list:
        print("\n" + "="*80)
        print("📛 以下是【未匹配品牌】的所有条目：")
        print("="*80)
        for item in unmatched_list:
            print(f"序号：{item['序号']} | 货品名称：{item['货品名称']}")
        print("="*80 + "\n")

    print(f"📁 Excel 文件已生成：品牌+规格+最终品名完整版.xlsx\n")

# ====================== 运行 ======================
if __name__ == "__main__":
    process_full_export("搜索名单.xlsx")