#####################
# 微博社交机器人在线识别
# Author: Xiao Meng
# Email: mengxiaocntc@163.com
# Update: 2023-03-05
#####################

import streamlit as st
import crawl_info
import model
import pandas as pd
import numpy as np
import login
from PIL import Image
import requests
import time
from sqlite3 import Cursor
import pymysql

# st.set_page_config(
#     page_title="Bot Finder",
#     page_icon="🤖️",
#     initial_sidebar_state="collapsed",
# #     layout="wide",
# )

st.markdown('# <center> 🤖️ Bot Finder</center>', unsafe_allow_html=True)
st.markdown(' <center> 微博社交机器人探测器 🛸 </center>', unsafe_allow_html=True)



####################
#显示已经识别的机器人数量
####################
def get_bot_num():
    try:
        mysql = pymysql.connect(host=st.secrets["db_host"], port=st.secrets["port"], user=st.secrets["db_username"], passwd=st.secrets["db_password"], database="Bot_check")

        cursor = mysql.cursor()
        cursor.execute(f"SELECT COUNT(*) AS nums FROM Bot WHERE bot=1")
        res = cursor.fetchall()
        mysql.commit()
        
        st.markdown(f' <center> 已经累计发现{res[0][0]}个疑似机器人账号 </center>', unsafe_allow_html=True)
    except Exception as e:
        st.write(e)
        pass
    
#get_bot_num()

st.write("\n  ")
st.write("\n  ")
st.write("\n  ")
st.write("\n  ")

############
# 预测模型加载
############

model = model.BotModel()
model.load_model()

###########
# 信息输入
###########

col1_search, col2_search = st.columns(2)
col1_search.markdown('🔍微博用户查找选项：')
select = col2_search.radio(
    "",
    ('昵称', '用户ID', '批量用户ID'),index=0, horizontal=True, label_visibility="collapsed")

if select == '昵称':
    st.text_input('请输入准确的用户昵称 (例如:微博小秘书)',key="user_name",help='根据用户昵称查找的原理是根据昵称搜索用户，对搜索到的第一个用户进行识别。')
elif select == '用户ID':
    st.text_input("请输入用户ID (例如:6374435213或https://weibo.com/u/6374435213 )：", key="uid")
elif select == '批量用户ID':
    uploaded_file = st.file_uploader("请上传包含'uid'列的CSV文件：")
    test_df = pd.read_csv('test_upload.csv').to_csv(index=False).encode("utf-8")
    st.download_button(
        label="下载示例文件",
        data=test_df,
        file_name='test_bot.csv',
        mime='text/csv',
    )
    
    if uploaded_file is not None:
        uid_df = pd.read_csv(uploaded_file)
        st.write('表格预览：')
        st.write(uid_df.head(100))
    
    
###########
# 识别结果
###########

# 显示信息
def show_info(user_data):
    info_col1, info_col2 = st.columns(2)
    
    try:
        # 显示头像
        res = requests.get(user_data['profile_image_url'].values[0])
        with open("profile_image.png","wb") as f:
            f.write(res.content)
        image = Image.open("profile_image.png")
        info_col1.image(image, caption='')
        # 显示昵称
        info_col2.metric("用户昵称", user_data['screen_name'].values[0])
        
    except:
        info_col1.markdown('获取用户信息失败，以下为根据用户内容的预测结果。')
        info_col2.metric("用户uid", user_data['uid'].values[0])
        pass
 
    
    # 显示预测结果
    result_col1, result_col2 = st.columns(2)
    print(user_data['bot'].values[0])
    bot_label = 1 if int(user_data['bot']) > 0.5 else 0
    result_col1.metric("是否是机器人", ['No', 'Yes'][bot_label])
    result_col2.metric("Bot Score", user_data['bot_prob'].values[0], help="模型输出的机器人分数，该分数分布在-10～10之间，大于0时模型将账号分类为机器人，小于0时模型将账号分类为人类。",)
    #st.markdown('😭识别结果不满意？[点击评论](https://docs.qq.com/sheet/DYXJNRGZzWnlJdmJk)，提出建议，帮助我们改进！')

# 缓存识别结果
def check_account(uid):
    user_data = crawl_info.crawl_info(str(int(uid)).strip())
    user_data = model.predict(user_data)
    return user_data
    
