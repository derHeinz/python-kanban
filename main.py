#/usr/bin/env python

"""A simple Kanban board application using Flask and SQLLite"""

import signal
import sys
import time

from app import NetworkAPI
from database import db

api = NetworkAPI(db)
exit_flag = False

def main():
	signal.signal(signal.SIGINT, signal_handler)
	api.setDaemon(True)
	api.start()
	
	signal.pause()
	sys.exit(0)
	
def signal_handler(sig, frame):
	exit_flag = True

if __name__ == '__main__':
    main()
