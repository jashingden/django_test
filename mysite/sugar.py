# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 17:22:07 2021

@author: eddyteng
"""
import mechanicalsoup
import re

sg_home = 'https://www.sugar-garden.org'
sg_login = '/login'
sg_search = '/dashboard/search'
sg_email = 'eddyden67@yahoo.com.tw'
sg_pwd = 'jan237'

def login_sugar(browser):
    login_url = sg_home + sg_login
    
    page = browser.get(login_url)
    form = page.soup.find('form')
    fields = form.findAll('input')
    formdata = dict( (field.get('name'), field.get('value')) for field in fields )
    formdata['email'] = sg_email
    formdata['password'] = sg_pwd
    page = browser.post(login_url, data=formdata)
    return page

def search_sugar(browser, agefrom = 18, ageto = 26, seqtime = 1):
    search_url = sg_home + sg_search
    page = browser.get(search_url)
    form = page.soup.find('form')
    fields = form.findAll('input')
    formdata = dict( (field.get('name'), field.get('value')) for field in fields )
    formdata['county'] = '臺北市'
    formdata['agefrom'] = int(agefrom)
    formdata['ageto'] = int(ageto)
    formdata['seqtime'] = int(seqtime)
    page = browser.post(search_url, data=formdata)
    return page

def view_sugar(browser, viewuser):
    view_url = sg_home + viewuser
    page = browser.get(view_url)
    return page

def parse_search(browser):
    page = search_sugar(browser)
    
    li_list = page.soup.find_all('li', class_='nt_fg')
    sugar_list = []
    for li in li_list:
        tagText = li.find_all('div', class_='tagText')
        link = li.find('a')['href']
        img = li.find('img', class_='lazy')['src']
        h2 = li.find('h2').strings
        name_age = []
        for s in h2:
            name_age.append(s)
        h3 = li.find_all('h3')
        for s in h3[0].strings:
            city = s.strip()
            break
        last_online = h3[1].text
        sugar = [tagText, link, img, name_age, city, last_online]
        sugar_list.append(sugar)
        #print(sugar)
    return sugar_list

def parse_sugar(browser, link):
    page = view_sugar(browser, link)
    print(page)
    
    d1 = page.soup.find('div', class_='swiper-wrapper')
    img_list = [img['src'] for img in d1.find_all('img')]
    d2 = page.soup.find('div', class_='xl_input')
    info = [d.text for d in d2.find_all('div', class_=re.compile('select_xx'))]

def run():
    browser = mechanicalsoup.StatefulBrowser()
    page = login_sugar(browser)
    sugar_list = parse_search(browser)
    
    sugar = sugar_list[0]
    parse_sugar(browser, sugar[1])

#print( run() )