# 识别过程
if st.button('🚀识别'):
    if select == '昵称':
        if (st.session_state.user_name).strip() == "":
            st.error('用户昵称不能为空！', icon="🚨")
        else:
            uid = crawl_info.get_uid(st.session_state.user_name)
            #st.write(uid)
        
            if pd.notna(uid):
                user_data = check_account(str(uid))
                show_info(user_data)
            else:
                st.error('未查找到该用户，请检查昵称输入或使用用户UID进行查找！', icon="🚨")
        
    elif select == '用户ID':
        if (st.session_state.uid).strip() == "":
            st.error('用户UID不能为空！', icon="🚨")
        else:
            user_data = check_account((st.session_state.uid).strip())
            show_info(user_data)
    elif select == '批量用户ID':
        if uploaded_file is not None:
            if 'uid' in uid_df.columns: 
                with st.spinner('正在执行 🚶 🚴 🛵 🚗 🏎️ 🚄 ...'):
                    my_bar = st.progress(0)
                    length = len(uid_df)
                    uid_df = uid_df.reset_index()
                    for idx, line in uid_df.iterrows():
                        try:
                            
                            user_data = check_account(line['uid'])
                            
                            uid_df.loc[idx,'bot'] = user_data['bot'].values[0]
                            uid_df.loc[idx,'bot_score'] = user_data['bot_prob'].values[0]
                        except Exception as e:
                            #st.write(e)
                            uid_df.loc[idx,'bot'] = np.NAN
                            uid_df.loc[idx,'bot_score'] = np.NAN
                        my_bar.progress((idx+1)/length)
                        #time.sleep(0.5)

                    uid_csv = uid_df.to_csv(index=False).encode('utf-8') 
                    st.write('识别完毕！')
                    st.download_button(
                        label="⏬ Download data as CSV",
                        data=uid_csv,
                        file_name='result_bot.csv',
                        mime='text/csv',
                    )
            else: 
                st.error('检测到CSV表格不包含‘uid’列，请重新上传！', icon="🚨")
            
                
        else:
            st.error('请上传用户ID的CSV表格！', icon="🚨")

            
            
###########
# 其他信息
###########
st.write("\n  ")
st.write("\n  ")
st.write("\n  ")
st.write("\n  ")
tab1, tab2, tab3 = st.tabs(["🌲背景", "📦模型简介", "📒更新日志"])

with tab1:
    st.markdown(" **社交机器人**(social bot)是活跃在社交媒体中，由自动化算法操纵的能够模仿人类行为、自动生成内容并和人类账号产生互动的社交媒体账号。")
    
with tab2:
    st.markdown('该工具通过提取微博可公开获取的社交账号信息，基于XGboost模型识别微博平台中的社交机器人，当前模型性能（准确率：94.12%，召回率：94.34%）。')
    
    st.markdown('注：模型预测结果仅表明该账号是否有类似社交机器人的行为，预测结果仅供参考。受限制于训练数据，在不同数据中表现可能会存在差异，建议配合人工验证使用。该工具仅供学术交流使用，请勿用于商业目的。')
    st.markdown('获取详情信息，请联系mengxiaocntc@163.com')
    
with tab3:
    st.markdown('## 🍀 2024-09-05')
    st.markdown('1. Bug修复')
    
    st.markdown('## 🍀 2023-03-05')
    st.markdown('1. 针对用户信息抓取失败导致信息不全下的报错问题进行调整。')
    st.markdown('2. 将预测结果保存到云数据库。')
    
    st.markdown('## 🐱 2023-03-04')
    st.markdown('1. 完善了批量识别的页面。')
    
    st.markdown('## 🌃 2023-01-15')
    st.markdown('1. 新增了转发分析功能。')
    
    st.markdown('## 🏠 2023-01-06')
    st.markdown('1. 优化了代码和运行速度。')
    
    st.markdown('## ❤️ 2023-01-05')
    st.markdown('1. 增加了批量识别功能。')
    
    st.markdown('## 🥱 2023-01-04')
    st.markdown('1. 更新模型，在训练数据中增加了微博话题机器人。')
    
    st.markdown('## 🔥 2023-01-03')
    st.markdown('1. 删除了登陆功能。')
    st.markdown('2. 简化了模型所需输入。')
    
    st.markdown('## ⚽️ 2023-01-02')
    st.markdown('1. 增加了登陆功能从而获取cookie。')
    
    st.markdown('## 🎈 2022-12-31')
    st.markdown('1. 将识别模型通过streamlit实现在线访问和部署。')
    st.markdown('2. 更新了网页的基本信息。')
    st.markdown('3. 添加昵称查找和UID查找两种查找方式。')
    st.markdown('4. 目前仍然存在因cookie过期而无法长期使用的问题。')
    




