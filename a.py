#!/usr/bin/env python
#-*- encoding:utf-8 -*-
import requests
import json

appid = 'wx73b4ffb0cd067e8f'
appsecret = '0c79e1fa963cd80cc0be99b20a18faeb'

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




if __name__ == '__main__':
    component_access_token = get_access_token('NSkFDXxffE9989504VpMBJiAISUBJRzOLlqzUQFKlxYm6Ie62gbyM-ZjR91tbhoolxOhvOSvdw2JT_8TETPxEg')
    print get_pre_auth_code(component_access_token)
