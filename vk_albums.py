#!/usr/bin/python3

import argparse
from bs4 import BeautifulSoup
import requests
import pickle
import os

DOMAIN = 'https://m.vk.com'
COOKIESFILE = 'session.txt'

arg_parser = argparse.ArgumentParser();
arg_parser.add_argument("-l", "--login", help="user login")
arg_parser.add_argument("-p", "--password", help="user password")
arg_parser.add_argument("-a", "--album", help="album (e.g album1111_000, where 1111 - user/group id, 000 - album id)")
arg_parser.add_argument("-c", "--count", help="album pic count")
arg_parser.add_argument("-o", "--output-dir", help="output directory, --album value if not presented")
args = arg_parser.parse_args();

print("login: ", args.login)
print("password: ", args.password)
print("album: ", args.album)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language':'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
    'Accept-Encoding':'gzip, deflate',
    'Connection':'keep-alive',
    'DNT':'1'
}


login_requisites = {
    'email': args.login,
    'pass': args.password
}

def open_session():
    try:
        fd = open(COOKIESFILE, 'rb')
    except:
        print("Can't open session file, login will be restarted")
        return session

    session = pickle.load(fd)

    return session

def save_session(session):
    try:
        fd = open(COOKIESFILE, 'wb')
    except:
        print("Can't open session file, session was not saved")
        return
   
    pickle.dump(session, fd)
    

def check_session(session):
    data = session.get('https://m.vk.com/feed', headers=headers)
    bs = BeautifulSoup(data.text, 'html.parser')
    forms = bs.find_all('form')
    if len(forms) != 1:
        print('check_session: Cookies is valid')
        return True
   
    if 'login.vk.com' in  forms[0]['action']:
        print('check_session: Cookies is invalid')
        return False

    print('check_session: Cookies is valid')
    return True


def login(session):
    data = session.get('https://m.vk.com', headers=headers)
    bs = BeautifulSoup(data.text, 'html.parser')
    form = bs.find_all('form')[0]
    
    data = session.post(form["action"], headers=headers, data={ 'email': args.login, 'pass': args.password })

    if not check_session(session):
        print("Invalid login/password, exit")
        exit()
    
    return session

def extract_pic_name(pic_link):
    s = pic_link.split('?')[0]
    s = s.split('/')
    return s[len(s) - 1]

def get_album(session):
    if not args.album:
        print('album not specified, exit')
        exit()
    if not args.count:
        print('count not specifioed, exit')
        exit()
    
    count = int(args.count)
    output_dir = args.output_dir
    if not args.output_dir:
        output_dir = args.album
    try:
        os.mkdir(output_dir)
    except:
        pass

    album = args.album
    output_dir = args.output_dir if args.output_dir else args.album
    pic_counter = 1
    offset = 0
    while True:
        qurl = "https://m.vk.com/%s?offset=%d" % (album, offset)
        print("Getting album part: %s" % qurl)
        data = session.get(qurl, headers=headers)
        bs = BeautifulSoup(data.text, 'html.parser')
        pics = bs.find_all('div', {'class': 'PhotosPhotoItem__photo'})
        offset += len(pics)
        print(" Pictures discovered: %d" % len(pics))
        for pic in pics:
            data_id = pic['data-id']
            qurl =  'https://m.vk.com/photo%s?list=%s#comments' % (data_id, args.album)
            print('  Getting album image %s' % qurl)
            data = session.get(qurl, headers=headers)
            bs = BeautifulSoup(data.text, 'html.parser')
            menu_links = bs.find_all('a', {'class': 'mva_item'})
            pic_link = None
            for link in menu_links:
                if link.text == 'Загрузить оригинал':
                    pic_link = link['href']
                    break
            
            data = session.get(pic_link)
            
            pic_name = extract_pic_name(pic_link)
            print('  Saving image #%d: %s' % (pic_counter, pic_name))
            fd = open(output_dir + '/' + pic_name, 'wb')
            fd.write(data.content)
            fd.close()

            pic_counter += 1

        if pic_counter >= count:
            break
            

# session = requests.session()
session = open_session()
if not check_session(session):
    session = login(session)
save_session(session)

get_album(session)
