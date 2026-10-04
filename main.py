import random
from itertools import chain

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Node, Plain, Image
from astrbot.core.message.components import Nodes

# Rider-Waite deck: card name -> (upright meaning, reversed meaning)
# Meanings cross-checked against Biddy Tarot, chatarot.ai and Deckaura keyword tables
RIDER_WAITE_CARDS = {
    # Major Arcana
    "愚者": ("新开始、冒险、自由、无限可能", "鲁莽冒失、优柔寡断、停滞不前"),
    "魔术师": ("创造力、行动力、潜能显化", "欺骗操纵、潜能未开发、优柔寡断"),
    "女祭司": ("直觉、神秘、内在智慧", "忽视直觉、秘密泄露、迷惘困惑"),
    "女皇": ("丰饶、滋养、收获", "创造力受阻、过度依赖、疏于自我照顾"),
    "皇帝": ("权威、稳定、掌控力", "专横、固执、失控"),
    "教皇": ("传统、精神指引、道德规范", "反叛传统、挑战权威、不合常规"),
    "恋人": ("契合、选择、价值观一致", "失衡、价值观冲突、错误的抉择"),
    "战车": ("胜利、前进、坚定意志", "方向不明、失控、内心冲突"),
    "力量": ("勇气、柔中带刚、内在力量", "自我怀疑、信心不足、情绪失控"),
    "隐士": ("内省、指引、寻求真理", "孤立、逃避、迷惘"),
    "命运之轮": ("转机、命运眷顾、周期变化", "厄运、时运不济、抗拒变化"),
    "正义": ("公正、平衡、因果报应", "不公、逃避责任、失衡"),
    "倒吊人": ("换位思考、等待、牺牲换来成长", "无谓牺牲、停滞、抗拒"),
    "死神": ("结束与新生、彻底转变", "抗拒改变、停滞、难以放手"),
    "节制": ("调和、耐心、恰到好处", "失衡、急躁、过犹不及"),
    "恶魔": ("束缚、诱惑、沉迷", "挣脱束缚、觉醒、斩断依赖"),
    "高塔": ("剧变、崩塌、意外打击", "勉强维持、逃避危机、延迟的崩坏"),
    "星星": ("希望、灵感、愿景", "失望、信心不足、梦想破灭"),
    "月亮": ("迷雾、不安、幻象", "拨云见日、真相浮现"),
    "太阳": ("喜悦、成功、光明前景", "阴霾、暂时的挫折"),
    "审判": ("觉醒、重生、重大决定", "自我怀疑、无视内心召唤、苛责自己"),
    "世界": ("圆满、达成、完美收官", "功亏一篑、尚未完成"),
    # Wands
    "权杖王牌": ("创造、行动、新机遇", "延宕、缺乏方向"),
    "权杖二": ("规划、抉择、远见", "犹豫、畏惧未知"),
    "权杖三": ("扩张、展望、合作", "受阻、缺乏远见"),
    "权杖四": ("稳定、庆祝、和谐", "过渡期、根基不稳"),
    "权杖五": ("竞争、碰撞、多元冲突", "回避冲突、内耗"),
    "权杖六": ("胜利、认可、自信", "失利、失去认可"),
    "权杖七": ("坚守、防御、立场坚定", "退让、力不从心"),
    "权杖八": ("迅速、进展、利好消息", "延迟、受阻"),
    "权杖九": ("警觉、坚韧、经验加持", "疲惫、防备过度"),
    "权杖十": ("重负、责任、坚持到底", "放下重担、不堪重负"),
    "权杖侍从": ("热情、探索、好奇心", "急躁浮躁、缺乏方向、三分钟热度"),
    "权杖骑士": ("冲劲、冒险、行动力强", "冲动莽撞、精力分散、急于求成"),
    "权杖王后": ("自信、魅力、活力四射", "善妒、自我中心、缺乏自信"),
    "权杖国王": ("领导力、远见、魄力", "独断、傲慢"),
    # Cups
    "圣杯王牌": ("情感、爱意、新开始", "压抑情感、内心空虚"),
    "圣杯二": ("吸引、伙伴、相互理解", "失衡、误解"),
    "圣杯三": ("友谊、庆祝、社群", "八卦、疏远"),
    "圣杯四": ("沉思、倦怠、错过的机会", "觉醒、重新振作"),
    "圣杯五": ("失落、悲伤、遗憾", "接纳、走出低谷"),
    "圣杯六": ("回忆、纯真、怀旧", "沉溺过去、停滞"),
    "圣杯七": ("幻想、多选、迷惑", "认清现实、下定决心"),
    "圣杯八": ("追寻、离开、内在探索", "徘徊、逃避"),
    "圣杯九": ("满足、愿望达成", "自满、虚假的快乐"),
    "圣杯十": ("圆满、幸福、家庭和睦", "分歧、不和谐"),
    "圣杯侍从": ("浪漫、灵感、直觉敏锐", "情绪化、不成熟"),
    "圣杯骑士": ("浪漫、邀约、魅力", "不切实际、善变"),
    "圣杯王后": ("共情、温柔、直觉", "情绪泛滥、过度依赖"),
    "圣杯国王": ("情感成熟、包容、平衡", "压抑情绪、情感操控"),
    # Swords
    "宝剑王牌": ("清晰、真相、突破", "混乱、误判"),
    "宝剑二": ("僵局、抉择、回避", "犹豫不决、迷惑、僵持不下"),
    "宝剑三": ("心碎、伤痛、真相刺痛", "疗愈、释怀、走出伤痛"),
    "宝剑四": ("休息、恢复、静养", "焦虑不安、倦怠未愈、无法静心休息"),
    "宝剑五": ("冲突、胜之不武", "和解、放下争执"),
    "宝剑六": ("过渡、远离纷争", "滞留、旧事重提"),
    "宝剑七": ("机敏、策略、暗中行事", "坦白、自食其果"),
    "宝剑八": ("束缚、自我设限", "挣脱枷锁、自我解放"),
    "宝剑九": ("焦虑、忧思、夜不能寐", "释怀、情况好转"),
    "宝剑十": ("终结、谷底、彻底结束", "恢复、触底反弹"),
    "宝剑侍从": ("机警、学习、观察", "多疑、言辞轻率"),
    "宝剑骑士": ("果决、激进、直言不讳", "鲁莽、好斗"),
    "宝剑王后": ("理性、洞察、独立", "冷酷、尖刻"),
    "宝剑国王": ("权威、理智、公正", "专横、冷酷无情"),
    # Pentacles
    "星币王牌": ("机遇、财富的种子、实际开端", "错失机会、财务不稳"),
    "星币二": ("平衡、灵活、多方统筹", "失衡、顾此失彼"),
    "星币三": ("协作、技艺、可见的成果", "敷衍、协作不畅"),
    "星币四": ("守成、稳固、掌控资源", "贪婪吝啬、物质主义、缺乏安全感"),
    "星币五": ("匮乏、困境、被忽视", "转机出现、互助"),
    "星币六": ("给予、分享、恩惠", "分配不均、有条件的交换"),
    "星币七": ("耐心、评估、长期投入", "急躁、回报延迟"),
    "星币八": ("勤奋、专注、精进", "完美主义、注意力分散、缺乏热忱"),
    "星币九": ("富足、自律、独立", "依赖、挥霍"),
    "星币十": ("稳固、传承、财富积累", "短期行为、财务吃紧"),
    "星币侍从": ("学习、踏实、新目标", "分心、不切实际"),
    "星币骑士": ("稳重、可靠、坚持不懈", "迟缓、固执"),
    "星币王后": ("务实、滋养、安全感", "操劳、缺乏安全感"),
    "星币国王": ("富足、成功、稳健经营", "贪婪固执、物质主义、因循守旧"),
}

