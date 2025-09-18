import regex as re
import sys
from std.unicode import strlen
from std import __set__, scan_conditionally, json_encode
from std.parser.markdown import *


class WritingStyle:
    def __init__(self, min_avg_length=sys.maxsize, texts=[]):
        self.min_avg_length = min_avg_length
        self.texts = texts

    def min(self, style):
        if style.min_avg_length < self.min_avg_length:
            return style
        return self
    
    def update(self, style):
        self.min_avg_length = style.min_avg_length
        self.texts = style.texts
    
    def merge(self, text, window_size):
        if isinstance(text, list):
            new = WritingStyle.from_texts(text, window_size)
        else:
            new = text.scan_list(window_size)
        self.update(self.min(new))

    @classmethod
    def from_texts(cls, texts, window_size, min_avg=sys.maxsize):
        # Find the window with the minimum average length
        target_start = -1
        texts_striped = [re.sub(r'\s+', ' ', text) for text in texts]
        texts.clear()
        [*texts] = filter(lambda s : s, texts_striped)
        for i in range(len(texts) - window_size + 1):
            window_avg = sum(strlen(s) for s in texts[i:i + window_size]) / window_size
            if window_avg < min_avg:
                min_avg = window_avg
                target_start = i

        if target_start < 0:
            window_size = 0
        style = cls(
            min_avg,
            texts[target_start: target_start + window_size]
        )
        return style

    def toJson(self):
        return {
            'score': self.min_avg_length,
            'min_avg_length' : self.min_avg_length,
            'texts' : self.texts
        }

    def __str__(self):
        return json_encode(self.toJson(), indent=4)

@__set__(Markdown)
def scan_element(self, texts):
    texts.extend((text.strip() for text in re.split("\n+", str(self).strip())))

@__set__(MarkdownP, MarkdownSPAN, MarkdownText)
def scan_list(self, window_size):
    texts = []
    self.scan_element(texts)
    return WritingStyle.from_texts(texts, window_size)

@__set__(MarkdownH)
def scan_list(self, window_size):
    style = WritingStyle()
    for this in self.hanging:
        style.merge(this, window_size)
    return style

@__set__(MarkdownArgs)
def scan_list(self, window_size):
    texts = []
    style = WritingStyle()
    for i, this in enumerate(self.args):
        match this:
            case MarkdownUL() | MarkdownOL() | MarkdownH():
                style.merge(texts, window_size)
                style.merge(this, window_size)
            case MarkdownP() | MarkdownSPAN() | MarkdownText():
                this.scan_element(texts)
            case MarkdownLI():
                texts_separated = []
                def scan_list(l):
                    style.merge(l, window_size)
                    texts_separated.append([])

                def scan_array(l):
                    texts = []
                    for arg in l:
                        arg.scan_element(texts)
                    texts_separated.append(texts)

                scan_conditionally(
                    this.args, 
                    lambda arg : isinstance(arg, (MarkdownUL, MarkdownOL)),
                    scan_list,
                    scan_array
                )

                first, *texts_separated = texts_separated
                texts += first
                if texts_separated:
                    style.merge(texts, window_size)
                    for texts in texts_separated:
                        style.merge(texts, window_size)
            case MarkdownTABLE():
                ...
            case _:
                style = style.min(WritingStyle.from_texts(texts, window_size))
    style.merge(texts, window_size)
    return style

def min_length_of_paragraphs_in_sliding_window(text, window_size=5):
    """
    Find the sliding window of consecutive paragraphs with the minimum average length after processing.
    
    Processing steps include stripping whitespace, optionally excluding reference paragraphs, 
    and removing markdown-style markers ('-', '*'). Valid paragraphs are those remaining after processing.
    
    Args:
        text (str): Input text to analyze.
        window_size (int): Number of consecutive paragraphs to consider in each window.
        no_ref_only (bool): If True, exclude paragraphs containing reference markers like [1], [2], etc.
        min_avg (float): Initial minimum average value (defaults to maximum system value).
    
    Returns:
        dict: Contains 'min_avg_length' (minimum average length in bytes), 
              'start'/'stop' (indices in original text for the best window).
    """
    return MarkdownParser.instance.build(text).scan_list(window_size)


def test_table(id=None, Rank=None, offset=0):
    import json
    from std import MySQL
    kwargs = {
        'where' : 'json_length(answer) > 0',
        'dictionary' : True,
    }
    if id:
        kwargs |= {
            'id' : id,
        }
    else:
        kwargs |= {
            'training': 20,
            'offset' : offset,
            'limit' : 1500000,
            'fetch_size' : 1024,
        }
    for data in MySQL.instance.select('reward', **kwargs):
        id = data['id']
        offset += 1
        print('testing id =', id, 'offset =', offset)
        for i, answer in enumerate(json.loads(data['answer'])):
            try:
                if Rank is not None:
                    if i != Rank - 1:
                        continue
                if isinstance(answer, str):
                    answer = [answer]
                for answer in answer:
                    res = min_length_of_paragraphs_in_sliding_window(answer)
                    print(res)
            except Exception as e:
                print('Rank', i + 1)
                print(f"http://192.168.18.133:8000/label/query.php?id={id}")
                import traceback
                traceback.print_exc()
                print(e)
                return

