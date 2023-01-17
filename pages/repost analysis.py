#####################
# 微博转发：社交机器人分析
# Author: Xiao Meng
# Email: mengxiaocntc@163.com
# Update: 2023-01-15
#####################

import sys 
sys.path.append("..") 

import streamlit as st
import model
import pandas as pd
import numpy as np
import login
from PIL import Image
import requests
import time
from RepostSpider import RepostSpider
import crawl_info
from streamlit_echarts import st_echarts
import streamlit.components.v1 as components

import json
from pyecharts import options as opts
from pyecharts.charts import Graph
from pyecharts.charts import Liquid
from pyecharts.charts import Bar,Grid,Page
from pyecharts.commons.utils import JsCode

from pyecharts import options as opts
from pyecharts.charts import WordCloud
from pyecharts.globals import SymbolType

import jieba
            
    
st.set_page_config(
    page_title="转发分析",
    page_icon="🤖️",
    #layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown('# <center> 🤖️ Bot Finder</center>', unsafe_allow_html=True)
st.markdown(' <center> 微博转发分析 🌍 </center>', unsafe_allow_html=True)
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
st.text_input('🔍请输入微博URL（例如 https://weibo.com/1861477054/Mn1tjc0bL ）：',key="weibo_url")
    
    
###########
# 识别结果
###########

if st.button('🚀分析'):

        if (st.session_state.weibo_url).strip() == "":
            st.error('用户昵称不能为空！', icon="🚨")
        else:
            #https://weibo.com/5303505085/Mk3Kizysq#repost
            mid = st.session_state.weibo_url.split('/')[-1].split('#')[0].strip()
            # 信息抓取
            cookie = ""   
            spider = RepostSpider(mid, cookie, print_progres=True, repost_dir='./reposts/', root_path='root_weibo.csv')
            spider.run()
            mid = spider.mid # 统一mid为62位
            
            # 批量识别
            print_info = st.empty()
            print_info.write("开始识别机器人...该过程可能会有些慢，请耐心等待(> <) ")
            uid_df = pd.read_csv(f'./reposts/{mid}.csv')
            uid_df = uid_df.reset_index()
            my_bar = st.progress(0)
            length = len(uid_df)
            
            for idx, line in uid_df.iterrows():
                print_info.write(f"正在识别{idx+1}/{len(uid_df)} 🎈")
                try:
                    user_data = crawl_info.crawl_info(str(int(line['uid'])).strip())
                    user_data = model.predict(user_data)
                    uid_df.loc[idx,'bot'] = user_data['bot'].values[0]
                    uid_df.loc[idx,'bot_score'] = user_data['bot_prob'].values[0]
                except Exception as e:
                    #st.write(e)
                    uid_df.loc[idx,'bot'] = np.NAN
                    uid_df.loc[idx,'bot_score'] = np.NAN
                my_bar.progress((idx+1)/length)
            print_info.write("机器人识别完毕🎉 ")
            
            #uid_csv = uid_df.to_csv(index=False).encode('utf-8')
            uid_df.to_csv(f'./reposts/{mid}.csv')

            # 结果可视化
            uid_df = pd.read_csv(f'./reposts/{mid}.csv')
            root_weibo = pd.read_csv('root_weibo.csv').query('mblogid == @mid')
            # 机器人比例
            bot_num = len(uid_df.query('bot == 1'))
            #st.write(bot_num)
            all_num =  len(uid_df)
            repo = str(root_weibo['reposts_count'].values[0])
            comm = str(root_weibo['comments_count'].values[0])
            atti = str(root_weibo['attitudes_count'].values[0])
            uid_df['bot'] = uid_df['bot'].fillna(0)
            
            col1, col2 = st.columns([1.5,1],gap='medium')
        
            with col1:
                st.markdown("**发布者**", unsafe_allow_html=True)
                st.markdown(root_weibo['screen_name'].values[0], unsafe_allow_html=True)
                st.markdown("**微博内容**", unsafe_allow_html=True)
                
                if len(root_weibo['text'].values[0]) >120:
                    show_content =root_weibo['text'].values[0][:120] + '... （内容过长已省略）'
                else:
                    show_content =root_weibo['text'].values[0]
                    
                st.markdown(show_content, unsafe_allow_html=True)
                st.markdown("转发数:"+repo+" 评论数:"+comm+" 点赞数:"+atti, unsafe_allow_html=True)
       
            with col2:
                st.markdown('**💧社交机器人比例**', unsafe_allow_html=True)
                w = (
                    Liquid(init_opts=opts.InitOpts(width='222px',height='222px'))
                    .add("lq", [bot_num/(all_num+1)], 
                         label_opts=opts.LabelOpts(font_size=36),
                         is_outline_show=False)
                    .render_embed()
                    #.set_global_opts(title_opts=opts.TitleOpts(title="Bot Ratio"))
                )

                components.html(w ,width=300, height=200)
            
            # 网络图
            uid_json = {}
            uid_json['nodes'] = [{'name':mid,
                                  'category':'Root',
                                  'value':999, 
                                  'text':root_weibo['text'].values[0],
                                  'user':root_weibo['screen_name'].values[0]
                                  }]
            uid_json['links'] = []
            categories = [{"name":'Bot'},{"name":'Human'},{"name":'Root'}]
            
            for idx, line in uid_df.iterrows():
                node_info = {}
                node_info['name'] = line['mblogid']
                node_info['category'] = ['Human','Bot'][int(line['bot'])]
                node_info['value'] = line['bot_score']
                node_info['text'] = str(line['text_raw']).split('//@')[0]
                node_info['user'] = str(line['username'])

                link_info = {}
                link_info['source'] = line['up_mid']
                link_info['target'] = line['mblogid']
                
                uid_json['nodes'].append(node_info)
                uid_json['links'].append(link_info)
            

            # 绘制转发网络
            
            js_code_str= '''
            function(params){
            return params.data.user + ': \n' + params.data.text;
            }
            '''
            white1, c1, white2, = st.columns([0.05, 1, 0.05])
            with c1:
                st.markdown("**🐟转发网络**", unsafe_allow_html=True)
                c = (
                    Graph(init_opts=opts.InitOpts(width='600px',height='500px',bg_color='#F8F8F8'))
                    .add(
                        "",
                        uid_json['nodes'],
                        uid_json['links'],
                        categories,
                        repulsion=50,
                        is_roam=True,
                        is_focusnode=True,
                        is_draggable=True,
                        linestyle_opts=opts.LineStyleOpts(curve=0.2),
                        label_opts=opts.LabelOpts(is_show=False),
                        tooltip_opts=opts.TooltipOpts(formatter=JsCode(js_code_str),border_width=1),
                    )
                    .set_global_opts(
                        legend_opts=opts.LegendOpts(orient="vertical", pos_left="2%", pos_top="10%"),
                        #title_opts=opts.TitleOpts(title="Reposting network"),

                    )
                    .render_embed()
                )
                components.html(c,width=600, height=500)

            # 词云图
            
            from pyecharts import options as opts
            from pyecharts.charts import WordCloud
            from pyecharts.globals import SymbolType
            
            bot = uid_df.query('bot == 1')
            human = uid_df.query('bot == 0')
            
            
            
            white1, wd1, white2, wd2, white3, = st.columns([0.05, 1, 0.2,1, 0.5,])
        
            with wd1:
                st.markdown("**🌧️机器人发布内容词云图**", unsafe_allow_html=True)
                wordcount = {}
                stopwords = [w.strip('\n') for w in open('hit-stopwords.txt','r').readlines()]
                for idx, line in bot.iterrows():
                    all_words = jieba.lcut(line['text_raw'].split('//@')[0])
                    for word in all_words:
                        if word not in stopwords:
                            wordcount[word] = wordcount.get(word, 0)+1
                words = sorted(wordcount.items(), key=lambda x: x[1], reverse=True)[:50]
                wc1 = (
                    WordCloud(init_opts=opts.InitOpts(width='300px',height='300px',bg_color='#F8F8F8'))
                    .add("", words, word_size_range=[10, 100], shape=SymbolType.DIAMOND)
                   # .set_global_opts(title_opts=opts.TitleOpts(title="机器人发布内容词云图"))
                    .render_embed()
                )
                
                components.html(wc1,width=300, height=300)
       
            with wd2:
                st.markdown("**☁️人类发布内容词云图**", unsafe_allow_html=True)
                wordcount = {}
                stopwords = [w.strip('\n') for w in open('hit-stopwords.txt','r').readlines()]
                for idx, line in human.iterrows():
                    all_words = jieba.lcut(line['text_raw'].split('//@')[0])
                    for word in all_words:
                        if word not in stopwords:
                            wordcount[word] = wordcount.get(word, 0)+1
                words = sorted(wordcount.items(), key=lambda x: x[1], reverse=True)[:50]
                wc2 = (
                    WordCloud(init_opts=opts.InitOpts(width='300px',height='300px',bg_color='#F8F8F8'))
                    .add("", words, word_size_range=[10, 100], shape=SymbolType.DIAMOND)
                   # .set_global_opts(title_opts=opts.TitleOpts(title="人类发布内容词云图"))
                    .render_embed()
                ) 

                components.html(wc2,width=300, height=300)
            


###########
# 其他信息
###########

