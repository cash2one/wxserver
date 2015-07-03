#/usr/bin/env python
# -*- coding: utf-8 -*-
from bson.json_util import dumps,loads
import base64
import settings
import json
import random
from bson.objectid import ObjectId
from datetime import datetime,timedelta
from copy import deepcopy
import mdb
import os.path
import logging
import time
import  string
import time
import server_name
#from smallgfw import GFW
import StringIO
#from utils.chars import *
import rsa
import hashlib
import requests
import qiniu
from  tornado import gen
from tornado.httpclient import AsyncHTTPClient,HTTPClient
from json import JSONEncoder
#import gen


class mdump(JSONEncoder):
    def default(self, obj, **kwargs):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:
            return JSONEncoder.default(obj, **kwargs)

def get_monday():
    today = datetime.today()
    return today + timedelta(days=-today.weekday())

def decrypt_data(data):
    """
    rsa揭秘
    """
    private_key = rsa.PrivateKey.load_pkcs1(settings.private_key)
    message = rsa.decrypt(data, private_key)
    return message


def get_exp_week_rank_name():
    return 'exp_week_rank_%s'%get_week_name()

def save_pic(file_dict,bucket_name='',folder='share',filename=""):
    """
    """
    file_type = file_dict['filename'].split('.')[-1]
    if not filename:
        if bucket_name in ('activity-pet-image','llbanner') :
            filename = tools.random_key(1,12)+'@2x.'+file_type
        else:
            filename = tools.random_key(1,12)+'.'+file_type
    f = open("%s/%s"%(folder,filename), "wb")
    f.write(file_dict["body"])
    f.close()
    res=petimg.upload_file(filename,filename,'group/%s'%folder,bucket_name)
    print 'save_pic:',res
    return filename

def update_web_file(pic_data,name,bucket_name=''):
    """
    把二进制图片直接传七牛
    """
    global client,headers
    if not bucket_name:
        bucket_name='lltmp'
    uptoken = petimg.get_uptoken(bucket_name)
    extra = qiniu.io.PutExtra()
    extra.mime_type = "image/jpeg"
    
    #r = client.get(web_url,headers=headers)
    #r = get_html(web_url,referer='http://tieba.baidu.com/p/2931020380')
    #data = StringIO.StringIO(r)
    data = StringIO.StringIO(pic_data)
    #print 'file size:',data.len
    #save_local_img(name,r)
    ret, err = qiniu.io.put(uptoken,name,data,extra)
    data.close()
    if ret:
        ret['fsize'] = data.len
        return ret
    else:
        sys.stderr.write('error: %s ' % err)
        return err


def check_content_length(content):
    """
    检查文本长度
    """
    if type(content) != unicode:
        content = content.decode("utf8")

    return len(content),content 

def transtime(stime):
    """
    将'11-12-13 11:30'类型的时间转换成unixtime
    """
    if stime and ':' in stime:
        res=stime.split(' ')
        year,mon,day=[int(i) for i in res[0].split('-')]
        hour,second=[int(i) for i in res[1].split(':')]
        unixtime=mktime(datetime.datetime(year,mon,day,hour,second))
        return unixtime
    else:
        return int(time.time())

def get_today_datetime_range():
    """
    获取今天datetime的范围
    """
    now = datetime.now()
    start = datetime(now.year,now.month,now.day)
    end = start+timedelta(days=1)
    #logging.info("start:%s,end:%s"%(start,end))
    return start,end

def get_today_time_range():
    """
    获取今天time时间戳的范围
    """
    start,end = get_today_datetime_range()
    return mktime(start),mktime(end)

def get_time_range(year,month,day,hour=0,minute=0):
    """
    获取某天的时间范围
    """
    start = datetime(year,month,day,hour,minute)
    end = start+timedelta(days=1)
    return mktime(start),mktime(end)


