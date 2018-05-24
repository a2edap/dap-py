'''
File: a2e.py
Author: Logan Dihel, Matt Macduff
Date: 5/24/2018
Last Modified: 5/24/2018
Description: This file shall be imported and handle 
all of the respective A2e APIs with simple, high-level
wrapper functions
'''

import os
import os.path
import re
import sys
import json
import base64
import requests
from getpass import getpass

class BadStatusCodeError(RuntimeError):
    def __init__(self, req):
        self.status_code = req.status_code
        self.reason = req.reason

    def __str__(self):
        return ((
            'Server Returned Bad Status Code\n'
            'Status Code: {}\n'
            'Reason: {}').format(self.status_code, self.reason)
        )

class A2e:

    def __init__(self, cert=None):
        '''cert can be an existing certificate
        or a file path to a .cert file
        '''
        self._api_url = 'https://l77987ttq5.execute-api.us-west-2.amazonaws.com/prod'
        self._cert = cert
        self._auth = None

        # TODO: certify from cert string
        # TODO: certify from ~/.cert file

    # --------------------------------------------------------------
    # - Getting Authenticated --------------------------------------
    # --------------------------------------------------------------
    
    def _request_cert(self, params):
        '''Request a certificate
        '''
        req = requests.put('{}/creds'.format(self._api_url), params=params)

        if req.status_code != 200:
            raise BadStatusCodeError(req)
        
        self.cert = json.loads(req.text)['text']


    def _create_cert_auth(self):
        '''Given an existing certificate, create an auth token
        '''
        self._auth = {
            "Authorization": "Cert {}".format(
                base64.b64encode(self._cert.encode("utf-8")).decode("ascii"))
        }
        

    def _request_cert_auth(self, params):
        '''Requests certificate and creates auth token
        '''
        self._request_cert(params)
        self._create_cert_auth()


    def setup_basic_auth(self, username=None, password=None):
        '''Create the auth token without a certificate
        '''

        username = username or input('username: ')
        password = password or getpass('password: ')

        self._auth = {
            "Authorization": "Basic {}".format(base64.b64encode(
                ("{}:{}".format(username, password)).encode("utf-8")
            ).decode("ascii"))
        }


    def setup_guest_auth(self):
        '''Just sets up basic auth as a guest
        '''
        self.setup_basic_auth('guest', 'guest')


    def setup_cert_auth(self, username=None, password=None):
        '''Given username and password request a
        cert token and generate an auth code
        '''
        # TODO: don't prompt if they already have a valid certificate
        # instead just renew their certificate? or nothing? talk to Matt
        params = {
            'username': username or input('username: '),
            'password': password or getpass('password: '),
        }

        self._request_cert_auth(params)


    def setup_two_factor_auth(self, username=None, password=None, email=None, authcode=None):
        '''Given username, password, email, and authcode,
        request a cert token and generate an auth code
        '''
        # TODO: don't prompt if they already have a valid certificate
        # instead just renew their certificate? or nothing? talk to Matt
        params = {
            'username': username or input('username: '),
            'password': password or getpass('password: '),
            'email': email or input('email: '),
            'authcode': authcode or getpass('authcode: '),
        }

        self._request_cert_auth(params)

    # --------------------------------------------------------------
    # - Search for Filenames ---------------------------------------
    # --------------------------------------------------------------

    def search(self, filter_arg, table='Inventory'):
        '''Search the table and return the matching file paths
        https://github.com/a2edap/tools/tree/master/lambda/api/get-info
        '''
        if not self._auth:
            raise Exception('Auth token cannot be None')

        req = requests.post(
            '{}/searches'.format(self._api_url),
            headers=self._auth,
            data=json.dumps({
                'source': table,
                'output': 'json',
                'filter': filter_arg
            })
        )

        if req.status_code != 200:
            raise BadStatusCodeError(req)
        
        req = req.json()
        files = [x['Filename'] for x in req]
        return files

    # --------------------------------------------------------------
    # - Placing Orders ---------------------------------------------
    # --------------------------------------------------------------

    def _place_order(self, files):
        '''Place an order and return the order ID
        '''
        if not self._auth:
            raise Exception('Auth token cannot be None')

        params = {
            'files': files,
        }

        req = requests.put(
            '{}/orders'.format(self._api_url), 
            headers=self._auth, 
            data=json.dumps(params)
        )

        if req.status_code != 200:
            raise BadStatusCodeError(req)

        id = json.loads(req.text)['id']
        return id

    # --------------------------------------------------------------
    # - Getting download URLs --------------------------------------
    # --------------------------------------------------------------

    def _get_download_urls(self, id):
        '''Given order ID, return the download urls
        '''
        if not self._auth:
            raise Exception('Auth token cannot be None')

        req = requests.get(
            '{}/orders/{}/urls'.format(self._api_url, id), 
            headers=self._auth
        )

        if req.status_code != 200:
            raise BadStatusCodeError(req)

        urls = json.loads(req.text)['urls']
        return urls
    
    # --------------------------------------------------------------
    # - Download from URLs -----------------------------------------
    # --------------------------------------------------------------

    def _download(self, url, path):
        ''' Actually download the files
        '''
        req = requests.get(url, stream=True)
        if req.status_code != 200:
            raise BadStatusCodeError(req)
        while True: # is this needed?
            with open(path, "wb") as fp:
                for chunk in req.iter_content(chunk_size=1024):
                    fp.write(chunk)
            print("Download successful! {}".format(path))
            break

    def _download_from_urls(self, urls, path='/var/tmp/', force=False):
        '''Given a list of urls, download them
        Returns the successfully downloaded file paths
        '''
        if not urls:
            raise Exception('No urls provided')

        downloaded_files = []
        
        # TODO: multi-thread this
        for url in urls:
            try:
                a = url.split('/')
                filename = a[5].split('?')[0]

                dataset = '{}.{}'.format(
                    a[4], '.'.join(a[5].split('.')[:3])
                )

                # /var/tmp/wfip2.lidar.z01.b0
                download_dir = os.path.join(path, dataset)
                os.makedirs(download_dir, exist_ok=True)
                # the final file path
                filepath = os.path.join(download_dir, filename)
            except:
                print('Incorrectly formmated file path in url: {}'.format(url))
                continue

            if not force and os.path.exists(filepath):
                print('File: {} already exists, skipping...'.format(filepath))
                continue

            try:
                self._download(url, filepath)
            except BadStatusCodeError as e:
                print('Could not download file: {}'.format(filepath))
                print(e)
                continue

            downloaded_files.append(filepath)
        return downloaded_files

    # --------------------------------------------------------------
    # - Place Order and Download  ----------------------------------
    # --------------------------------------------------------------

    def download_files(self, files, path='/var/tmp/', force=False):
        '''places order, gets download urls, downloads files
        '''
        if not files:
            print('No files provided')
            return

        try:
            id = self._place_order(files)
        except BadStatusCodeError as e:
            print('Could not place order')
            print(e)
            return

        try:
            urls = self._get_download_urls(id)
        except BadStatusCodeError as e:
            print('Could not get download urls')
            print(e)
            return

        try:
            downloaded_files = self._download_from_urls(urls)
        except Exception as e:
            print(e)
            return

        return downloaded_files

    # --------------------------------------------------------------
    # - Download All matching Search  ------------------------------
    # --------------------------------------------------------------
        
    def _search_for_urls(self, filter_arg):
        '''uses the alternative api /downloads method
        to search the inventory table and return
        the download urls to files in s3
        '''
        if not self._auth:
            raise Exception('Auth token cannot be None')

        req = requests.post(
            '{}/downloads'.format(self._api_url),
            headers=self._auth,
            data=json.dumps(filter_arg)
        )

        if req.status_code != 200:
            raise BadStatusCodeError(req)

        # does not work
        return req.text

    def download_search(self, filter_arg, path='/var/tmp/', force=False):
        '''Uses the /downloads api method to download straight from 
        the search without placing orders and downloading from there
        '''
        try:
            urls = self._search_for_urls(filter_arg)
        except BadStatusCodeError as e:
            print('Could not find download urls')
            print(e)
            return
        except Exception as e:
            print(e)
            return

        if not urls:
            print('No files found')

        # TODO: finish
        try:
            downloaded_files = self._download_from_urls(urls)
        except Exception as e:
            print(e)
            return
        return downloaded_files

