#!/usr/bin/env python
#-*- encoding:utf-8 -*-
import tornado.ioloop
import tornado.web
import requests
import json
import redis
from  wxdecry.WXBizMsgCrypt import WXBizMsgCrypt
from bs4 import BeautifulSoup as bs4

rcon = redis.StrictRedis(host='localhost', port=6379, db=1)

appid = 'wx8e080139ced94edd'
appsecret = '0c79e1fa963cd80cc0be99b20a18faeb'
token='kini'
encodingAESKey = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
host="wxtest.oookini.com"

def get_authorizer_account_info(auth_appid):
    """
    获取授权方的账户信息
    该API用于获取授权方的公众号基本信息，包括头像、昵称、帐号类型、认证类型、微信号、原始ID>    和二维码图片URL。
    需要特别记录授权方的帐号类型，在消息及事件推送时，对于不具备客服接口的公众号，需要在5秒>    内立即响应；而若有客服接口，则可以选择暂时不响应，而选择后续通过客服接口来发送消息触达粉丝。 88     """
    url = "https://api.weixin.qq.com/cgi-bin/component/api_get_authorizer_info?component_acc    ess_token=%s"%component_access_token
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
    return r.json()

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
    soup = bs4(decryp_xml,'xml')
    component_verify_ticket = soup.ComponentVerifyTicket.text
    return component_verify_ticket

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print 'requests:',self.request
        auth_code = self.get_argument('auth_code','')
        expires_in = self.get_argument('expires_in','')
        if auth_code:
            print "auth_code:%s  <br> expires_in%s"%(auth_code,expires_in)
            self.write("auth_code:%s  <br> expires_in%s"%(auth_code,expires_in))
            app_info = get_authorization_info(auth_code)
            print 'app_info:',app_info
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
        self.write("success")

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
    (r"/component_verify_ticket", MainHandler),
    (r"/wxtest", wxtest),
    (r"/auth", Login),
    (r"/snsapi_userinfo", SnsInfo),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {"path": "static"})
],**app_settings)

if __name__ == "__main__":
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()
