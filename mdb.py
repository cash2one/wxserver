#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import redis
#from gevent import monkey
#monkey.patch_all()
from pymongo import MongoClient

#mongodb global connection
con = None
liuliu = None
#redis global connection
rcon = None
bcon = None

def mongo_init(db_para):
    """
    初始化mongodb """
    global con,liuliu,bcon
    mclient = MongoClient(host = db_para['host'],port=db_para['port']) 
    con = mclient[db_para['dbname']]
    #bcon = mclient[db_para['backend']]

def find(spec,**kwargs):
    """
    查询
    """
    pass

def redis_init(redis_para):
    """
    初始化redis
    """
    global rcon
    rcon = redis.StrictRedis(host=redis_para['host'], port=redis_para['port'], db=redis_para['db'])

def init():
    import settings
    mongo_init(settings.get('mongo_database'))
    redis_init(settings.get('redis_para'))

if __name__ == '__main__':
    init()
    print rcon.get("%s_uid"%'zso6voe4ee610fezi2rq5gjq3wed8tuk')
