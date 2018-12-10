import pymysql
from config import conf

class DB:
    def __init__(self, name):
        self.__cfg = conf()
        self.cursor = ''
        self.__name = name

    def __enter__(self):
        db_host = self.__cfg.get(self.__name, 'db_host')
        db_user = self.__cfg.get(self.__name, 'db_user')
        db_pwd = self.__cfg.get(self.__name, 'db_pwd')
        db_dbname = self.__cfg.get(self.__name, 'db_dbname')
        self.connection = pymysql.connect(host=db_host,
                                          user=db_user,
                                          password=db_pwd,
                                          db=db_dbname)
        self.cursor = self.connection.cursor()

        self.__handle = self.cursor
        return self.__handle

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__handle.close()

# tbs的邮箱地址
# sql = "SELECT * FROM t_erp_employee WHERE email_account LIKE 'sonny.zhang%';"

if __name__ == "__main__":
    #     rdm = DB()
    # sql = "select version()"
    # rdm.connect('RDM-SQL', sql)
    with DB('RDM-SQL') as db:
        sql = 'select version()'
        db.execute(sql)
        data = db.fetchone()
        print(data)
