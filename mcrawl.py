#!/usr/bin/env python3
import argparse
import socket
from queue import Queue

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-n", metavar = "max-flows", type=int, help = "number of maximum threads your crawler can spawn to perform a cooperative crawl", required = True)
    parser.add_argument("-h", metavar = "hostname", help = "hostname of the server to crawl data from", required = True)
    parser.add_argument("-p", metavar = "port", type=int, help = "port number on the server where the web server is running", required = True)
    parser.add_argument("-f", metavar = "file", help = "local directory to host the download files", required = True)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()

main()
