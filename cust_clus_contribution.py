#會員貢獻分析
#訂單下訂區間為20210315-20210415，共23506位客戶
#以RFM作為客戶的特徵，找出性別*年齡個客群的貢獻


import os
import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

###1.連線至Postgresql###
host = ""
dbname = ""
user = ""
password = ""

conn_string = "host={0} user={1} dbname={2} password={3}".format(host, user, dbname, password)
conn = psycopg2.connect(conn_string)
cursor = conn.cursor()
cursor.execute("select *,(case when mch_3 = '111' then mch_description_2 else sap_product_line end) as new_cate \
                  from ec2_order_item_detail_all a \
                  left join \
                 (select * from public.ec2_mch_category) b \
                  on a.mch = b.mch \
                  where Sales_Status = '銷貨' and Profit_Center = 'C001';")
                       
data = pd.DataFrame(cursor.fetchall())
column_names = [i[0] for i in cursor.description]
data.columns = column_names

#import member_data
cursor.execute("select  user_id,sex,card_level_ind,age,last_spend_date,\
               accumulate_money,accumulate_amount \
               from public.ec_member_account")
                       
mem_data = pd.DataFrame(cursor.fetchall())
column_names = [i[0] for i in cursor.description]
mem_data.columns = column_names


###2.filter data###
#filter date interval
data['main_order_day2'] = pd.to_datetime(data['main_order_day'], format='%Y-%m-%d')

data_0315 = data[(data.main_order_day2 >= '20210315') & (data.main_order_day2 <= '20210415')]

#filter out 贈品及運費
data_0315_2 =data_0315[~((data_0315['new_cate'] == '99_其他') | (data_0315['new_cate'] == '98_運費'))]

###3.計算會員RFM
from datetime import date
cur_time = date(2021, 4, 30)

rfmTable = data_0315_2.groupby('user_id').agg({'main_order_day': lambda x: (cur_time - x.max()).days, 
                                                 'main_order_id': lambda x: len(x.unique()), 
                                                 'real_item_amount': lambda x: x.sum()})

#會員平均訂單價
rfmTable['avg_money'] = rfmTable['real_item_amount'] / rfmTable['main_order_id']

rfmTable.rename(columns={'main_order_day': 'recency', 
                         'main_order_id': 'freq', 
                         'real_item_amount': 'money'}, inplace=True)

#test specific customer
outlier = rfmTable[rfmTable['freq'] == 15911]
outlier2 = data_0315_2[data_0315_2['user_id'] == 2039157]

#RFM分組串會員基本資料
rfmTable2 = rfmTable.merge(mem_data,
               how = 'left',
               left_on = 'user_id',
               right_on = 'user_id')

###4.RFM分組
rfmTable2.describe()

r_bins = [5,10,20,50]
rfmTable2['r_cate'] = pd.cut(rfmTable2['recency'],r_bins)
f_bins = [1,2,3,4,5,110]
rfmTable2['f_cate'] = pd.cut(rfmTable2['freq'],f_bins)
m_bins = [0,1000,2000,5000,100000]
rfmTable2['m_cate'] = pd.cut(rfmTable2['money'],m_bins)
ma_bins = [0,1000,2000,5000,100000]
rfmTable2['ma_cate'] = pd.cut(rfmTable2['avg_money'],ma_bins)
#age recode
def age_recode(age):
    if age <= 10 :
        return 1
    elif age > 10 and age <=20:
        return 2
    elif age > 20 and age <= 30:
        return 3
    elif age > 30 and age <= 40:
        return 4
    elif age > 40 and age <= 50:
        return 5
    elif age > 50:
        return 6
    
rfmTable2['age_cate'] = rfmTable2['age'].apply(age_recode)
    
    
###5.視覺化
sns.set_theme(style="darkgrid")
sns.countplot(x="r_cate", data=rfmTable2)
sns.countplot(x="f_cate", data=rfmTable2)
sns.countplot(x="m_cate", data=rfmTable2)
sns.countplot(x="ma_cate", data=rfmTable2)

g = sns.FacetGrid(rfmTable2,
              col = "sex",
              row = "m_cate",
              margin_titles=True)

g = g.map_dataframe(sns.barplot, # 資料顯示的模式
                    x= 'age_cate', # 小圖表X資料來源
                    y ='avg_money', # 小圖表Y資料來源
                    palette = sns.color_palette("muted")) #畫布色調.
 
g = g.set_axis_labels('sex','m_cate').add_legend()

#6.驗證發現
#(1.)40-50歲的男性花費能力優於女性
age_sex_groupby = rfmTable2.groupby(['age_cate','sex','m_cate']). \
agg({'age_cate':lambda x : len(x),'avg_money':lambda x : x.sum() / len(x)})

#(2.)以性別與年齡做客戶分群，哪群人的人均貢獻最好
age_sex_segment = rfmTable2.groupby(['age_cate','sex']). \
agg({'m_cate':lambda x : len(x),'avg_money':lambda x : x.sum() / len(x),'money' :lambda x : x.sum()})

#以平均貢獻來看                                    
sns.relplot(x="age_cate", 
            y="avg_money", 
            hue="sex", 
            size="m_cate",
            sizes=(40, 400), alpha=.5, 
            palette="muted",height=6, 
            data=age_sex_segment)

#以總貢獻來看
sns.relplot(x="age_cate", 
            y="money", 
            hue="sex", 
            size="m_cate",
            sizes=(40, 400), alpha=.5, 
            palette="muted",height=6, 
            data=age_sex_segment)