def test():
    text = '''
**1. 耐磨性**

*   **技术参数：**
    *   **磨耗量（mm³）：** 通常在 100-300 mm³ 之间，越低越好。例如，某些纳米钛酸钠/钛酸钾晶须增强的制动材料，在相同条件下表现出更低的磨损率[57]。
    *   **磨耗指数：** 一些国家可能有特定的磨耗指数标准。例如，长春花壳粒度对无石棉刹车片磨损性能有影响，粒度越小，刹车片的磨损系数增加[48]。
    *   **耐磨等级：** 一些标准可能会将材料分为不同的耐磨等级，例如，超高分子量聚乙烯支腿垫板的耐磨性居塑料之冠，比尼龙66和聚四氟乙烯高4倍，比碳钢高6倍[53]。
    *   **测试方法：** 通常采用 Taber 磨耗试验、 DIN 53516、ISO 4649 等标准测试方法。例如，汽车座椅结构性能研究中，使用 YG065H 电子织物强力仪测试耐磨性能[58]。

*   **行业标准：**
    *   **中国：** GB/T 24135-2009 《橡胶脚垫》、GB 8624-2012 《建筑材料及制品燃烧性能分级》、GB 32085-2022 《乘用车内空气质量评价指南》等。汽车用真皮坐垫质量检测项目包括耐磨性[51]。
    *   **美国：** ASTM D3389 《地毯和垫料磨耗测试标准》、FMVSS 302 《汽车内饰材料燃烧特性》、CPSIA 《消费品安全改进法案》等。
    *   **欧洲：** EN ISO 12947 《纺织品抗磨损试验》、EN 455 《医用手套》、REACH 《化学品注册、评估、授权和限制》等。
    *   **日本：** JIS D 1201 《汽车内饰材料燃烧试验方法》、JIS K 6251 《橡胶磨耗试验方法》等。

*   **不同材料的优缺点：**
    *   **橡胶：** 耐磨性较好，弹性好，但易老化、易燃。橡胶脚垫是汽车脚垫的一种，其特点在于清洗方便，变形小，但是由于驾驶员长时间驾驶车辆，双脚后跟长时间接触脚垫，易导致脚垫部分位置会发生磨损甚至破洞[15]。
    *   **聚氯乙烯 (PVC)：** 耐磨性一般，易清洁，价格便宜，但易老化、易碎。PVC脚垫(或称塑料脚垫)的价格很便宜，但是其缺点也同样明显：味道重，会滑动，冬天容易变硬[25]。
    *   **聚氨酯 (PU)：** 耐磨性好，弹性好，耐老化，但价格较高。聚氨酯型汽车脚垫性能可以比橡胶型做得更好，而其成本比相同性能橡胶更低[4]。
    *   **热塑性弹性体 (TPE/TPU)：** 耐磨性好，弹性好，耐老化，环保，但价格较高。例如，一种镀层改性的防滑耐磨聚氨酯汽车脚垫，通过在溅射镀层二硫化钼的过程中掺入不规则的石英砂防滑填料，在聚氨酯脚垫基材表面形成镶嵌有防滑石英砂的二硫化钼耐磨层[7]。
    *   **纺织材料：** 耐磨性因材料而异，舒适性好，但易吸水、易脏。例如，全包围或者大包围结构的脚垫主体与木质垫脚板相结合，在与使用者脚底接触最为频繁的底片上设置木质垫脚板，大大增加了汽车脚垫的耐磨性[23]。

**2. 阻燃性**

*   **技术参数：**
    *   **极限氧指数 (LOI)：** 通常在 26-35 之间，越高越好。例如，纳米钛酸钠/钛酸钾晶须增强的制动材料，氧指数在 36.5LOI 左右[12]。
    *   **燃烧速度：** 通常以 mm/min 为单位，越低越好。
    *   **阻燃等级：** 通常分为 V-0、V-1、V-2、HB 等级，其中 V-0 最高。例如，一种无卤阻燃弹性体材料，包括按质量份数计的如下组分：苯乙烯类弹性体10～30份，白矿油5～15份，烯烃类弹性体5～25份，无卤阻燃母粒45～65份，功能助剂1～5份，达到UL94 5VA级无卤阻燃[19]。
    *   **测试方法：** 通常采用 UL 94、ISO 4589、GB/T 2408 等标准测试方法。

*   **行业标准：**
    *   **中国：** GB 8624-2012 《建筑材料及制品燃烧性能分级》、GB 20286-2006 《客车内饰材料阻燃性能要求》、GB 32085-2022 《乘用车内空气质量评价指南》等。
    *   **美国：** FMVSS 302 《汽车内饰材料燃烧特性》、ASTM E84 《建筑材料表面燃烧特性》、NFPA 101 《生命安全规范》等。
    *   **欧洲：** EN 455 《医用手套》、EN 13823 《建筑制品对火反应试验》、REACH 《化学品注册、评估、授权和限制》等。
    *   **日本：** JIS D 1201 《汽车内饰材料燃烧试验方法》、JIS K 7201 《塑料燃烧性能试验方法》等。

*   **不同材料的优缺点：**
    *   **橡胶：** 阻燃性较差，需要添加阻燃剂。例如，橡胶脚垫的味道较重[25]。
    *   **聚氯乙烯 (PVC)：** 阻燃性较好，但燃烧时会释放有毒气体。例如，PVC耐磨性差且非常不环保，易释放有毒气体[9]。
    *   **聚氨酯 (PU)：** 阻燃性较好，可以通过添加阻燃剂提高。例如，阻燃环保型汽车脚垫用TPU合成革的制造方法，包含以下步骤：1)基布的处理；2)压制改性TPU膜；3)压制初级合成革；4)表面处理及修饰[25]。
    *   **热塑性弹性体 (TPE/TPU)：** 阻燃性较好，可以通过添加阻燃剂提高。例如，一种无卤阻燃弹性体材料，包括按质量份数计的如下组分：苯乙烯类弹性体10～30份，白矿油5～15份，烯烃类弹性体5～25份，无卤阻燃母粒45～65份，功能助剂1～5份[19]。
    *   **纺织材料：** 阻燃性因材料而异，需要进行阻燃处理。例如，防水环保XPE席纹汽车脚垫，包括XPE汽车脚垫本体，XPE汽车脚垫本体的至少一侧表面上模压成型有沿其本体长度或宽度方向倾斜布置的席纹[38]。

**3. 防滑性**

*   **技术参数：**
    *   **摩擦系数：** 通常在 0.5-1.0 之间，越高越好。例如，汽车脚垫的防滑层与底层是通过针刺的方式连接在一起的，牢固性不够，影响脚垫的防滑性[17]。
    *   **防滑等级：** 一些标准可能会将材料分为不同的防滑等级。
    *   **测试方法：** 通常采用 DIN 51130、ISO 20344、GB/T 14799 等标准测试方法。

*   **行业标准：**
    *   **中国：** GB/T 14799-2008 《鞋类防滑性能测试方法》、GB 32085-2022 《乘用车内空气质量评价指南》等。
    *   **美国：** ASTM F1677 《运动场地面材料防滑性能》、ASTM D5118 《鞋类防滑性能》等。
    *   **欧洲：** EN ISO 20344 《个人防护装备鞋类》、EN 13893 《建筑地面防滑性能》等。
    *   **日本：** JIS T 8111 《鞋类防滑性能》、JIS K 6301 《塑料摩擦系数》等。

*   **不同材料的优缺点：**
    *   **橡胶：** 防滑性较好，但易老化。
    *   **聚氯乙烯 (PVC)：** 防滑性一般，需要进行防滑处理。例如，塑料汽车脚垫通常采用配料、高混、造粒以及注塑进行成型，而改性塑料行业因为原材料产地差异、生产过程中的压力、温度催化剂活性的变化等诸多因素会导致不同批次产品的相关物料物性参数会有一定差异和质量波动[30]。
    *   **聚氨酯 (PU)：** 防滑性较好，可以通过表面处理提高。
    *   **热塑性弹性体 (TPE/TPU)：** 防滑性较好，可以通过表面处理提高。例如，一种具有耐磨防滑结构的TPE汽车脚垫，包括脚垫本体，脚垫本体的底端设置有第二防滑机构，脚垫本体的顶端设置有收集机构[26]。
    *   **纺织材料：** 防滑性因材料而异，需要进行防滑处理。例如，一种防滑性能好的新型纤维汽车脚垫，包括纤维垫，纤维垫的一侧固定连接有前垫，纤维垫上端对称固定连接有侧板，两个侧板相向的侧壁上对称开设有活动槽[36]。

**总结：**

汽车脚垫材料的选择需要综合考虑耐磨性、阻燃性、防滑性以及其他因素（如舒适性、环保性、价格等）。不同材料各有优缺点，需要根据具体应用场景和需求进行选择。例如，丝圈脚垫的综合体验是最好的，旗舰级3M全包围汽车脚垫，采用3D压模工艺[21]。同时，需要遵守相关的行业标准，确保产品的安全性和可靠性。例如，汽车脚垫改性PVC专用料，以质量分数计含有PVC树脂：100份，DOTP：8～10份，DOP：28～32份，甲基丙烯酸异冰片酯：25～30份，表面改性的碳酸钙：20～25份[32]。
'''

    print(min_length_of_paragraphs_in_sliding_window(text))

if __name__ == '__main__':
    test()
    # test_table(
        # id=10877, 
        # Rank=2
    # )


