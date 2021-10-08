#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    def get_scheme(self, url):
        return url.scheme + "://"

    def get_host(self, url):
        str_url = url.geturl()
        no_scheme = str_url.replace(self.get_scheme(url), "")
        no_path = no_scheme.replace(self.get_path(url), "")
        return no_path

    def get_host_no_port(self, url):
        str_url = url.geturl()
        no_scheme = str_url.replace(self.get_scheme(url), "")
        no_port = no_scheme.replace(":" + str(self.get_host_port(url)), "")
        no_path = no_port.replace(self.get_path(url), "")
        return no_path

    def get_host_port(self, url):
        if (url.port == None):
            return 80
        return url.port

    def get_path(self, url):
        return url.path

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        if (len(data) > 0 and len(data[0]) > 0):
            return int(data[0].split()[1])
        return 500

    def get_headers(self,data):
        if (len(data) > 0):
            return '\n'.join(data[1:data.index("")]) # skip status code
        return ''

    def get_body(self, data):
        if (len(data) > 0):
            return '\n'.join(data[data.index(""):][1:]) # start after double CRLF (stripped down to "")
        return ''
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    # based on: https://stackoverflow.com/a/17697651
    # original recvall() did not work for me
    # reformatted to look like recvall()
    def recvall2(self, sock):
        buffer = b''
        done = False
        while (not done):
            part = sock.recv(1024)
            buffer += part
            if (len(part) < 1024):
                done = True
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        url = urllib.parse.urlparse(url)

        scheme = self.get_scheme(url)
        host = self.get_host(url)
        host_no_port = self.get_host_no_port(url)
        port = self.get_host_port(url)
        path = self.get_path(url)

        path_no_slash = ""
        if (len(path) > 0):
            path_no_slash = path[1:]

        self.connect(host_no_port, port)

        self.sendall(f'GET {path} HTTP/1.1\r\n' + \
                     f'Host: {host}\r\n' + \
                      '\r\n')

        data = self.recvall2(self.socket)
        self.close()

        response_list = data.split('\r\n')

        code = self.get_code(response_list)
        body = path_no_slash

        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        url = urllib.parse.urlparse(url)

        scheme = self.get_scheme(url)
        host = self.get_host(url)
        host_no_port = self.get_host_no_port(url)
        port = self.get_host_port(url)
        path = self.get_path(url)

        path_no_slash = ""
        if (len(path) > 0):
            path_no_slash = path[1:]

        self.connect(host_no_port, port)

        request_body = ""
        if (len(path_no_slash) > 0):
            request_body = f"path={path_no_slash}&"
        if (args != None):
            for key in args:
                request_body += f"{key}={args[key]}&"
        if (len(request_body) > 0 and request_body[len(request_body) - 1] == "&"):
            request_body = request_body[:len(request_body) - 1]

        self.sendall(f'POST {path} HTTP/1.1\r\n' + \
                     f'Host: {host}\r\n' + \
                      'Content-Type: application/x-www-form-urlencoded\r\n' + \
                     f'Content-Length: {len(request_body)}\r\n' + \
                      '\r\n' + \
                     f'{request_body}')

        data = self.recvall2(self.socket)
        self.close()

        response_list = data.split('\r\n')

        code = self.get_code(response_list)

        body = str(args).replace("'", '"')
        body = body.replace(":", ":[")
        body = body.replace(",", "],")
        body = body.replace("}", "]}")

        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
