import requests
import pandas as pd
import numpy as np
import re
import json
import time

def get_uid(nickname):
    try:
        url = f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{nickname}&page_type=searchall"
        res = requests.get(url, timeout=2).json()
        cards = res.get("data", {}).get("cards", [])
        if not cards:
            return np.NAN
        
        group = cards[0].get("card_group", [])
        if not group:
            return np.NAN

        try:
            return group[0]["user"]["id"]
        except:
            return group[0]["users"][0]["id"]
    except Exception as e:
        print("get_uid error:", e)
        return np.NAN


def clean_text(text):
    pattern = re.compile(r'<[^>]+>', re.S)
    result = pattern.sub(' ', str(text))
    return result


def get_long_weibo(long_id):
    try:
        url = f'https://m.weibo.cn/statuses/extend?id={long_id}'
        res = requests.get(url, timeout=3).json()
        return res.get("data", {}).get("longTextContent", np.NAN)
    except:
        return np.NAN

def get_user_weibo(uid, cookie="", proxies=None):
    # 当 cookie 为空时仍然提供空 cookie 字段，接口仍可访问
    headers = {
        'cookie': cookie if cookie else "",
        'referer': 'https://m.weibo.cn/',
        'user-agent': (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 '
            'Mobile/15E148 Safari/604.1'
        )
    }

    base_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}"

    try:
        x = requests.get(base_url, headers=headers, timeout=3).json()
    except Exception as e:
        print("request error:", e)
        return pd.DataFrame(columns=[
            'created_at','mid','reposts_count','comments_count','attitudes_count',
            'isLongText','region_name','text','retweeted_text','location'
        ])

    # 账号空内容情况
    if x.get('msg') == '这里还没有内容':
        return pd.DataFrame(columns=[
            'created_at','mid','reposts_count','comments_count','attitudes_count',
            'isLongText','region_name','text','retweeted_text','location'
        ])

    cards = x.get("data", {}).get("cards", [])
    x_ = pd.DataFrame(cards)
    all_line = pd.DataFrame()

    # 解析微博（与你原结构完全一致）
    for line in x_.query("card_type == 9").get('mblog', []):
        try:
            created_at = pd.to_datetime(line.get('created_at', np.NAN))
            mid = line.get('mid', np.NAN)
            reposts_count = line.get('reposts_count', np.NAN)
            comments_count = line.get('comments_count', np.NAN)
            attitudes_count = line.get('attitudes_count', np.NAN)
            isLongText = line.get('isLongText', np.NAN)
            region_name = line.get('region_name', np.NAN)

            text = clean_text(line.get('text', np.NAN))

            if "retweeted_status" in line:
                retweeted_text = clean_text(
                    line["retweeted_status"].get("text", np.NAN)
                )
            else:
                retweeted_text = np.NAN

            location = np.NAN
            page_info = line.get("page_info", None)
            if isinstance(page_info, dict) and page_info.get("type") == "place":
                location = page_info.get("page_title", np.NAN)

            if isLongText:
                long_text = get_long_weibo(mid)
                if isinstance(long_text, str):
                    text = clean_text(long_text)

            row = pd.DataFrame([[
                created_at, mid, reposts_count, comments_count, attitudes_count,
                isLongText, region_name, text, retweeted_text, location
            ]], columns=[
                'created_at','mid','reposts_count','comments_count',
                'attitudes_count','isLongText','region_name','text',
                'retweeted_text','location'
            ])

            all_line = pd.concat([all_line, row], ignore_index=True)
        except Exception as e:
            print("parse error:", e)
            continue

    return all_line



def get_user_info(uid, cookie):
    try:
        url = f'https://m.weibo.cn/api/container/getIndex?&containerid=100505{uid}'
        headers = {
            'cookie': cookie,
            'referer': 'https://m.weibo.cn/',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)'
        }

        res = requests.get(url, timeout=3, headers=headers).json()
        user = res.get("data", {}).get("userInfo", {})

        df_ = pd.DataFrame([[
            uid,
            user.get("screen_name", np.NAN),
            user.get("verified", np.NAN),
            user.get("verified_type", np.NAN),
            user.get("urank", np.NAN),
            user.get("mbrank", np.NAN),
            user.get("statuses_count", np.NAN),
            user.get("follow_count", np.NAN),
            user.get("followers_count", np.NAN),
            user.get("gender", np.NAN),
            user.get("description", np.NAN),
            user.get("profile_image_url", np.NAN)
        ]], columns=['uid','screen_name','verified','verified_type','urank','mbrank',
                     'statuses_count','follow_count','followers_count','gender','description','profile_image_url'])

        return df_
    except Exception as e:
        print("get_user_info error:", e)
        df_ = pd.DataFrame([[np.NAN]*12], columns=['uid','screen_name','verified','verified_type','urank','mbrank',
                                                   'statuses_count','follow_count','followers_count','gender','description','profile_image_url'])
        df_['uid'] = uid
        return df_


