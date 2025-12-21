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
import pymysql

# st.set_page_config(
#     page_title="Bot Finder",
#     page_icon="🤖️",
#     initial_sidebar_state="collapsed",
# #     layout="wide",
# )

st.markdown('# <center> 🤖️ Bot Finder</center>', unsafe_allow_html=True)
st.markdown(' <center> 微博社交机器人探测器 🛸 </center>', unsafe_allow_html=True)

st.markdown("---")

st.markdown(
    """
    <div style="
        background-color:#fff3cd;
        padding:20px;
        border-radius:10px;
        border:1px solid #ffeeba;
        margin-bottom:20px;
    ">
    <h3>⚠️ 项目状态说明 | Project Status</h3>

    <b>本项目已暂停维护（No longer actively maintained）</b>。<br><br>

    这个项目在磕磕绊绊中维护了将近 <b>三年</b>。  
    非常感谢每一位使用、反馈和支持过它的朋友。<br><br>

    随着研究目标和应用场景的不断演进，
    当前版本在架构与功能层面已难以支撑我对该系统的预期。  
    因此，在数据接口受限与部署方式调整的背景下，
    原微博社交机器人识别系统已完成重构，并迁移至新项目：<br><br>

    👉 <b>pybotfinder</b><br>
    <a href="https://github.com/mengxiao2000/pybotfinder" target="_blank">
    https://github.com/mengxiao2000/pybotfinder
    </a><br><br>

    新项目在模型稳定性、特征工程和使用方式上均进行了系统性优化，
    更适合当前与未来的研究与实践需求。
    </div>
    """,
    unsafe_allow_html=True
)


####################
# 显示已经识别的机器人数量
####################

st.write("\n  ")
st.write("\n  ")
st.write("\n  ")
st.write("\n  ")

############
# 预测模型加载
############

bot_model = model.BotModel()  # 重命名为 bot_model，避免与 module 冲突
bot_model.load_model()

###########
# 信息输入
###########

col1_search, col2_search = st.columns(2)
col1_search.markdown('🔍微博用户查找选项：')
select = col2_search.radio(
    "",
    ('用户ID', '批量用户ID'), index=0, horizontal=True, label_visibility="collapsed")

if select == '用户ID':
    detect_user_id = st.text_input("请输入用户ID (例如:6374435213或https://weibo.com/u/6374435213 )：")
elif select == '批量用户ID':
    uploaded_file = st.file_uploader("请上传包含'uid'列的CSV文件：")
    if uploaded_file is not None:
        uid_df = pd.read_csv(uploaded_file)
        st.write('表格预览：')
        st.write(uid_df.head(100))
    else:
        st.warning('请上传包含用户ID的CSV文件！')
    cookie = st.text_input("请输入m.weibo.cn的cookie (可选)：", help="当访问过频繁时可能会出现数据采集失败，可尝试替换为自己的cookie。")

###########
# 识别结果
###########

# 显示信息
def show_info(user_data):
    info_col1, info_col2 = st.columns(2)

    try:
        # 显示头像
        res = requests.get(user_data['profile_image_url'].values[0])
        image = Image.open(requests.get(user_data['profile_image_url'].values[0], stream=True).raw)
        info_col1.image(image, caption='')
        # 显示昵称
        info_col2.metric("用户昵称", user_data['screen_name'].values[0])
    except:
        # info_col1.image("default_image.png", caption="用户头像")  # 使用默认图片
        info_col2.metric("用户ID", user_data['uid'].values[0])

    # 显示预测结果
    #st.write(user_data['bot_prob'])
    result_col1, result_col2 = st.columns(2)

    bot_label = 1 if user_data['bot_prob'].values[0] > 0 else 0

    result_col1.metric("是否是机器人", ['No', 'Yes'][bot_label])
    result_col2.metric("Bot Score", user_data['bot_prob'].values[0], help="模型输出的机器人分数，该分数分布在-10～10之间，大于0时模型将账号分类为机器人，小于0时模型将账号分类为人类。")

# 缓存识别结果
def check_account(uid, cookie="SCF=Aj5aK-M2tabhVQiDI9uEh6lBNQXKBAr3ZnahCEVfO73_1_8tczH9nqjvtX0xHIJninH0AUg6LYArK4guqlgfplc.; SUB=_2A25EGrP_DeRhGeBN7FYV8yvOyj-IHXVnVkk3rDV6PUJbktAbLRbykW1NRC0emn9OdTYEf5MXq2DO-USV6s2jtsdn; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5OmjT406FM.waPJ-C1Fwpp5JpX5KMhUgL.Foq0S0BXe0-EeKe2dJLoI0YLxKqL1KMLBK.LxKnLBo-LBoMLxKqL1KMLBK.LxKML1-BLBK2LxK-L12zLBKBLxK.L1KBLB.zLxKML1hzLB.et; SSOLoginState=1763623856; ALF=1766215856; MLOGIN=1; _T_WM=22387716469; XSRF-TOKEN=a36605; WEIBOCN_FROM=1110003030; mweibo_short_token=d0f27ec956; M_WEIBOCN_PARAMS=uicode%3D20000174"):
    try:
        user_data = crawl_info.crawl_info(str(int(uid)).strip(), cookie)
        st.write(user_data)
        pred_user_data = bot_model.predict(user_data)
        st.write(pred_user_data[['screen_name','bot_prob']])
        return pred_user_data
    except Exception as e:
        st.error(f"数据抓取或预测失败: {str(e)}", icon="🚨")
        return None
    
# 识别过程
if st.button('🚀识别'):
    if select == '用户ID':
        if detect_user_id.strip() == "":
            st.error('用户UID不能为空！', icon="🚨")
        else:
            
            try:
                if 'https://weibo.com/u/' in str(detect_user_id):
                    detect_user_id = str(detect_user_id).strip().strip('https://weibo.com/u/')
                pred_user_data = check_account(str(detect_user_id).strip())
                show_info(pred_user_data)
            except Exception as e:
                st.error(f"识别失败: {str(e)}", icon="🚨")
            
                
                    
    elif select == '批量用户ID':
        if uploaded_file is not None:
            if 'uid' in uid_df.columns:
                with st.spinner('正在执行 🚶 🚴 🛵 🚗 🏎️ 🚄 ...'):
                    my_bar = st.progress(0)
                    length = len(uid_df)
                    uid_df = uid_df.reset_index()
                    for idx, line in uid_df.iterrows():
                        try:
                            detect_user_id = str(line['uid'])
                            if 'https://weibo.com/u/' in detect_user_id:
                                detect_user_id = str(detect_user_id).strip().strip('https://weibo.com/u/')

                            
                            url = st.secrets["server_func"]
                            data = {"uid": detect_user_id, "cookie": cookie}
                            response = requests.post(url, json=data).json()
                            uid_df.loc[idx, 'bot'] = response['bot_label']
                            uid_df.loc[idx, 'bot_score'] = response['bot_prob']
                            time.sleep(3.5)
                            
                        except Exception as e:
                            uid_df.loc[idx, 'bot'] = np.NAN
                            uid_df.loc[idx, 'bot_score'] = np.NAN
                        my_bar.progress((idx + 1) / length)

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
    st.markdown('## 🏹 2025-01-26')
    st.markdown('1. 增强批量识别稳定性')
    st.markdown('2. Bug修复: 单账号识别时返回其他账号的结果')
    
    st.markdown('## 🍀 2024-10-31')
    st.markdown('1. Bug修复: 输入id和识别id不一致')
    st.markdown('2. 简化功能')
    
    st.markdown('## 🍀 2024-09-05')
    st.markdown('1. Bug修复: 依赖更新')
    
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
