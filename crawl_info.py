
import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import re
import json
# import streamlit as st
# from PIL import Image


# 获取昵称用户对应的UID
def get_uid(nickname):
    
    try:
        res = json.loads(requests.get(f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{nickname}&page_type=searchall', timeout=1).text)
        try:
            uid = res['data']['cards'][0]['card_group'][0]['user']['id']
        except:
            uid = res['data']['cards'][0]['card_group'][0]['users'][0]['id']
        return uid
    except Exception as e:
        print(e)
        return np.NAN

def clean_text(text):
    pattern = re.compile(r'<[^>]+>',re.S)    # 匹配两个尖括号并将其作为一个整体
    result = pattern.sub(' ', str(text))  
    return result

# 获取长推文
def get_long_weibo(long_id):
    try:
        long_text = requests.get(f'https://m.weibo.cn/statuses/extend?id={long_id}', timeout=3).json()['data']['longTextContent']
        return long_text
    except Exception as e:
        return np.NAN

#获取用户微博
def get_user_weibo(uid, cookie, proxies=None,):
    headers={
            'cookie': cookie,
            #'accept': 'application/json, text/plain, */*',
            #'accept-language': 'zh-CN,zh;q=0.9',
            #'mweibo-pwa': '1',
            #'priority': 'u=1, i',
            #'sec-fetch-dest': 'empty',
            #'sec-fetch-mode': 'cors',
            'referer': 'https://m.weibo.cn/',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            #'x-requested-with': 'XMLHttpRequest',
            #'x-xsrf-token': '332c0a',
    }
    #x = requests.get(f'https://m.weibo.cn/api/container/getIndex?containerid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page=1', proxies=proxies, headers=headers).json()
    x = requests.get(f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}',proxies=proxies, timeout=2, headers=headers).json()
    #print(x)
    if x.get('msg',0) ==  '这里还没有内容':
        with open('郑州暴雨-deleted_account.txt',mode='a',encoding='utf-8') as w:
            w.write(str(uid)+'\n')
            return None
    x_ = pd.DataFrame(x['data']['cards'])

    all_line = pd.DataFrame()
    
    # 有时候第一页没有个人的微博，此时尝试向后翻页
    if len(x_.query('card_type == 9')) == 0:
        if x['data']['cardlistInfo'].get('since_id',0) != 0:
            x_ = pd.DataFrame()
            for i in range(4):
                since_id = x['data']['cardlistInfo'].get('since_id',0)
                #print(since_id)
                x = requests.get(f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}&since_id={since_id}', headers=headers, timeout=1).json()
                x_info = pd.DataFrame(x['data']['cards'])
                #time.sleep(1)
                x_ = pd.concat([x_, x_info], axis=0)
                
    # 整理微博信息
    for line in x_.query('card_type == 9')['mblog']:
        created_at = pd.to_datetime(line['created_at'])
        mid = line['mid']
        reposts_count = line.get('reposts_count',np.NAN)
        comments_count = line.get('comments_count',np.NAN)
        attitudes_count = line.get('attitudes_count',np.NAN)
        isLongText = line.get('isLongText',np.NAN)
        region_name = line.get('region_name',np.NAN) 
        text = clean_text(line.get('text',np.NAN))
        retweeted_text = clean_text(line['retweeted_status']['text']) if 'retweeted_status' in line.keys() else np.NAN
        source = line['source']
        # 判断是否有地理位置
        if  line.get('page_info',0) != 0:
            if line['page_info'].get('type',0) == 'place':
                location =  line['page_info']['page_title']
            else:
                location = np.NAN
        else:
            location = np.NAN
        # 获取长微博
        if isLongText:
            text = clean_text(get_long_weibo(mid))

        line = pd.DataFrame([[created_at,mid,reposts_count,comments_count,attitudes_count,isLongText,region_name, 
                             text, retweeted_text, location]], 
                     columns=['created_at','mid','reposts_count','comments_count','attitudes_count','isLongText','region_name',
                              'text', 'retweeted_text', 'location'])
        all_line = pd.concat([all_line, line])

    print(all_line)

    return all_line

    

def get_user_info(uid, cookie):

    #url = 'https://m.weibo.cn/api/container/getIndex?mod=pedit_more%3Fmod%3Dpedit_more&jumpfrom=weibocom&containerid=100505' + str(uid) #6374435213
    #https://m.weibo.cn/api/container/getIndex?&containerid=1005056308541867
    try:
        url = 'https://m.weibo.cn/api/container/getIndex?&containerid=100505' + str(uid) #6374435213

        headers={
            'cookie': cookie,
            #'accept': 'application/json, text/plain, */*',
            #'accept-language': 'zh-CN,zh;q=0.9',
            #'mweibo-pwa': '1',
            #'priority': 'u=1, i',
            #'sec-fetch-dest': 'empty',
            #'sec-fetch-mode': 'cors',
            'referer': 'https://m.weibo.cn/',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            #'x-requested-with': 'XMLHttpRequest',
            #'x-xsrf-token': '332c0a',
    }

        res = requests.get(url, timeout=1, headers=headers).text
        #st.write(res)
        
        info = json.loads(res)

        screen_name = info['data']['userInfo']['screen_name']

        verified = info['data']['userInfo']['verified']
        verified_type = info['data']['userInfo']['verified_type']

        urank = info['data']['userInfo']['urank']
        mbrank = info['data']['userInfo']['mbrank']

        statuses_count = info['data']['userInfo']['statuses_count']
        follow_count = info['data']['userInfo']['follow_count']
        followers_count = info['data']['userInfo']['followers_count']

        gender =  info['data']['userInfo']['gender']
        description = info['data']['userInfo']['description']

        profile_image_url = info['data']['userInfo']['profile_image_url']

        df_ = pd.DataFrame([[uid, screen_name, verified, verified_type, urank, mbrank, statuses_count, follow_count, followers_count, gender, description, profile_image_url]], columns = ['uid', 'screen_name', 'verified', 'verified_type', 'urank', 'mbrank', 'statuses_count', 'follow_count', 'followers_count', 'gender', 'description', 'profile_image_url'])

        return df_
        st.write(df_)
        #print(df_)
    except Exception as e:

        df_ = pd.DataFrame([[np.NAN for i in range(12)]], columns = ['uid', 'screen_name', 'verified', 'verified_type', 'urank', 'mbrank', 'statuses_count', 'follow_count', 'followers_count', 'gender', 'description', 'profile_image_url'])
        df_['uid'] = uid

    return df_
    #df_.to_csv('user_info.csv',mode='w', index=None)
    #st.write(df_)
    #print(df_)

# 分析微博内容
def wan_transfer(text):
    
    try:
        text = str(text)
        if '万' in text:
            num = float(text.strip('万'))
            return int(num*10000)
        elif '亿' in text:
            num = float(text.strip('亿'))
            return int(num*100000000)
        else:
            return int(text.strip())
    except:
        return np.NAN

def cal_origin(csv_):
    try:
        csv_['is_origin'] = csv_['retweeted_text'].apply(lambda x: 1 if pd.isna(x) else 0)
       
        csv_['publish_time'] = pd.to_datetime(csv_['created_at'])
        csv_.index = csv_['publish_time']
        
        origin_rate = np.mean(csv_['is_origin'])
        like_num = np.mean(csv_['attitudes_count'].apply(lambda x: wan_transfer(x)))
        
        forward_num = np.mean(csv_['reposts_count'].apply(lambda x: wan_transfer(x)))
        
        comment_num = np.mean(csv_['comments_count'].apply(lambda x: wan_transfer(x)))
        
        post_freq = len(csv_)/len(csv_['publish_time'].resample('24h').count())
        post_location = 1 if sum(pd.notna(csv_['location']))>1 else 0
        
        richness = []
        content_length_list = []
        hashtag_list = []
        at_list = []
        hashtag_list  = []
        for cont in csv_['text'].values:
            cont = str(cont).split('// @')[0]
            richness.append(cont)
            content_length_list.append(len(cont))
            hashtag_list.append(str(cont).count('#'))
            at_list.append(str(cont).count('@'))
            
        richness = len(set(''.join(richness)))
        content_length = np.mean(content_length_list)
        content_std = np.std(content_length_list)
        hashtag = np.mean(hashtag_list)
        at = np.mean(at_list)

        return pd.DataFrame([[origin_rate, like_num, forward_num, comment_num, post_freq, post_location, content_length, content_std, richness, hashtag, at]], columns=['origin_rate','like_num','forward_num','comment_num','post_freq', 'post_location', 'content_length', 'content_std', 'richness','hashtag', 'at'])
    
    except Exception as e:

        return pd.DataFrame([[np.NAN for i in range(11)]],columns=['origin_rate','like_num','forward_num','comment_num','post_freq', 'post_location', 'content_length', 'content_std','richness','hashtag', 'at'])


# 提取微博用户属性特征
# 昵称文本
import re
def nickname_digit(s):
    res = re.findall('\d+',s)
    return len(res)

# 提取用户属性
def user_attr(data):
    try:
        data['verified'] = data['verified'].map({True:1,False:0})

    #     data['sunshine_credit_level'] = data['sunshine_credit_level'].map({'信用极低':0,'信用较低':1,'信用一般':2,'信用较好':3,'信用极好':4})

    #    data['school'] = data['school'].apply(lambda x: 1 if pd.notna(x) else 0)

    #     data['location'] = data['location'].apply(lambda x: 1 if pd.notna(x) else 0)

        data['gender'] = data['gender'].map({'m':1,'f':0})

    #     data['created_at'] = pd.to_datetime(data['created_at'])
    #     data['created_year'] = data['created_at'].apply(lambda x: x.year)

        data['description'] = data['description'].apply(lambda x: 0 if  x=='暂无简介' else 1)

    #     data['birthday_date'] = data['birthday'].apply(lambda x: 1 if pd.notna(x) else 0)

        # 粉丝数、微博数、关注数
        data['follow_count'] = data['follow_count'].apply(lambda x: wan_transfer(x))
        data['followers_count'] = data['followers_count'].apply(lambda x: wan_transfer(x))
        data['statuses_count'] = data['statuses_count'].apply(lambda x: wan_transfer(x))

        data['followers_follow'] = data['followers_count']/(data['follow_count']+1)
        data['statuses_follow'] = data['statuses_count']/(data['follow_count']+1)

        data['name_digit'] = data['screen_name'].apply(lambda x:1 if nickname_digit(x)>= 1 else 0)
        data['name_length'] = data['screen_name'].apply(lambda x: len(x))
    
    
        return data
    except:
        data['followers_follow'] = np.NAN
        data['statuses_follow'] = np.NAN

        data['name_digit'] =  np.NAN
        data['name_length'] =  np.NAN
     
        return data

##################
# 抓取信息并分析内容
##################
def crawl_info(uid, cookie):
    try:
        #抓取信息
        uid = str(uid).strip('https://weibo.com/u/')
        if cookie.strip() == "":
            cookie = ''
            
        
        user_info = get_user_info(uid, cookie)
        #print(user_info)
        user_posts = get_user_weibo(uid, cookie)
        #print(user_posts)
        
        #分析内容
        df_uid = cal_origin(user_posts)
        data = user_attr(user_info)

        #合并微博发布特征与用户属性特征
        user_data = pd.concat([data, df_uid], axis=1)
        
        
        return user_data
        
    except Exception as e:
        #print(e)
        pass
