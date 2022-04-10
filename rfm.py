import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime as dt
from helpers import eda
pd.set_option('display.expand_frame_repr', False)


transactions= eda.excel_file("transactions","Transactions",refresh=False)
cat_cols, num_cols, cat_but_car,typless_cols =eda.col_types(transactions)
na_col,null_high_col_name=eda.desc_statistics(transactions,num_cols,cat_cols,refresh=True)
transactions.dropna(inplace=True)
today_date = transactions["Transaction_Date"].max() +dt.timedelta(days=7)
unique_custom_df = transactions.groupby('Customer_Number').agg({'Transaction_Date': lambda x:(today_date - x.max()).days,
                                                                'Customer_Number': lambda x: x.count(),
                                                                'Total_Amount': lambda x: x.sum()}).rename(columns={'Transaction_Date': 'Recency',
                                                                                                                     'Customer_Number': 'Frequency',
                                                                                                                     'Total_Amount': 'Monetary'}).reset_index()
unique_custom_df=pd.merge(unique_custom_df,transactions.groupby('Customer_Number').agg({'Transaction_Date': lambda x: (today_date - x.min()).days}).rename(columns={'Transaction_Date':'First_Shopping_Day'}).reset_index(),on="Customer_Number")

unique_custom_df.sort_values(by="Frequency",ascending=False).head(10)
rfm_ = unique_custom_df.loc[unique_custom_df["Frequency"]<170].copy()


def rfm(dataframe,col_Recency,col_Frequency,col_Monetary):
    dataframe["Recency_Score"], bins_Recency = pd.qcut(dataframe[col_Recency], 5, labels=[5, 4, 3, 2, 1], retbins=True)
    dataframe["Frequency_Score"], bins_Frequency = pd.qcut(dataframe[col_Frequency], 5, labels=[1, 2, 3, 4, 5],retbins=True)
    dataframe["Monetary_Score"], bins_Monetary= pd.qcut(dataframe[col_Monetary], 5, labels=[1, 2, 3, 4, 5],retbins=True)
    dataframe["Recency_Score"] =dataframe["Recency_Score"].astype(int)*10
    dataframe["Frequency_Score"] = dataframe["Frequency_Score"].astype(int) * 1
    dataframe["Monetary_Score"] = dataframe["Monetary_Score"].astype(int) * 100
    return dataframe,bins_Recency, bins_Frequency,bins_Monetary
rfm_,bins_Recency, bins_Frequency,bins_Monetary=rfm(rfm_,"Recency","Frequency","Monetary")


def rfm_Score(dataframe, col_Recency_Score="Recency_Score", col_Frequency_Score='Frequency_Score', col_Monetary_Score="Monetary_Score", col_First_Shopping_Day="First_Shopping_Day", platin_Value=545, gold_Value=434, silver_Value=322):
    dataframe["Score"] = dataframe[col_Monetary_Score]+ dataframe[col_Frequency_Score] + dataframe[col_Recency_Score]
    dataframe["Segment"]=np.where(dataframe[col_First_Shopping_Day] <=60 , 'New_Customer',[ "Platin" if x > platin_Value else 'Gold'  if x>gold_Value else
                                                                                            'Silver' if x>silver_Value else 'Bronze'
                                                                                             for x in dataframe['Score']] )
    print((dataframe["Segment"].value_counts() / len(dataframe) *100).sort_values())
    dataframe["Segment"].value_counts().plot(kind='barh',color="navy")
    plt.yticks(rotation=60)
    return dataframe
rfm_=rfm_Score(rfm_)

def lift_calc(dataframe,col_Monetary, col_Frequency,col_Segment):
    new_df= pd.DataFrame()
    new_df["Sum_Monetary"]=dataframe[[col_Monetary,col_Segment]].groupby(col_Segment).agg(["sum"])
    new_df["Sum_Cust"]=dataframe[[col_Frequency,col_Segment]].groupby(col_Segment).agg(["count"])
    new_df["Monetary_Rate"] = new_df["Sum_Monetary"] / new_df["Sum_Monetary"].sum()
    new_df["Cust_Rate"] = new_df["Sum_Cust"] / new_df["Sum_Cust"].sum()
    new_df["Lift"] =  new_df["Monetary_Rate"] /new_df["Cust_Rate"]
    print(new_df.sort_values(by="Lift",ascending=False))
lift_calc(rfm_,"Monetary","Frequency","Segment")

def diff_df(dataframe_diff,dataframe,key_col):
    key_diff = set(dataframe_diff[key_col]).difference(dataframe[key_col])
    diff_df = dataframe_diff[dataframe_diff[key_col].isin(key_diff)]
    return diff_df
predict_df=diff_df(unique_custom_df,rfm_,"Customer_Number")


def predict_score_df(dataframe,dataframe_add,list,col,col_score,reverse=False):
    df=pd.concat([pd.DataFrame(list,columns=["Bins"]),pd.DataFrame(sorted(dataframe[col_score].unique(),reverse=reverse))],axis=1)
    for j in range(len(list)-1):
        for i in dataframe_add[col]:
            if (df["Bins"][j] <=i <df["Bins"][j+1]) or i>df["Bins"].max():
                dataframe_add[col_score]=df[0][j]
    return dataframe_add

predict_score_df(rfm_,predict_df,bins_Recency,"Recency","Recency_Score",reverse=True)
predict_score_df(rfm_,predict_df,bins_Frequency,"Frequency","Frequency_Score")
predict_score_df(rfm_,predict_df,bins_Monetary,"Monetary","Monetary_Score")
rfm_Score(predict_df)
