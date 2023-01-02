import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import re
import json
import streamlit as st
#from DecryptLogin import login
#from PIL import Image
session = ""



# 获取昵称用户对应的UID
def get_uid(nickname):
    headers = {'cookie':'__bid_n=184f088b36db02316c4207; FPTOKEN=30$PAUX8Dz8K/L3a7V2YwGCjKWsdPWYpdp0GEgyWHa9MU8XuCcuBs7XF7oSV7uYfVic8WnnWwnR6R8t8OoggALL/uGULsE3+I9vX6U6penwfX4RmaHs1pVREzzj5VBpjaSTw+v/MwvwOK6QeKyAhqnUIK2t9wcBZX3cMqN9zVnYh9os71aDVFeGJMTn2TFXyAEF2a37hQHStk7Xpd6l3UHZUQhpW5AL1Yyzz4kk64KPIBbXaU0++gCdP2PJ3czzO39rAiMVSO+PSa4Z0LyAqOSBoyQPezIUROs9qenxeWW4HvC3GW3X7M7rlhbWsb2YnQI98gYlYaB49AzfG7NGOuUdIVQ8hPTyqtmLZpG4SJSylUNsk7alOoxvn4CtEcPG4XKG|p3zCWu7Rj0akcUNwwmA35f+iZRS5ltxNoRUzfjVLgOI=|10|750222c78c0c50edc08ab2f821fa5c27; SCF=AgMK9ULMpSret7t0LYUhCOFIC1B_rvBqdWoRrGPJlvV9_NLx19V9yjbTPIXLGTCuxMiXIKFcCgi6ngYQAyEwOOw.; SUB=_2A25OrUR-DeRhGeBN7FYV8yvOyj-IHXVqbmw2rDV6PUJbktANLRj4kW1NRC0empmtWo4k-RjNz3whIwHCfqreCsJd; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5OmjT406FM.waPJ-C1Fwpp5JpX5K-hUgL.Foq0S0BXe0-EeKe2dJLoI0YLxKqL1KMLBK.LxKnLBo-LBoMLxKqL1KMLBK.LxKML1-BLBK2LxK-L12zLBKBLxK.L1KBLB.zLxKML1hzLB.et; SSOLoginState=1672033326; ALF=1674625326; _T_WM=01354eedaa035b0648b1b9ee9b8bce1c; FEID=v10-34b8a658a34ae086daaa4c407a69bb6d51318cd0; __xaf_fpstarttimer__=1672036633970; __xaf_thstime__=1672036634086; FPTOKEN=z4/KqF1G9tat54xcfZf1qOZHlI3HLc23CWXrKXT5H8OaAf3PsuJWIG9ZdXiFrj5PjxXAQEpG/LM5r9FTepjbTnQ3IiCfKggtCFqcua5mEGajHVsIMMW3Io46NNke1G96yLKiVpCW7fsadiLfTgs0wlFOI+MJrnmAnU2Kc+yGG0s7R+ggqmMFWxw9RuVHximylZu9FPU8BLOFKk52H9XoHHyKCiaD2pofknEI+PRhqHtdh2Dd9rqFBXh1Mm5KZwHoLjAYyiyl9i0z0prbqpxpRuI9IuRgrzBnBuKS0ITlD4VEI07qE7WPNUR4OU9/YB0TExx42lAufJvWrun2Ts7uYIekvwiFpVaDf0MaHbYDGCfNfBc5FTfac+dj4umWDdQo2+sN+Dhsza8hfcsjOI8qgA==|5G3rBgk+TOZ2u3VRb9VV83e9bfcevTNzr0gdZ9Lc2pQ=|10|a1fc083d54668516a59fb84ace4aff57; __xaf_fptokentimer__=1672036634166; MLOGIN=1; XSRF-TOKEN=4aa16e; WEIBOCN_FROM=1110006030; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D100103type%253D39%2526q%253D%25E9%2583%2591%25E5%25B7%259E123%2526t%253D%26fid%3D100103type%253D1%2526q%253D%25E9%2583%2591%25E5%25B7%259E123%26uicode%3D10000011'}
    res = json.loads(requests.get(f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{nickname}&page_type=searchall',headers=headers).text)
    
    try:
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
        long_text = requests.get(f'https://weibo.com/ajax/statuses/longtext?id={long_id}', headers=headers, proxies=None).json()['data']['longTextContent']
        return long_text
    except Exception as e:
        return np.NAN

def get_user_weibo(uid=6374435213, proxies=None):
    
    #x = requests.get(f'https://m.weibo.cn/api/container/getIndex?containerid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page=1', proxies=proxies, headers=headers).json()
    x = requests.get(f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}',proxies=proxies).json()
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
                x = requests.get(f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}&since_id={since_id}',).json()
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
    
    all_line.to_csv(str(uid)+'.csv')
    
headers = {
    'authority': 'weibo.com',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded',
    'accept': '*/*',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://weibo.com/1192329374/KnnG78Yf3?filter=hot&root_comment_id=0&type=comment',
    'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
    'cookie':  'SINAGLOBAL=6602183114630.345.1640853107889; UOR=,,login.sina.com.cn; SSOLoginState=1672033332; wvr=6; _s_tentry=-; Apache=3779125990160.492.1672033337757; ULV=1672033337771:9:2:1:3779125990160.492.1672033337757:1670478971009; wb_view_log_6374435213=1440*9002; webim_unReadCount=%7B%22time%22%3A1672627967074%2C%22dm_pub_total%22%3A88%2C%22chat_group_client%22%3A3%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A151%2C%22msgbox%22%3A0%7D; wb_timefeed_6374435213=1; SCF=Ar4ZhtzuLmtMYJFXdWZAedifVOMGLRRw7OQIWSdROtwzMW9tVB80Fb8HYUxV0M0Fc2lPJuD3wps7dWTJPIA0J8I.; SUB=_2A25OtjoRDeRhGeBN7FYV8yvOyj-IHXVtwizZrDV8PUJbmtANLUfEkW9NRC0empgQxmHSD8HK51bE0DbRQTAhy-VR; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5OmjT406FM.waPJ-C1Fwpp5JpX5K-hUgL.Foq0S0BXe0-EeKe2dJLoI0YLxKqL1KMLBK.LxKnLBo-LBoMLxKqL1KMLBK.LxKML1-BLBK2LxK-L12zLBKBLxK.L1KBLB.zLxKML1hzLB.et; ALF=1675220788; PC_TOKEN=a101daa09a'
}

headers2 = {
    'authority': 'm.weibo.cn',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded',
    'accept': '*/*',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://weibo.com/1192329374/KnnG78Yf3?filter=hot&root_comment_id=0&type=comment',
    'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
#     'cookie':  '__bid_n=184f088b36db02316c4207; FPTOKEN=30$PAUX8Dz8K/L3a7V2YwGCjKWsdPWYpdp0GEgyWHa9MU8XuCcuBs7XF7oSV7uYfVic8WnnWwnR6R8t8OoggALL/uGULsE3+I9vX6U6penwfX4RmaHs1pVREzzj5VBpjaSTw+v/MwvwOK6QeKyAhqnUIK2t9wcBZX3cMqN9zVnYh9os71aDVFeGJMTn2TFXyAEF2a37hQHStk7Xpd6l3UHZUQhpW5AL1Yyzz4kk64KPIBbXaU0++gCdP2PJ3czzO39rAiMVSO+PSa4Z0LyAqOSBoyQPezIUROs9qenxeWW4HvC3GW3X7M7rlhbWsb2YnQI98gYlYaB49AzfG7NGOuUdIVQ8hPTyqtmLZpG4SJSylUNsk7alOoxvn4CtEcPG4XKG|p3zCWu7Rj0akcUNwwmA35f+iZRS5ltxNoRUzfjVLgOI=|10|750222c78c0c50edc08ab2f821fa5c27; SCF=AgMK9ULMpSret7t0LYUhCOFIC1B_rvBqdWoRrGPJlvV9_NLx19V9yjbTPIXLGTCuxMiXIKFcCgi6ngYQAyEwOOw.; SUB=_2A25OrUR-DeRhGeBN7FYV8yvOyj-IHXVqbmw2rDV6PUJbktANLRj4kW1NRC0empmtWo4k-RjNz3whIwHCfqreCsJd; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5OmjT406FM.waPJ-C1Fwpp5JpX5K-hUgL.Foq0S0BXe0-EeKe2dJLoI0YLxKqL1KMLBK.LxKnLBo-LBoMLxKqL1KMLBK.LxKML1-BLBK2LxK-L12zLBKBLxK.L1KBLB.zLxKML1hzLB.et; SSOLoginState=1672033326; ALF=1674625326; _T_WM=01354eedaa035b0648b1b9ee9b8bce1c; FEID=v10-34b8a658a34ae086daaa4c407a69bb6d51318cd0; __xaf_fpstarttimer__=1672036633970; __xaf_thstime__=1672036634086; FPTOKEN=z4/KqF1G9tat54xcfZf1qOZHlI3HLc23CWXrKXT5H8OaAf3PsuJWIG9ZdXiFrj5PjxXAQEpG/LM5r9FTepjbTnQ3IiCfKggtCFqcua5mEGajHVsIMMW3Io46NNke1G96yLKiVpCW7fsadiLfTgs0wlFOI+MJrnmAnU2Kc+yGG0s7R+ggqmMFWxw9RuVHximylZu9FPU8BLOFKk52H9XoHHyKCiaD2pofknEI+PRhqHtdh2Dd9rqFBXh1Mm5KZwHoLjAYyiyl9i0z0prbqpxpRuI9IuRgrzBnBuKS0ITlD4VEI07qE7WPNUR4OU9/YB0TExx42lAufJvWrun2Ts7uYIekvwiFpVaDf0MaHbYDGCfNfBc5FTfac+dj4umWDdQo2+sN+Dhsza8hfcsjOI8qgA==|5G3rBgk+TOZ2u3VRb9VV83e9bfcevTNzr0gdZ9Lc2pQ=|10|a1fc083d54668516a59fb84ace4aff57; __xaf_fptokentimer__=1672036634166; WEIBOCN_FROM=1110006030; XSRF-TOKEN=430081; MLOGIN=1'
}


def parseUid(uid):
    response = requests.get(url=f'https://weibo.com/ajax/profile/info?custom={uid}', headers=headers)
    try:
        return response.json()['data']['user']['id']
    except:
        return None

    
def getUserInfo(uid=6374435213):
    
    global session
    try:
        uid = int(uid)
    except:
        # 说明是 xiena 这样的英文串
        uid = parseUid(uid)
        if not uid:
            return None
    response = session.get(f'https://weibo.com/ajax/profile/detail?uid={uid}')
#     if session != "":
#         response = session.get(f'https://weibo.com/ajax/profile/detail?uid={uid}')
#     else:
#         response = requests.get(url=f'https://weibo.com/ajax/profile/detail?uid={uid}', headers=headers)
    #print(response.text)
    
    if response.status_code == 400:
        return {
            'errorMsg': '用户可能注销或者封号',
            'location': None,
            'user_link': f'https://weibo.com/{uid}'
        }
    resp_json = response.json().get('data', None)
    if not resp_json:
        return None
    sunshine_credit = resp_json.get('sunshine_credit', None)
    if sunshine_credit:
        sunshine_credit_level = sunshine_credit.get('level', None)
    else:
        sunshine_credit_level = None
    education = resp_json.get('education', None)
    if education:
        school = education.get('school', None)
    else:
        school = None
    resp_json
    location = resp_json.get('location', None)
    gender = resp_json.get('gender', None)

    birthday = resp_json.get('birthday', None)
    created_at = resp_json.get('created_at', None)
    description = resp_json.get('description', None)
    # 我关注的人中有多少人关注 ta
#     followers = resp_json.get('followers', None)
#     if followers:
#         followers_num = followers.get('total_number', None)
#     else:
#         followers_num = None
    region = resp_json.get('ip_location', None)
    if region:
        region = region.split('：')[1]
    
    user_info = {
        'sunshine_credit_level': sunshine_credit_level,
        'school': school,
        'location': location,
        'gender': gender,
        'birthday': birthday,
        'created_at': created_at,
        'description': description,
        # 'followers_num': followers_num,
        'region':region
        
    }
    df_ = pd.DataFrame([user_info.values()], columns=user_info.keys())
    
    return df_

def getUserInfo2(uid=6374435213):

    url = 'https://m.weibo.cn/api/container/getIndex?mod=pedit_more%3Fmod%3Dpedit_more&jumpfrom=weibocom&containerid=100505' + str(uid) #6374435213
    res = requests.get(url, headers=headers2).text
    info = json.loads(res)
    #print(info)
    
    uid = info['data']['userInfo']['id']
    screen_name = info['data']['userInfo']['screen_name']

    verified = info['data']['userInfo']['verified']
    verified_type = info['data']['userInfo']['verified_type']

    urank = info['data']['userInfo']['urank']
    mbrank = info['data']['userInfo']['mbrank']

    statuses_count = info['data']['userInfo']['statuses_count']
    follow_count = info['data']['userInfo']['follow_count']
    followers_count = info['data']['userInfo']['followers_count']
    
    df_ = pd.DataFrame([[uid, screen_name, verified, verified_type, urank, mbrank, statuses_count, follow_count, followers_count]], columns = ['uid', 'screen_name', 'verified', 'verified_type', 'urank', 'mbrank', 'statuses_count', 'follow_count', 'followers_count'])
    return df_ 

def run_info_spider(uid):
    df1 = getUserInfo(uid)
    df2 = getUserInfo2(uid)
    df = pd.concat([df2, df1],axis=1)
    df.to_csv('user_info.csv',mode='w', index=None)


# 分析微博内容
def wan_transfer(text):
    text = str(text)
    try:
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

def cal_origin(csv_name):
    try:
        csv_ = pd.read_csv(csv_name)
        
        csv_['is_origin'] = csv_['retweeted_text'].apply(lambda x: 1 if pd.isna(x) else 0)
       
        csv_['publish_time'] = pd.to_datetime(csv_['created_at'])
        csv_.index = csv_['publish_time']
        
        origin_rate = np.mean(csv_['is_origin'])
        like_num = np.sum(csv_['attitudes_count'].apply(lambda x: wan_transfer(x)))
        
        forward_num = np.sum(csv_['reposts_count'].apply(lambda x: wan_transfer(x)))
        
        comment_num = np.sum(csv_['comments_count'].apply(lambda x: wan_transfer(x)))
        
        post_freq = len(csv_)/len(csv_['publish_time'].resample('24h').count())
        post_location = 1 if sum(pd.notna(csv_['location']))>1 else 0
        
        richness = []
        content_length_list = []
        for cont in csv_['text'].values:
            cont = str(cont).split('// @')[0]
            richness.append(cont)
            content_length_list.append(len(cont))

        richness = len(set(''.join(richness)))
        content_length = np.mean(content_length_list)
        content_std = np.std(content_length_list)
        return pd.DataFrame([[origin_rate, like_num, forward_num, comment_num, post_freq, post_location, content_length, content_std,richness]],
                            columns=['origin_rate','like_num','forward_num','comment_num','post_freq', 'post_location', 'content_length', 'content_std','richness'])
    except Exception as e:
        print(e)
        return pd.DataFrame([[np.NAN for i in range(8)]],columns=['origin_rate','like_num','forward_num','comment_num','post_freq', 'post_location', 'content_length', 'content_std','richness'])

# 提取微博用户属性特征
def wan_transfer(text):
    text = str(text)
    try:
        if '万' in text:
            num = float(text.strip('万'))
            return int(num*10000)
        elif '亿' in text:
            num = float(text.strip('亿'))
            return int(num*100000000)
        else:
            return int(text)
    except:
        return np.NAN

# 昵称文本
import re
def nickname_digit(s):
    res = re.findall('\d+',s)
    return len(res)
    
def user_attr(data):
    data['verified'] = data['verified'].map({True:1,False:0})

    data['sunshine_credit_level'] = data['sunshine_credit_level'].map({'信用极低':0,'信用较低':1,'信用一般':2,'信用较好':3,'信用极好':4})

    data['school'] = data['school'].apply(lambda x: 1 if pd.notna(x) else 0)

    data['location'] = data['location'].apply(lambda x: 1 if pd.notna(x) else 0)

    data['gender'] = data['gender'].map({'m':1,'f':0})

    data['created_at'] = pd.to_datetime(data['created_at'])
    data['created_year'] = data['created_at'].apply(lambda x: x.year)

    data['description'] = data['description'].apply(lambda x: 0 if  x=='暂无简介' else 1)

    data['birthday_date'] = data['birthday'].apply(lambda x: 1 if pd.notna(x) else 0)

    # 粉丝数、微博数、关注数
    data['follow_count'] = data['follow_count'].apply(lambda x: wan_transfer(x))
    data['followers_count'] = data['followers_count'].apply(lambda x: wan_transfer(x))
    data['statuses_count'] = data['statuses_count'].apply(lambda x: wan_transfer(x))

    data['followers_follow'] = data['followers_count']/(data['follow_count']+1)
    data['statuses_follow'] = data['statuses_count']/(data['follow_count']+1)
    
    data['name_digit'] = data['screen_name'].apply(lambda x:1 if nickname_digit(x)>= 1 else 0)
    data['name_length'] = data['screen_name'].apply(lambda x: len(x))
    
    return data



def crawl_info(uid):
    try:
        uid = str(uid)
        run_info_spider(uid)
        get_user_weibo(uid)
        #time.sleep(0.5)
        #分析内容
        df_uid = cal_origin(str(uid)+'.csv')
        df_uid['uid'] = int(uid)
        print(df_uid)
        user_info = pd.read_csv('user_info.csv')
        data = user_attr(user_info)
        print(data)

        #合并微博发布特征与用户属性特征
        user_data = pd.merge(left=data, right=df_uid, on='uid', how='left')
        return user_data
    except Exception as e:
        print(uid)
        print(e)
        

