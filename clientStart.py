import os,time
from socket import *
from xinyou.caction import *
from xinyou.clientActor import *

# 当前管理的游戏目录 [client对象,client对象备份，目录名称]
currentGame = ['empty','','']
currentMsg = ''
# 启动游戏后 所有server端的消息集合
allGameInfo = {}
clientDict = {}
cmdtype = ['game']


# 从config.ini获取 所有连接的配置信息  ip  port
serverList = getServerIpPort()
print(serverList)
# 判断配置文件内容是否完整
if serverList == False:
    exit()
# 根据上面的ip port 创建client组
clientList = getClientGroup(serverList)
# 从服务器获取 初始目录消息
allGameInfo,clientDict = client_getServerGameInfo(clientList)


while True:
    returnMSG = []
    data = input(currentGame[2]+':>')
    cmd = data.strip()
    # 对输入命令分析判断
    checkResult = command_simpleCheck(cmd,allGameInfo,currentGame,cmdtype,clientDict)

    print(checkResult)
    if checkResult == False:
        continue
    # 输入exit后  退出程序操作
    elif checkResult ==1:
        break
    # 合法的命令，发送到服务器 端
    elif type(checkResult) == list:
        # 发送命令 到对应的服务器
        returnMSG = sendMSG(checkResult,currentGame,cmdtype)
    else:
        print('程序出错 checkResult:')
        print(checkResult)
        break


    if returnMSG[0] == 'print':
        print(returnMSG[1])

    elif returnMSG[0] in ['get','put','update']:
        transfer_File(currentGame,returnMSG[1],returnMSG[0])
    # elif returnMSG[0] == 'get':
    #     transfer_File(currentGame,returnMSG[1], 'get')
    # elif returnMSG[0] == 'put':
    #     transfer_File(currentGame,returnMSG[1],'put')
    # elif returnMSG[0] =='update':
    #     transfer_File(currentGame,returnMSG[1],'update')
    elif returnMSG[0] == 'compare':
        compare_cmd_client(currentGame[2],returnMSG[1])
    elif returnMSG[0] == 'stopRoom':
        stopRoomMSG_pre(returnMSG)
        stopSyc(currentGame[1])
    else:
        pass

        # 解析返回的消息







