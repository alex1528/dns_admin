# -*- coding: utf-8 -*-

import urllib2
import cookielib
import urllib
import ujson


class LoginException(Exception):

    '''my defined login exception'''

    def __init__(self, data):
        Exception.__init__(self, data)
        self.__data = data

    def __str__(self):
        return str(self.__data)


class Ldapapi(object):

    '''class for api that authenticate via ldap'''
    is_login = False
    host_url = "127.0.0.1:8080"

    @classmethod
    def login(cls, username, password, url):
        '''login via username and password for ldap
        @params:
        username: username
        password: password
        url: url to auth
        '''
        auth_url = r"http://" + cls.host_url + r"/" + url
        cookie = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
        urllib2.install_opener(opener)
        data = urllib.urlencode({"username": username, 'password': password})
        login_response = urllib2.urlopen(auth_url, data)
        response = login_response.read()

        ret_dict = ujson.loads(response)

        # update to check the response content to check if passed
        # authentication
        if ret_dict["result"] == "success":
            cls.is_login = True
        else:
            cls.is_login = False

    @classmethod
    def post_wrapper(cls, url, username, password,
                     data_dict, auth_url="api/v1/ldapauth"):
        '''wrapper for the post api
        @params:
        url: url to visit
        username: username for ldap authenticate
        password: password for ldap authenticate
        data_dict: data to post. e.g. {"name":"xxxx","xxxxk":"xxxv"}
        auth_url: url to login
        return the response string
        '''
        if not cls.is_login:
            cls.login(username, password, auth_url)

        if not cls.is_login:
            raise LoginException(
                "login to %s failed with username:%s and password:%s"
                % (auth_url, username, password))

        data = urllib.urlencode(data_dict)
        visit_url = r"http://" + cls.host_url + r"/" + url
        login_response = urllib2.urlopen(visit_url, data)
        response = login_response.read()
        ret_dict = ujson.loads(response)

        return ret_dict

    @classmethod
    def get_wrapper(cls, url, username, password,
                    data_dict, auth_url="api/v1/ldapauth"):
        '''wrapper for the get api
        @params:
        url: url to visit
        username: username for ldap authenticate
        password: password for ldap authenticate
        data_dict: data to post. e.g. {"name":"xxxx","xxxxk":"xxxv"}
        auth_url: url to login
        return the response string
        '''
        if not cls.is_login:
            cls.login(username, password, auth_url)

        if not cls.is_login:
            raise LoginException(
                "login to %s failed with username:%s and password:%s"
                % (auth_url, username, password))

        data = urllib.urlencode(data_dict)
        visit_url = r"http://" + cls.host_url + r"/" + url
        login_response = urllib2.urlopen(visit_url + "?" + data)
        response = login_response.read()
        ret_dict = ujson.loads(response)

        return ret_dict


def test_login():
    '''test login'''
    url = "api/v1/ldapauth"
    username = "autodeploy"
    password = "0+9@q8h#VlbE56Z4_=-YGH!St"    

    Ldapapi.login(username, password, url)
    if Ldapapi.is_login:
        print "login succeed!"
    else:
        print "login failed!"


def test_post_wrapper():
    '''test post_wrapper'''
    username = "autodeploy"
    password = "0+9@q8h#VlbE56Z4_=-YGH!St"    

    url = "api/v1/add"
    data_dict = {
        "dnslist": [{"hostname": "test512.hy01", "ip": "10.0.11.100"}, {"hostname": "test513.hy01", "ip": "10.0.11.101"}]}
    print Ldapapi.post_wrapper(url, username, password, data_dict)

    url = "api/v1/modify"
    data_dict = {"key": "ip", "dnslist":
                 [{"ip": "10.0.11.100", "hostname": "test1000.hy01"}, {"ip": "10.0.11.101", "hostname": "test1001.hy01"}]}
    print Ldapapi.post_wrapper(url, username, password, data_dict)


def test_get_wrapper():
    '''test post_wrapper'''
    url = "api/v1/query"
    username = "autodeploy"
    password = "0+9@q8h#VlbE56Z4_=-YGH!St"    
    data_dict = {"key": "hostname", "dnslist": ["vmh100.hy01", "vmh200.hy01"]}
    print Ldapapi.get_wrapper(url, username, password, data_dict)

    data_dict = {"key": "ip", "dnslist": ["10.0.11.100", "10.0.11.101"]}
    print Ldapapi.get_wrapper(url, username, password, data_dict)


if __name__ == "__main__":
    test_login()
    test_get_wrapper()
    test_post_wrapper()