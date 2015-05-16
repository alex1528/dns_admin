#-*- coding: utf-8 -*-

LOG_DIR = "./logs"
LOG_FILE = "dns-admin.log"

BIND_IP = "0.0.0.0"
BIND_PORT = 8083

# named 模板文件路径
BIND_TEMPLATE_DIR = "dns_admin/conf/"
BIND_TEMPLATE_FILE = "template.conf"

# Redis 用于存储 session 信息.
REDIS_HOST = ""
REDIS_PORT = 6379
REDIS_DB = "0"

# Mysql 配置.
MYSQL_HOST = ""
MYSQL_PORT = "" 
MYSQL_USER = ""
MYSQL_PASSWD = "" 
MYSQL_DATABASE = ""
