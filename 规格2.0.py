import pandas as pd
import re

# ====================== 你确认好的品牌库 ======================
brand_lib = {
    "赫莲娜": ["HR", "HelenaRubinstein", "Helena Rubinstein", "赫莲娜"],
    "海蓝之谜": ["LM", "LaMer", "La Mer", "腊梅", "海蓝"],
    "莱珀妮": ["LP", "LaPrairie", "La Prairie", "莱珀妮", "莱珀"],
    "希思黎": ["Sisley", "希思黎"],
    "法尔曼": ["Valmont", "法尔曼"],
    "兰蔻": ["Lancome", "Lancôme", "兰蔻"],
    "娇兰": ["Guerlain", "娇兰"],
    "倩碧": ["Clinique", "倩碧"],
    "娇韵诗": ["Clarins", "娇韵", "娇韵诗"],
    "科颜氏": ["Kiehls", "Kiehl's", "科颜", "科颜氏"],
    "碧欧泉": ["Biotherm", "碧欧", "碧欧泉"],
    "薇姿": ["Vichy", "薇姿"],
    "德美乐嘉": ["Dermalogica", "德美", "德美乐嘉"],
    "雅诗兰黛": ["EsteeLauder", "Estée Lauder", "ESTEE LAUDER", "雅诗", "雅诗兰黛"],
    "大宝": ["Embryolisse", "大宝"],
    "薇迪薇奇": ["VidiVici", "Vidi Vici", "薇迪", "薇迪薇奇"],

    "肌肤之钥": ["CPB", "CleDePeauBeaute", "Cle de Peau Beauté", "肌肤之钥", "cledepece"],
    "SK-II": ["SK2", "SKII", "SK-II"],
    "资生堂": ["Shiseido", "资生", "资生堂"],
    "黛珂": ["Decorte", "Decorté", "黛珂"],
    "城野医生": ["DrCiLabo", "Dr.Ci:Labo", "城野", "城野医生"],
    "茵芙莎": ["IPSA", "茵芙", "茵芙莎"],
    "宝丽": ["POLA", "宝丽"],
    "兰芝": ["Laneige", "兰芝"],
    "植村秀": ["ShuUemura", "Shu Uemura", "植村秀"],

    "汤姆福特": ["TF", "TomFord", "Tom Ford", "汤姆福特"],
    "圣罗兰": ["YSL", "YvesSaintLaurent", "Yves Saint Laurent", "圣罗", "圣罗兰"],
    "魅可": ["MAC", "M.A.C", "魅可"],
    "纳斯": ["NARS", "纳斯"],
    "芭比布朗": ["BobbiBrown", "Bobbi Brown", "BB", "芭比", "芭比布朗"],
    "纪梵希": ["Givenchy", "纪梵", "纪梵希"],
    "苏秘": ["Sum37", "Su:m37", "苏秘", "苏秘37"],
    "衰败城市": ["UrbanDecay", "Urban Decay", "衰败", "衰败城市"],
    "罗拉": ["LauraMercier", "Laura Mercier", "罗拉"],

    "后": ["WHOO", "TheHistoryOfWhoo", "The History Of Whoo", "后"],
    "雪花秀": ["Sulwhasoo", "雪花", "后雪", "雪花秀"],

    "祖玛珑": ["JM", "JoMalone", "Jo Malone", "祖马龙", "祖玛", "祖玛珑"],
    "芦丹氏": ["SL", "SergeLutens", "Serge Lutens", "芦丹氏"],
    "百瑞德": ["Byredo", "百瑞", "百瑞德"],
    "爱马仕": ["Hermes", "Hermès", "爱马", "爱马仕"],
    "古驰": ["Gucci", "古驰"],
    "范思哲": ["Versace", "范思", "范思哲"],
    "阿玛尼": ["Armani", "阿玛", "阿玛尼"],
    "巴宝莉": ["Burberry", "巴宝莉", "博柏利"],
    "蔻依": ["Chloe", "Chloé", "克洛伊", "蔻依"],
    "莫杰": ["MarcJacobs", "Marc Jacobs", "MJ", "莫杰"],
    "纳西索": ["Narciso", "纳西索"],
    "帕尔玛之水": ["AcquaDiParma", "Acqua di Parma", "帕尔玛之水"],
    "梅森马吉拉": ["MaisonMargiela", "Maison Margiela", "MM", "梅森马吉拉", "马丁马吉拉"],
    "欧珑": ["AtelierCologne", "Atelier Cologne", "欧珑"],
    "潘海利根": ["Penhaligons", "Penhaligon’s", "潘海利根"],
    "蒂普提克": ["Diptyque", "Diptyque Paris", "蒂普提克"],
    "宝格丽": ["Bvlgari", "宝格", "宝格丽"],
    "杜鲁萨迪": ["Trussardi", "杜鲁", "杜鲁萨迪"],
    "卡尔文克雷恩": ["CK", "CalvinKlein", "Calvin Klein", "卡尔文克雷恩"],
    "缪缪": ["MiuMiu", "miumiu", "Miu Miu", "缪缪"],
    "香奈儿": ["Chanel", "香奈", "香奈儿"],

    "卡诗": ["Kerastase", "Kérastase", "卡诗"],
    "欧舒丹": ["Loccitane", "L'Occitane", "欧舒", "欧舒丹"],
    "欧莱雅": ["Loreal", "L'Oréal", "欧莱", "欧莱雅"],
    "潘婷": ["Pantene", "潘婷"],
    "大卫杜夫": ["Davidoff", "大卫", "大卫杜夫"],
    "拉夫劳伦": ["RalphLauren", "Ralph Lauren", "拉夫", "拉夫劳伦"],
    "馥蕾诗": ["Fresh", "馥蕾", "馥蕾诗"],

    "伟博": ["Webber", "伟博"],
    "慕拉得塑": ["Murad", "慕拉", "慕拉得"],
    "未来驱蚊": ["VAPE", "未來", "未来驅蚊"],
    "澳洲NatureBOBO": ["NatureBOBO", "Nature BOBO", "澳洲"],
    "旧街场": ["OldTown", "Old Town", "旧街场"],
    "费列罗": ["Ferrero", "费列", "费列罗"]
}


