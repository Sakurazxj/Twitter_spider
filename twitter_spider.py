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


def driver_get():
    # chromedriver连接，最大化页面
    global driver
    driver = webdriver.Chrome()
    driver.maximize_window()
    print("爬虫出发...")

def driver_spider():

    # 下面的代码用来进入用户主页，对个人信息、历史推文、关注的人和粉丝爬取
    global username
    click_wrong_cnt = 0
    username = "bbcchinese"
    url = "https://www.twitter.com/" + username
    driver = webdriver.Chrome()
    driver.get(url)
    driver.maximize_window()
    handle = driver.current_window_handle


    """# 爬昵称
    nk = driver.find_elements_by_xpath("//a[@class = 'ProfileHeaderCard-nameLink u-textInheritColor js-nav']")
    if len(nk) > 0:
        nickname = nk[0].get_attribute("textContent")
    else:
        nickname = "None"

    # 爬简介
    if len(driver.find_elements_by_xpath("//p[@class='ProfileHeaderCard-bio u-dir']")) > 0:
        introduction = driver.find_elements_by_xpath("//p[@class='ProfileHeaderCard-bio u-dir']")[
            0].get_attribute("textContent")
    else:
        introduction = "None"
    # 爬注册地
    if len(driver.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']")) > 0:
        if "</a>" in driver.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']//span")[
            1].get_attribute("outerHTML"):
            reg_place = driver.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']//a")[
                0].get_attribute("textContent")
        else:
            reg_place = driver.find_elements_by_xpath("//*[@class='ProfileHeaderCard-location ']//span")[
                1].get_attribute("textContent").strip()
    else:
        reg_place = "None"
    # 爬注册时间
    if len(driver.find_elements_by_xpath("//*[@class='ProfileHeaderCard-joinDate']//span")) > 1:
        reg_times = driver.find_elements_by_xpath("//*[@class='ProfileHeaderCard-joinDate']//span")
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
    # 对个人页面向下加载k次
    k = 3  # 次数
    m = 10000  # 不用动，滚轴的参数
    while (k > 0):
        js = "var q=document.documentElement.scrollTop="
        js = js + str(m)
        driver.execute_script(js)
        time.sleep(1.5)
        k -= 1
        m += 10000
    js = "document.documentElement.scrollTop=300"
    driver.execute_script(js)
    xpath = "//div[@data-screen-name='%s']" % username
    content_add = []
    cnt = len(driver.find_elements_by_xpath(xpath))
    i = cnt
    print(cnt)
    wrong_cnt = 0
    while i > 0:
        if wrong_cnt > 4:
            print("超出错误次数上限，此人跳过")
            break
        one = driver.find_elements_by_xpath(xpath)[cnt - i]
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

        try:
            content[0].click()

            # 点开之后睡，等待爬地址和关闭
            time.sleep(1.5)

            # 如果页面变了则进行下述处理
            if driver.current_url != url and "status" not in driver.current_url:
                print(driver.current_url)
                driver.close()
                driver = webdriver.Chrome()
                driver.get(url)
                driver.maximize_window()
                print("页面跳出，回退")
                time.sleep(2)
                # 对个人页面向下加载k次
                k = 3  # 次数
                m = 10000  # 不用动，滚轴的参数
                while (k > 0):
                    js = "var q=document.documentElement.scrollTop="
                    js = js + str(m)
                    driver.execute_script(js)
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
                    driver.find_elements_by_xpath("//*[@class='PermalinkProfile-dismiss modal-close-fixed']")[
                        0].click()  # 点关闭
                except:
                    print("点击错误")
            print("这条点击错误：" + tweet_content)
            print(e)
            add = {"tweet_time": tweet_time, "tweet_place": "Wrong",
                   "tweet_content": tweet_content}  # 插入每个推文的时间，地点，内容
            content_add.append(add)
            continue

        cnt2 = len(driver.find_elements_by_xpath("//a[@class='u-textUserColor js-nav js-geo-pivot-link']"))
        if cnt2 > 0:
            tweet_place = driver.find_elements_by_xpath("//a[@class='u-textUserColor js-nav js-geo-pivot-link']")[
                0].get_attribute("textContent")
        else:
            tweet_place = "None"  # 地点若没有则为None
        try:
            driver.find_elements_by_xpath("//*[@class='PermalinkProfile-dismiss modal-close-fixed']")[0].click()  # 点关闭
        except:
            print("点击错误")

        handles = driver.window_handles
        if len(handles) > 1:
            driver.switch_to.window(handles[1])
            driver.close()
            driver.switch_to.window(handle)
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

    user_set.insert(
        {"username": username, "nickname": nickname, "introduction": introduction, "place": reg_place, "time": reg_time,
         "content": content_add})
    username_set.update_many({'username': username}, {'$set': {'ok': 'yes'}})"""

    # 下面的代码用来登录然后爬取粉丝和关注的人的username
    login_name = driver.find_element_by_name("session[username_or_email]")
    login_name.send_keys("Sakuradyz")
    login_password = driver.find_element_by_name("session[password]")
    login_password.send_keys("zy199622")
    button = driver.find_element_by_xpath(
            "//*[@class='EdgeButton EdgeButton--primary EdgeButton--medium submit js-submit']")
    time.sleep(3)
    button.click()
    time.sleep(3)
    """#打开关注的人网页
    url = "https://twitter.com/" + username + "/following"
    driver.get(url)
    driver.maximize_window()
    # 对页面向下加载k次
    k = 3  # 次数
    m = 10000  # 不用动，滚轴的参数
    while (k > 0):
        js = "var q=document.documentElement.scrollTop="
        js = js + str(m)
        driver.execute_script(js)
        time.sleep(2)
        k -= 1
        m += 10000

    following_names = driver.find_elements_by_xpath("//b[@class='u-linkComplex-target']")
    for i in following_names:
        print(i.get_attribute('textContent'))
        if(i.get_attribute("textContent") == username):
            continue
        #先将关注的人与user的关系存进去，默认为没有他的信息
        username_set.insert_one({"username": i.get_attribute('textContent'), "ok": "no",
                                 "isFollower": "none","isFollowee": "yes",
                                 "follower_name": username,"followee_name": "none"})
        #查找是否已经爬取了他的信息
        username_find = {"username": i.get_attribute('textContent'), "ok": "yes"}
        result = []
        for k in username_set.find(username_find):
            result.append(k)
        if len(result) > 0:
            print("%-20s" % i.get_attribute('textContent') + "信息已有")
            try:
                username_set.update_many({'username': i.get_attribute('textContent')}, {'$set': {'ok': 'yes'}})
                print("更新成功")
            except:
                print("更新未成功")
            continue"""

    # 打开粉丝网页
    url = "https://twitter.com/" + username + "/followers"
    driver.get(url)
    driver.maximize_window()
    # 对页面向下加载k次
    k = 3  # 次数
    m = 10000  # 不用动，滚轴的参数
    while (k > 0):
        js = "var q=document.documentElement.scrollTop="
        js = js + str(m)
        driver.execute_script(js)
        time.sleep(2)
        k -= 1
        m += 10000

    follower_names = driver.find_elements_by_xpath("//b[@class='u-linkComplex-target']")
    for i in follower_names:
        print(i.get_attribute('textContent'))
        if (i.get_attribute("textContent") == username):
            continue
        # 先将关注的人与user的关系存进去，默认为没有他的信息
        username_set.insert_one({"username": i.get_attribute('textContent'), "ok": "no",
                                     "isFollower": "yes", "isFollowee": "none",
                                     "follower_name": "none", "followee_name": username})
        # 查找是否已经爬取了他的信息
        username_find = {"username": i.get_attribute('textContent'), "ok": "yes"}
        result = []
        for k in username_set.find(username_find):
            result.append(k)
        if len(result) > 0:
            print("%-20s" % i.get_attribute('textContent') + "信息已有")
            try:
                username_set.update_many({'username': i.get_attribute('textContent')}, {'$set': {'ok': 'yes'}})
                print("更新成功")
            except:
                print("更新未成功")
            continue






if __name__ == '__main__':
    db_connect()

    driver_spider()
