'''
Author: Edward Wen
Last Edit: 2022.10.7
github: https://github.com/Edelweiss-qianyu
用于下载抗大云课堂中课程视频的库
'''

import requests as rq
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import hashlib
import json
from logging import warn
import os

# =================加密=================


# 统一认证登录的密码加密方案
def randomString(n):
    return '2'*n

def getAesString(data:str, key0, iv0):
    data = data.encode('utf-8')
    data = pad(data, 16,'pkcs7')
    key0 = key0.encode('utf-8')
    iv0 = iv0.encode('utf-8')

    encrypted = AES.new(key=key0, mode=AES.MODE_CBC,iv=iv0)
    return encrypted.encrypt(data)

def encryptAES(data, aesKey):
    if(not aesKey): return data
    encrypted = getAesString(randomString(64) +data, aesKey, randomString(16))
    return encrypted

def encryptPassword(pwd0, key): # 实际用来加密的函数
    res= encryptAES(pwd0, key)
    return base64.b64encode(res)


# 访问云课堂应用云函数时需要的validCode
def md5(s):
    md5hash = hashlib.md5(s.encode('utf-8'))
    return md5hash.hexdigest()

def validCode():
    validCode.val = md5("&signKey=123123")
    return validCode.val

def validCodeVideo(videoDetailId):
    t="id="+videoDetailId+"&signKey=123123"
    return md5(t)

def validCodeUserId(userId):
    t="id="+userId+"&signKey=123123"
    return md5(t)


# html查找元素的函数
def findValueById(html:str, id):
    # 用来在html中找到指定id的元素对应的value
    pattern = f'id="{id}"'
    pos = html.find(pattern)
    if pos == -1: raise ValueError(f'"{id} not found')

    pattern = 'value="'
    begin = html.find(pattern, pos) + len(pattern)
    end = html.find('"', begin)
    return html[begin: end]

h = {  # header
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    }


# =========云课堂网络应用函数===============
def yktLogin(sess:rq.session, user:str, passwd:str, /,h=h):
    # 返回userId

    urlloginpage = 'http://authserver.cumt.edu.cn/authserver/login?service=http://class.cumt.edu.cn/ssoserver/login/singleSignOnSchool?platform=002,4,010'
    urllogin = 'http://authserver.cumt.edu.cn/authserver/login?service=http%3A%2F%2Fclass.cumt.edu.cn%2Fssoserver%2Flogin%2FsingleSignOnSchool%3Fplatform%3D002%2C4%2C010'
    
    # 获取登录页
    resp1 =sess.get(urlloginpage,headers=h)
    loginpage = resp1.text
    
    # 登录
    body = {
        'username': user,
        'password': encryptPassword(passwd, findValueById(loginpage, 'pwdEncryptSalt')),
        'captcha': '',
        '_eventId': 'submit',
        'cllt': 'userNameLogin',
        'dllt': 'generalLogin',
        'lt': '',
        'execution': findValueById(loginpage, 'execution')
    }
    resp2 = sess.post(urllogin,data=body, headers=h,allow_redirects=False)

    # 获取ticket
    assert(resp2.status_code == 302)
    redirect1 = sess.get(resp2.headers['location'],headers=h,allow_redirects=False)
    assert(redirect1.status_code == 302)
    redirect2 = sess.get(redirect1.headers['location'], headers=h,allow_redirects=False)

    urlWithTicket = redirect2.headers['location']
    ticket = urlWithTicket[urlWithTicket.find('ticket=') + len('ticket='): ]

    # 获取userId
    urlGetUserId = f'http://class.cumt.edu.cn:8080/authoritycontrolplatformapi//api/v1/tickets/{ticket}?ticket={ticket}&validCode={validCode()}'
    sess.options(urlGetUserId,headers=h,allow_redirects=False)
    resp3 = sess.get(urlGetUserId, headers=h,allow_redirects=False)
    userId = json.loads(resp3.text)['userId']
    
    return userId

def yktGetTerms(sess, /,h=h):
    # 获取学年和学期，返回四元数组，分别表示本学期，上一个学期，上两个学期，上三个学期
    urlGetTerms = f'http://class.cumt.edu.cn:8080/courseApi//v1/terms/nowandlastthreeterm?validCode={validCode()}'
    resp4 = sess.get(urlGetTerms, headers=h)
    terms = json.loads(resp4.text)
    return terms

