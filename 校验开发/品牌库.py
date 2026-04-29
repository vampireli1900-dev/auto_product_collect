import pandas as pd

# ====================== 【你的品牌字典】 ======================
brand_lib = {
    # 奢护护肤
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

    # 日韩护肤
    "肌肤之钥": ["CPB", "CleDePeauBeaute", "Cle de Peau Beauté", "肌肤之钥", "cledepeau"],
    "SK-II": ["SK2", "SKII", "SK-II"],
    "资生堂": ["Shiseido", "资生", "资生堂"],
    "黛珂": ["Decorte", "Decorté", "黛珂"],
    "城野医生": ["DrCiLabo", "Dr.Ci:Labo", "城野", "城野医生"],

    "茵芙莎": ["IPSA", "茵芙", "茵芙莎"],
    "宝丽": ["POLA", "宝丽"],
    "兰芝": ["Laneige", "兰芝"],
    "植村秀": ["ShuUemura", "Shu Uemura", "植村秀"],

    # 彩妆
    "汤姆福特": ["TF", "TomFord", "Tom Ford", "汤姆福特"],
    "圣罗兰": ["YSL", "YvesSaintLaurent", "Yves Saint Laurent", "圣罗", "圣罗兰"],
    "魅可": ["MAC", "M.A.C", "魅可"],
    "纳斯": ["NARS", "纳斯"],
    "芭比布朗": ["BobbiBrown", "Bobbi Brown", "BB", "芭比", "芭比布朗"],
    "纪梵希": ["Givenchy", "纪梵", "纪梵希"],
    "苏秘": ["Sum37", "Su:m37", "苏秘", "苏秘37"],
    "衰败城市": ["UrbanDecay", "Urban Decay", "衰败", "衰败城市"],
    "罗拉": ["LauraMercier", "Laura Mercier", "罗拉"],

    # 韩系
    "后": ["WHOO", "TheHistoryOfWhoo", "The History Of Whoo", "后",],
    "雪花秀": ["Sulwhasoo", "雪花", "后雪", "雪花秀"],

    # 香水 / 轻奢香氛
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

    # 洗护 / 身体 / 生活类
    "卡诗": ["Kerastase", "Kérastase", "卡诗"],
    "欧舒丹": ["Loccitane", "L'Occitane", "欧舒", "欧舒丹"],
    "欧莱雅": ["Loreal", "L'Oréal", "欧莱", "欧莱雅"],
    "潘婷": ["Pantene", "潘婷"],
    "大卫杜夫": ["Davidoff", "大卫", "大卫杜夫"],
    "拉夫劳伦": ["RalphLauren", "Ralph Lauren", "拉夫", "拉夫劳伦"],
    "馥蕾诗": ["Fresh", "馥蕾", "馥蕾诗"],

    # 补充定制品牌
    "伟博": ["Webber", "伟博"],
    "慕拉得塑": ["Murad", "慕拉", "慕拉得"],
    "未来驱蚊": ["VAPE", "未來", "未来驅蚊"],
    "澳洲NatureBOBO": ["NatureBOBO", "Nature BOBO", "澳洲"],
    "旧街场": ["OldTown", "Old Town", "旧街场"],
    "费列罗": ["Ferrero", "费列", "费列罗"]
}
# ====================== 【检测函数】 ======================
def check_unmatched_brands(file_path):
    # 读取Excel
    df = pd.read_excel(file_path)

    # 必须包含的列
    required_cols = ["货品名称", "关键词", "序号"]
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ 表格缺少列：{col}")
            return

    # 把所有品牌别名展开成一个列表
    all_brand_keywords = []
    for names in brand_lib.values():
        all_brand_keywords.extend(names)

    # 统一转小写，避免大小写问题
    lower_brands = [b.lower() for b in all_brand_keywords]

    # 未匹配列表
    unmatched = []

    # 逐行检查
    for idx, row in df.iterrows():
        product_name = str(row["货品名称"]).lower()
        keyword = str(row["关键词"]).lower()
        serial = row["序号"]

        # 判断：品牌是否出现在 货品名称 或 关键词 中
        matched = False
        for b in lower_brands:
            if b in product_name or b in keyword:
                matched = True
                break

        if not matched:
            unmatched.append({
                "序号": serial,
                "货品名称": row["货品名称"],
                "关键词": row["关键词"],
                "未匹配原因": "未在品牌库中找到任何匹配"
            })

    # ====================== 输出结果 ======================
    print("\n" + "=" * 60)
    print(f"✅ 总共检查行数：{len(df)}")
    print(f"⚠️ 未匹配品牌条目数量：{len(unmatched)}")
    print("=" * 60)

    if unmatched:
        print("\n【未匹配品牌的条目清单】")
        for item in unmatched:
            print(f"序号 {item['序号']} | {item['货品名称']} | {item['关键词']}")

        # 导出未匹配条目为新Excel
        unmatched_df = pd.DataFrame(unmatched)
        unmatched_df.to_excel("未匹配品牌条目.xlsx", index=False)
        print("\n📁 已导出未匹配条目 → 未匹配品牌条目.xlsx")
    else:
        print("\n🎉 所有条目都匹配到品牌！无异常数据")

# ====================== 运行 ======================
if __name__ == "__main__":
    # 把你的Excel文件名改这里
    check_unmatched_brands("../搜索名单.xlsx")