def random_key(key_amount,key_len=12):
    """
    生成激活码
    """
    key_list = set()
    key_chars = string.lowercase+string.digits
    #logging.info('key_chars:%s'%key_chars)
    for i in xrange(key_amount):
        random_char_list = [random.choice(key_chars) for i in range(key_len)]
        key_list.add(''.join(random_char_list))
    if key_amount == 1:
        return key_list.pop()
    return key_list

def random_str(key_amount,key_len=12):
    """
    生成激活码
    """
    key_list = set()
    key_chars = string.lowercase
    #logging.info('key_chars:%s'%key_chars)
    for i in xrange(key_amount):
        random_char_list = [random.choice(key_chars) for i in range(key_len)]
        key_list.add(''.join(random_char_list))
    if key_amount == 1:
        return key_list.pop()
    return key_list

def imgurl(key,space='petimg_host'):
    space_path = settings.get(space)
    #print 'space:',space
    if not space_path:
        space_path = space
    return os.path.join(space_path,key)

def getkey(imgurl):
    """
    获取图片的key
    """
    return os.path.split(imgurl)[-1]

def mktime(dbtime):
    """
    convert datetime to int
    """
    return time.mktime(dbtime.timetuple())

def u2s(utime,type=0):
    if type==0:
        stime=time.strftime("%Y-%m-%d %H:%M",time.localtime(utime))
        return stime
    elif type==1:
        stime=time.strftime("%m.%d",time.localtime(utime))
        return stime


def __zadd__(name,key,value):
    """
    增强版redis zadd
    """
    delta = 0.0001
    total_count = mdb.rcon.zcard(name)
    same_key = mdb.rcon.zrangebyscore(name,value,value+1-delta)
    if same_key:
        #当有相同分数人的时候
        mdb.rcon.zadd(name,value+delta,key)
        for index,key in enumerate(same_key):
            mdb.rcon.zadd(name,value+delta*(index+2),key)
    else:
        mdb.rcon.zadd(name,value,key)

def zadd(name,key,value):
    """
    扩展redis 的zadd
    当分数一样时,取最早进入队列的
    """
    total_count = mdb.rcon.zcard(name)
    rank = mdb.rcon.zrevrank(name,key)
    total_count = mdb.rcon.zcard(name) 
    #print 'rank:',rank
    #print 'total count:',total_count
    if total_count < 1000:
        __zadd__(name,key,value)
    elif rank and rank < 1000:
        __zadd__(name,key,value)
    else:
        mdb.rcon.zadd(name,value,key)

def is_today(last_time):
    """
    检测时间戳是否为今天
    """
    now = datetime.now()
    dtime = datetime.fromtimestamp(last_time)
    if now.day == dtime.day:
        return True
    else:
        return False

def dumps(data):
    """
    json dumps
    """
    res = json.dumps(data,cls=mdump)
    return res

def add_manage_log(uid,operator,data,reason=''):
    """
    纪录后台日志
    """
    mdb.con.managelog.insert(
            {
                'uid':uid, 
                'operator':operator, 
                'data':data, 
                'reason':reason, 
                'create_time':time.time(), 
                }
            )

def signature_js():
    """

    """
    noncestr = 'Wm3WZYTPz0wzccnW'
    jsapi_ticket = 'bxLdikRXVbTPdHSM05e5uwkkGx1-FNs8acGd6cjOtML2lAdbrb4a1t0G_cXbuEiQ2_EnD5lbPCPZ8OIs2VmBmg'
    timestamp=1414587457
    arg_list = 'jsapi_ticket=%s&noncestr=%s&timestamp=1414587457&url=http://%s/wxtest'%(
            settings.get('host'),
            jsapi_ticket,
            noncestr,
            )
    print 'arg_list:',arg_list
    signature_sha = hashlib.sha1(arg_list).hexdigest()
    return signature_sha

def get_system_key(key):
    v = mdb.rcon.get(key)
    if not v:
        v = settings.system_key[key]
    if v.isdigit():
        v = int(v)
    return v

