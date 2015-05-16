#!/bin/bash

export PYTHONPATH=.

ps -ef |grep main.py |grep -v grep  |awk '{print $2}' |xargs sudo kill 

nohup python dns_admin/web/main.py &
