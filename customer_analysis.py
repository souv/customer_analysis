import pandas as pd  
import matplotlib.pyplot as plt # for plotting graphs
import seaborn as sns

#order_data to find top 10 customers
orderdata.user_id.value_counts()[:10].plot(kind='bar')

#filter the subset data 
chinese_data = orderdata[orderdata.sap_product_line=='中文線']

#see the big pic of the data
chinese_data.info()
chinese_data.describe() #for continuous vars

#for categorical var
type_counts = chinese_data['card_type'].value_counts()
df2 = pd.DataFrame({'card_type': type_counts}, 
                     index = ['white', 'black', 'gold']
                   )
df2.plot.pie(y='card_type', figsize=(10,10), autopct='%1.1f%%')


#filter data
chinese_data_over0 = chinese_data[(chinese_data['real_amount_value']>0)]

#time min and max
chinese_data_over0['main_order_date'].min(),chinese_data_over0['main_order_date'].max()

#datetime management
import datetime as dt
PRESENT = dt.datetime(2021,05,03)

#rfm analysis
rfm= orderdata.groupby('userid').agg({'main_order_date': lambda date: (PRESENT - date.max()).days,
                                      'main_order_id': lambda num: len(num),
                                      'real_amount_value': lambda price: price.sum()})

rfm.columns

# Change the name of columns
rfm.columns=['monetary','frequency','recency']

rfm['recency'] = rfm['recency'].astype(int)

#using qcut to get different segematation
rfm['r_quartile'] = pd.qcut(rfm['recency'], 4, ['1','2','3','4'])
rfm['f_quartile'] = pd.qcut(rfm['frequency'], 4, ['4','3','2','1'])
rfm['m_quartile'] = pd.qcut(rfm['monetary'], 4, ['4','3','2','1'])


rfm.head()

rfm['RFM_Score'] = rfm.r_quartile.astype(str)+ rfm.f_quartile.astype(str) + rfm.m_quartile.astype(str)
rfm.head()

# Filter out Top/Best cusotmers
rfm[rfm['RFM_Score']=='111'].sort_values('monetary', ascending=False).head()

#reference
https://www.datacamp.com/community/tutorials/introduction-customer-segmentation-python

