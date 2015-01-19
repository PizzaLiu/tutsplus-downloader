#! /usr/bin/env python
#-*- coding: utf-8 -*-

import requesocks as requests
# import requests
from bs4 import BeautifulSoup
import os


class Tutsplus:

    login_url= 'https://tutsplus.com/sign_in'
    login_post_url = 'https://tutsplus.com/sessions'

    def __init__(self, username, password):

        self.username = username
        self.password = password

        self.login()

    # Return the html source for a specified url
    def get_source(self, url):

        r = self.s.get(url)
        return r.content

    # It logs in and store the sesson for the future requests
    def login(self):
        self.s = requests.session()

        #self.s.proxies = {'http': 'http://127.0.0.1:8087','https': 'http://127.0.0.1:8087'}
                           
        soup = BeautifulSoup(self.get_source(self.login_url))
        authenticity_token =  soup.find_all(attrs={"name": "authenticity_token"})[0]['value']
        utf8 =  soup.find_all(attrs={"name": "utf8"})[0]['value']
        data = {
            'utf8':utf8,
            'session[login]':self.username,
            'session[password]':self.password,
            'authenticity_token' : authenticity_token
        }

        self.s.post(soup.select('.sign-in__form')[0]['action'], data = data)

        soup = BeautifulSoup(self.get_source('https://tutsplus.com/account/courses'))
        account_name = soup.select('.account-header__name')[0].string

        if not account_name :
            return False

        print 'Logined success, account name: '+account_name
        return True

    # Download all video from a course url
    def download_course(self, url):
        # Variable needed to increment the video number
        self.video_number = 1

        source = self.get_source(url)

        soup = BeautifulSoup(source)

        # the course's name
        self.course_title = soup.select('.content-header__title')[0].string.replace('?','')
        if not os.path.exists(self.course_title) :
            os.makedirs(self.course_title)

        # array who stores the information about a course
        course_info = self.get_info_from_course(soup)

        for video in course_info:
            print "[+] Downloading " + video['titolo']
            self.download_video(video)
            self.video_number = self.video_number + 1


    def download_courses(self,courses):

        for course in courses:

            self.download_course(course)

    # pass in the info of the lesson and it will download the video
    # lesson = {
    #   "titolo": 'video title',
    #   "link" : 'http://link_to_download'
    # }
    def download_video(self,lesson):
        # If it finds more than 1 download link it will skip
        # the video files and will download the video only
        download_link = lesson['link']
        # String name of the file
        name = self.course_title + '/[' + str(self.video_number) + '] ' + lesson['titolo'].replace('/','-').replace('?','').replace(': ','-').replace(self.course_title+'__', '')
        self.download_file(download_link,name)
        print '[*] Downloaded > ' + lesson['titolo']

    # Function who downloads the file itself
    def download_file(self,url, name):
        name = name + '.mp4'
        r = self.s.post(url, self.download_access_data)
        url = r.headers['location']
        r = self.s.get(url)

        if not os.path.isfile(name) :
            with open(name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
        return name

    # return an array with all the information about a video (title, url)
    def get_info_from_course(self, soup):
        if not self.set_download_token(soup):
            return []
        arr = []
        videos = soup.select('.lesson-index__lesson .lesson-index__download-link')
        for video in videos:
            titolo = video['data-ga-event-label']
            link = video['href']
            info = {
                "titolo":titolo,
                "link":link
            }
            arr.append(info)
        return arr

    # Function to set download token
    def set_download_token(self, soup):
        method = 'post'
        token = soup.find_all(attrs={"name": "csrf-token"})[0]['content']
        if not token:
            return False
        self.download_access_data = {
            'authenticity_token':token,
            '_method':method
        }
        return True