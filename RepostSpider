import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
import os
import re
import streamlit as st

class RepostSpider():
    # 初始化
    def __init__(self, mid, cookie, print_progres=True, root_path = 'root_weibo.csv', repost_dir='./reposts/' ):
        self.mid = mid
        self.cookie = cookie
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "cookie":self.cookie
        }
        
        self.print_progress = print_progres # 是否打印过程
        
        self.max_page = 1000
        
        self.user_info = pd.DataFrame() # 用户信息
        self.weibo_info = pd.DataFrame() # 微博信息
        self.repost_df = pd.DataFrame() # 转发数据
        
        self.path = root_path # 根微博信息
        self.repost_dir = repost_dir # 转发微博文件夹
        
    # 获取长推文内容
    def get_long_weibo(self, mid):
        try:
            long_text = requests.get(f'https://m.weibo.cn/statuses/extend?id={mid}').json()['data']['longTextContent']
            return long_text
        except Exception as e:
            return np.NAN
    
    # 获取微博信息
    def get_weibo_info(self):
        res = requests.get(f'https://m.weibo.cn/statuses/show?id={self.mid}').json()
        if res['ok'] == 1:
            # 微博内容信息
            mblogid = self.mid
            created_at = res['data']['created_at']
            mid = res['data']['mid']
            text = res['data']['text']
            reposts_count = res['data']['reposts_count']
            comments_count = res['data']['comments_count']
            attitudes_count = res['data']['attitudes_count']
            islongtext = res['data']['isLongText']
            pic_num = res['data']['pic_num']
            
            # 用户信息
            uid = res['data']['user']['id']
            screen_name = res['data']['user']['screen_name']
            gender = res['data']['user']['gender']

            verified_type = res['data']['user']['verified_type']
            verified = res['data']['user']['verified']
            #verified_reason = res['data']['user']['verified_reason']

            follow_count = res['data']['user']['follow_count']
            followers_count = res['data']['user']['followers_count']
            
            if islongtext:
                long_text = self.get_long_weibo(self.mid)
                if pd.notna(long_text):
                    text = long_text

            self.weibo_info = pd.DataFrame([[mblogid, created_at, mid, text, reposts_count, comments_count, attitudes_count, 
                           pic_num, uid, screen_name, gender, verified,  verified_type,
                          follow_count, followers_count]], columns=
                        ["mblogid","created_at", "mid", "text", "reposts_count", "comments_count", "attitudes_count", 
                           "pic_num", "uid", "screen_name", "gender", "verified", "verified_type",
                          "follow_count", "followers_count"])
            
            if self.print_progress:
                print(f'抓取根微博信息完成。')
                    
            return 1
        
        else:
            
            if self.print_progress:
                print(f'抓取根微博信息失败。')
                    
            return 0
    
    # 获取单页微博
    def get_one_page(self, page):
        url = f"https://weibo.com/ajax/statuses/repostTimeline?id={self.mid}&page={page}&moduleID=feed&count=20"
        res = requests.get(url, headers=self.headers).json()
        max_page = res['max_page']
        if page == 0: # 获取页数
            self.max_page = max_page
            return -1 
        
        if res['ok'] == 1:
            df = pd.DataFrame(res['data'])
            df['uid'] = df['user'].apply(lambda x: x['id'])
            df['username'] = df['user'].apply(lambda x: x['screen_name'])
            df = df[['created_at','mid', 'mblogid', 'uid','username','text_raw','reposts_count','comments_count','attitudes_count']]
            self.repost_df = pd.concat([self.repost_df, df], axis=0)

            return 1 # 表示爬取成功

        else:
            return 0 # 表示爬取失败


    # 获取全部转发
    def get_all_page(self):
        page = 1
        error = 0
        # 获取页数
        self.get_one_page(0)
        # 开始抓取
        crawl_info = st.empty()
        crawl_info.write("Start ！ 🎈")
        crawl_bar = st.progress(0)

        for page in np.arange(1,self.max_page+1,1):
            
            crawl_bar.progress(page/self.max_page) # 进度条
            if error > 10:
                break
            try:
                flag = self.get_one_page(page)

                if flag == 2:
                    break

                if page > 300:
                    break
                    
                if self.print_progress:
                    crawl_info.write(f'抓取第{page}页/{self.max_page}页，当前共抓取到{len(self.repost_df)}条。')

            except Exception as e:
                if self.print_progress:
                    crawl_info.write(f'抓取第{page}页:发生异常:{e}')
                
                error += 1
                continue
            
                
 
    # 构造转发结构 up_mid 和 root_mid
    def construct_repost_structure(self):
        self.repost_df['up_mid'] = np.NAN # 上级微博
        self.repost_df['root_mid'] = self.mid # 根微博
        self.repost_df = self.repost_df.drop_duplicates('mid')
        self.repost_df = self.repost_df.reset_index()
        
        crawl_info = st.empty()
        crawl_info.write("开始构造转发网络！ ")
        crawl_bar = st.progress(0)


        for idx in tqdm(range(len(self.repost_df))):
            crawl_bar.progress((idx+1)/len(self.repost_df)) # 进度条
            
            line = self.repost_df.loc[idx, :]
            usernames = re.findall('//@(.*?):',line['text_raw'])
            
            if len(usernames) > 0:
                for up_username in usernames:
                    #print(up_username)
                    up_line = self.repost_df.query('username == @up_username')
                    #print(up_line)
                    if len(up_line) == 1:
                        up_mid =  up_line['mblogid'].values[0]
                        #print(up_mid)
                        self.repost_df.loc[idx, 'up_mid'] = up_mid
                        break
                    elif len(up_line) > 1:
                        #print(up_line)
                        up_mid =  up_line['mblogid'].values[0] # 默认选第一个
                        self.repost_df.loc[idx, 'up_mid'] = up_mid
                        break
                    else:
                        # 如果没有找到上级用户
                        # 所有上级都没找到，连接到根用户
                        if  up_username == usernames[-1]:
                            self.repost_df.loc[idx, 'up_mid'] = self.mid
                            break
                        # 继续寻找上上级用户
                        else:
                            pass
            else:
                self.repost_df.loc[idx, 'up_mid'] = self.mid
    
        crawl_info.write("构造转发网络完成🎉 ")
        
    # 保存到csv
    def save_repost(self):
        # 存储转发
        if not os.path.exists(self.repost_dir):
            os.mkdir(self.repost_dir)
        else:
            pass
        self.repost_df.to_csv(self.repost_dir+str(self.mid)+'.csv',index=None)
        if self.print_progress:
                    print(f'存储转发微博完成。')
    
    def save_weibo_info(self):
        # 存储微博信息
        if not os.path.exists(self.path):
            self.weibo_info.to_csv(self.path,index=None)
        else:
            self.weibo_info.to_csv(self.path,index=None, mode='a+', header=None)
        
        if self.print_progress:
                    print(f'存储微博信息完成。')
    
    # 执行
    def run(self):
        # 抓取
        get_info_status = self.get_weibo_info()
        self.get_all_page()
        
        # 构造
        self.construct_repost_structure()
        
        # 存储
        self.save_repost()
        if get_info_status == 1:
            self.save_weibo_info()

        
        
        
