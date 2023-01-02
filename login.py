import os
import re
import time
import json
import requests
#from ..utils import removeImage, showImage, saveImage
import imghdr
import shutil
from PIL import Image
import streamlit as st
import pickle

'''保存图像'''
def saveImage(image, imagepath):
    fp = open(imagepath, 'wb')
    fp.write(image)
    fp.close()
    filetype = imghdr.what(imagepath)
    assert filetype in ['jpg', 'jpeg', 'png', 'bmp', 'gif']
    imagepath_correct = f"{'.'.join(imagepath.split('.')[:-1])}.{filetype}"
    shutil.move(imagepath, imagepath_correct)
    return imagepath_correct

'''扫码登录微博'''
@st.cache(allow_output_mutation=True)
class weiboScanqr():
    is_callable = True
    def __init__(self, **kwargs):
        for key, value in kwargs.items(): setattr(self, key, value)
        self.info = 'login in weibo in scanqr mode'
        self.cur_path = os.getcwd()
        self.rootdir = os.path.split(os.path.abspath(__file__))[0]
        self.website_name = 'weibo_bot_'
        self.session = requests.Session()
        self.__initialize()
        
    '''登录函数'''
    def login(self, username='', password='', crack_captcha_func=None, **kwargs):
        # 设置代理
        self.session.proxies.update(kwargs.get('proxies', {}))
        # 获取二维码
        params = {
            'entry': 'weibo',
            'size': '180',
            'callback': str(int(time.time() * 1000)),
        }
        response = self.session.get(self.qrcode_url, params=params)
        response_json = json.loads(response.text.split('(')[-1].split(')')[0])
        qrid = response_json['data']['qrid']
        imageurl = 'https:' + response_json['data']['image']
        response = self.session.get(imageurl)
        qrcode_path = saveImage(response.content, os.path.join(self.cur_path, 'qrcode.jpg'))
        #showImage(qrcode_path)
        # 显示登陆二维码
        image = Image.open('qrcode.png')
        st.image(image, caption='请用微博客户端扫描二维码登陆')
        # 检测二维码状态
        while True:
            params = {
                'entry': 'weibo',
                'qrid': qrid,
                'callback': 'STK_%s' % int(time.time() * 10000)
            }
            response = self.session.get(self.check_url, params=params)
            response_json = json.loads(response.text.split('(')[-1].split(')')[0])
            if response_json['retcode'] in [20000000]: break
            time.sleep(0.5)
        #removeImage(qrcode_path)
        # 模拟登录
        params = {
            'entry': 'weibo',
            'returntype': 'TEXT',
            'crossdomain': '1',
            'cdult': '3',
            'domain': 'weibo.com',
            'alt': response_json['data']['alt'],
            'savestate': '30',
            'callback': 'STK_' + str(int(time.time() * 1000)),
        }
        response = self.session.get(self.login_url, params=params)
        response_json = json.loads(response.text.split('(')[-1].split(')')[0])
        response_json['crossDomainUrlList'][0] = response_json['crossDomainUrlList'][0] + '&action=login'
        for url in response_json['crossDomainUrlList']:
            response = self.session.get(url)
        # 登录成功
        response = self.session.get(self.home_url)
        print('[INFO]: Account -> %s, login successfully' % response_json.get('nick', username))
        infos_return = {'username': username}
        infos_return.update(response_json)
        # 存储登陆状态
        self.savehistory('default', infos_return, self.session)
        
        return infos_return, self.session
    
    '''存储历史数据'''
    def savehistory(self, username, infos_return, session):
        #history_path = os.path.join(self.rootdir, self.website_name+'.pkl')
        history_path = self.website_name+'.pkl'
        history_infos = {}
        if os.path.exists(history_path):
            fp = open(history_path, 'rb')
            history_infos = pickle.load(fp)
            fp.close()
        history_infos[username] = [infos_return, session]
        fp = open(history_path, 'wb')
        pickle.dump(history_infos, fp)
        fp.close()
    
    
    '''导入历史数据'''
    def loadhistory(self, username):
        #history_path = os.path.join(self.rootdir, self.website_name+'.pkl')
        history_path = self.website_name+'.pkl'
        # 不存在历史文件
        if not os.path.exists(history_path): return None, None, True
        # 读取history文件
        fp = open(history_path, 'rb')
        history_infos = pickle.load(fp)
        fp.close()
        # 如果username不存在
        if username not in history_infos: return None, None, True
        # 提取对应的数据
        infos_return, session = history_infos[username]
        # 检查是否已经过期
        try:
            if self.checksessionstatus(session, infos_return):
                return None, None, True
        except Exception as e:
            st.write(e)
            return None, None, True
        # 返回可用的数据
        return infos_return, session, False
    
    '''检查会话是否已经过期, 过期返回True'''
    def checksessionstatus(self, session, infos_return):
        if 'nick' in infos_return:
            url = 'http://weibo.com/'
            response = session.get(url)
            if infos_return['nick'] in response.text:
                return False
            return True
        else:
            url = 'http://m.weibo.com/'
            response = session.get(url)
            if 'screen_name' in response.text:
                return False
            return True
    
    '''初始化'''
    def __initialize(self):
        self.headers = {
            'Referer': 'https://mail.sina.com.cn/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
        }
        self.home_url = 'https://weibo.com'
        self.qrcode_url = 'https://login.sina.com.cn/sso/qrcode/image'
        self.check_url = 'https://login.sina.com.cn/sso/qrcode/check'
        self.login_url = 'http://login.sina.com.cn/sso/login.php'
        self.session.headers.update(self.headers)


# 微博登陆
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def login_weibo():
    qr = weiboScanqr()
    infos_return, session, need_login = qr.loadhistory('default')
    #st.write(infos_return)
    if need_login:
        infos_return, session = qr.login()
    
    return infos_return, session 
