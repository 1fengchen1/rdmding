# rdmding是一个将redmine上bug提醒到钉钉群组的一个功能
## 实现业务思路
1，在钉钉群组里开启“群机器人-自定义机器人”，获取webhook，由每个群的群主(产品经理)设置；每个redmine项目对应一个群，如果一个项目有同时有多个需求，就创建多个群(ERP1,ERP2)   
2，监控redmine日志，当日志出现一定格式的信息(信息包含需要的信息)，就触发一个request请求发送到对应的钉钉项目群里  
3，数据部分：将redmine里的user映射到钉钉user；解析redmine日志信息设置触发条件，触发request；  
## 环境 
OS：Windows、linux  
python：py3  
## 配置
在config.ini文件里配置redmine数据库，钉钉数据库，钉钉群组
## 运行
python rmdingding.py  
## linux 后台运行
运行前先查看后台运行的个数：  
ps -ef |grep rmdingding.py  
如果没有进程，再运行下面，否则就先kill掉已经在运行的
setsid python rmdingding.py  
