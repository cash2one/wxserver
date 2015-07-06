#!/usr/bin/env python
#-*- encoding:utf-8 -*-
import requests
import json
import hashlib

appid = 'wx8e080139ced94edd'
appsecret = '0c79e1fa963cd80cc0be99b20a18faeb'
component_access_token = '4zA58BCCeQ9k7SmyFem6hrEZ4e2gU5-wpIhvodFAx7GQZ0DtfhrxCcsIR_GerVv9WOYk9Ovxy2kQg_0igzV655Z1-TNeoKzC3COJ5HLQrf0'

def get_jsapi_ticket(auth_token):
    """
    获取jsapi ticket
    """
    ticket_url = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi"%auth_token
    res = requests.get(ticket_url)
    return res.json()

def signature_js(jsapi_ticket):
    """
    
    """
    noncestr = '47engYD33OfURgI2'
    timestamp=1423817458
    arg_list = 'jsapi_ticket=%s&noncestr=%s&timestamp=1423817458&url=http://weixin.liuliu.co/wxtest'%(
            jsapi_ticket,
            noncestr,
            )
    print 'arg_list:',arg_list
    signature_sha = hashlib.sha1(arg_list).hexdigest()
    return signature_sha

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
    return r.json()['pre_auth_code']

def get_authorization_info(auth_code):
    """
    授权码换取公众号的授权信息
    """
    url = "https://api.weixin.qq.com/cgi-bin/component/api_query_auth?component_access_token=%s"%(component_access_token)
    data=  {
            'component_appid':appid,
            'authorization_code':auth_code,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    return r.json()
    
def reflush_authorizer_access_token(auth_appid,refresh_token_value):
    """
    获取（刷新）授权公众号的令牌
    @authorizer_refresh_token
    """
    url = "https://api.weixin.qq.com/cgi-bin/component/api_authorizer_token?component_access_token=%s"%component_access_token
    data = {
            "component_appid":appid,
            "authorizer_appid":auth_appid,
            "authorizer_refresh_token":refresh_token_value,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    return r.json()

def get_authorizer_account_info(auth_appid):
    """
    获取授权方的账户信息
    该API用于获取授权方的公众号基本信息，包括头像、昵称、帐号类型、认证类型、微信号、原始ID和二维码图片URL。
    需要特别记录授权方的帐号类型，在消息及事件推送时，对于不具备客服接口的公众号，需要在5秒内立即响应；而若有客服接口，则可以选择暂时不响应，而选择后续通过客服接口来发送消息触达粉丝。
    """
    url = "https://api.weixin.qq.com/cgi-bin/component/api_get_authorizer_info?component_access_token=%s"%component_access_token
    data = {
            "component_appid":appid,
            "authorizer_appid":auth_appid,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    return r.json()

def get_authorizer_option(auth_appid,option_name):
    """
    获取授权方的选项设置信息
    该API用于获取授权方的公众号的选项设置信息，如：地理位置上报，语音识别开关，多客服开关。注意，获取各项选项设置信息，需要有授权方的授权，详见权限集说明。
    """
    url = "https://api.weixin.qq.com/cgi-bin/component/api_get_authorizer_option?component_access_token=%s"%component_access_token
    data = {
            "component_appid":appid,
            "authorizer_appid":auth_appid,
            "option_name":option_name,
            }
    r = requests.post(url,data=json.dumps(data),allow_redirects=True)
    print r.text
    #return r.json()

def get_web_access_token(aid,code):
    """
    通过代替服务号获取到的网页授权code来申请网页授权的access token
    """
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






if __name__ == '__main__':
    pass
    #print get_access_token('9A3_J1TqonBH2rRskyANvgj9QwUG3SW3U09ZwYnEBhrYrPR2Ty7LKbrjrJR1skuHDLV_8pq_gXfPvFhm7Eh4AQ')
    #print get_pre_auth_code(component_access_token)
    print get_authorization_info('')
    #print reflush_authorizer_access_token('wxb8987f3d8ae92870','KvrAMRxFa6pps8_4xVYvOTOpsP4zRUcBJVwRK_QNEUA')
    #print get_authorizer_account_info('wx5d3a0689f3a6bcb5')
    #print get_authorizer_option('wxb8987f3d8ae92870','location_report')
    #print get_jsapi_ticket('zbeL_WZMFNGkdT1cLEnTiGb_1iNMZWYN3VByFhws_LuD-_qC3Bqid0KwcWnJKJYa84LeW_hw8d-NUFyzLvRTpAXw2d2OdFANBX_Fyy51lWUR6fJgKON_0lQ_3n09CRDv')
    #print signature_js('52Tw1_qSfGvjmabRE6VHqXFzejXMrYHoAHqKOT5FwBQzz2VqN24i0MwT1jYaMYItbiL_WMRi19GVpNIKTwHAsw')
    #get_web_access_token('wx5d3a0689f3a6bcb5','001aa68ae4fac0bd6f6e64d445e9f5c5')
    #print get_snsapi_userinfo('OezXcEiiBSKSxW0eoylIeAbG1YtjO5NzZDGhcS5YSI4YlsYGuts8NjztUjq2Lr-RVZb1vC096TxVsdMO4rOrHPvhb3uRrYqMu1_4tA6g0GZRtU8Uds5JbsVwbf6h1XEMLJMekSApT7rppkRfZPh0R7dTFyRjvVvm166bPnQn5Dw','o73HYs4n5S_Y9GZXVv2kvXwuh3zU',lang='zh_CN')