@gen.coroutine
def get_weixin_access_token():
    """
    获取微信服务号的access_token
    """
    access_token = mdb.rcon.get('fuwuhao_access_token_%s'%settings.get('weixin_fuwuhao_appid'))
    if access_token:
        print '============find access token  cache============'
        logging.info('find weixin access token cache:%s'%access_token)
        raise gen.Return(access_token)
    else:
        print '============not find access token  cache============'
        token_url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s"%(settings.get('weixin_fuwuhao_appid'),settings.get('weixin_fuwuhao_secret'))
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(token_url)
        res = json.loads(res.body)
        access_token = res['access_token']
        mdb.rcon.set('fuwuhao_access_token_%s'%settings.get('weixin_fuwuhao_appid'),access_token,ex=res['expires_in']-1000)
        mdb.rcon.set('fuwuhao_access_token_expires_time_%s'%settings.get('weixin_fuwuhao_appid'),int(time.time())+res['expires_in']-1000)
        raise gen.Return(access_token)

@gen.coroutine
def get_weixin_jsapi_ticket():
    """
    获取jsapi ticket
    """
    jsapi_ticket = mdb.rcon.get('weixin_jsapi_ticket_%s'%settings.get('weixin_fuwuhao_appid'))
    if jsapi_ticket:
        print '============find js ticket cache============'
        raise gen.Return(jsapi_ticket)
    else:
        print '============not find js ticket cache============'
        access_token = yield get_weixin_access_token()
        ticket_url = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi"%access_token
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(ticket_url)
        res = json.loads(res.body)
        #print 'res:',res
        mdb.rcon.set('weixin_jsapi_ticket_%s'%settings.get('weixin_fuwuhao_appid'),res['ticket'],ex=res['expires_in']-1000)
        mdb.rcon.set('fuwuhao_jsapi_ticket_expires_time_%s'%settings.get('weixin_fuwuhao_appid'),int(time.time())+res['expires_in']-1000)
        raise gen.Return(res['ticket'])

@gen.coroutine
def get_weixin_jsconfig_info(host,url):
    """
    获取微信jsapi config信息
    """
    jsapi_ticket = yield get_weixin_jsapi_ticket()
    jsconfig = {'appid':settings.get('weixin_fuwuhao_appid'),'timestamp':int(time.time()),'nonceStr':'liuliutest'}
    arg_list = 'jsapi_ticket=%s&noncestr=%s&timestamp=%s&url=http://%s%s'%(
        jsapi_ticket,
        jsconfig['nonceStr'],
        jsconfig['timestamp'],
        host, 
        url,
        )
    print 'arg_list:',arg_list
    signature_sha = hashlib.sha1(arg_list).hexdigest()
    jsconfig['signature'] = signature_sha
    raise gen.Return(jsconfig)

@gen.coroutine
def get_weixin_web_access_token(code,active='fuwuhao'):
    """
    通过web code 获取网页授权用户的 access token
    """
    url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code"%(
            settings.get('weixin_fuwuhao_appid'),
            settings.get('weixin_fuwuhao_secret'),
            code,
            )
    http_client = AsyncHTTPClient()
    res = yield http_client.fetch(url)
    res = json.loads(res.body)
    res['create_time'] = time.time()
    mdb.con.wxsns.update(
            {'active':active,'openid':res['openid']},
            {'$set':res},
            upsert=True
            )
    raise gen.Return(res) 
     
@gen.coroutine
def get_weixin_web_snsinfo(openid,token,lang='zh_CN',active='fuwuhao'):
    """
    获取微信网页授权的用户信息
    """
    url  = "https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s&lang=%s"%(
            token,
            openid,
            lang
            )

    http_client = AsyncHTTPClient()
    res = yield http_client.fetch(url)
    res = json.loads(res.body)
    res['create_time'] = time.time()
    res['like'] = 0
    mdb.con.wxsns.update(
            {'openid':res['openid'],
             'active':active,
                },
            {'$set':res},
            upsert=True
            )
    raise gen.Return(res) 