def yktGetClassesInfo(sess, userId, term, /, h=h):
    # 获取指定学期的所有课程的信息
    urlGetClassesInfo = f'http://class.cumt.edu.cn:8080/teachingApi//v1/videoinfo/student/courses?studentId={userId}&schoolYear={term["schoolYear"]}&term={term["term"]}&validCode={validCode()}'
    sess.options(urlGetClassesInfo, headers=h)
    resp5 = sess.get(urlGetClassesInfo,headers=h)
    classes = json.loads(resp5.text)
    return classes

def yktGetCourseVideos(sess,term, classItem, /, h=h):
    # 获取指定学期指定课程所有视频的简要信息
    classId = classItem['classIds']
    urlGetCourseVideos = f'http://class.cumt.edu.cn:8080/teachingApi//v1/videoinfos?groupIds={classId}&openStatus=1&week=&schoolYear={term["schoolYear"]}&term={term["term"]}&validCode={validCode()}'
    sess.options(urlGetCourseVideos, headers=h)
    resp6 = sess.get(urlGetCourseVideos, headers=h)
    videos = json.loads(resp6.text)
    return videos

def yktGetVideoDetail(sess, video):
    # 获取一个视频的详细信息
    urlGetCourseDetail = f'http://class.cumt.edu.cn:8080/teachingApi//v1/videoinfo/{video["id"]}?validCode={validCodeVideo(video["id"])}'
    sess.options(urlGetCourseDetail, headers=h)
    resp7 = sess.get(urlGetCourseDetail, headers=h)
    videoDetail = json.loads(resp7.text)
    return videoDetail


# ================处理课程信息的几个简单函数================

def findClassInfoByName(classes, className):
    # 在课程列表中寻找指定名称的课程，可以不区分大写、部分匹配，如想查找Python编程之美，
    # 可以设置className='python'
    className = className.lower()
    for item in classes:
        if className in item['courseName'].lower():
            return item
    return None

def getVideoDate(video):
    # 获得指定课程信息中的日期时间，如08-23 19:00-19:50
    return video['videoInfoName']

def getVideoWeek(video):
    # 获取当前视频是第几周的
    return int(video['week'])

def getVideoUrl1(videoDetail):
    # 获得指定课程信息中黑板视角视频的链接
    viewFiles = videoDetail['studentViewFiles']
    if len(viewFiles) == 0: return None
    return videoDetail['innerIp'] + '/' + viewFiles[0]['videoStorePath']

def getVideoUrl2(videoDetail):
    # 获得指定课程信息中电脑投屏视频的链接
    viewFiles = videoDetail['vgaViewFiles']
    if len(viewFiles) == 0: return None
    return videoDetail['innerIp'] + '/' + viewFiles[0]['videoStorePath']

def getVideoUrl3(videoDetail):
    # 获得指定课程信息中教师视角视频的链接
    viewFiles = videoDetail['teacherViewFiles']
    if len(viewFiles) == 0: return None
    return videoDetail['innerIp'] + '/' + viewFiles[0]['videoStorePath']

def download(url, saveto):
    # 下载url到本地
    resp = rq.get(url)
    if resp.status_code == 404:
        return False
    with open(saveto, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024*1024*5):
            # 每1024个字节为一块进行读取
            if chunk:
                # 如果chunk不为空
                f.write(chunk)                
    return True

