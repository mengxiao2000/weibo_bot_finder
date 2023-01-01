import streamlit as st
import crawl_info
import pandas as pd

st.set_page_config(
    page_title="微博机器人识别",
    page_icon="🤖️",
    layout="wide",
)

# 预测模型
import pickle
#import xgboost
# load model from file 模型加载
#random_forest = pickle.load(open("random_forest.pickle.dat", "rb"))
xgb_cls = pickle.load(open("xgb1222.pickle.dat", "rb"))
scaler = pickle.load(open("scale1222.pickle.dat", "rb"))

@st.cache
def predict_bot(user_data):
    user_input  = user_data[['verified','urank','mbrank','statuses_count','follow_count','followers_count','sunshine_credit_level','school','location','gender', 'created_year', 'description','birthday_date','followers_follow','origin_rate','like_num','forward_num','comment_num','post_freq', 'post_location','statuses_follow', 'content_length','content_std', 'name_digit','name_length','richness']]
    user_input = scaler.transform(user_input)
    user_data['bot'] = xgb_cls.predict(user_input)
    user_data['bot_prob'] = xgb_cls.predict(user_input,output_margin=True)

    return user_data



st.markdown('# <center> 🤖️ 微博机器人识别 </center>', unsafe_allow_html=True)
st.write("\n  ")
st.write("\n  ")
st.write("\n  ")
st.write("\n  ")

select = st.radio(
    "🔍微博用户查找选项：",
    ('昵称', '用户UID'),index=0, horizontal=True)

if select == '昵称':
    st.text_input('请输入准确的用户昵称 (例如:人民日报)',key="user_name",help='根据用户昵称查找的原理是根据昵称搜索用户，对搜索到的第一个用户进行识别。')
else:
    st.text_input("输入用户ID (例如:6374435213)", key="uid")

if st.button('🚀识别'): 
    if select == '昵称':
        if (st.session_state.user_name).strip() == "":
            st.error('用户昵称不能为空！', icon="🚨")
        uid = crawl_info.get_uid(st.session_state.user_name)
        #st.write(uid)
        if pd.notna(uid):
            user_data = crawl_info.crawl_info(str(uid))
            user_data = predict_bot(user_data)
        else:
            st.error('未查找到该用户，请检查昵称输入或使用用户UID进行查找！', icon="🚨")
    else:
        if (st.session_state.uid).strip() == "":
            st.error('用户ID不能为空！', icon="🚨")
        user_data = crawl_info.crawl_info((st.session_state.uid).strip())
    
        user_data = predict_bot(user_data)

    col1, col2, col3 = st.columns(3)
    col1.metric("用户昵称", user_data['screen_name'].values[0])
    col2.metric("是否是机器人", ['否','是'][user_data['bot'].values[0]])
    col3.metric("Bot Score", user_data['bot_prob'].values[0], help="模型输出的机器人分数，该分数分布在-10～10之间，大于0时模型将账号分类为机器人，小于0时模型将账号分类为人类。",)
    
    st.markdown('😭识别结果不满意？[点击评论](https://docs.qq.com/sheet/DYXJNRGZzWnlJdmJk)，提出建议，帮助我们改进！')
    
    

st.write("\n  ")
st.write("\n  ")
st.write("\n  ")
st.write("\n  ")
tab1, tab2, tab3 = st.tabs(["🌲背景", "📦模型介绍", "📒更新日志"])

with tab1:
    st.markdown(" **社交机器人**(social bot)是活跃在社交媒体中，由自动化算法操纵的能够模仿人类行为、自动生成内容并和人类账号产生互动的社交媒体账号。在国内舆论场中，社交机器人已经被发现操纵娱乐生态，干扰算法评价体系。社交机器人能够营造虚假人气，通过群体压力和网络传染，使复杂的社交媒体环境更加不确定。")
    
with tab2:
    st.markdown('该工具利用微博可公开获取的社交账号信息作为实验数据集，基于XGboost模型识别微博平台中的社交机器人。从新浪微博社交机器人商家处购买了不同智能水平的机器人账号共247个，再从亲友处、非广告的微博评论中以及具有代表性的公众人物、机构账号中人工筛选出人类账号共255个，利用爬虫采集这两类账号的公开数据，构建了账号原始数据集。然后，将获得的502个新浪微博账号数据进行数据预处理。参考以往文献在社交机器人识别方面使用的账号级别、内容级别等方面的特征，对每一个账号共抽取了25个特征，包括用户的性别、等级、是否认证、关注数、粉丝数、关注数和粉丝数之比、发布内容的原创率、发布频率等。选择随机森林、XGboost、决策树、支持向量机、Logistic回归、感知机、KNN和朴素贝叶斯作为二分类机器学习算法，构建社交机器人检测模型。为比较模型预测性能，采用5折交叉验证，XGBoost模型在测试集上预测性能最优，准确率为96.02%，F1值为95.89。')
    st.markdown('获取详情信息，请联系mengxiaocntc@163.com')
    
with tab3:
    
    st.markdown('## 🎈 2021-12-31')
    st.markdown('1. 将识别模型通过streamlit实现在线访问和部署。')
    st.markdown('2. 更新了网页的基本信息。')
    st.markdown('3. 添加昵称查找和UID查找两种查找方式。')
    st.markdown('4. 目前仍然存在因cookie过期而无法长期使用的问题。')
    



