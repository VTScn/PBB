#coding=utf-8

import tornado.web
import time
from markdown import Markdown
import re
from tornado.escape import xhtml_escape

html_killer = re.compile('<[^>]*>')
url_replace = re.compile(u'((?:HTTP|HTTPS|FTP|ED2K|THUNDER|FLASHGETX|http|https|ftp|ed2k|thunder|flashgetx)://[^ <"]+(?!</a>)[^ "])')
username_finder = re.compile(u'@([\u4e00-\u9fa5A-Za-z0-9]+)')

md = Markdown(extensions=['fenced_code','smart_strong','tables'])

class BaseHandler(tornado.web.RequestHandler):

    def __init__(self,*args,**kwargs):
        tornado.web.RequestHandler.__init__(self,*args,**kwargs)
        #方便调用
        self.db = self.application.db

    def get_current_user(self):
        user = self.get_secure_cookie('user')
        return self.db.users.find_one({'username':user})

    def get_error_html(self,status_code, **kwargs):
        return self.render_string('404.html')

    def render(self, template_name, **kwargs):
        unread = 0
        try:
            for x in self.get_current_user()['notification']:
                if not x['read']:
                    unread += 1
        except:
            pass
        tornado.web.RequestHandler.render(self,template_name=template_name,db=self.db,unread=unread,**kwargs)



def time_span(t):
    timecha = int(time.time()) - t
    if timecha < 60:
        return str(timecha)+u'秒前'
    elif timecha < 3600:
        return str(timecha/60)+u'分钟前'
    elif timecha < 86400:
        return str(timecha/3600)+u'小时前'
    elif timecha < 1296000:
        return str(timecha/86400)+u'天前'
    else:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t+28800))

def md_convert(txt,notice=False,time=None,user=None,db=None,postid=None):
    #滤去html标签
    for x in set(html_killer.findall(txt)):
        txt = txt.replace(x,xhtml_escape(x))

    txt = md.convert(txt).replace('\n','<br />')

    mentions = []

    for x in set(url_replace.findall(txt)):
        txt = txt.replace(x,u'<a href="%s">%s</a>%s' % (x[:-1],x[:-1],x[-1]))

    for u in set(username_finder.findall(txt)):
        mentions.append(u)
        txt = txt.replace(u'@'+u,u'<a href="/user/%s">@%s</a>' % (u,u))

    if notice:
        for u in mentions:
            db.users.update({'username':u},
            {'$push':
                     {'notification':
                              {'from':user,
                               'content':txt,
                               'time':time,
                               'postid':postid,
                               'read':False,
                               }
                     },
            })

    return txt


def getvalue(dict,keyname):
    try:
        return dict[keyname]
    except:
        return ''