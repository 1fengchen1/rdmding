import configparser as config
import sys

def conf():
    file = 'config.ini'
    cfg = config.ConfigParser()  # 创建一个管理对象cfg
    try:
        cfg.read(file, encoding='utf-8')  # 把ini文件读到cfg中
        return cfg
    except Exception as e:
        print('ERROR：', e)
        sys.exit(1)
