from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.support.select import Select
from pymongo import MongoClient
import datetime
import time
import winsound
import re
import pygame
def date_input():
    # 每次只爬一天，先爬这一天所有用户的用户名，保存在数据库内，然后再爬每个用户
    global since, now, until
    since = input("请输入爬取起始时间(例:2019-03-03):")
    now = datetime.datetime.now()
    now.strftime('%Y-%m-%d')
    delta = datetime.timedelta(days=1)
    since_max = now - delta
    try:
        d1 = datetime.datetime.strptime(since, '%Y-%m-%d')
    except:
        print("输入日期有误!")
        exit()
    if d1 > since_max:
        print("日期超过最大限制!")
        exit()
    until = since + delta
    until = until.strftime('%Y-%m-%d')
    since = since.strftime('%Y-%m-%d')
    print("爬取至" + until)
    print("爬虫启动中...")
def db_connect():
    # pattern = re.compile(r"#((?!#)(?!,)(?! ).)*$")
    # pattern2 = re.compile(r".com$")
    # print(re.findall(pattern, "asaslkdf ,dfawij,,awef#aw,ea,we,f,a ,a,, ,, ,faw #jhu123"))
    # print(re.findall(pattern2, "tian.com sdjfiawef.com"))
    # 连接至数据库
    global user_set, username_set, conn, db
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn.mydb
    user_set = db.user_set  # 用户数据
    username_set = db.username_set  # 用户名数据
    print("数据库连接成功...")

def driver_get():
    # chromedriver连接，最大化页面
    global driver
    driver = webdriver.Chrome()
    driver.maximize_window()
    print("爬虫出发...")

def driver_search():
    # 下面的代码用来控制twitter的高级搜索
    driver.get("https://www.twitter.com/search-advanced")
    Select(driver.find_element_by_xpath("//*[@class='t1-select']")).select_by_visible_text("中文 (中文)")
    button = driver.find_elements_by_xpath("//*[@class='search advanced-search']//button")
    input_since = driver.find_element_by_name("since")
    input_since.send_keys(since)
    input_until = driver.find_element_by_name("until")
    input_until.send_keys(until)
    time.sleep(3)
    button[0].click()
    time.sleep(3)

def username_get():
    global usernames, user_cnt
    #下面的代码是用来控制滚动条的，k是滚动次数
    k = 5
    m = 10000
    r1 = 0
    cnt_page = 1
    while (True):
        js = "var q=document.documentElement.scrollTop="
        js = js + str(m)
        driver.execute_script(js)
        r = driver.execute_script("return document.documentElement.scrollTop")
        print("加载第"+str(cnt_page)+"页")
        if r == r1:
            break
        cnt_page += 1
        r1 = r
        time.sleep(2)
        # k -= 1
        m += 10000

    # 下面几行是收集此页所有的用户名，收集所有带有<b>标签的，但是有可能有重复的，需要判断重复
    usernames = driver.find_elements_by_xpath("//*[@class='username u-dir u-textTruncate']//b")
    user_cnt = 0
    user_have_cnt = 0
    for i in usernames:
        username_find = {"username": i.get_attribute('textContent')}
        result = []
        for k in username_set.find(username_find):
            result.append(k)
        if len(result) > 0:
            print("%-20s" % i.get_attribute('textContent') + "信息已有")
            user_have_cnt += 1
            continue
        print(i.get_attribute('textContent'))
        username_set.insert_one({"username": i.get_attribute('textContent'), "time_since": since, "ok": "no"})
        user_cnt += 1
    print("本次共获取了" + str(user_cnt) + "个用户")
    print("获取到了"+str(user_have_cnt)+"个重复用户")
    time.sleep(3)
    try:
        driver.close()
    except:
        pass

