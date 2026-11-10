from pyecharts.charts import Bar, Line, Pie, Page
import pandas as pd
from pyecharts import options as opts

df = pd.read_csv("E:\\PycharmProject\\18数据分析(考研数据)\\各院校历年数据采集.csv")

new_df = df[df['录取年份'] == 2026]

school_count = new_df.groupby('学校').size().sort_values(ascending=False).reset_index(name = '人数')

school_x = school_count['学校'].tolist()
school_y = school_count['人数'].tolist()
bar = Bar()
bar.add_xaxis(school_x)
bar.add_yaxis('招生人数',school_y,color_by='data')
bar.set_global_opts(title_opts=opts.TitleOpts(title='招生人数Top10'),xaxis_opts=opts.AxisOpts(axislabel_opts={"rotate":0}))
#横着的柱状图
bar.reversal_axis()

bar.render('招生人数Top10_Bar.html')

line = Line()
line.add_xaxis(school_x)
line.add_yaxis('招生人数',school_y,color_by='data')
line.set_global_opts(title_opts=opts.TitleOpts(title='招生人数Top10'),xaxis_opts=opts.AxisOpts(axislabel_opts={"rotate":30}))
line.render('招生人数Top10_Line.html')

pie_data = list(zip(school_x, school_y))
pie = Pie()
pie.add('招生人数Top10', pie_data)
pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{c} ({d}%)"))
pie.render('招生人数Top10_Pie.html')

mix_bar = Bar()
mix_bar.add_xaxis(school_x)
mix_bar.add_yaxis('招生数量', school_y, color_by='data')

mix_line = Line()
mix_line.add_xaxis(school_x)
mix_line.add_yaxis('招生数量', school_y, color_by='data')
mix_bar.set_global_opts(title_opts=opts.TitleOpts(title='招生人数Top10'),xaxis_opts=opts.AxisOpts(axislabel_opts={"rotate":30}))
mix_bar.overlap(mix_line)
mix_bar.render('招生人数Top10_Pro.html')

page = Page(layout=Page.SimplePageLayout)
page.add(bar, line, pie, mix_bar)
page.render('招生人数Top10_Pro_Max.html')