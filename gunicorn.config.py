# file gunicorn.conf.py
# coding=utf-8
# Reference: https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

import os

loglevel = 'info'

bind = '0.0.0.0:' + os.environ['PORT']
workers = 1

timeout = 1 * 60  # 1 minutes
keepalive = 24 * 60 * 60  # 1 day

capture_output = True
