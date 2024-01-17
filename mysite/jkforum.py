# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 17:48:11 2020

@author: eddyteng
"""
from myapp.models import JKFPost
from myapp.models import JKFTag
import mechanicalsoup
from datetime import datetime, timezone, timedelta
import os
import traceback

name_list = ["中山區.林森北路","板橋.中永和","大台北","萬華.西門町","三重.新莊"]
url_list = ["type-1128-1476.html","type-1128-1950.html","type-1128-1949.html","type-1128-1948.html","type-1128-1951.html"]

home = "https://www.jkforum.net/"
mydir = os.getcwd()+'/staticfiles/jkforum/'
mylocal = True

def parse_url(zone, url, max_count=10, show=False):
    body = ""
    start_url = home + url
    
    browser = mechanicalsoup.StatefulBrowser()
    page = browser.get(start_url)
    
    a_list = [a for a in page.soup.find_all("a") if a.get("href") is not None]
    count = 0
    match = 0
    find = 0
    update = 0
    for a in a_list:
        link = a["href"]
        if "forum.php?mod=viewthread" in link:
            if a.get("onclick") is not None:
                click = a["onclick"]
                if "atarget(this)" in click:
                    count += 1
                    tid = get_tid(link)
                    name = a.text if len(a.text) <= 50 else a.text[0:50]
                    content_url = home + link
                    plist = JKFPost.objects.filter(tid=tid)
                    og_url = ""
                    if len(plist) > 0:
                        p = plist[0]
                        if p.is_found == True:
                            if (p.name != name):
                                update += 1
                                p.save()
                            if (show):
                                body, og_url, tag = parse_content(zone, tid, content_url, body, name, show)
                                find += 1
                            else:
                                og_url = p.url
                    else:
                        p = JKFPost(tid=tid, zone=zone, name=name)
                        body, og_url, tag, price, status = parse_content(zone, tid, content_url, body, name, show)
                        find += 1
                        if len(og_url) > 0:
                            p.is_found = True
                            p.url = og_url
                            p.tag = tag
                            p.price = price
                        p.status = status
                        p.save()
                        
                    if len(og_url) > 0:
                        match += 1
                        body = body + "<br><h1><a href='"+og_url+"' target='_blank'>"+name+"</a></h1><br>\r\n"
                        body = body + "<hr>"
                        #print(a.text)
                        #print(content_url)
                        #print("-----------------")
        if count >= max_count:
            break
    return body, find, match, update

def get_tid(link):
    idx = link.index("tid=")
    start = idx+4
    end = link.index("&", idx)
    tid = link[start:end]
    return tid

def parse_content(zone, tid, url, body, name="", show=False):
    txt_path = mydir+tid+'.txt'
    text = ''
    if show == False and os.path.exists(txt_path):
        text = loadHTML(txt_path)
    else:
        browser = mechanicalsoup.StatefulBrowser()
        page = browser.get(url)
        table_list = page.soup.find_all("table", class_="view-data")
        if len(table_list) > 0:
            table = table_list[0]
            text = table.text
            if (mylocal):
                a_list = table.find_all("a")
                for a in a_list:
                    link = a["href"]
                    if link.startswith("http"):
                        text += '\n' + link
                saveHTML(txt_path, text)
        
    og_url = ""
    tag = ""
    price = 0
    status = 0
    if find_spa(text, name) == False:
        meta = page.soup.find("meta", property='og:url')
        if meta is not None:
            og_url = meta["content"]
            tag = get_tag(text, zone)
            price = get_price(text, name)
            status = get_status(text, name)
            if (show):
                img_list = [img for img in table.find_all("img") if img.get("file") is not None]
                if len(img_list) < 10:
                    for img in img_list:
                        img_file = img["file"]
                        if img_file.startswith('/'):
                            img_file = home + img_file[1:]
                            #img_width = img["width"]
                            body = body + "<img src='"+img_file+"'>\r\n"
                            #print(img_file, img_width)
    return body, og_url, tag, price, status

def find_content(tid, url, tag):
    txt_path = mydir+tid+'.txt'
    text = ''
    if os.path.exists(txt_path):
        text = loadHTML(txt_path)
    else:
        browser = mechanicalsoup.StatefulBrowser()
        page = browser.get(url)
        table_list = page.soup.find_all("table", class_="view-data")
        if len(table_list) > 0:
            table = table_list[0]
            text = table.text
            if (mylocal):
                a_list = table.find_all("a")
                for a in a_list:
                    text += '\n' + a["href"]
                saveHTML(txt_path, text)
    
    print(txt_path)
    print(text)
    return tag in text

def find_spa(table_text, name=""):
    #font_list = table.find_all("font")
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

def request(zone, max_count, times, show=False):
    try:
        if zone < 0 or zone >= len(name_list):
            return "", ""
        
        name = name_list[zone]
        url = url_list[zone]
        title = ''
        body = ''
        
        for i in range(0, times):
            p_body, find_count, match_count, update_count = parse_url(zone, url, max_count, show)
            dt = datetime.now(timezone(timedelta(hours=+8)))
            title = name+" 找到"+str(match_count)+"筆,搜尋"+str(find_count)+"筆,更新"+str(update_count)+"筆,總共"+str(max_count)+"筆 "+dt.strftime("%c")
            if show == False:
                p_body = title
                title = 'jkforum'
            body += p_body+"<br>"
    except:
        title = "Server Error"
        exc = traceback.format_exc().splitlines()
        body = ""
        for e in exc:
            body += e + "<br>"
    return title, body

def select(zone, max_count, is_found=True, show=False):
    slist = JKFPost.objects.filter(zone=zone, is_found=is_found).order_by('-created_at')
    
    name = name_list[zone]
    dt = datetime.now(timezone(timedelta(hours=+8)))
    title = name+" 找到"+str(len(slist))+"筆,總共"+str(JKFPost.objects.count())+"筆 "+dt.strftime("%c")
    body = "標籤：<button onclick=\"showByStatus(1);\">保留</button> "
    body = body + "<button onclick=\"showByStatus(2);\">90幫</button> "
    tlist = JKFTag.objects.filter(zone=zone).order_by('-created_at')
    tag_list = []
    for t in tlist:
        tag_list.append(t.tag)
        body += "<button onclick=\"showByTag('"+t.tag+"');\">"+t.tag+"</button> "
    
    body = body + "<br><label id='show_list'>未分類/未定價</label>：<br>\r\n"
    count = 0
    for s in slist:
        if len(s.url) > 0:
            if (show):
                body, og_url, tag = parse_content(zone, s.tid, s.url, body, s.name, show)
                body = body + "<br><h1><button onclick=\"delByTid('"+s.tid+"', '"+s.name+"');\">刪除</button> <a href='"+s.url+"' target='_blank'>"+s.name+"</a></h1><br>\r\n"
                body = body + "<hr>"
            else:
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

def tag(zone, tag, act, is_found=True):
    if act == 'd':
        tlist = JKFTag.objects.filter(zone=zone, tag=tag)
        if len(tlist) > 0:
            t = tlist[0]
            t.delete()
            title = "已刪除" + tag
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

def run():
    zone = 0
    max_count = 10
    title, output = request(zone, max_count)
    print(output)
    return title

#print( run() )