# ====================== 【终极规格提取：全覆盖 + 优先级 + 匹配后删除】 ======================
def extract_specs(text):
    text = str(text).strip()
    temp_text = text
    result = []
    import re
    import pdb  # 调试库

    # ====================== 你的原版规则 完全不动 ======================
    rules = [
        # 1. 最高：# 完整色号（L3#, #666, 610#）
        r'[A-Za-z0-9]+#',
        r'#[A-Za-z0-9]+',

        # 2. 字母+数字完整型号（1W0, 2C0, NC12, PO-01）
        r'[0-9][A-Za-z][0-9]',
        r'[A-Za-z]+[0-9]+[A-Za-z]*',
        r'(?<!\.)\d+[A-Za-z]+',
        r'[A-Za-z]+-[0-9]+',

        # 3. xx色 / xx号
        r'\d+色',
        r'\d+号',

        # 4. 完整容量（4.5g, 400ml, 1.5g）
        r'\d+\.\d+\s*[mlgMLG]+',
        r'\d+\s*[mlgMLG]+',
        r'\d+\s*[条粒支瓶盒装片]',

        # 5. 香水类型
        r'EDT|EDP|浓香|淡香',

        # 6. 套装
        r'对装|两支装|三支装|两瓶装|双支装|\*2|x2|X2',

        # 7. 版本/年份（必须匹配，不遗漏）
        r'新款|新版|旧版|经典款',
        r'\d+款|\d+年',

        # 8. 最后：纯数字（最低优先级）
        r'(?<![A-Za-z])\d+\.?\d*(?![A-Za-z#])',
    ]

    # ====================== 关键：遇到 4.5g 自动断点调试 ======================
    # if re.search(r'\d+\.\d+[gml]', temp_text, re.I):
    #     print("\n⚠️  检测到 4.5g 格式，自动进入调试断点！")

    # 正常匹配流程
    for pattern in rules:
        matches = re.findall(pattern, temp_text, re.IGNORECASE)
        for val in matches:
            val = val.strip()
            if len(val) < 1 or val in result:
                continue
            result.append(val)
            temp_text = temp_text.replace(val, " ")

    # 去重
    final = []
    seen = set()
    for item in result:
        if item not in seen:
            seen.add(item)
            final.append(item)

    return " | ".join(final) if final else "无规格"


# ====================== 主函数 ======================
def extract_and_export(file_path):
    df = pd.read_excel(file_path)
    df_out = df.copy()

    print("=" * 80)
    print("【规格型号提取结果】")
    print("=" * 80)

    spec_list = []
    for idx, row in df.iterrows():
        name = str(row["货品名称"]).strip()
        spec = extract_specs(name)
        spec_list.append(spec)

        print(f"序号 {row['序号']}")
        print(f"原名：{name}")
        print(f"规格：{spec}")
        print("-" * 80)

    df_out["规格型号"] = spec_list
    df_out.to_excel("已提取规格型号.xlsx", index=False)
    print("\n✅ 提取完成！已输出：已提取规格型号.xlsx")


# ====================== 运行 ======================
if __name__ == "__main__":
    extract_and_export("搜索名单.xlsx")