from DrissionPage import ChromiumPage
import os,time,csv
#创建目录
if not os.path.exists('小红书数据'):
    os.makedirs('小红书数据')
else:
    pass
filename = input("请输入你要保存的文件名：")
#搜索内容
keyword = input("请输入你要搜索的内容：")
#创建浏览器
page = ChromiumPage()
#监听网页(这里监听的只是搜索的内容的变化，不是监听整个小红书的变化，注意请求方式)
page.listen.start("https://so.xiaohongshu.com/api/sns/web/v2/search/notes",method="POST")
#打开搜索的网页
page.get(f"https://www.xiaohongshu.com/search_result_ai?keyword={keyword}&source=web_explore_feed")
time.sleep(5)
#创建空列表以便后续保存数据
all_data = []
#循环滚动翻页
for i in range(5):
    print(f'滚动的第{i+1}次！')
    page.scroll.to_bottom()
    time.sleep(2)
    #接收监听结果(翻页，页面新增内容，接收新增的内容)
    res = page.listen.wait()
    #转获取监听的内容的格式，以便提取所需数据
    result = res.response.body
    #'items'有想要的数据，就进入'items'里
    items = result['data']['items']
    #循环找一条笔记的所需的各个数据
    for item in items:
        #有些标签不存在数据，通过try丢弃该条数据防止程序中断
        try:
            #各种标签数据
            note_card = item["note_card"]
            id = item['id']
            token = item['xsec_token']
            title = note_card['display_title']
            username = item['note_card']['user']['nickname']
            avatar = item['note_card']['user']['avatar']

            comment_count = item['note_card']['interact_info']['comment_count']
            shared_count = item['note_card']['interact_info']['shared_count']
            liked_count = item['note_card']['interact_info']['liked_count']
            collected_count = item['note_card']['interact_info']['collected_count']
            #在上面的空列表中追加获取到的数据
            all_data.append([id, token, title, username, avatar, comment_count, shared_count, liked_count, collected_count])
        except Exception as e:
            print(f'程序报错了，错误内容是：{e}')
#保存获取的数据  newline=''-->换行
with open(f'小红书数据/{filename}.csv', 'w', encoding='utf-8', newline='') as f:
    cf = csv.writer(f)
    #先写一行(每一列的标题)
    cf.writerow(['id','token','title','username','avatar','comment_count','shared_count','like_count','collected_count'])
    #保存获取的数据
    cf.writerows(all_data)


