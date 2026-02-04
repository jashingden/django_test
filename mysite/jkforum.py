# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 17:48:11 2020

@author: eddyteng
"""
from myapp.models import JKFPost
from myapp.models import JKFTag
from datetime import datetime, timezone, timedelta
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import os
import traceback

name_list = ["中山區.林森北路","板橋.中永和","大台北","萬華.西門町","三重.新莊"]
url_list = ["/p/type-1128-1476.html","/p/type-1128-1950.html","/p/type-1128-1949.html","/p/type-1128-1948.html","/p/type-1128-1951.html"]

home = "https://jkforum.net"
mydir = os.getcwd()+'/staticfiles/jkforum/'
mylocal = True

def parse_url(zone, url, max_count=10, times: int = 1):
    body = ""
    start_url = home + url

    # 先取得文章列表
    with sync_playwright() as playwright:
        scroll = int(max_count / 80) if max_count > 80 else 1
        post_links = parse_page(playwright, start_url, scroll)
    
    count = 0  # 搜尋文章總筆數
    match = 0  # 符合文章筆數
    find = 0   # 找到新文章筆數
    update = 0 # 更新文章內文筆數

    # 檢查是否已存在於DB
    post_list = []
    for _, link in enumerate(post_links):
        count += 1
        name = link['name']
        tid = link['tid']
        plist = JKFPost.objects.filter(tid=tid)
        if len(plist) > 0:
            p = plist[0]
            if p.is_found == True and p.name != name:
                update += 1
                p.save()
        else:
            find += 1
            post_list.append(link)
        
        # 最大處理筆數
        if count >= max_count:
            break

    # 各別取得文章內文
    with sync_playwright() as playwright:
        post_content = parse_content(playwright, post_list)

    # 處理新文章列表
    for _, link in enumerate(post_content):
        name = link['name']
        content_url = link['url']
        tid = link['tid']
        content = link['content']
        og_url, tag, price, status = handle_content(content, zone, tid, content_url, name)
        
        # 寫入DB
        p = JKFPost(tid=tid, zone=zone, name=name)
        if len(og_url) > 0:
            p.is_found = True
            p.url = og_url
            p.tag = tag
            p.price = price
        p.status = status
        p.save()
        match = match + 1 if len(og_url) > 0 else match
    return find, match, update

def get_tid(link):
    idx = link.index("thread-")
    start = idx+7
    end = link.index("-", start)
    tid = link[start:end]
    return tid

def get_title(title):
    idx = title.find(']')
    if idx > 0:
        title = title[idx+1:]
        title = title if title.find('\n') == -1 else title[0:title.find('\n')]
    return title if len(title) <= 50 else title[0:50]

def get_title2(title):
    idx = title.find('<span class="">')
    if idx > 0:
        title = title[idx+15:title.find('</span>', idx+15)]
        title = title if title.find('\n') == -1 else title[0:title.find('\n')]
    return title if len(title) <= 50 else title[0:50]

def over18(page):
    # 處理 "我已滿18歲" 的確認彈窗
    try:
        # 等待 "不再提醒" 的 checkbox 出現，最多等5秒
        page.get_by_role("checkbox", name="不再提醒").wait_for(timeout=5000)
        page.get_by_role("checkbox", name="不再提醒").check()
        page.get_by_test_id("pass-button").click()
    except Exception:
        pass

def parse_page(playwright: Playwright, start_url: str, scroll: int = 1) -> list:
    # 啟動瀏覽器，headless=False 會顯示瀏覽器畫面，方便除錯
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    # 前往目標網頁
    page.goto(start_url)
    over18(page)

    # 模擬向下捲動頁面以載入更多文章
    for _ in range(7, scroll*7):
        page.mouse.wheel(0, 1000) # 捲動距離可以依據網頁調整
        time.sleep(3) # 等待新內容載入

    # 找到所有文章的連結元素
    post_links = page.locator('a[href*="thread-"]').all()

    # 遍歷每一篇文章連結
    post_list = []
    for _, link_locator in enumerate(post_links):
        name = get_title(link_locator.inner_text().strip())
        if len(name) == 0:
            name = get_title2(link_locator.inner_html())
        href = link_locator.get_attribute("href")
        content_url = home + href
        tid = get_tid(href)
        post_list.append({'name': name, 'url': content_url, 'tid': tid})
        
    # ---------------------
    page.close()
    context.close()
    browser.close()
    return post_list

def parse_content(playwright: Playwright, post_links: list) -> list:
    # 啟動瀏覽器，headless=False 會顯示瀏覽器畫面，方便除錯
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})

    post_content = []
    for _, link in enumerate(post_links):
        name = link['name']
        content_url = link['url']
        tid = link['tid']

        # 前往目標網頁
        page = context.new_page()
        page.goto(content_url)
        over18(page)

        try:
            # 取得第一個帖子的內文
            # 使用 first 來確保只抓取到第一個符合條件的元素
            content_element = page.locator(".mb-7-5").first
            content = content_element.inner_text()
            #html = content_element.inner_html()
            ll = content_element.get_by_role("link").all()
            content = content + f"\n\n\n連結數量: {len(ll)}\n"
            for _, l in enumerate(ll):
                content = content + f"連結: {l.get_attribute('href')}\n"

            post_content.append({'name': name, 'url': content_url, 'tid': tid, 'content': content})
        except Exception:
            pass
        finally:
            page.close()
        
    # ---------------------
    context.close()
    browser.close()
    return post_content

def handle_content(content, zone, tid, content_url, name):
    txt_path = mydir+tid+'.txt'
    text = ''
    if os.path.exists(txt_path):
        text = loadHTML(txt_path)
    else:
        text = content
        saveHTML(txt_path, text)
        
    og_url = ""
    tag = ""
    price = 0
    status = 0
    if find_spa(text, name) == False:
        og_url = content_url
        tag = get_tag(text, zone)
        price = get_price(text, name)
        status = get_status(text, name)
    return og_url, tag, price, status

def find_content(tid, url, tag):
    txt_path = mydir+tid+'.txt'
    text = ''
    if os.path.exists(txt_path):
        text = loadHTML(txt_path)
    return tag in text

def find_spa(table_text, name=""):
    spa_text = ("定點","幹部","紅牌","24H")
    for t in spa_text:
        if len(name) > 0 and t in name:
            return True
        if t in table_text:
            return True
    return False

def get_tag(table_text, zone):
    tlist = JKFTag.objects.filter(zone=zone).order_by('-created_at')
    for t in tlist:
        if t.tag in table_text:
            return t.tag
    return ""

def get_price(text, name=""):
    if len(name) > 0:
        if "2000" in name or "2k" in name or "2K" in name:
            return 2000
        if "2100" in name or "2.1k" in name or "2.1K" in name:
            return 2100
        if "2200" in name or "2.2k" in name or "2.2K" in name:
            return 2200
        if "2300" in name or "2.3k" in name or "2.3K" in name:
            return 2300
        if "2400" in name or "2.4k" in name or "2.4K" in name:
            return 2400
        if "2500" in name or "2.5k" in name or "2.5K" in name:
            return 2500
        if "2600" in name or "2.6k" in name or "2.6K" in name:
            return 2600
        if "2700" in name or "2.7k" in name or "2.7K" in name:
            return 2700
        if "2800" in name or "2.8k" in name or "2.8K" in name:
            return 2800
        if "2900" in name or "2.9k" in name or "2.9K" in name:
            return 2900
        if "1900" in name or "1.9k" in name or "1.9K" in name:
            return 1900
        if "1800" in name or "1.8k" in name or "1.8K" in name:
            return 1800
        if "1700" in name or "1.7k" in name or "1.7K" in name:
            return 1700
        if "1600" in name or "1.6k" in name or "1.6K" in name:
            return 1600
        if "1500" in name or "1.5k" in name or "1.5K" in name:
            return 1500
    #table text
    if "2000" in text or "2k" in text or "2K" in text:
        return 2000
    if "2100" in text or "2.1k" in text or "2.1K" in text:
        return 2100
    if "2200" in text or "2.2k" in text or "2.2K" in text:
        return 2200
    if "2300" in text or "2.3k" in text or "2.3K" in text:
        return 2300
    if "2400" in text or "2.4k" in text or "2.4K" in text:
        return 2400
    if "2500" in text or "2.5k" in text or "2.5K" in text:
        return 2500
    if "2600" in text or "2.6k" in text or "2.6K" in text:
        return 2600
    if "2700" in text or "2.7k" in text or "2.7K" in text:
        return 2700
    if "2800" in text or "2.8k" in text or "2.8K" in text:
        return 2800
    if "2900" in text or "2.9k" in text or "2.9K" in text:
        return 2900
    if "1900" in text or "1.9k" in text or "1.9K" in text:
        return 1900
    if "1800" in text or "1.8k" in text or "1.8K" in text:
        return 1800
    if "1700" in text or "1.7k" in text or "1.7K" in text:
        return 1700
    if "1600" in text or "1.6k" in text or "1.6K" in text:
        return 1600
    if "1500" in text or "1.5k" in text or "1.5K" in text:
        return 1500
    return 0

def get_status(text, name=""):
    if len(name) > 0:
        if "90分" in name or "/90" in name:
            return 2
    #table text
    if "90分" in name or "/90" in name:
        return 2
    return 0

def saveHTML(path, html):
    file = open(path, 'w', encoding='UTF-8')
    file.write(html)
    file.close()

def loadHTML(path):
    file = open(path, 'r', encoding='UTF-8')
    lines = file.readlines()
    content = ""
    for line in lines:
        content += line
    file.close()
    return content

def deleteFiles(path):
    for file_name in os.listdir(path):
        file = path + file_name
        if (os.path.isfile(file)):
            #print('deleting file: '+file)
            os.remove(file)

def request(zone, max_count, times):
    try:
        if zone < 0 or zone >= len(name_list):
            return "", ""
        
        name = name_list[zone]
        url = url_list[zone]
        title = ''
        body = ''
        for _ in range(0, times):
            find_count, match_count, update_count = parse_url(zone, url, max_count)
            dt = datetime.now(timezone(timedelta(hours=+8)))
            p_body = name+" 找到"+str(match_count)+"筆,搜尋"+str(find_count)+"筆,更新"+str(update_count)+"筆,總共"+str(max_count)+"筆 "+dt.strftime("%c")
            body += p_body+"<br>"
        title = 'jkforum'
    except:
        title = "Server Error"
        exc = traceback.format_exc().splitlines()
        body = ""
        for e in exc:
            body += e + "<br>"
    return title, body

def select(zone, max_count):
    slist = JKFPost.objects.filter(zone=zone, is_found=True).order_by('-created_at')
    
    name = name_list[zone]
    dt = datetime.now(timezone(timedelta(hours=+8)))
    title = name+" 找到"+str(len(slist))+"筆,總共"+str(JKFPost.objects.count())+"筆 "+dt.strftime("%c")
    body = "標籤：<button onclick=\"showByStatus(1);\">保留</button> "
    body = body + "<button onclick=\"showByStatus(2);\">90幫</button> "
    tlist = JKFTag.objects.filter(zone=zone).order_by('tag')
    tag_list = []
    for t in tlist:
        tag_list.append(t.tag)
        body += "<button onclick=\"showByTag('"+t.tag+"','"+t.name+"');\">"+t.tag+"</button> "
    
    body = body + "<br><label id='show_list'>未分類/未定價</label>：<br>\r\n"
    count = 0
    for s in slist:
        if len(s.url) > 0:
            body += "<div id='"+s.tid+"' class='row'"
            tagged = "0"
            if (len(s.tag) > 0 and s.tag in tag_list) or s.status > 0 or s.price > 0:
                body += " style=\"display:none\""
                tagged = "1"
            body += " price='"+str(s.price)+"'"
            body += "><div class='col'><button onclick=\"delByTid('"+s.tid+"');\">刪除</button>"
            body += "<button onclick=\"keepByTid('"+s.tid+"');\">保留</button>"
            body += "<button id='"+s.tid+"' status='"+str(s.status)+"' class='show_tag' hidden>"+s.tag+"</button>"
            body += " <a id='"+s.tid+"' href='"+s.url+"' tagged='"+tagged+"' target='_blank'>"+s.name+"</a></div></div>\r\n"
        else:
            s.delete()
        count += 1
        if count >= max_count:
            break;
    return title, body

def delete(tid):
    plist = JKFPost.objects.filter(tid=tid)
    if len(plist) > 0:
        p = plist[0]
        p.is_found = False
        p.save()
        title = "已刪除" + tid
    else:
        title = "找不到" + tid
    return title

def deleteAll():
    JKFPost.objects.all().delete()
    deleteFiles(mydir)

def tag(zone, tag, name, act, is_found=True):
    if act == 'd':
        tlist = JKFTag.objects.filter(zone=zone, tag=tag)
        if len(tlist) > 0:
            t = tlist[0]
            t.delete()
            title = "已刪除" + tag
        else:
            title = "找不到" + tag
    elif act == 'e':
        tlist = JKFTag.objects.filter(zone=zone, tag=tag)
        if len(tlist) > 0:
            t = tlist[0]
            t.name = name
            t.save()
            title = "已編輯" + tag
        else:
            title = "找不到" + tag
    else:
        slist = JKFPost.objects.filter(zone=zone, is_found=is_found).order_by('-created_at')
        count = 0
        print("tag, len="+str(len(slist)))
        for s in slist:
            if len(s.tag) > 0:
                if (s.tag == tag):
                    count += 1
            else:
                if find_content(s.tid, s.url, tag) == True:
                    s.tag = tag
                    s.save()
                    count += 1
        if count > 0:
            t = JKFTag(zone=zone, tag=tag)
            t.save()
        title = "找到"+str(count)+"筆,總共"+str(len(slist))+"筆"
    return title

def keep(tid, status):
    plist = JKFPost.objects.filter(tid=tid)
    if len(plist) > 0:
        p = plist[0]
        p.status = status
        p.save()
        title = "已保留" + tid
    else:
        title = "找不到" + tid
    return title

