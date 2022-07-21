# 这是一个多线程版本的，如果爆了，我也不知道该咋办了
import os
import random
import requests
import time
import threading
from itertools import count
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class MyError(Exception):
    def __init__(self, msg):
        super().__init__(self)
        self.message = msg

    def __str__(self):
        return self.message


class paramete:  # 参数
    def __init__(self, url=''):
        self.header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
            "authority": "www.maofly.com",
            "referer": url,
        }
        # self.path


class Webdriver:  # selenium的driver类
    def __init__(self, show=False):
        if show:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            self.driver = webdriver.Chrome(chrome_options=chrome_options)
        else:
            self.driver = webdriver.Chrome()
        self.driver.set_page_load_timeout(300)
        self.driver.set_script_timeout(300)
        # 这两种设置都进行才有效，等学过之后再用吧

    def close(self):
        self.driver.close()


class Page_info:  # 获取网页信息的类，这是我目前写过的最能用的类
    def __init__(self, html):
        self.soup = bs(html, "html.parser")
        self.tab_panes = self.soup.find("div", {"id": "comic-book-list"}).find_all("div", {"class": "tab-pane"})
        self.name = self.soup.h1.string
        for i in [i for i in "\\  /  :  *  ?  \"  <  >  |".split()]:
            self.name = self.name.replace(i, '_')
        pass

    def get_tab(self):
        tab_ls = []
        for tab_pane in self.tab_panes:
            tab = tab_pane.h2.string
            tab_ls.append(tab)
        self.tab = tab_ls
        return self.tab

    def get_chapt(self, num):
        chapts = self.tab_panes[num].find("ol").find_all("li")
        self.chapts = []
        for chapt in chapts:
            a = chapt.a
            self.chapts.append([a.string, a.attrs["href"]])
        return self.chapts[::-1]


def exchange(chapt, path):
    test_code = 0
    while True:
        driver = Webdriver(True).driver
        try:
            download(driver, chapt, path)
        except MyError as e:
            print(chapt[0], e)
            test_code += 1
            if test_code > 100:
                break
            continue
        except:
            test_code += 1
            if test_code > 100:
                print(f"\r{chapt[0]} 出现问题")
                break
            continue
        else:
            break
        finally:
            driver.close()


def multi_thread(chapts, path):
    threads = []
    for chapt in chapts:
        threads.append(threading.Thread(target=exchange, args=(chapt, path,)))
    for thread in threads:
        time.sleep(1+random.random())
        thread.start()
    for thread in threads:
        thread.join()
    print("多线程完毕，真他妈的吊")


def download(driver, chapt, path):
    global page
    # driver = Webdriver(True).driver
    # chapt_page_num = 0
    chapt_name, chapt_url = chapt
    path.path2 = chapt_name
    path_chapt = "./" + path.path1 + '/' + path.path2
    if not os.path.exists(path_chapt):
        os.mkdir(path_chapt)
    header = paramete(chapt_url).header
    url = chapt_url.replace(".html", "_{}.html")
    for i in count(start=1):
        path_img_1 = path_chapt + "/{:0>3d}.jpg".format(i)
        path_img_2 = path_chapt + "/{:0>3d}.png".format(i)
        if os.path.exists(path_img_1) or os.path.exists(path_img_2):
            continue
        driver.get(url.format(i))
        div_all = driver.find_element(By.ID, "all")
        waiting_times = 1500
        while True:
            try:
                img_url = div_all.find_element(By.TAG_NAME, "img").get_attribute('src')
            except:
                if waiting_times > 0:
                    waiting_times -= 1
                    time.sleep(0.2)
                    continue
                else:
                    raise MyError("漫画图片加载时间异常")
            else:
                break
        r = requests.get(img_url, headers=header)
        if r.status_code != 200:
            break
        with open(path_chapt + "/{:0>3d}.".format(i) + img_url.split('.')[-1],
                  "wb") as fo:  # path + "/{:0>3d}".format() + img.split('.')[-1]
            # chapt_page_num += 1
            page += 1
            fo.write(r.content)
        print(f"\r{chapt_name} 已完成 {i} 页", end='')

    print(f"\r{chapt_name} 已完成，共 {i - 1} 页")
    if i > 1000:
        print("请检查本章页数")
    # driver.close()
    # return chapt_page_num


def main(url):
    header = paramete().header
    path = paramete()
    r = requests.get(url, headers=header)
    r.encoding = r.apparent_encoding
    if not r.status_code == 200:
        print("这里有亿点儿问题")
        return 0
    else:
        print("漫画信息提取正常")
        page_info = Page_info(r.text)
        path.path1 = page_info.name
        path_name = './' + path.path1
        if not os.path.exists(path_name):
            os.mkdir(path_name)
        print(path.path1)
        print(page_info.get_tab())
        if len(page_info.get_tab()) == 1:
            num = '0'
        else:
            num = input("请输入想爬取的tab序号(从0开始，多个序号用','隔开)：")
        for i in num.split(','):
            start_time = time.time()
            chapts = page_info.get_chapt(eval(i))
            [print(i) for i in chapts]
            # print(chapts)
            start_chapt, end_chapt = input("请输入起始及结束章节(第一章为1，最后一章为-1，以','隔开)：").split(',')
            start_chapt = eval(start_chapt) - 1 if eval(start_chapt)>0 else eval(start_chapt)
            end_chapt = eval(end_chapt)
            if end_chapt == -1:
                chapt_slice = chapts[start_chapt:]
            elif end_chapt < -1:
                chapt_slice = chapts[start_chapt: end_chapt + 1]
            else:
                chapt_slice = chapts[start_chapt: end_chapt]
            multi_thread(chapt_slice, path)

            print(f"\n已完成,共获取{page}页,共耗时{time.time() - start_time:.2f}s")


if __name__ == "__main__":
    url = input("请输入漫画页URL: ").strip()
    page = 0
    main(url)

# https://www.maofly.com/author/1705.html 不可直接用 板垣惠介
# https://www.maofly.com/author/415.html 不可直接用 黄玉郎
# https://www.maofly.com/author/102.html 手冢治虫
# https://www.maofly.com/manga/4598.html 鬼太郎
# https://www.maofly.com/manga/13879.html 鬼太郎妖怪千物语
# https://www.maofly.com/author/1316.html 矢吹健太朗
# https://www.maofly.com/manga/19599.html 希德尼娅的骑士
# https://www.maofly.com/manga/844.html 葬送的芙莉莲
# https://www.maofly.com/manga/11400.html 功夫旋风儿
# https://www.maofly.com/manga/10226.html 家庭教师
# https://www.maofly.com/author/15145.html タイザン5
# https://www.maofly.com/manga/21947.html 超能力美空
# https://www.maofly.com/manga/36790.html 超能力少女




