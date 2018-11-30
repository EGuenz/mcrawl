#!/usr/bin/env python3
import argparse
import socket
from queue import Queue
import sys
import re
import os

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-n", metavar = "max-flows", type=int, help = "number of maximum threads your crawler can spawn to perform a cooperative crawl", required = True)
    parser.add_argument("-h", metavar = "hostname", help = "hostname of the server to crawl data from", required = True)
    parser.add_argument("-p", metavar = "port", type=int, help = "port number on the server where the web server is running", required = True)
    parser.add_argument("-f", metavar = "file", help = "local directory to host the download files", required = True)
    args = parser.parse_args()
    return args

def open_socket():
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as err:
      eprint('1: Cant open socket')
      exit(1)
    return s

def try_connect(s, host, port):
    try:
        s.connect((host, port))
    except Exception as err:
        s.close()
        eprint('1: Cant connect to server')
        exit(1)

def format_request(file, host, cookie):
    message = "GET " + file + " HTTP/1.1\r\n"
    message += "Host: " + host + "\r\n"
    if not cookie:
       message += "\r\n"
       return message
    message += "Set-Cookie: " + cookie + "\r\n\r\n"
    return message

def try_request(s):
    response = s.recv(1024).decode("utf-8")
    print(response)
    if not response.startswith('HTTP/1.1 200 OK'):
      return(response, 0)
    return(response, 1)

'''
def response_length(s, response):
    length_line = response.splitlines()[6]
    if not length_line.startswith('Content-Length:'):
        s.close()
        eprint('1: Bad Request: Content-Length not included')
        exit(1)
    nums = re.search(r'\d+', length_line)
    if nums is None:
      s.close()
      eprint('1: Bad Request: Content-Length not included')
      exit(1)
    return int(nums.group())
'''

def get_cookie(response):
    index = response.find('Set-Cookie: ')
    if index < 0:
        return ''
    index += 12
    response = response[index:]
    semi = response.find(';')
    if semi < 0:
        return '', ''
    cookie = response[:semi]
    return cookie

def handle_links(response, queue):
    #r = re.compile('/<a\s[^>]*href=\"([^\"]*)\"[^>]*>(.*)<\/a>/siU')
    r = re.compile('(?<=href=").*?(?=")', re.IGNORECASE)
    links = r.findall(response)
    if not links:
        return
    for link in links:
        print(link)
        queue.put(link)
    return

def crawl(s, first_response, q, host, file):
    path=os.getcwd()+file
    f = open(path, 'w')
    f.write(first_response)
    length = len(first_response)
    cookie = get_cookie(first_response)
    handle_links(first_response, q)
    while length == 1024:
        response = s.recv(1024).decode("utf-8")
        length = len(response)
        if length <= 0:
            break
        f.write(response)
        handle_links(response, q)
    f.close()

    if not q.empty():
        good = 0
        while not good:
          file = q.get()
          message = format_request(file, host, cookie)
          print(message)
          s.sendall(message.encode('utf-8'))
          response, good = try_request(s)
        #bytes_expected = response_length(s, response)
        crawl(s, response, q, host, file)
    return

def main():
    args = parse_args()
    s = open_socket()
    try_connect(s, args.h, args.p)
    message = format_request(args.f, args. h, '')
    s.sendall(message.encode('utf-8'))
    response, good = try_request(s)
    if not good:
        s.close()
        eprint("1: bad request")
        exit(1)
    #bytes_expected = response_length(s, response)
    q = Queue()
    crawl(s, response, q, args.h, args.f)
    return

main()
