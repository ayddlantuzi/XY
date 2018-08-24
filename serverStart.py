# encoding: utf-8
from socket import *
from time import ctime
from xinyou.saction import *

import tempfile

HOST = ''
# 获取Sconfig.ini  返回gamedir,PORT
gamedir,PORT = getSconfig()

print('端口：' + str(PORT))
print('游戏目录：' + gamedir)

#当前管理的游戏
currentGame=['']


BUFSIZ = 2048
ADDR = (HOST, PORT)



tcpSerSock = socket(AF_INET,SOCK_STREAM)
# tcpSerSock.setblocking(0)
tcpSerSock.bind(ADDR)
tcpSerSock.listen(5)

#初始化 serverGameInfo
serverGameInfoList = gameInfoFile(gamedir)

while True:
    print('waiting for connection...')
    tcpCliSock,addr = tcpSerSock.accept()
    print('...connectecd from:',addr)

    data = tcpCliSock.recv(BUFSIZ).decode()

    if not data:
        break

    dataList = json.loads(data)

    # 命令检查
    if dataList == ['getinfo']:
        tcpCliSock.send(bytes(json.dumps(serverGameInfoList),encoding='utf-8'))
    elif dataList == ['checkMSG']:
        msg = checkMSG_Server()
        tcpCliSock.send(bytes(json.dumps(msg), encoding='utf-8'))
    else:
        msg = command_ServerCheck(dataList,serverGameInfoList)
        print('msg:',msg) 
        # 消息反馈
        tcpCliSock.send(bytes(json.dumps(msg),encoding='utf-8'))

    tcpCliSock.close()
tcpSerSock.close()