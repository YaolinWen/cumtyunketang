from ykt import Ykt
import os

if __name__ == '__main__':
    from passwd import user, passwd

    ykt = Ykt()
    if ykt.login(user,passwd):
        print('登录成功')

        print('课程列表', ykt.getClassNames(0))

        if os.path.exists('.\\output1'): os.mkdir('.\\output1')
        ykt.downloadAllByClassName('python编程之美', 0, '.\\output1',12)
    else:
        print('登录失败')
    

    


