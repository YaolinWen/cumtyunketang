from ykt import Ykt
import os

if __name__ == '__main__':
    from passwd import user, passwd

    ykt = Ykt()
    if ykt.login(user,passwd): # 登录
        print('登录成功') 

        print('课程列表', ykt.getClassNames(0)) # 打印云课堂上有记录的课程名称

        if not os.path.exists('.\\output1'): os.mkdir('.\\output1') # 新建一个文件夹用来保存下载好的课程。
        ykt.downloadAllByClassName('python编程之美', 0, '.\\output1',12) # 不区分大小写，支持只给子串
    else:
        print('登录失败')
    

    
