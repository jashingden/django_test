# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 17:48:11 2020

@author: eddyteng
"""
from myapp.models import JKFPost
import mechanicalsoup
import datetime
import os
import traceback

name_list = ["中山區.林森北路","板橋.中永和","大台北","萬華.西門町","三重.新莊"]
url_list = ["type-1128-1476.html","type-1128-1950.html","type-1128-1949.html","type-1128-1948.html","type-1128-1951.html"]

home = "https://www.jkforum.net/"
mydir = os.getcwd()+'/templates'

def parse_url(zone, url, max_count=10, show=False):
    body = ""
    start_url = home + url
    
    browser = mechanicalsoup.StatefulBrowser()
    page = browser.get(start_url)
    
    a_list = [a for a in page.soup.find_all("a") if a.get("href") is not None]
    count = 0
    match = 0
    find = 0
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
                            if (show):
                                body, og_url = parse_content(content_url, body, name)
                                find += 1
                            else:
                                og_url = p.url
                    else:
                        p = JKFPost(tid=tid, zone=zone, name=name)
                        body, og_url = parse_content(content_url, body, name)
                        find += 1
                        if len(og_url) > 0:
                            p.is_found = True
                            p.url = og_url
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
    return body, find, match

def get_tid(link):
    idx = link.index("tid=")
    start = idx+4
    end = link.index("&", idx)
    tid = link[start:end]
    return tid

def parse_content(url, body, name=""):
    browser = mechanicalsoup.StatefulBrowser()
    page = browser.get(url)
    
    table_list = [table for table in page.soup.find_all("table") if table.get("class") is not None]
    for table in table_list:
        cls = table["class"]
        if "view-data" in cls:
            og_url = ""
            if find_spa(table, name) == False:# and find_line(table, name):
                #print(table)
                #print("-----------------")
                meta = page.soup.find("meta", property='og:url')
                if meta is not None:
                    img_list = [img for img in table.find_all("img") if img.get("file") is not None]
                    if len(img_list) < 10:
                        og_url = meta["content"]
                        for img in img_list:
                            img_file = img["file"]
                            if img_file.startswith('/'):
                                img_file = home + img_file[1:]
                            #img_width = img["width"]
                            body = body + "<img src='"+img_file+"'>\r\n"
                            #print(img_file, img_width)
            return body, og_url

def find_line(table, name=""):
    font_list = table.find_all("font")
    for font in font_list:
        line_text = ("Line","LINE","賴","本人")
        for t in line_text:
            if len(name) > 0 and t in name:
                return True
            if t in font.text:
                #print(font)
                #print("-----------------")
                return True
    return False

def find_spa(table, name=""):
    font_list = table.find_all("font")
    for font in font_list:
        spa_text = ("定點","會館","幹部","紅牌","24H")
        for t in spa_text:
            if len(name) > 0 and t in name:
                return True
            if t in font.text:
                #print(font)
                #print("-----------------")
                return True
    return False

def saveHTML(path, html):
    file = open(path, 'w', encoding='UTF-8')
    file.write(html)
    file.close()

def request(zone, max_count, show=False):
    try:
        if zone < 0 or zone >= len(name_list):
            return "", ""
        
        name = name_list[zone]
        url = url_list[zone]
        body, find_count, match_count = parse_url(zone, url, max_count, show)
        
        dt = datetime.datetime.now()
        title = name+" 找到"+str(match_count)+"筆,搜尋"+str(find_count)+"筆,總共"+str(max_count)+"筆 "+dt.strftime("%c")
        if show == False:
            body = title
            title = 'jkforum'
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
    dt = datetime.datetime.now()
    title = name+" 找到"+str(len(slist))+"筆,總共"+str(JKFPost.objects.count())+"筆 "+dt.strftime("%c")
    body = ""
    count = 0
    for s in slist:
        if len(s.url) > 0:
            if (show):
                body, og_url = parse_content(s.url, body, s.name)
                body = body + "<br><h1><button onclick=\"delByTid('"+s.tid+"', '"+s.name+"');\">刪除</button> <a href='"+s.url+"' target='_blank'>"+s.name+"</a></h1><br>\r\n"
                body = body + "<hr>"
            else:
                body += "<div id='"+s.tid+"' class='row'><div class='col'><button onclick=\"delByTid('"+s.tid+"');\">刪除</button> <a id='"+s.tid+"' href='"+s.url+"' target='_blank'>"+s.name+"</a></div></div>\r\n"
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

def run():
    zone = 0
    max_count = 10
    title, output = request(zone, max_count)
    saveHTML(mydir + '/' + 'jkf.html', output)
    return title

#print( run() )
