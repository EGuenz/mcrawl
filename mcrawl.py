#!/usr/bin/env python3
import argparse
import socket
from queue import Queue
import sys
import re
import os
import threading

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
    return(message)

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


def is_success(header):
    return header.startswith('HTTP/1.1 200 OK')

def get_chunk_size(s):
    size_str = s.recv(2)
    while size_str[-2:] != b"\r\n":
        size_str += s.recv(1)
    return int(size_str[:-2], 16)

def get_chunk_data(s, chunk_size):
    bytes_left = chunk_size
    chunk = b''
    while bytes_left > 0:
      buf_size = min(1024, bytes_left)
      data = s.recv(buf_size)
      chunk += data
      bytes_left -= len(data)
    return chunk

def is_text(response):
    index = response.find('Content-Type: ')
    if index < 0:
        return ''
    index += 14
    return("text" in response[index:])

def has_same_host(file, host):
    r = re.compile('(?:(?<=http)|(?<=https))://(.*?)(?:(?=/)|(?=$))', re.IGNORECASE)
    file_hosts = r.findall(file)
    if not file_hosts:
        return True
    return(file_hosts[0] == host)

def handle_links(response, queue, host, parsed_links):
    response_text = response.decode('utf-8')
    r = re.compile('(?:(?<=href=")|(?<=src=")).*?(?=")', re.IGNORECASE)
    links = r.findall(response_text)
    if not links:
        return
    for link in links:
        if has_same_host(link, host) and link not in parsed_links:
          queue.put(link)
          parsed_links.append(link)
    return

def open_file(filename, local_file):
  filename = os.path.basename(filename.rstrip('/'))
  filename = os.getcwd() + '/' + local_file + '/' + filename
  new_filename = filename
  if os.path.isfile(filename):
     v = 1
     k = filename.rfind(".")
     while True:
       new_filename = filename[:k] + "-" + str(v) + filename[k:]
       if not os.path.isfile(new_filename):
           break
       v+=1
  filename = new_filename
  if not os.path.exists(os.path.dirname(filename)):
      try:
        os.makedirs(os.path.dirname(filename))
      except OSError as exc:
        if exc.errno != errno.EEXIST:
          raise
  if os.path.isdir(filename):
       return -1
  f = open(filename, 'wb')
  return f

def get_header(s):
    total_response = s.recv(3)
    while True:
        response = s.recv(1)
        if not response:
            return ''
        total_response += response
        if total_response[-4:] == "\r\n\r\n".encode('utf-8'):
            break
    return total_response.decode('utf-8')

def download_file(s):
 header = get_header(s)
 if not is_success(header):
       return '', ''
 file = b''
 while True:
    chunk_size = get_chunk_size(s)
    if (chunk_size == 0):
        break
    else:
        chunk = get_chunk_data(s, chunk_size)
        file += chunk
        s.recv(2)
 s.recv(2)
 return header, file

def crawl(s, q, host, parsed_links, local_file, cookie):
    while True:
      if q.empty():
          try:
              filename = q.get(block=True, timeout= 2)
          except:
              return
      else:
          filename = q.get()

      if (not has_same_host(filename, host)) or ("#" in filename):
        continue
      filename = '/' + filename
      message = format_request(filename, host, cookie)
      s.sendall(message.encode('utf-8'))
      header, file = download_file(s)
      if not header or not file:
          continue
      isText = is_text(header)
      f = open_file(filename, local_file)
      if f == -1:
          continue
      break
    f.write(file)
    if isText:
       handle_links(file, q, host, parsed_links)
    f.close()
    if not cookie:
        cookie = get_cookie(header)
    crawl(s, q, host, parsed_links, local_file, cookie)
    return

def new_user(host, port, link_queue, parsed_links, local_file):
    s = open_socket()
    try_connect(s, host, port)
    crawl(s, link_queue, host, parsed_links, local_file, '')
    return

def main():
    args = parse_args()
    link_queue = Queue()
    link_queue.put('/index.html')
    parsed_links = []
    max_threads = min(args.n, 8)
    if max_threads < 1:
        return
    threads = []
    for x in range(max_threads):
       try:
          t = threading.Thread(target=new_user, args=(args.h, args.p, link_queue, parsed_links, args.f))
          t.start()
          threads.append(t)
       except:
          eprint('7: Unable to start user_thread')
          exit(1)

    for t in threads:
       t.join()
    return

main()