def wan_transfer(text):
    try:
        text = str(text)
        if '万' in text:
            return int(float(text.replace('万', '')) * 10000)
        if '亿' in text:
            return int(float(text.replace('亿', '')) * 100000000)
        return int(text)
    except:
        return np.NAN


def cal_origin(csv_):
    try:
        csv_ = csv_.copy()
        csv_['is_origin'] = csv_['retweeted_text'].apply(lambda x: 1 if pd.isna(x) else 0)
        csv_['publish_time'] = pd.to_datetime(csv_['created_at'])
        csv_.index = csv_['publish_time']

        origin_rate = np.mean(csv_['is_origin'])
        like_num = np.mean(csv_['attitudes_count'].apply(wan_transfer))
        forward_num = np.mean(csv_['reposts_count'].apply(wan_transfer))
        comment_num = np.mean(csv_['comments_count'].apply(wan_transfer))
        post_freq = len(csv_) / len(csv_['publish_time'].resample('24h').count())
        post_location = 1 if csv_['location'].notna().sum() > 1 else 0

        richness_list = []
        content_length_list = []
        hashtag_list = []
        at_list = []
        for cont in csv_['text'].values:
            cont = str(cont).split('// @')[0]
            richness_list.append(cont)
            content_length_list.append(len(cont))
            hashtag_list.append(cont.count('#'))
            at_list.append(cont.count('@'))

        richness = len(set(''.join(richness_list)))
        content_length = np.mean(content_length_list)
        content_std = np.std(content_length_list)
        hashtag = np.mean(hashtag_list)
        at = np.mean(at_list)

        return pd.DataFrame([[origin_rate, like_num, forward_num, comment_num, post_freq,
                              post_location, content_length, content_std, richness, hashtag, at]],
                            columns=['origin_rate','like_num','forward_num','comment_num',
                                     'post_freq','post_location','content_length','content_std',
                                     'richness','hashtag','at'])
    except Exception as e:
        print("cal_origin error:", e)
        return pd.DataFrame([[np.NAN]*11], columns=['origin_rate','like_num','forward_num',
                                                    'comment_num','post_freq','post_location',
                                                    'content_length','content_std','richness',
                                                    'hashtag','at'])


def nickname_digit(s):
    res = re.findall('\d+', str(s))
    return len(res)


def user_attr(data):
    try:
        data['verified'] = data['verified'].map({True:1, False:0})
        data['gender'] = data['gender'].map({'m':1,'f':0})
        data['description'] = data['description'].apply(lambda x: 0 if x=='暂无简介' else 1)

        data['follow_count'] = data['follow_count'].apply(wan_transfer)
        data['followers_count'] = data['followers_count'].apply(wan_transfer)
        data['statuses_count'] = data['statuses_count'].apply(wan_transfer)

        data['followers_follow'] = data['followers_count']/(data['follow_count']+1)
        data['statuses_follow'] = data['statuses_count']/(data['follow_count']+1)

        data['name_digit'] = data['screen_name'].apply(lambda x: 1 if nickname_digit(x)>= 1 else 0)
        data['name_length'] = data['screen_name'].apply(lambda x: len(str(x)))

        return data
    except:
        data['followers_follow'] = np.NAN
        data['statuses_follow'] = np.NAN
        data['name_digit'] = np.NAN
        data['name_length'] = np.NAN
        return data


def crawl_info(uid, cookie):
    try:
        # 保证 UID 解析不改变你的字段格式
        uid = str(uid).replace("https://weibo.com/u/", "")

        user_info = get_user_info(uid, cookie)
        user_posts = get_user_weibo(uid, cookie)

        df_uid = cal_origin(user_posts)
        data = user_attr(user_info)

        user_data = pd.concat([data, df_uid], axis=1)
        return user_data

    except Exception as e:
        print("crawl_info error:", e)
        return None
