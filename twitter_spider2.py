from selenium import webdriver
from pymongo import MongoClient

import time
def db_connect():
    # 连接至数据库
    global user_set, username_set, conn
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn.twitter
    user_set = db.user  # 用户数据
    username_set = db.username  # 用户名数据
    print("数据库连接成功...")
