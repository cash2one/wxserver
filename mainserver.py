#!/usr/bin/env python
#-*- encoding:utf-8 -*-
import tornado.ioloop
import tornado.web
import requests
import json
import redis
from  wxdecry.WXBizMsgCrypt import WXBizMsgCrypt
from bs4 import BeautifulSoup as bs4
from wechat_server import BaseRequest,WeChatHandler
from bson.objectid import ObjectId
from pymongo import MongoClient
from json import JSONEncoder
import time

rcon = redis.StrictRedis(host='wxtest.oookini.com', port=6379, db=1)
con = MongoClient(host = 'wxtest.oookini.com',port=27017)['wx']

class mdump(JSONEncoder):
    def default(self, obj, **kwargs):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:
            return JSONEncoder.default(obj, **kwargs)


appid = 'wx8e080139ced94edd'
appsecret = '0c79e1fa963cd80cc0be99b20a18faeb'
token='kini'
encodingAESKey = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
host="wxtest.oookini.com"

class mdump(JSONEncoder):
    def default(self, obj, **kwargs):
         if isinstance(obj, ObjectId):
             return str(obj)
         else:
             return JSONEncoder.default(obj, **kwargs)

def dumps(obj):
    return json.dumps(obj,cls=mdump)

def search_shop(appid,location):
    """
    """
    query_attr = {
                  '$geoNear': {
                    'near': { 'type': "Point", 'coordinates': location},
                    'distanceField': "dist.calculated",
                    #'maxDistance': 10,
                    'includeLocs': "dist.location",
                    'num': 5,
                    'spherical': True
                  }
    }
    shop_list = list(con.wxshop.aggregate([query_attr]))
    return shop_list


class WXHandler(tornado.web.RequestHandler):

    def prepare(self):
        appid = self.get_cookie("appid","")
        appid = 'wx86fed2909860741b'
        if not appid:
            self.redirect("/auth")
            return
        else:
            self.appid=appid

