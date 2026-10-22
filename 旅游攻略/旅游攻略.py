import csv
import json
import requests
from pathlib import Path

# gao_de_API_KEY用于从高德获取地理信息
gao_de_API_KEY = "576ec063223d84ec0e434ed3d7f643ef"
# deepseek_API_KEY用于通过AI搜索分析某个景点的门票和攻略
siliconflow_API_KEY = "sk-rmowtxsqnozzmimshgbyszudpvfvzcnlbxbdecwnpswtpkts"
# 请求网址
search_url = "https://restapi.amap.com/v3/place/text"
siliconflow_url = "https://api.siliconflow.cn/v1/chat/completions"
# 1.获取景点的信息
def search_collect(keyword, city):
    # 携带参数拼接
    params = {
        # 带上 key请求高德接口获取地图数据
        'key': gao_de_API_KEY,
        # 传入想去的景点类型
        'keywords':keyword,
        # 传入想去的城市
        'city':city,
        # 限制搜索范围为输入的城市
        'citylimit':'true',
        # 每页返回前 8个景点
        'offset':'8',
        # 返回一页
        'page':'1'
    }
    # 发请求并转为字典
    res = requests.get(search_url, params=params).json()
    # print(res)
    # 先判断请求状态是否成功，成功则取键为 pois 的值，若键不存在则返回空列表，请求失败返回空列表。
    return res.get('pois', []) if res['status'] == '1' else []

def clean_collect(city, black_lst=None, popular_lst=None):
    # all_data 用于存储所有景点的信息
    all_data = []
    # seen = set() 创建一个空的集合，集合自带去重功能，用于存储已查询到的景点名称，避免重复查询
    seen = set()
    # black_lst 用于存储黑名单中的景点名称，避免查询到黑名单中的景点，默认为空列表
    black_lst = black_lst or []
    # popular_lst 用于存储热门景点类型，默认包含 ['古镇', '公园', '博物馆', '寺庙', '海洋馆', '文创园']
    popular_lst = popular_lst or ['古镇', '公园', '博物馆', '寺庙', '海洋馆', '文创园']
    # 遍历所有景点类型
    for popul in popular_lst:
        print(f'正在搜索{popul}的景点信息...')
        # 遍历所有景点信息
        # 调用 search_collect 函数获取景点信息
        for i in search_collect(popul, city):
            # 提取景点名称，如果没有则返回空字符串
            name = i.get('name', '')
            # 遍历 black_lst 中的每个 word，只要任意一个 word 出现在 name 中，结果就是 True，
            # 如果结果为 True，跳过该景点
            if any(word in name for word in black_lst):
                continue
            # 提取景点名称的前缀，用于判断是否重复查询
            clean_name = name.split('-')[0]
            # 过滤掉重复查询景点
            if clean_name in seen:
                continue
            # 将景点名称的前缀添加到集合中，用于判断是否重复查询
            # 这样可以避免重复查询相同的景点
            seen.add(clean_name)
            # 将景点信息添加到 all_data 中
            all_data.append({
                '景点':name,
                '类型':popul,
                '城市':city,
                '地址':i.get('address', ''),
                '区域': i.get('adname', ''),
                '电话':i.get('tel'),
                '经纬度':i.get('location', ''),
                '门票':'',
                '攻略':''})
        print(f'{popul}的景点信息已搜索完成\n')
    print(f'共查询到{len(all_data)}个景点信息\n')
    print(all_data)
    return all_data

