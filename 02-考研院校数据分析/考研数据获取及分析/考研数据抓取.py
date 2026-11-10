import requests, pandas

url = "https://api.kaoyan.cn/pc/school/schoolList"
headers = {
    "user-agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0',
    "referer":'https://www.kaoyan.cn/'
}
data = {
    "feature":"",
    "limit":20,
    "page":1,
    "province_id":"",
    "school_name":"",
    "type":""
}
response = requests.post(url,headers=headers,data=data)

resdata = response.json()
data_list = resdata['data']['data']
all_data = []
for i in data_list:
    name = i['school_name']
    id = i['school_id']
    for j in range(2023, 2027):
        score_url = "https://api.kaoyan.cn/pc/school/schoolScore"
        score_data = {
            "degree_type":"",
            "school_id":id,
            "year":j
        }
        score_res = requests.post(score_url, headers=headers, data=score_data)
        score_res_datas = score_res.json()
        for score in score_res_datas['data']:
            dat = {
                '学校':score['school_name'],
                '专业':score['name'],
                '代码':score['code'],
                '招生院系':score['depart_name'],
                '外语':score['english'],
                '政治':score['politics'],
                '专业课一':score['special_one'],
                '专业课二':score['special_two'],
                '总分':score['total'],
                '录取年份':score['year']
            }
            all_data.append(dat)
df = pandas.DataFrame(all_data)
df.to_csv('各院校历年数据采集.csv', index=False)