def get_authorizer_account_info(auth_appid):
    """
    获取授权方的账户信息
    该API用于获取授权方的公众号基本信息，包括头像、昵称、帐号类型、认证类型、微信号、原始ID>    和二维码图片URL。
    需要特别记录授权方的帐号类型，在消息及事件推送时，对于不具备客服接口的公众号，需要在5秒>    内立即响应；而若有客服接口，则可以选择暂时不响应，而选择后续通过客服接口来发送消息触达粉丝。 88     """
    component_access_token = rcon.get('component_access_token') 
    url = "https://api.weixin.qq.com/cgi-bin/component/api_get_authorizer_info?component_access_token=%s"%component_access_token
    data = {
            "component_appid":appid,
            "authorizer_appid":auth_appid,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    return r.json()

def get_authorization_info(auth_code):
    """
    授权码换取公众号的授权信息
    """
    component_access_token = rcon.get('component_access_token') 
    print 'component_access_token:',component_access_token
    url = "https://api.weixin.qq.com/cgi-bin/component/api_query_auth?component_access_token=%s"%(component_access_token)
    data=  {
            'component_appid':appid,
            'authorization_code':auth_code,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    res = r.json()
    if res:
        print 'res:',res
        app_account_info = get_authorizer_account_info(res['authorization_info']['authorizer_appid'])
        print 'app_account_info:',app_account_info
        res.update(app_account_info)
        rcon.set(res['authorization_info']['authorizer_appid'],json.dumps(res))
    return res

def get_web_access_token(aid,code):
    """
    通过代替服务号获取到的网页授权code来申请网页授权的access token
    """
    component_access_token = rcon.get('component_access_token')
    url = "https://api.weixin.qq.com/sns/oauth2/component/access_token?appid=%s&code=%s&grant_type=authorization_code&component_appid=%s&component_access_token=%s"%(aid,code,appid,component_access_token)
    r = requests.get(url,allow_redirects=True)
    #print r.text
    return r.json()

def get_snsapi_userinfo(access_token,openid,lang='en'):
    """
    获取网页授权的用户信息
    """
    url = "https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s&lang=%s"%(access_token,openid,lang)
    r = requests.get(url,allow_redirects=True)
    return json.loads(r.content)

def get_access_token(component_verify_ticket):
    """
    获取第三方平台access_token
    """
    url = 'https://api.weixin.qq.com/cgi-bin/component/api_component_token'
    data = {
            'component_appid':appid,
            'component_appsecret':appsecret,
            'component_verify_ticket':component_verify_ticket,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    print 'get_access_token:',r.text
    return r.json()['component_access_token']

def get_pre_auth_code(component_access_token):
    """
    获取预授权码
    """
    url = "https://api.weixin.qq.com/cgi-bin/component/api_create_preauthcode?component_access_token=%s"%(component_access_token)
    data = {
            'component_appid':appid,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    print 'get_pre_auth_code:',r.text
    return r.json()['pre_auth_code']

def decry_component_verify_ticket(from_xml,msg_sign,timestamp,nonce):
    """
    解密component_verify_ticket
    在公众号第三方平台创建审核通过后，微信服务器会向其“授权事件接收URL”每隔10分钟定时推送component_verify_ticket。第三方平台方在收到ticket推送后也需进行解密 
    """
    decrypt_test = WXBizMsgCrypt(token,encodingAESKey,appid)
    ret ,decryp_xml = decrypt_test.DecryptMsg(from_xml, msg_sign, timestamp, nonce)
    print 'ret:',ret
    print 'decryp_xml:',decryp_xml
    soup = bs4(decryp_xml,'xml')
    component_verify_ticket = soup.ComponentVerifyTicket.text
    return component_verify_ticket

class Test(BaseRequest):
    """
    第三方平台授权上线
    """
    def get_event(self):
        """
        """
        self.send_text(self.event_key+"from_callback")

    def get_text(self):
        if self.wxtext == 'TESTCOMPONENT_MSG_TYPE_TEXT':
            self.send_text("TESTCOMPONENT_MSG_TYPE_TEXT_callback")
        else:
            self.send_text("")
            #url = "https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s"%




class Adidas(BaseRequest):
    """
    adidas 篮球足球公众号
    """
    def get_text(self):
        print 'aaaaaaaaaaaaaaaa'
        if self.wxtext == 't':
            self.send_text('test')
        else:
            self.send_text(u'为客家人')

    def search_shop(self,location):
        """
        """
        query_attr = {
                      '$geoNear': {
                        'near': { 'type': "Point", 'coordinates': location},
                        'distanceField': "dist.calculated",
                        #'maxDistance': 10,
                        'includeLocs': "dist.location",
                        'num': 5,
                        'spherical': True
                      }
        }
        shop_list = list(con.wxshop.aggregate([query_attr]))
        print 'shop_list:',shop_list
        return shop_list

    def get_event(self):
        if self.event_key == 'fb_post':
            #足球post
            self.send_img('tvjtoklXBSTpwwOFdjw1UL22LyaJQ4oA6evlCydptTw')

    def get_video(self):
        self.send_text(u'感谢你的互动。如你已上传#火拼#视频，请留下真实姓名和手机号码，完成#火拼#报名。谢谢！')

    def get_subscribe(self):
        """
        收到新用户关注
        """
        self.send_text('Welcome to adidas.')

    def get_location(self):
        res = []
        shop_list = self.search_shop([self.location_y,self.location_x])
        for shop in shop_list:
            res.append(
                    (
                    shop['name']+u'(距离您%s米)'%int(shop['dist']['calculated']),
                    u'距离您%s米'%int(shop['dist']['calculated']),
                    "http://www.costa.co.uk/media/1054/store-locator-2x.jpg",
                    "http://wxtest.oookini.com/shopmap?shop_id=%s"%shop['_id'],
                    )
                    )
        #self.send_text('Welcome to adidas.')
        self.send_artical_list(res)

class www(WeChatHandler):
    """
    微信公众号
    """
    app_list ={
        #adidas test
        'gh_76308e64a3c4':{'handler':Adidas,'token':'kini'},
        #adidas product
        'gh_51058468179a':{'handler':Adidas,'token':'kini'},
        #test
        'gh_3c884a361561':{'handler':Test,'token':'kini'},
    }

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print 'requests:',self.request
        auth_code = self.get_argument('auth_code','')
        expires_in = self.get_argument('expires_in','')
        if auth_code:
            print "auth_code:%s  <br> expires_in%s"%(auth_code,expires_in)
            app_info = get_authorization_info(auth_code)
            self.set_cookie("appid",app_info['authorization_info']['authorizer_appid'])
            self.write("auth_code:%s  <br> expires_in%s"%(auth_code,expires_in))
            print 'app_info:',app_info
            self.redirect("/shop")
        else:
            self.write("Hello, world")
            
    def post(self):
        print 'requests:',self.request
        print 'requests:',self.request.body
        timestamp = self.get_argument('timestamp')
        nonce = self.get_argument('nonce')
        msg_sign = self.get_argument('msg_signature')
        from_xml = self.request.body
        component_verify_ticket = decry_component_verify_ticket(from_xml,msg_sign,timestamp,nonce)
        print 'component_verify_ticket:',component_verify_ticket
        rcon.set('component_verify_ticket',component_verify_ticket)
        component_access_token = get_access_token(component_verify_ticket)
        print 'component_access_token:',component_access_token
        rcon.set('component_access_token',component_access_token,ex=7000)
        self.finish("success")

class Login(tornado.web.RequestHandler):

    def get(self):
        component_access_token = rcon.get('component_access_token')
        pre_auth_code = get_pre_auth_code(component_access_token)
        self.render("auth.html",appid=appid,host=host,pre_auth_code=pre_auth_code)

class SnsInfo(tornado.web.RequestHandler):
    def get(self):
        print 'requests:',self.request
        code = self.get_argument('code')
        stat = self.get_argument('state')
        res = get_web_access_token('wx86fed2909860741b',code)
        print 'access token info:',res
        access_token = res['access_token']
        openid = res['openid']
        sns_info = get_snsapi_userinfo(access_token,openid,'zh_CN')
        print 'sns_info:',sns_info
        tmp="""
        <html>
        <body>
        <h1>%s</h1>
        <h2>%s</h2>
        <img src="%s" />
        <p>%s</p>
        <p>%s</p>
        </body>
        </html>
        """%(sns_info['nickname'],sns_info['openid'],sns_info['headimgurl'],sns_info['country'],sns_info)
        self.finish(tmp)

        
class Shop(WXHandler):

    def get(self):
        shop_id = self.get_argument('shop_id','')
        appid = self.get_argument('appid')
        print 'appid:',appid
        print 'shop_id:',shop_id
        ainfo = rcon.get(appid)
        print 'ainfo:',ainfo
        ainfo = json.loads(ainfo)
        self.render("addshop.html",ainfo=ainfo,sinfo={})

    def post(self):
        shop_id = self.get_argument('shop_id')
        appid = self.get_argument('appid')
        name = self.get_argument('name')
        address = self.get_argument('address')
        longitude = float(self.get_argument('longitude'))
        latitude = float(self.get_argument('latitude'))
        data = {
                'name':name,
                'address':address,
                'location':[longitude,latitude],
                }
        if shop_id:
            con.wxshop.update({'_id':ObjectId(shop_id)},{'$set':data}) 
        else:
            appinfo = json.loads(rcon.get(self.appid))
            data['create_time'] = time.time()
            data['appid'] = self.appid
            data['app_name'] = appinfo['authorizer_info']['nick_name']
            con.wxshop.insert(data) 
        self.redirect("/shoplist?appid=%s"%appid)


class ShopMap(tornado.web.RequestHandler):

    def get(self):
        shop_id = self.get_argument('shop_id')
        print 'shop_id:',shop_id
        shop = con.wxshop.find_one({'_id':ObjectId(shop_id)})
        print 'shop:',shop
        self.render('shopmap.html',shop=shop)

class ShopList(tornado.web.RequestHandler):
    """
    店铺列表
    """
    def get(self):
        appid = self.get_argument('appid')
        shoplist = con.wxshop.find({'appid':appid})
        self.render("shoplist.html",shoplist=shoplist,appid=appid)

class wxtest(tornado.web.RequestHandler):
    def get(self):
        print 'requests:',self.request
        self.render('wxtest.html')


app_settings = { 'debug':True,
                 'autoreload':True,
                 'template_path':"template",
}
application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/.*/callback", www),
    (r"/component_verify_ticket", MainHandler),
    (r"/wxtest", wxtest),
    (r"/auth", Login),
    (r"/shop", Shop),
    (r"/shoplist", ShopList),
    (r"/shopmap", ShopMap),
    (r"/snsapi_userinfo", SnsInfo),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {"path": "static"})
],**app_settings)

if __name__ == "__main__":
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()
