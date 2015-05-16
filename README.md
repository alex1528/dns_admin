# 说明

1. 此系统用于管理机房服务器的 DNS 记录, 主域是 nosa.me;

2. 包含三个机房, 分别是 hy01, db01, hlg01, 用来表示主机名, 主机名唯一, 不可重复添加, 添加反向记录;

3. 包括一个内网域名, 叫 internal, 凡是 internal.nosa.me 的域名都表示内网域名, 可重复添加,
   但不添加反向记录, 故内网域名只能通过 "hostname" 来删除, 通过 "hostname" 删除会把所有内网域名
   都删掉;


# 功能

1. 对于增加操作, 如果是主机名, 会增加反向记录; 如果是内网域名, 不增加反向记录, 是不是内网域名通过是否是 internal 判断;

2. 对于修改操作, 需要指定是通过 hostname 还是 ip 修改, 如果指定了通过 hostname 修改, 会把匹配 hostname 的所有 IP 
   都修改成新的值, 反之亦然, 正向和反向记录都会被修改;

3. 对于查询操作, 需要指定是通过 hostname 还是 ip 查询;

4. 对于删除操作, 需要指定是通过 hostname 还是 ip 删除, 如果指定了通过 hostname 删除, 会把匹配上的所有记录都会删除;
   如果指定通过 ip 删除, 先根据 ip 查反向记录, 根据查到的 hostname 列表(可能有多个)拿到正向域列表, 然后去对应的正向域
   里删, 匹配到 ip 的反向记录也会删除(因为内网域名的 ip 不会记录到反向域中, 所以根据 ip 删内网域名没有效果, 
   故内网域名只能通过 hostname 删除);

5. 支持取某个域名信息的 API, 由 DomainHandler 实现;

6. 支持取所有域名信息的 API, 由 DomainALLHandler 实现;

7. 支持取某个域所有记录的 API, 由 RecordHandler 实现;

8. 支持取所有域所有记录的 API, 由 RecordALLHandler 实现;


# 操作脚本

在 root 身份下执行 sh [start.sh | stop.sh | restart.sh]


# 建表脚本

create database nosa_idc_dns;
use nosa_idc_dns;

create table hy01 (
    id int unsigned not null auto_increment,
    name varchar(100) not null,
    type varchar(10) not null,    
    value varchar(100) not null,
    primary key (id)
);

create table db01 (
    id int unsigned not null auto_increment,
    name varchar(100) not null,
    type varchar(10) not null,    
    value varchar(100) not null,
    primary key (id)
);

create table hlg01 (
    id int unsigned not null auto_increment,
    name varchar(100) not null,
    type varchar(10) not null,    
    value varchar(100) not null,
    primary key (id)
);

create table internal (
    id int unsigned not null auto_increment,
    name varchar(100) not null,
    type varchar(10) not null,    
    value varchar(100) not null,
    primary key (id)
);

create table reverse (
    id int unsigned not null auto_increment,
    name varchar(100) not null,
    type varchar(10) not null,    
    value varchar(100) not null,
    primary key (id)
);

create table domain (
    name varchar(50) not null,
    domain varchar(100) not null,    
    path varchar(100) not null,    
    serial int unsigned not null
);
insert into domain values("hy01", "hy01.nosa.me", "/var/named/named.hy01.nosa.me", 5500);
insert into domain values("db01", "db01.nosa.me", "/var/named/named.db01.nosa.me", 1200);
insert into domain values("hlg01", "hlg01.nosa.me", "/var/named/named.hlg01.nosa.me", 1500);
insert into domain values("internal", "internal.nosa.me", "/var/named/named.internal.nosa.me", 200);
insert into domain values("reverse", "10.in-addr.arpa", "/var/named/named.10.in-addr.arpa", 8000);


# 依赖, 程序里用到了如下库
pip install ujson 
pip install tornado
pip install DBUtils
pip install jinja2
yum -y install python-ldap MySQL-python 