# ===============封装成对象=================
class Ykt:
    def __init__(self, session = None):
        if session is None:
            session = rq.session()
        self.sess = session
    
    def login(self, user, passwd):
        try:
            self.userId = yktLogin(self.sess,user,passwd)
            return True
        except:
            return False
        
    def getTerms(self):
        return yktGetTerms(self.sess)
    def getClassesInfo(self, term):
        return yktGetClassesInfo(self.sess, self.userId, term)
    
    def getClassesInfoByName(self, className, termId=0):
        term = self.getTerms()[termId]
        classes = self.getClassesInfo(term)
        classItem = findClassInfoByName(classes, className)
        return classItem
    
    def getClassNames(self,termId=0):
        term = self.getTerms()[termId]
        classes = self.getClassesInfo(term)
        ret = []
        for classItem in classes:
            ret.append(classItem['courseName'])
        return ret
        
    
    def getCourseVideos(self,term, classInfo):
        return yktGetCourseVideos(self.sess, term, classInfo)

    def getVideoDetail(self, video):
        return yktGetVideoDetail(self.sess,video)
    
    def download(self, videoDetail, saveToDir='.', select=12, replace_old=False, print_info=True):
        '''
            下载一节课的一个或多个视角视频
            select 要下载的视角可选 1,2,3,或者几个数字的组合，如12，23，13，123
            三个数字各代表下面三个视角：
                1  学生视角
                2  电脑屏幕录像
                3  教师视角
            replace_old 是否覆盖旧文件，默认不覆盖
        '''
        if videoDetail['studentViewFiles'] is None:
            videoDetail = self.getVideoDetail(videoDetail)

        dateinfo = getVideoDate(videoDetail)
        weekinfo = getVideoWeek(videoDetail)

        if print_info:
            print(f"正在下载:第{weekinfo}周 {dateinfo}")
        
        select = str(select)
        if '1' in select:

            url = getVideoUrl1(videoDetail)
            if url is None:
                warn('f{dateinfo} 对应的1号"学生视角"视频不存在')
            else:
                path = os.path.join(saveToDir, f'week{weekinfo} '+dateinfo.replace(':','.') + ' ch1.mp4')
                
                if not replace_old and not os.path.exists(path): 
                    download(url,path)
        
        if '2' in select:
            url = getVideoUrl2(videoDetail)
            if url is None:
                warn(f'{dateinfo} 对应的2号"电脑屏幕录像"视频不存在')
            else:
                path = os.path.join(saveToDir, f'week{weekinfo} '+dateinfo.replace(':','.') + ' ch2.mp4')
                
                if not replace_old and not os.path.exists(path): 
                    download(url,path)
        
        if '3' in select:
            url = getVideoUrl3(videoDetail)
            if url is None:
                warn(f'{dateinfo} 对应的3号"教师视角"视频不存在')
            else:
                path = os.path.join(saveToDir, f'week{weekinfo} '+dateinfo.replace(':','.') + ' ch3.mp4')
                
                if not replace_old and not os.path.exists(path): 
                    download(url,path)

    def downloadAll(self, videos, saveToDir='.', select=12, replace_old=False, print_info=True):
        if print_info: print(f'即将下载课程：{videos[0]["courseName"]} 到:{os.path.abspath(saveToDir)}')
        for video in videos:
            videoDetail = self.getVideoDetail(video)
            self.download(videoDetail,saveToDir,select, replace_old, print_info)
    
    def downloadAllByClassName(self,className, termId=0, saveToDir='.', select=12,replace_old=False, print_info=True):
        '''
            按课程名称下载指定课程录像
            className 课程名称
            termId 0表示当前学期，1表示上学期，2表示上两学期，3表示上三学期。
            select 要下载的视角可选 1,2,3,或者几个数字的组合，如12，23，13，123
            三个数字各代表下面三个视角：
                1  学生视角
                2  电脑屏幕录像
                3  教师视角
            replace_old 是否覆盖旧文件，默认不覆盖
        '''
        term = self.getTerms()[termId]
        classes = self.getClassesInfo(term)
        classItem = findClassInfoByName(classes, className)
        videos = self.getCourseVideos(term, classItem)
        self.downloadAll(videos, saveToDir,select,replace_old, print_info)



if __name__ == '__main__':
    user = input('请输入账号:')
    passwd = input('请输入密码:')

    sess = rq.session()

    userId = yktLogin(sess,user,passwd) # 登录
    print(userId)
    term = yktGetTerms(sess)[0] # 0表示当前学期
    
    classes = yktGetClassesInfo(sess,userId,term) # 本学期所有课程信息
    pythonClass = findClassInfoByName(classes, 'python编程') # 允许匹配子串和不区分大小写

    videos = yktGetCourseVideos(sess,term, pythonClass) # 所有视频的简介
    
    for video in videos: # 打印每堂课的三个视角
        videoDetail = yktGetVideoDetail(sess, video)
        
        dateinfo = getVideoDate(video)
        weekinfo = getVideoWeek(video)
        url1 = getVideoUrl1(videoDetail)
        url2 = getVideoUrl2(videoDetail)
        url3 = getVideoUrl3(videoDetail)

        print(f'第{weekinfo}周：', dateinfo )
        print('学生视角视频链接：', url1)
        print('电脑录频视频链接：', url2)
        print('教师视角视频链接：', url3)
    
    # 对象化
    # ykt = Ykt()
    # if ykt.login(user,passwd):
    #     print('登录成功')

    #     print('课程列表', ykt.getClassNames(0))

    #     if os.path.exists('.\\output1'): os.mkdir('.\\output1')
    #     ykt.downloadAllByClassName('python编程之美', 0, '.\\output1',12)
    # else:
    #     print('登录失败')
    
    
    
