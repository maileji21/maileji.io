from 数据分析服务 import ai_fenxi_and_report
import pandas as pd

df = pd.read_csv('各院校历年数据采集.csv')
school = df.groupby('学校')

put = input('请输入想查看的学校：')
major = school.get_group(put)['专业'].tolist()

for i in major:
    print(i)

maj_put = input('请输入想查看的专业：')

stu_data = school.get_group(put)
maj_data = stu_data[stu_data['专业'] == maj_put]

aver_score = maj_data['总分'].mean()
print(f'{put}的{maj_put}历年平均分数线：{aver_score:.1f}分')

ideal_score = input('请输入您的预估分数：')

result = ai_fenxi_and_report(put, maj_put, ideal_score)