def AI_collect(spots, city):
    # 批量大小，一次最多分析 5 个景点
    BATCH_SIZE = 5
    # info 用于存储所有景点的信息
    info = {}
    # 按 BATCH_SIZE 分批，避免小模型一次输出截断
    # for i in range(0, len(spots), BATCH_SIZE) 记录景点个数，每次取出 BATCH_SIZE 个景点
    # 取出景点的顺序按 spots[i:i + BATCH_SIZE] 随 i 递增
    batches = [spots[i:i + BATCH_SIZE] for i in range(0, len(spots), BATCH_SIZE)]
    # 记录 batches 的长度，即分批后的批次数量
    total = len(batches)
    print(f'[AI] 硅基流动(Qwen2.5-7B)正在分{total}批分析{len(spots)}个景点......')

    # 从 1 开始计数，取出每个批次的景点信息，共 total 批次
    for idx, batch in enumerate(batches, 1):
        # 从批次中提取景点名称
        names = [spot['景点'] for spot in batch]
        prompt = (
            f'你是穷游专家。给下面{city}的小众景点逐个补充信息：\n'
            # 把列表 names 转换为 JSON 字符串，ensure_ascii = False ，确保中文字符正常显示 ，True 则会将中文字符转换为 ASCII 码
            f'{json.dumps(names, ensure_ascii = False)}\n'
            '门票写参考价(如"免费"/"10元")。'
            '攻略写150-250字，包含：亮点值得看什么、门票和预约注意事项、什么时候人最少'
            '公交地铁怎么坐最省钱、附近便宜的美食。景点名照抄。\n'
            '只输出json，格式：{"结果":[{"景点":"...","门票":"...","攻略":"..."}]}'
        )
        print(f'  → 第{idx}/{total}批 ({len(batch)}个景点)...')
        try:
            # 发送请求
            # 调用 siliconflow_url 函数获取模型回复
            resp = requests.post(
                siliconflow_url,
                headers={"Authorization": f"Bearer {siliconflow_API_KEY}"},
                json={"model": "Qwen/Qwen2.5-7B-Instruct",
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=120
            )
            # 检查状态码是否为 200
            # 如果不是 200，打印警告并跳过该批次
            if resp.status_code != 200:
                print(f"    [警告] 第{idx}批请求失败，跳过。状态码: {resp.status_code}")
                continue
            # 解析 JSON 响应
            # 如果 choices 字段不存在，打印警告并跳过该批次
            data = resp.json()
            if "choices" not in data:
                print(f"    [警告] 第{idx}批返回格式异常，跳过。")
                continue
            # 提取模型回复的 JSON 字符串
            content = data["choices"][0]["message"]["content"]
            # 移除 JSON 字符串前后的 ```json 和 ``` 标签
            # 并去掉首尾的空格
            content = content.strip().removeprefix("```json").removesuffix("```").strip()
            # 将content转换为Python字典，提取结果字段
            # 并将结果字段转换为字典，键为景点名称，值为字典
            batch_info = {item['景点']: item for item in json.loads(content)['结果']}
            # 合并结果到 info 中
            info.update(batch_info)
            print(f"    ✓ 成功解析{len(batch_info)}个景点")
        except Exception as e:
            print(f"    [警告] 第{idx}批出错: {e}，跳过")

    # 合并结果到原始 spots
    for spot in spots:
        # 从 info 中获取该景点的额外信息
        extra = info.get(spot['景点'], {})
        # 更新原始景点的门票字段，没有则保持不变
        spot['门票'] = extra.get('门票', spot['门票'])
        # 更新原始景点的攻略字段，没有则保持不变
        spot['攻略'] = extra.get('攻略', spot['攻略'])
    # 计算成功获取的攻略数量，即攻略字段不为空的景点数量
    success = sum(1 for s in spots if s['攻略'])
    print(f'AI分析完成！成功获取{success}/{len(spots)}个景点的攻略')

if __name__ == '__main__':
    # 输入要查询的城市
    city = input('请输入要查询的城市').strip() or '北京'
    black_lst = [i for i in input("请输入你不想去的景点，用空格隔开：").split(' ')]
    popular_lst = [j for j in input("请输入你想去的景点类型，用空格隔开，例如：公园，文创馆，博物馆，海洋馆，动物园，游乐园：").split(' ')]
    # 输出文件路径
    OUTPUT_CSV = Path(f"{city}_景点.csv")  # 注意 city 此时才可用
    # 清理数据
    spots = clean_collect(city, black_lst, popular_lst)
    # 调用AI分析函数
    AI_collect(spots, city)
    # 保存数据到csv文件
    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    # 写入数据到csv文件
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        # 写入csv文件的表头
        writer = csv.DictWriter(f, fieldnames=spots[0].keys())
        # 写入表头
        writer.writeheader()
        # 写入数据
        writer.writerows(spots)
    print(f"[保存] {OUTPUT_CSV.name} (共{len(spots)}个景点)")