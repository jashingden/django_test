# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 17:22:07 2021

@author: eddyteng
"""
import mechanicalsoup
#import re
#import time
#import zlib
from urllib.parse import unquote

sg_home = 'https://www.sugar-garden.org'
sg_login = '/login'
sg_search = '/dashboard/search'
sg_search_data = '/getSearchData'

def login_sugar(browser):
    login_url = sg_home + sg_login    
    page = browser.get(login_url)
    
    cfp_url = sg_home + '/cfp'
    cfp = browser.get(cfp_url)

    with open('sg.txt', mode='r') as sg:
        my = sg.readlines()
        sg_email = my[0].rstrip('\n')
        sg_pwd = my[1].rstrip('\n')
    
    form = page.soup.find('form')
    fields = form.findAll('input')
    formdata = dict( (field.get('name'), field.get('value')) for field in fields )
    formdata['email'] = sg_email
    formdata['password'] = sg_pwd
    page = browser.post(login_url, data=formdata)
    
    formdata.pop('email')
    formdata.pop('password')
    return page, cfp, formdata
'''
def search_sugar(browser, cfp, formdata, agefrom = 18, ageto = 26, seqtime = 1):
    search_url = sg_home + sg_search
    page = browser.get(search_url)
    
    token = formdata['_token']
    token_time = round(time.time())
    cfp_url = sg_home + '/check-cfp?' + token + '=' + str(token_time)
    check_cfp = browser.post(cfp_url, data=formdata)
    return page, check_cfp
'''
def parse_search(browser):
    cookies = browser.session.cookies.items()
    data_url = sg_home + sg_search_data
    data_header = {
        'Content-Type': 'application/json',
        'X-XSRF-TOKEN': unquote(cookies[0][1])
        }
    file_data = open('file.txt', mode='rb')
    page = browser.request(method='POST', url=data_url, headers=data_header, data=file_data)
    
    sugar_data = page.json()
    sugar_total = sugar_data['allPageDataCount']
    sugar_list = sugar_data['dataList']
    return sugar_total, sugar_list

def print_to_file(page):
    with open('page.txt', mode='w') as file_object:
        print(page.soup, file=file_object)

def run():
    browser = mechanicalsoup.StatefulBrowser()
    
    page, cfp, formdata = login_sugar(browser)
    #print_to_file(page)
    
    #formdata['_token'] = 'eoIvrfOu2KjcEEWvUGbEyh2RT16Yty8yBNzanBSs'
    #formdata['hash'] = 'fUihTT3jsiU8sediyzRXUxz1zewKpr7wkWThAtsYDsOcRZdn4t'
    #page, check_cfp = search_sugar(browser, cfp, formdata)
    #print_to_file(page)
    
    sugar_total, sugar_list = parse_search(browser)
    
    sugar = sugar_list[0]

#print( run() )