# Spreads used for the gacha luck reading
SPREAD_ONE = "单张牌"
SPREAD_NO_POSITION = "无牌阵三张"  # three cards without positional meanings


# 插件指令
GACHA_LUCK = "抽卡运势"

@register("tarot_lite", "YourName", "一个简单的塔罗牌插件", "1.0.0")
class TarotLite(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""


    @filter.command(GACHA_LUCK)
    async def gacha_luck(self, event: AstrMessageEvent):
        """抽一张或三张韦特塔罗牌（三张为无牌阵），测试当前抽卡运势并由大模型解读"""
        user_name = event.get_sender_name()

        # Randomly draw 1 or 3 cards, each with a random upright/reversed orientation
        card_num = random.choice([1, 3])
        spread = SPREAD_ONE if card_num == 1 else SPREAD_NO_POSITION
        card_names = random.sample(list(RIDER_WAITE_CARDS.keys()), card_num)

        drawn = []
        result_text = f"{user_name}，正在洗牌……\n"
        yield event.plain_result(result_text)
        result_text = f"{user_name}，本次抽牌结果如下：\n"
        #result_text = f"{user_name}，正在为你洗牌…本次采用「{spread}」，抽取 {card_num} 张塔罗牌\n"
        for i, name in enumerate(card_names):
            is_upright = random.random() < 0.5
            up, down = RIDER_WAITE_CARDS[name]
            drawn.append((name, is_upright, up if is_upright else down))
            result_text += f"第{i + 1}张「{name}{'正位' if is_upright else '逆位'}」：{up if is_upright else down}\n"

        # Build the prompt and ask the LLM for a gacha luck interpretation
        cards_desc = "\n".join(
            f"第{i + 1}张「{name}{'正位' if is_upright else '逆位'}」，牌意：{meaning}"
            for i, (name, is_upright, meaning) in enumerate(drawn)
        )
        prompt = (
            f"用户「{user_name}」想测试当前的抽卡运势（游戏抽卡）。"
            f"使用{spread}抽取了{card_num}张韦特塔罗牌：\n{cards_desc}\n\n"
            "请作为专业的塔罗牌占卜师，结合牌面（含正逆位牌意）解读用户当前的抽卡运势："
            "首先一句话给出结论，再进行运势评级（如 用★表示，满分五星）以及简洁的运势分析，"
            "并可附上一条抽卡建议，如推荐抽取的时机、地点或幸运元素（若牌面有暗示）。回答约150-250字。不需要用md文档的表述"
        )
        interpretation = ""
        try:
            provider = self.context.get_using_provider()
            if provider is None:
                interpretation = "未配置大语言模型，无法进行 AI 解读，请先在管理面板中启用 LLM 提供商。"
            else:
                llm_response = await provider.text_chat(
                    prompt=prompt,
                    session_id=None,
                    contexts=[],
                    image_urls=[],
                    system_prompt="你是一位专业的塔罗牌占卜师，擅长根据牌面解读抽卡运势，回答简洁。",
                )
                interpretation = llm_response.completion_text.strip()
        except Exception as e:
            logger.error(f"生成抽卡运势 AI 解读失败: {e}")
            interpretation = "抱歉，AI 解读生成失败，请稍后再试。"

        chain = Nodes([])
        node = Node(
            uin=1037016070,
            name="占卜师",
            content=[Plain(result_text), ],
        )
        chain.nodes.append(node)
        ai_node = Node(
            uin=1037016070,
            name="占卜师",
            content=[Plain(f"{interpretation}"), ],
        )
        chain.nodes.append(ai_node)


        yield event.chain_result([chain])
        #yield event.plain_result(f"属于你的抽卡运势分析如下：\n{interpretation}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
