# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 17:48:11 2020

@author: eddyteng
"""
import mechanicalsoup
import datetime
import os

name_list = ["中山區.林森北路","板橋.中永和","大台北","萬華.西門町","三重.新莊"]
url_list = ["type-1128-1476.html","type-1128-1950.html","type-1128-1949.html","type-1128-1948.html","type-1128-1951.html"]

home = "https://www.jkforum.net/"
mydir = os.getcwd()+'/mysite/templates'

def parse_url(url, max_count=10):
    body = ""
    start_url = home + url
    
    browser = mechanicalsoup.StatefulBrowser()
    page = browser.get(start_url)
    
    a_list = [a for a in page.soup.find_all("a") if a.get("href") is not None]
    count = 0
    match = 0
    for a in a_list:
        link = a["href"]
        if "forum.php?mod=viewthread" in link:
            if a.get("onclick") is not None:
                click = a["onclick"]
                if "atarget(this)" in click:
                    count += 1
                    content_url = home + link
                    body, og_url = parse_content(content_url, body, a.text)
                    if len(og_url) > 0:
                        match += 1
                        body = body + "<br><h1><a href='"+og_url+"' target='_blank'>"+a.text+"</a></h1><br>\r\n"
                        body = body + "<hr>"
                        #print(a.text)
                        #print(content_url)
                        #print("-----------------")
        if count >= max_count:
            break
    return body, match

def parse_content(url, body, name=""):
    browser = mechanicalsoup.StatefulBrowser()
    page = browser.get(url)
    
    table_list = [table for table in page.soup.find_all("table") if table.get("class") is not None]
    for table in table_list:
        cls = table["class"]
        if "view-data" in cls:
            og_url = ""
            if find_spa(table, name) == False and find_line(table, name):
                #print(table)
                #print("-----------------")
                meta = page.soup.find("meta", property='og:url')
                if meta is not None:
                    img_list = [img for img in table.find_all("img") if img.get("file") is not None]
                    if len(img_list) < 10:
                        og_url = meta["content"]
                        for img in img_list:
                            img_file = img["file"]
                            #img_width = img["width"]
                            body = body + "<img src='"+img_file+"'>\r\n"
                            #print(img_file, img_width)
            return body, og_url

def find_line(table, name=""):
    font_list = table.find_all("font")
    for font in font_list:
        line_text = ("Line","LINE","賴")
        spa_text = ("館")
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
        spa_text = ("舒壓","紓壓","定點","幹部","18-25y","單親媽","24H")
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

def request(zone, max_count):
    if zone < 0 or zone >= len(name_list):
        return "", ""
    
    name = name_list[zone]
    url = url_list[zone]
    body, match_count = parse_url(url, max_count)
    dt = datetime.datetime.now()
    title = name+" 找到"+str(match_count)+"筆,搜尋"+str(max_count)+"筆 "+dt.strftime("%c")
    head = "<head><meta http-equiv='Content-Type' content='text/html; charset=utf-8' /><title>"+title+"</title></head>"
    
    output = "<html>"+head+"<body>"+body+"</body></html>"
    #print(output)
    return title, output

def run():
    zone = 0
    max_count = 10
    title, output = request(zone, max_count)
    saveHTML(mydir + '/' + 'jkf.html', output)
    return title

#print( run() )