def refresh_weixin_web_token(openid,active='fuwuhao'):
    """
    刷新web token
    """
    token = mdb.con.wxsns.find_one({'openid':openid,'active':active})
    if token:
        url = "https://api.weixin.qq.com/sns/oauth2/refresh_token?appid=%s&grant_type=refresh_token&refresh_token=%s"%(
            settings.get('weixin_fuwuhao_appid'),
            token['refresh_token']
            )
        r = requests.get(url,allow_redirects=True)
        res = r.json()
        res['create_time'] = time.time()
        mdb.con.wxsns.update(
                {'active':active,'openid':res['openid']},
                {'$set':res},
                upsert=True
                )
        return res

@gen.coroutine
def get_weixin_snsinfo_by_code(code,active='fuwuhao'):
    """
    根据code获取微信 用户信息
    """
    token = yield get_weixin_web_access_token(code,active)
    snsinfo = yield get_weixin_web_snsinfo(token['openid'],token['access_token'],active=active)
    snsinfo.update(token)
    raise gen.Return(snsinfo) 

def get_weixin_snsinfo_by_openid(openid,active='fuwuhao'):
    snsinfo = mdb.con.wxsns.find_one({'openid':openid,'active':active}) 
    return snsinfo

def init_fb_img():
    teams = mdb.con.adifb.team.find()
    for t in teams:
        print '======================================='
        print 'team name:',t['team_name']
        sns = mdb.con.wxsns.find_one({'openid':t['wechat_id']})
        if sns:
            mdb.con.adifb.team.update({'_id':t['_id']},{'$set':{'pic':sns.get('headimgurl','')}})
        else:
            print u'没有发现头像'

def update_fbteam_status(city_id):
    mdb.con.adifb.team.update({'status':'0','city_id':str(city_id)},{'$set':{'status':'-1'}},multi=True)


if __name__ == '__main__':
    import time
    mdb.init() 
    a = time.time()
    #user = User('5294555dd77d5e7afba55c91')
    #pet = rpet('5294555dd77d5e7afba55c19')
    #print time.time() - a
    #remove_test_user()
    #print get_week_name()
    #print decrypt_data("\x7f\xf5=/O*\x19\xbf\xd2\xbcL\xccD\xa3/DF\xc6\x86\x11\x06\xedC\xb4g\x07\rF\xe7p\xad\xdab~\x198\x1e\xf8\xe7@\xb7]\xfb\xf3$\x89\xa6T6>\xca\xd2)\x17h\x8a\x13\t\x15\x89\xaaO\xe5T-a\x80\x16v\xce\xbf\xb04\x9c\xeepne\xf0\x16\xfe\xafB\xe6\xa0\xe4\xd5<f\x8d\x08\xfaH\xea\xf0A\xc2P\x89\xe5\xda\x03zs@`\x1f,\xce\xb17\xd3\xed.\x98\xc5g\x1d@D\xd1'}(w'\x00A")
    #print get_jsapi_ticket()
    #print  get_system_key('daxingchongwu') 
    #print get_weixin_jsconfig_info('/download')
    #print get_weixin_web_access_token('041fe0fa7a46e03cf5918ebf7ed3b17G')
    #print get_weixin_web_snsinfo('o73HYs4n5S_Y9GZXVv2kvXwuh3zU','OezXcEiiBSKSxW0eoylIeAbG1YtjO5NzZDGhcS5YSI4YlsYGuts8NjztUjq2Lr-REYIbC5e0A6_u_E9WzlVvHhW_Zq-pxGne-DIiI4rX42ut6SPu1iHLUpwD4bk7i9Cj')
    #print refresh_weixin_web_token('o73HYs4n5S_Y9GZXVv2kvXwuh3zU')
    #print get_weixin_snsinfo_by_code('02164e763a679cc98aedc95b85712bfn')
    #print get_weixin_snsinfo_by_openid('o73HYs4n5S_Y9GZXVv2kvXwuh3zU')
    #print get_exp_week_rank_name()
    #print get_weixin_access_token()
    #print get_weixin_jsapi_ticket()
    update_fbteam_status('3')
