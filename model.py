import xgboost
import pandas as pd
import numpy as np
import pickle
from sklearn.metrics import accuracy_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlite3 import Cursor
import pymysql
import streamlit as st
class BotModel():
    '''
    Function: 社交机器人预测模型的训练、存储、载入、预测相关操作。
    '''
    
    def __init__(self):
        self.model = ""
        self.scaler = ""
        
    # 载入模型
    @st.cache_resource
    def load_model(self, scale_path="scale_online.pickle.dat",xgb_path="xgb_online.pickle.dat"):
        self.scaler = pickle.load(open(scale_path, "rb"))
        self.model = pickle.load(open(xgb_path, "rb"))
    
    # 存储模型
    def save_model(self, version='test'):
        pickle.dump(self.model, open("xgb_online"+version+".pickle.dat", "wb"))
        pickle.dump(self.scaler, open("scale_online"+version+".pickle.dat", "wb"))

    # 训练模型
    def train(self, model_data):
        # 归一化
        self.scaler = StandardScaler()
        columns = model_data.columns
        model_data = scaler.fit_transform(model_data)
        
        # 训练模型
        X_train, X_test, y_train, y_test = train_test_split(model_data, y, test_size=0.2, random_state=100)
        self.xgb = xgboost.XGBClassifier(learning_rate=0.1,n_estimators=200,max_depth=3,min_child_weight=0.7).fit(X_train, y_train)
        #learning_rate=0.1,n_estimators=1000,max_depth=5,min_child_weight=1,
        y_pred = xgb.predict(X_test)
        
        # 输出精度
        acc_xgb = accuracy_score(y_test, y_pred)*100
        recall_xgb = recall_score(y_test, y_pred)*100
        f1_xgb = f1_score(y_test, y_pred)*100
        precision_xgb = precision_score(y_test, y_pred)*100
        print(acc_xgb, recall_xgb, precision_xgb, f1_xgb)


    
    # 预测
    def predict(self, user_data):
        try:
            user_input  = user_data[['verified','urank','mbrank','statuses_count','follow_count','followers_count','gender', 'description','followers_follow','origin_rate','like_num','forward_num','comment_num','post_freq', 'post_location','statuses_follow', 'content_length','content_std', 'name_digit','name_length','richness', 'hashtag', 'at']]
            user_input = self.scaler.transform(user_input)
            user_data['bot'] = self.model.predict(user_input)
            user_data['bot_prob'] = self.model.predict(user_input,output_margin=True)
            #st.write('sssss')
            
            self.update(int(float(user_data['uid'].values[0])), user_data['bot_prob'].values[0], user_data['bot'].values[0])
            return user_data
        except Exception as e:
            return np.NAN
            
    # 生成模拟数据
    def generate_data(self):
        sample_data = [[7755053577, '希望明天是个大大晴天', 0, -1, 0, 0, 403, 38, 21, 1, 1,
        'https://tvax4.sinaimg.cn/crop.0.0.600.600.180/008sPpHjly8h1f6coqljdj30go0gojrw.jpg?KID=imgbed,tva&Expires=1672915944&ssig=3TskAkq3%2BK',
        0.5384615384615384, 10.333333333333334, 0, 10, 1.0, 0.2, 0.0,
        0.0, 2.0, 0, 79.7, 13.0080744155313, 303, 2.6, 0.0]]
        
        columns = ['uid', 'screen_name', 'verified', 'verified_type', 'urank', 'mbrank',
       'statuses_count', 'follow_count', 'followers_count', 'gender',
       'description', 'profile_image_url', 'followers_follow',
       'statuses_follow', 'name_digit', 'name_length', 'origin_rate',
       'like_num', 'forward_num', 'comment_num', 'post_freq', 'post_location',
       'content_length', 'content_std', 'richness', 'hashtag', 'at']
        
        return pd.DataFrame(sample_data, columns=columns)
    
    # 上传数据
    def update(self, uid, bot_score, bot):
        try:
            mysql = pymysql.connect(host=st.secrets["db_host"], port=st.secrets["port"], user=st.secrets["db_username"], passwd=st.secrets["db_password"], database="Bot_check")
            
            cursor = mysql.cursor()
            cursor.execute(f"INSERT INTO Bot (uid, bot_score, bot) VALUES ({uid}, {bot_score}, {bot})")
            res = cursor.fetchall()
            mysql.commit()
            
        except Exception as e:
            st.write(e)
            pass
