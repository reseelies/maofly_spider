import os
import random
import requests
import time
from itertools import count
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class paramete:  # 参数
    def __init__(self, url=''):
        self.header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
            "authority": "www.maofly.com",
            "referer": url,
            # "":"",
            # "":""
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
        # self.driver.set_page_load_timeout(30)
        # self.driver.set_script_timeout(30)
        # 这两种设置都进行才有效，等学过之后再用吧

    def close(self):
        self.driver.close()


class Page_info:  # 获取网页信息的类，这是我目前写过的最能用的类
    def __init__(self, html):
        self.soup = bs(html, "html.parser")
        self.tab_panes = self.soup.find("div", {"id": "comic-book-list"}).find_all("div", {"class": "tab-pane"})
        self.name = self.soup.h1.string
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


def download(chapts, path):
    driver = Webdriver(True).driver
    chapt_page_num = 0
    for chapt in chapts:
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
            while True:
                try:
                    img_url = div_all.find_element(By.TAG_NAME, "img").get_attribute('src')
                except:
                    time.sleep(0.2)
                    continue
                else:
                    break
            r = requests.get(img_url, headers=header)
            if r.status_code != 200:
                break
            with open(path_chapt + "/{:0>3d}.".format(i) + img_url.split('.')[-1],
                      "wb") as fo:  # path + "/{:0>3d}".format() + img.split('.')[-1]
                fo.write(r.content)
            print("\r已完成 {} 页".format(i), end='')

        # chapts.pop(chapt)
        print("\r{} 已完成，共 {} 页".format(chapt_name, i - 1))
        chapt_page_num += i - 1
        if i > 1000:
            print("请检查本章页数")
    driver.close()
    return chapt_page_num


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
            start_chapt = eval(start_chapt) - 1
            end_chapt = eval(end_chapt)
            if end_chapt == -1:
                chapt_slice = chapts[start_chapt:]
                # chapt_page_num = download(chapts[start_chapt:], path)
            elif end_chapt < -1:
                chapt_slice = chapts[start_chapt: end_chapt + 1]
                # chapt_page_num = download(chapts[start_chapt: end_chapt + 1], path)
            else:
                chapt_slice = chapts[start_chapt: end_chapt]
                # chapt_page_num = download(chapts[start_chapt: end_chapt], path)
            test_code = 0
            while True:
                try:
                    chapt_page_num = download(chapt_slice, path)
                except:
                    test_code += 1
                    time.sleep(1)
                    if test_code > 10:
                        print("出现异常")
                        break
                    continue
                else:
                    break
            print("\n已完成,共计{}页,共耗时{:.2f}s\n".format(chapt_page_num, time.time() - start_time))


if __name__ == "__main__":
    url = input("请输入漫画页URL: ").strip()
    main(url)