def content_get():
    global username
    print("*****开始获取某日用户的历史推文*****")
    while(True):
        get_since = input("请输入日期(例:2019-03-03):")
        try:
            d1 = datetime.datetime.strptime(get_since, '%Y-%m-%d')
            break
        except:
            print("输入日期有误!")
            continue

    # ok选项是这个用户是否被爬取过，被爬取过的为yes，否则为no
    username_find = {"time_since": get_since,"ok": "no"}
    result = []
    for i in username_set.find(username_find):
        result.append(i['username'])

    if len(result) == 0:
        print("没有该日的用户数据")
        try:
            driver.close()
        except:
            pass
        exit()
    print("准备爬取用户共"+str(len(result))+"个")
    print("开始!")
    click_wrong_cnt = 0
    user_cnt1 = 0
    for username in result:
        now2 = datetime.datetime.now()
        # 这里是检查数据库里是否有这个用户的历史推文了
        print("进度为%.5f%%" % (user_cnt1 * 100 /len(result)))
        user_find = {"username": username}
        result2 = []
        for i in user_set.find(user_find):
            result2.append(i)
        if len(result2) > 0:
            print("%-20s" % username + "信息已有")
            try:
                username_set.update_many({'username': username}, {'$set': {'ok': 'yes'}})
                print("更新成功")
            except:
                print("更新未成功")
            continue
        url = "https://twitter.com/" + username
        driver2 = webdriver.Chrome()
        driver2.get(url)
        driver2.maximize_window()
        handle = driver2.current_window_handle
        # 对个人页面向下加载k次
        k = 3  # 次数
        m = 10000  # 不用动，滚轴的参数
        while (k > 0):
            js = "var q=document.documentElement.scrollTop="
            js = js + str(m)
            driver2.execute_script(js)
            time.sleep(1.5)
            k -= 1
            m += 10000

        # 爬昵称
        if len(driver2.find_elements_by_xpath("//a[@class = 'ProfileHeaderCard-nameLink u-textInheritColor js-nav']")) > 0:
            nickname = driver2.find_elements_by_xpath("//a[@class = 'ProfileHeaderCard-nameLink u-textInheritColor js-nav']")[0].get_attribute("textContent")
        else:
            nickname = "None"

        # 爬简介
        if len(driver2.find_elements_by_xpath("//p[@class='ProfileHeaderCard-bio u-dir']")) > 0:
            introduction = driver2.find_elements_by_xpath("//p[@class='ProfileHeaderCard-bio u-dir']")[0].get_attribute(
                "textContent")
        else:
            introduction = "None"
        # 爬注册地
        if len(driver2.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']")) > 0:
            if "</a>" in driver2.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']//span")[
                1].get_attribute("outerHTML"):
                reg_place = driver2.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']//a")[
                    0].get_attribute("textContent")
            else:
                reg_place = driver2.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']//span")[
                    1].get_attribute("textContent").strip()
        else:
            reg_place = "None"
        # 爬注册时间
        if len(driver2.find_elements_by_xpath("//*[@class='ProfileHeaderCard-joinDate']//span")) > 1:
            reg_times = driver2.find_elements_by_xpath("//*[@class='ProfileHeaderCard-joinDate']//span")
            for i in reg_times:
                if i.get_attribute("class") == "ProfileHeaderCard-joinDateText js-tooltip u-dir":
                    reg_time = i.get_attribute("title")
        else:
            reg_time = "None"
        print("***************************************")
        print("用户昵称：" + nickname)
        print("用户介绍：" + introduction)
        print("用户注册地点：" + reg_place)
        print("用户注册时间：" + reg_time)




        # 下面的代码是用来获取每个用户的历史推文的
        # 这里的问题是不能使用换driver，如果driver一旦切换，之前的usernames的数据就没了
        # 所以新思路是开一个新页面或者开一个新的driver
        print("用户历史推文：")
        js = "document.documentElement.scrollTop=300"
        driver2.execute_script(js)
        xpath = "//div[@data-screen-name='%s']" % username
        content_add = []
        cnt = len(driver2.find_elements_by_xpath(xpath))
        i = cnt
        print(cnt)
        wrong_cnt = 0
        while i > 0:
            if wrong_cnt > 4:
                print("超出错误次数上限，此人跳过")
                break
            one = driver2.find_elements_by_xpath(xpath)[cnt - i]
            # 下面这行非常重要，过滤掉那些没有<p>标签的但是data-screen-name标签与用户名相同的用户
            if "</p>" not in one.get_attribute("innerHTML"):
                i -= 1
                continue
            # click_element = one.find_elements_by_xpath(".//div[@class='ProfileTweet-action ProfileTweet-action--more js-more-ProfileTweet-actions']")[0]
            content = one.find_elements_by_xpath(
                ".//p[@class='TweetTextSize TweetTextSize--normal js-tweet-text tweet-text']")

            tweet_time = one.find_elements_by_xpath(".//a[@class='tweet-timestamp js-permalink js-nav js-tooltip']")[
                0].get_attribute("title")
            tweet_content = content[0].get_attribute("textContent")

            # 点开之前睡
            time.sleep(0.5)

            # if "</s>" in content[0].get_attribute("innerHTML"):
            #     print("有#不点击")
            #     tweet_place = "None"
            # # elif "</a>" in content[0].get_attribute("innerHTML"):
            # #     print("有链接不点击")
            # #     tweet_place = "None"
            # else:
            try:
                content[0].click()

                # 点开之后睡，等待爬地址和关闭
                time.sleep(1.5)

                # 如果页面变了则进行下述处理
                if driver2.current_url != url and "status" not in driver2.current_url:
                    print(driver2.current_url)
                    driver2.close()
                    driver2 = webdriver.Chrome()
                    driver2.get(url)
                    driver2.maximize_window()
                    print("页面跳出，回退")
                    time.sleep(2)
                    # 对个人页面向下加载k次
                    k = 3  # 次数
                    m = 10000  # 不用动，滚轴的参数
                    while (k > 0):
                        js = "var q=document.documentElement.scrollTop="
                        js = js + str(m)
                        driver2.execute_script(js)
                        time.sleep(2)
                        k -= 1
                        m += 10000
                    i -= 1
                    add = {"tweet_time": tweet_time, "tweet_place": "None",
                           "tweet_content": tweet_content}  # 插入每个推文的时间，地点，内容
                    content_add.append(add)
                    wrong_cnt += 1
                    continue
                # 如果打开了别的页面进行下述处理
            except Exception as e:
                i -= 1
                click_wrong_cnt += 1
                # click_wrong_cnt是连续出现点击错误的次数，过高可能是点开的页面没关闭
                if click_wrong_cnt > 5:
                    try:
                        driver2.find_elements_by_xpath("//*[@class='PermalinkProfile-dismiss modal-close-fixed']")[0].click()  # 点关闭
                    except:
                        print("点击错误")
                print("这条点击错误：" + tweet_content)
                print(e)
                add = {"tweet_time": tweet_time, "tweet_place": "Wrong",
                       "tweet_content": tweet_content}  # 插入每个推文的时间，地点，内容
                content_add.append(add)
                continue


            cnt2 = len(driver2.find_elements_by_xpath("//a[@class='u-textUserColor js-nav js-geo-pivot-link']"))
            if cnt2 > 0:
                tweet_place = driver2.find_elements_by_xpath("//a[@class='u-textUserColor js-nav js-geo-pivot-link']")[
                    0].get_attribute("textContent")
            else:
                tweet_place = "None"  # 地点若没有则为None
            try:
                driver2.find_elements_by_xpath("//*[@class='PermalinkProfile-dismiss modal-close-fixed']")[0].click()  # 点关闭
            except:
                print("点击错误")
            handles = driver2.window_handles
            if len(handles) > 1:
                driver2.switch_to.window(handles[1])
                driver2.close()
                driver2.switch_to.window(handle)
                print("打开了别的网页，关闭")
            i -= 1
            add = {"tweet_time": tweet_time, "tweet_place": tweet_place,
                   "tweet_content": tweet_content}  # 插入每个推文的时间，地点，内容
            content_add.append(add)

            print(tweet_content)
            print(tweet_time)
            print(tweet_place)
            if click_wrong_cnt > 0:
                click_wrong_cnt -= 1
            print("***************************************")
        user_set.insert_one({"username": username, "nickname":nickname, "introduction": introduction, "place": reg_place, "time": reg_time,
                             "content": content_add})
        user_cnt1 += 1
        if wrong_cnt > 4:
            username_set.update_many({'username': username}, {'$set': {'ok': 'wrong'}})
        else:
            username_set.update_many({'username': username}, {'$set': {'ok': 'yes'}})
        now3 = datetime.datetime.now()
        print("开始于" + now2.strftime("%Y-%m-%d %H:%M:%S"))
        print("结束于" + now3.strftime("%Y-%m-%d %H:%M:%S"))
        print("用时",now3 - now2)
        driver2.quit()


if __name__ == '__main__':
    file = r'C:\a.mp3'
    pygame.mixer.init()
    track = pygame.mixer.music.load(file)

    db_connect()
    while(True):
        choose = input("您想做什么？（1：爬取用户名列表，2：爬取某日用户推文，0：退出）：")
        if choose == '0':
            print("再见！")
            exit()
        elif choose == '1':
            try:
                date_input()
                driver_get()
                driver_search()
                username_get()
            except:
                print("出现问题！！！")
                pygame.mixer.music.play()
                time.sleep(5)
                pygame.mixer.music.stop()
        elif choose == '2':
            try:
                content_get()
            except:
                print("出现问题！！！")
                username_set.update_many({'username': username}, {'$set': {'ok': 'wrong'}})
                pygame.mixer.music.play()
                time.sleep(5)
                pygame.mixer.music.stop()
        else:
            print("输入错误！")

