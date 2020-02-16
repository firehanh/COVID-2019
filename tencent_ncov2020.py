import time
import requests
import json
import pandas as pd
import os
import datetime
from pyecharts import options as opts
from pyecharts.charts import *
import pymysql

while True:
    time_now = time.strftime("%H:%M:%S", time.localtime())  # 刷新
    if time_now == "15:14:10":  # 此处设置每天定时的时间
        def getCon():
            '''获取操作数据库的curcor即游标，首先的建立连接，需要服务器地址，端口号，用户名，密码和数据库名'''
            conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456", db="sinan",
                                   charset="utf8")
            return conn


        def insertcrawler(date, province, city, new_confirm, new_heal, new_death, sum_confirm, sum_heal, sum_death):
            '''向数据库中patentinfo表插入书本信息，patentinfo为PatentInfo类对象，包含专利基本信息'''
            sql = "insert into ncov(date,province,city,new_confirm,new_heal,new_death,sum_confirm,sum_heal,sum_death) values(%s, %s, %s, %s, %s,%s,%s, %s, %s)"

            conn = getCon();
            if conn == None:
                return

            cursor = conn.cursor()
            cursor.execute(sql,
                           (date, province, city, new_confirm, new_heal, new_death, sum_confirm, sum_heal, sum_death))

            conn.commit()
            cursor.close()
            conn.close()


        cities1 = []
        cities2 = []
        cities3 = []

        def get_ncov_data() -> str:
            url = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5'
            data = requests.get(url).json()['data']

            return data


        def get_daily_data() -> list:
            all = json.loads(get_ncov_data())
            return all['chinaDayList']


        def flatten_ncov_data() -> list:
            all = json.loads(get_ncov_data())
            date = all['lastUpdateTime']

            # 第一层：国家
            zh = all['areaTree'][0]

            zh_ncov = {
                    '日期': date,
                    '省份': zh['name'],
                    '新增确认': zh['today']['confirm'],
                    '新增治愈': zh['today']['heal'],
                    '新增死亡': zh['today']['dead'],
                    '累计确认': zh['total']['confirm'],
                    '累计治愈': zh['total']['heal'],
                    '累计死亡': zh['total']['dead']
                }
            # print(zh_ncov)
            insertcrawler(zh_ncov['日期'], zh_ncov['省份'], 'null', zh_ncov['新增确认'], zh_ncov['新增治愈'], zh_ncov['新增死亡'], zh_ncov['累计确认'],
                          zh_ncov['累计治愈'], zh_ncov['累计死亡'])
            print(zh_ncov['日期'], zh_ncov['省份'], 'null', zh_ncov['新增确认'], zh_ncov['新增治愈'], zh_ncov['新增死亡'],zh_ncov['累计确认'],
                          zh_ncov['累计治愈'], zh_ncov['累计死亡'])
            china = all['areaTree'][0]['children']  # get China data
            for province in china:
                # 第二层：省
                chengshi_ncov = {
                    '日期': date,
                    '省份': province['name'],
                    '新增确认': province['today']['confirm'],
                    '新增治愈': province['today']['heal'],
                    '新增死亡': province['today']['dead'],
                    '累计确认': province['total']['confirm'],
                    '累计治愈': province['total']['heal'],
                    '累计死亡': province['total']['dead']
                }
                # print(chengshi_ncov)
                cities1.append(chengshi_ncov)
                province_ncov = province['children']
                # 第三层：市
                for city in province_ncov:
                    # 输出格式
                    city_ncov = {
                        '日期': date,
                        '省份': province['name'],
                        '市': city['name'],
                        '新增确认': str(city['today']['confirm']),
                        '新增治愈': city['today']['heal'],
                        '新增死亡': city['today']['dead'],
                        '累计确认': city['total']['confirm'],
                        '累计治愈': city['total']['heal'],
                        '累计死亡': city['total']['dead']
                    }

                    cities2.append(city_ncov)


        def export_excel():
            cities1.clear()
            cities2.clear()
            # cities3.clear()
            flatten_ncov_data()
            for city in cities1:
                print(city['日期'], city['省份'], city['新增确认'], city['新增治愈'], city['新增死亡'], city['累计确认'],
                              city['累计治愈'], city['累计死亡'])
                insertcrawler(city['日期'], city['省份'], 'null', city['新增确认'], city['新增治愈'], city['新增死亡'], city['累计确认'],
                              city['累计治愈'], city['累计死亡'])
            for city in cities2:
                print(city['日期'], city['省份'], city['市'], city['新增确认'], city['新增治愈'], city['新增死亡'], city['累计确认'],
                              city['累计治愈'], city['累计死亡'])
                insertcrawler(city['日期'], city['省份'], city['市'], city['新增确认'], city['新增治愈'], city['新增死亡'], city['累计确认'],
                              city['累计治愈'], city['累计死亡'])
            # df = pd.DataFrame(cities)

            # 导出Excel
            # path = os.path.dirname(os.path.abspath(__file__))
            # output_file = os.path.join(path, 'output.xlsx')

            # df.to_excel(output_file)


        def render_map_chart():
            cities.clear()
            flatten_ncov_data()
            df = pd.DataFrame(cities)

            # Render Map chart
            map_chart = Map()
            map_chart.add(
                "中国",  # map name
                [list(z) for z in zip(list(df["省份"]), list(df['累计确认']))],
                "china",
                is_map_symbol_show=False
            )

            map_chart.set_global_opts(
                title_opts=opts.TitleOpts(
                    title="nCoV疫情地图(" + str(datetime.date.today()) + ")"
                ),
                visualmap_opts=opts.VisualMapOpts(
                    max_=10000,
                    is_piecewise=True,
                    pieces=[
                        {"min": 1, "max": 9, "label": "10人以下", "color": "#FFE6BE"},
                        {"min": 10, "max": 99, "label": "10-99人", "color": "#FFB769"},
                        {"min": 100, "max": 499, "label": "100-499人", "color": "#FF8F66"},
                        {"min": 500, "max": 999, "label": "500-999人", "color": "#ED514E"},
                        {"min": 1000, "max": 10000, "label": "1000人以上", "color": "#CA0D11"}
                    ]))

            map_chart.render('ncov_map_chart_{}.html'.format(datetime.date.today()))


        def render_line_chart():
            daily_data = get_daily_data()
            df = pd.DataFrame(daily_data)

            line_chart = Line()
            line_chart.add_xaxis(list(df["date"]))
            line_chart.add_yaxis("确认", list(df["confirm"]))
            line_chart.add_yaxis("疑似", list(df["suspect"]))
            line_chart.set_global_opts(
                title_opts=opts.TitleOpts(title="nCoV确认病例与疑似病例曲线")
            )

            line_chart.render('ncov_line_chart-{}.html'.format(datetime.date.today()))


        if __name__ == "__main__":
            export_excel()
            # render_map_chart()
            # render_line_chart()
time.sleep(2)  # 因为以秒定时，所以暂停2秒，使之不会在1秒内执行多次