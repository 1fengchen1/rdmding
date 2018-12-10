import re
import tail
import requests
import json
from connectdb import DB
from config import conf


def isHTML(line):
    if re.compile(r'IssuesController#create as HTML').findall(line):
        now = '1'
    elif re.compile(r'IssuesController#update as HTML').findall(line):
        now = '2'
    else:
        now = '0'
    # print(now)
    with open('rmding.txt', 'r+') as f:
        old = [line.strip() for line in f.readlines()]
        # print('isHtml1:', old)
        old[0] = old[1] + '\n'
        old[1] = now + '\n'
        # print('isHtml2:', old)
    with open('rmding.txt', 'w+') as f:
        new = f.writelines(old)


class RMDATA:
    'redmine数据获取'

    def __init__(self, line, up):
        self.line = line
        self.tracker = 7  # bug是7
        self.data = {}
        self.up = up

    def __str__(self):
        return 'data is {}'.format(self.data)

    def get(self):
        '''
        解析create as HTML
        parameter: tracker_id issue的属性[bug, 需求...]
        return： list[up, project_id, tracker_id, status_id, subject, assigned_to_id]
        '''
        tracker_id = re.compile(r'"tracker_id"=>"(\d*)"').findall(self.line)[0]

        if int(tracker_id) != self.tracker:
            return False

        if self.up == '1':
            # create as HTML
            project_id = re.compile(r'"project_id"=>"(.*?)"').findall(self.line)[0]
            self.up = 'create'
            due_date = re.compile(r'"due_date"=>"(.*?)"').findall(self.line)[0]
            if due_date:
                # due_date为空，redmine会报错，这里进行为空的过滤
                self.data.update({'due_date': due_date})
            else:
                return False
        elif self.up == '2':
            # update as HTML
            project_id = re.compile(r'"project_id"=>"(\d*)"').findall(self.line)[0]
            self.up = 'update'
            bug_id = re.compile(r'"id"=>"(\d*)"').findall(self.line)[0]
            self.data.update({'bug_id': bug_id})
        else:
            return False
        status_id = re.compile(r'"status_id"=>"(\d*)"').findall(self.line)[0]
        print(re.compile(r'"status_id"=>"(\d*)"').findall(self.line))
        subject = re.compile(r'"subject"=>"(.*?)"').findall(self.line)[0]
        assigned_to_id = re.compile(r'"assigned_to_id"=>"(\d*)"').findall(self.line)[0]
        parent_issue_id = re.compile(r'"parent_issue_id"=>"(\d*)"').findall(self.line)[0]
        priority_id = re.compile(r'"parent_issue_id"=>"(\d*)"').findall(self.line)[0]

        self.data.update({'now': self.up, 'project_id': project_id, 'tracker_id': tracker_id, 'subject': subject,
                          'assigned_to_id': assigned_to_id, 'parent_issue_id': parent_issue_id,
                          'priority_id': priority_id, 'status_id': status_id})
        print('self.data: ', self.data)
        return self.data


class DATA:
    '将redmine获得数据进行处理'

    def __init__(self, msg):
        self.msg = msg
        self.__cfg = conf()
        self.now = ''
        self.project = ''
        self.parent = ''
        self.email = ''
        self.subject = ''
        self.phone = ''
        self.url = ''
        self.token = ''
        self.status = ''

    def data_map(self):
        """
        将redmine获得的mes，进行tbs映射处理
        :param mes:
        :return: 直接要发送到钉钉的数据:父级名，项目名，bug主题，指派人phone，bugurl(父级url)
        """
        if self.msg is False:
            return False

        with DB('RDM-SQL') as db:
            # sql_parent = 'select subject from issues where id="{}";'.format(self.msg['parent_issue_id'])
            sql_email = 'SELECT address FROM email_addresses WHERE user_id="{}";'.format(self.msg['assigned_to_id'])
            sql_status = 'SELECT name FROM issue_statuses WHERE id="{}";'.format(self.msg['status_id'])

            db.execute(sql_email)
            self.email = list(db.fetchone())[0].split('@')[0]

            db.execute(sql_status)
            self.status = list(db.fetchone())[0].split('@')[0]
            print(self.status)
            self.parent = self.msg['parent_issue_id']

            self.subject = self.msg['subject']

            if self.msg['now'] == 'create':
                # sql_project = 'select name from projects where identifier="{}";'.format(self.msg['project_id'])
                self.project = self.msg['project_id']
                self.url = 'http://172.16.1.62/redmine/issues/' + self.msg['parent_issue_id']
            elif self.msg['now'] == 'update':
                sql_project = 'select identifier from projects where id="{}";'.format(self.msg['project_id'])
                db.execute(sql_project)
                self.project = list(db.fetchone())[0]
                self.url = 'http://172.16.1.62/redmine/issues/' + self.msg['bug_id']

            self.now = self.msg['now']

        with DB('TBS-SQL') as db:
            sql_phone = 'SELECT phone FROM t_erp_employee WHERE email_account LIKE "{}%";'.format(self.email)
            db.execute(sql_phone)
            # 返回数据('18617023010',)需要进行处理为'18617023010': 先转化成list，再取值
            self.phone = list(db.fetchone())[0]
        try:
            self.token = self.__cfg.get('dingding', self.project)
        except Exception as e:
            print('Error:', e)
            return False

        if self.status == '已解决' or '重新打开' or '拒绝' or '新建':
            # print(self.parent, self.email, self.subject, self.project, self.url, self.phone, self.token)
            return {'project': self.project, 'subject': self.subject, 'status':self.status,
                    'phone': self.phone, 'url': self.url, 'token': self.token}
        else:
            return False


def request(data):
    '''
    parameter: list(data), str(dingding)
    return: True Flae
    '''
    url = 'https://oapi.dingtalk.com/robot/send?access_token=' + data['token']
    headers = {"Content-Type": "application/json; charset=utf-8"}
    msg = {
        "msgtype": "text",
        "text": {
            "content": "【{}】\n[bug标题]: {}\n[url]: {}\n@{}".format(data['status'], data['subject'], data['url'], data['phone'])
        },

        "at": {
            "atMobiles": ["{}".format(data['phone'])],
            "isAtAll": False,
        }
    }

    msg = json.dumps(msg)
    r = requests.post(url, data=msg, headers=headers)
    print(r.text)


def data(txt):
    '回调函数'
    isHTML(txt)
    with open('rmding.txt', 'r') as f:
        # 将上游数据暂时存在rmding.txt文件，up为1则开始记录数据
        up = [line.strip() for line in f.readlines()]
    if up[0] != '0':
        msg = RMDATA(txt, up[0]).get()
        # 对data进行映射
        msg = DATA(msg).data_map()
        if msg:
            print(msg)
            request(msg)


def run():
    t = tail.Tail('/opt/redmine-3.4.5-0/apps/redmine/htdocs/log/production.log')
    t.register_callback(data)
    t.follow(s=3)


def runding():
    data = ''
    dingding = 'https://oapi.dingtalk.com/robot/send?access_' \
               'token=f14f165490fbba76611d47b36ea0ca3f49184e220448ad877d2f0ba3ec826125'
    request(data, dingding)


if __name__ == "__main__":
    run()
