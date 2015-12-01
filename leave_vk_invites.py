import requests
from BeautifulSoup import BeautifulSoup
import re
import getpass
from numbers import Number

"""
This module provides convenient possibility to leave vkontakte (vk.com) groups. It works via VK api.
For the API documentation refer to https://vk.com/dev/main
"""

__author__ = 'oleh.ilnytkskyi'

BASE_API_URL = "https://api.vk.com/method/"
TIMEOUT = 5

class Token(object):
    AUTH_URL = 'https://oauth.vk.com/'

    def get_token(self, username, password, client_id):
        """
        Retrieves access_token that provides possibility to interact with VK API.
        :param username: specifies user email
        :param password: specifies password
        :param client_id: specifies application id
        :return: access_token string
        """
        print 'Requesting access for application with id', client_id
        params = {"client_id":client_id,
                  "scope":"groups",
                  "redirect_uri":"https://oauth.vk.com/blank.html",
                  "display":"page",
                  "response_type":"token"}

        url = self.AUTH_URL + "authorize"
        req = requests.get(url, params, timeout=TIMEOUT)

        print 'Parsing login window parameters'
        credentials_page = BeautifulSoup(req.content)

        def get_value(name):
            return credentials_page.find("", {"name":name}).get("value")

        ip_h = get_value('ip_h')
        lg_h = get_value('lg_h')
        to = get_value('to')
        url_to_post = credentials_page.find("form", {"method":"post"}).get("action")

        print 'Login in and requesting access_token'
        response = requests.post(url_to_post,
                                    data={"_origin":"https://oauth.vk.com",
                                          "ip_h":ip_h, "lg_h":lg_h, "to":to,
                                          "email":username, "pass":password, "expires": "0"},
                                    cookies=req.cookies, timeout=TIMEOUT)

        if ("access_token" not in response.url):
            raise Exception("Response URL was not as expected. Verify credentials", response.url)

        print 'Parsing access token from response url'
        token = re.search("access_token=([0-9a-z])+", response.url).group().split("=")[1]
        return token


class CommunitiesManager(object):

    def __init__(self, token):
        self.token = token

    def get_invites_to_communities(self):
        """
        Retrieves list of invites for current user.
        :return: list of communities id
        """
        url = BASE_API_URL + "groups.getInvites"
        params = {"access_token":self.token, "count":"1000"}

        print 'Getting list of groups for user'
        req = requests.get(url, params, timeout=TIMEOUT)
        invites = req.json()['response']
        # Retrieves groups ids
        groups_ids = map(lambda group: group['gid'], filter(lambda group: not isinstance(group, Number), invites))

        return groups_ids

    def leave_community(self, group_id, attempts=5):
        """
        Provides possibility to leave a single group
        :param group_id: specifies group id
        :param attempts: specifies number of attempts if leaving procedure fails. Default 3
        :return: true if operation succeed
        """
        url = BASE_API_URL + "groups.leave"
        params = {"access_token":self.token, "group_id":group_id}

        print 'Leaving group with Id:', group_id

        def result(req):
            print req.content
            if '"response":1' in req.content:
                print 'Successful'
                return True
            else:
                print 'Failed to leave group with Id:', group_id
                return False

        for attempt in range(attempts):
            req = requests.get(url, params, timeout=TIMEOUT)
            if result(req):
                break

# Lets start
def main():
    disclaimer = "This application will unsubscribe your [vkontakte] account from all the invitations to events. " \
                  "Please note, that you are providing access to your groups for this application."
    print "*" * len(disclaimer)
    print disclaimer
    print "*" * len(disclaimer)
    username = raw_input('VK username: ')
    password = getpass.getpass('VK password: ')
    application_id = '3259134'

    token = Token().get_token(username, password, application_id)
    manager = CommunitiesManager(token)
    communities_ids = manager.get_invites_to_communities()

    if (len(communities_ids) > 0):
        print 'Groups that will be abandoned by current user:', communities_ids
    else:
        print 'No groups to leave.'

    for id in communities_ids:
        manager.leave_community(id)


if __name__ == '__main__':
    main()