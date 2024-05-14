import os

loglevel = 'info'

bind = '0.0.0.0:' + os.environ['PORT']
workers = 2

timeout = 1 * 60  # 1 minutes
keepalive = 24 * 60 * 60  # 1 day

capture_output = True
