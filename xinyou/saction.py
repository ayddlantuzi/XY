#encoding: utf-8
import os
import socket
import os.path
import configparser
import codecs
import re
import tempfile
import time
import subprocess
import shutil
import win32gui,win32api,win32con
import threading
import json


game_match_serviceDict = {}
gamedir = ''
# 默认桌面目录
desktop_dir = 'D:\\Desktop\\'


timerState = False
timerList = []
timerMsg = []
timerLock = threading.Lock()

def runServiceLoader(path,xml):
    '''
    运行房间 path路径，xml配置文件端口的list
    :param path: 游戏路径 str
    :param xml: 游戏配置文件 list
    :return: 启动游戏后的消息  格式 'E:/game/游戏/12001.xml   命令执行！/r/n' 返回
    '''

    # 启动房间返回的消息
    run_msg_list = []
    # 筛选房间xml
    # 判断传入的是 部分xml还是all 并做初步的错误检查
    xml_list_getgamexml,error_msg_1 = get_gamexmlANDport(path,xml)
    # 判断端口是否被占用 占用的剔除
    xml_list,error_msg = check_xml_port_open(xml_list_getgamexml)
    error_msg.extend(error_msg_1)


    # xml = '疯狂跑得快初级场12611'
    # path = 'D:\\Game\\26CrazyRunFastServer'
    if xml_list[0] != 0:
        out_temp = tempfile.SpooledTemporaryFile(max_size=10 * 1000)
        fileno = out_temp.fileno()

        for xml_name in xml_list[1]:
            a=subprocess.run("for /f %i in (\'dir \""+path+"\\run\\"+xml_name+"\" /s /b\') do (start "+path+"\\ServiceLoader.exe \"auto\" \"%i\" && ping 127.0.0.1 /n 3 >nul)",stdout=fileno,shell=True)
            # a=subprocess.run("for /f %i in (\'dir \""+path+"\\run\\"+xml_name+".xml\" /s /b\') do (start "+path+"\\ServiceLoader.exe \"auto\" \"%i\" && ping 127.0.0.1 /n 3 >nul)",stdout=fileno,shell=True)
            time.sleep(0.5)
        # a.wait()
        out_temp.seek(0)
        lines = out_temp.readlines()
        out_temp.close()
        linesSend=[]
        for i in lines[1::2]:
            linesSend.append(i.decode('gbk'))
            print(i)

        run_msg_list = format_RunserviceLoader_Log(linesSend)


    all_msg_list = error_msg + run_msg_list
    all_msg_str = msgList_2_msgStr(all_msg_list)
    print('runServiceLoader  return:',end='')
    print(all_msg_str)
    return ['print',all_msg_str]




def format_RunserviceLoader_Log(msgList):
    '''
    将cmd启动脚本返回的str 过滤 简约显示，内容：*****.xml  启动成功
    :param msgList:启动消息List
    :return:
    '''
    # print('formatbefore:',end='')
    # print(msgList)
    return_msg_list = []
    for msg in msgList:
        a = msg.find('auto')+7
        b = msg.find('.xml')+4
        c = msg[a:b].split('\\\\')
        return_msg_list.append(c[0] + '   启动命令执行!')
    # print('formatafter:',end='')
    # print(return_msg_list)
    return return_msg_list



def msgList_2_msgStr(msgList):
    '''
    将信息的list 转换成str 返回给send
    :param msgList: 所有消息集合的Lists
    :return: 所有消息的str
    '''
    # print('msglist:')
    # print(msgList)
    n = len(msgList)
    # print('msglist   len:'+str(n))
    msgStr = ''
    for msg in msgList:
        msgStr += msg
        n -= 1
        if n != 0:
            msgStr += '\r\n'
    # print('msgStr:')
    # print(msgStr)
    return msgStr


def get_gamexmlANDport(path,xml):
    '''
    获得run目录下所有的房间配置
    :param path: 游戏目录
    :param xml: 启动的 游戏xml
    :return:[n,[],[]] [xml文件List，对应xml的Port List]   ,  消息List['','','','']
            [2,[ '疯狂跑得快新手场12601.xml' , '疯狂跑得快初级场12611.xml' ],[ 12601 , 12611 ]]
    端口号都是5位数字 文件名称末尾的5位
    '''
    # print('get_gamexmlANDport   start')
    temp_file = []
    xml_file = []
    temp_port = []
    error_msg = []
    n = 0

    all_file = os.listdir(path + '\\run')
    status = True

    # 遍历房间目录  所有xml文件存放到 xml_file
    for file in all_file:
        if os.path.splitext(file)[1] == '.xml':
            xml_file.append(file)
            status = False

    if status:
        msg = gamedir + '游戏目录run下没有xml '
        error_msg.append(msg)
        returnList = [0,[],[]]
        return returnList,error_msg


# 输入的[10021,10022] 检测端口 是否在xml 房间配置文件名中
    if type(xml) == list:
        for port in xml:
            status = True
            for file in xml_file:
                fileport = file[:-4][-5:]
                if port == fileport:
                    temp_file.append(file)
                    temp_port.append(port)
                    n += 1
                    status = False
            if status:
                msg = port + '   未匹配到对应的房间名称!'
                error_msg.append(msg)

# 信息提示需要修改？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？
    elif xml == 'all':
        for file in xml_file:
            port = file[:-4][-5:]
            if port.isdigit():
                temp_file.append(file)
                temp_port.append(port)
                n += 1
            else:
                error_msg.append(file+'端口异常，请检查!(文件名末尾5位数字端口 命名规则)')

    else:
        status = True
        for file in xml_file:
            port = file[:-4][-5:]
            # print('port:'+port)
            # print('xml:'+ xml)
            if xml == port:
                temp_file.append(file)
                temp_port.append(port)
                n += 1
                status = False
                break
        if status:
            error_msg.append(xml + '   未匹配到对应的房间名称!')

    returnList = [n,temp_file,temp_port]

    print('get_gamexmlANDport  end')
    print(returnList)
    return returnList,error_msg




def check_xml_port_open(xmllist,type = 'start'):
    '''
    检查房间xml的端口是否占用   xmllst中 相关占用端口移除，并返回消息
    :param xmllist:   [3,[ '疯狂跑得快新手场12601.xml' , '疯狂跑得快初级场12611.xml' , '疯狂跑得快顶级场12631.xml'],[ 12601 , 12611 , 12631]]
    :return:  筛选后的xmllist,端口占用消息['','']
        xmllist   [3,[ '疯狂跑得快新手场12601.xml' , '疯狂跑得快初级场12611.xml' , '疯狂跑得快顶级场12631.xml'],[ 12601 , 12611 , 12631]]
        如果12601，12611 被占用
        返回 [1,[ '疯狂跑得快顶级场12631.xml'],[ 12631]]  , ['12601   端口被占用！'，'12611   端口被占用！']

    '''
    print('check_xml_port_open   start')
    print('xmllist:',end='')
    print(xmllist)
    error_msg = []
    n = xmllist[0]
    if xmllist[0] != 0:
        for port in xmllist[2][:]:
            if type == 'start':
                if portISopen(int(port)):
                    index = xmllist[2].index(port)
                    xmllist[1].pop(index)
                    xmllist[2].pop(index)
                    n -= 1
                    msg = port + '   房间端口被占用！'
                    error_msg.append(msg)
            elif type == 'stop':
                if not portISopen(int(port)):
                    index = xmllist[2].index(port)
                    xmllist[1].pop(index)
                    xmllist[2].pop(index)
                    n -= 1
                    msg = port + '   房间端口未启用，无需关闭！'
                    error_msg.append(msg)
            else:
                pass

        xmllist[0] = n
    print('check_xml_port_open  end')
    return xmllist,error_msg



def getServerGameInfo_xml_check(path):
    '''
    判断目录下是否有xml 房间配置文件
    :param path: 游戏run配置文件目录
    :return: List列表 目录中的xml文件 ，Flase 不存在xml后缀文件
    '''
    file_path = os.listdir(path)
    if file_path == []:
        return False
    else:
        file_xml = []
        for i in file_path:
            if i[-4:] == '.xml':
                file_xml.append(i)

        if file_xml == []:
            return False
        else:
            return file_xml



def getServerGameInfo(game_match_serviceDict):
    '''
    返回游戏目录下  所有的游戏目录 run目录 xml文件
    :param path:  游戏根目录
    :return:原
        [[包含房间run文件夹的 游戏目录],[对应游戏目录 下的房间xml]]

     return  改
      {'gamedir':[[包含房间run文件夹的 游戏目录],[对应游戏目录 下的房间xml]] , 'matchdir':['DDZ-Flow-match','DDZ-Monthly-match'] ， 'servicedir':['redserver','rankserver']}

     return 改2
      {'gamedir':[包含房间run文件夹的 游戏目录] , 'matchdir':['DDZ-Flow-match','DDZ-Monthly-match'] ， 'servicedir':['redserver','rankserver']}


    '''
    gameInfo = {}
    if 'game' in game_match_serviceDict:
        path = game_match_serviceDict.get('game')
        firstList = os.listdir(path)
        secondList = []
        # thirdList = []
        for i in firstList:
            a = path + i
            xmlPath = a+'\\run'
            if os.path.isdir(a) and os.path.isdir(xmlPath):
                xmlresult = getServerGameInfo_xml_check(xmlPath)
                if xmlresult:
                    secondList.append(i)
                    # thirdList.append(xmlresult)
        # gameInfo.update({'game':[secondList,thirdList]})
        gameInfo.update({'game':secondList})

    if 'match' in game_match_serviceDict:
        path = game_match_serviceDict.get('match')
        matchList = os.listdir(path)
        mfirstList = []
        for i in matchList:
            a = path + i
            gsPath = a + '\\GS'
            msPath = a + '\\MS'
            matchexePath = msPath + '\\matchserver_x64_r.exe'
            if os.path.isdir(gsPath) and os.path.isdir(msPath) and os.path.exists(matchexePath):
                mfirstList.append(i)
        gameInfo.update({'match':mfirstList})

    if 'service' in game_match_serviceDict:
        path = game_match_serviceDict.get('service')
        serviceList = os.listdir(path)
        sfirstList = []
        for i in serviceList:
            a = path + i
            serviceExePath = a + '\\matchserver_x64_r.exe'
            if os.path.exists(serviceExePath):
                sfirstList.append(i)
        gameInfo.update({'service':sfirstList})
    print(gameInfo)
    return gameInfo

    # return [secondList,thirdList]


def gameInfoFile(game_match_serviceDict):
    '''
    启动时 将ServerGameInfo 保存到文件中， Client连接时候 读取发送，节省遍历目录的IO时间
    :param game_match_serviceDict:
    :return:
    '''
    gameInfoDict = []
    if not os.path.exists('dirinfo.ini'):
        file = open('dirinfo.ini','w')
        gameInfoDict = getServerGameInfo(game_match_serviceDict)
        json.dump(gameInfoDict,file)
    else:
        file = open('dirinfo.ini','r')
        gameInfoDict = json.load(file)

    return gameInfoDict


def getSconfig():
    '''
    读取服务器端配置文件 Sconfig.ini
    原  来：return gamedir,port
    修改后：return game_match_serviceDict,port
           game_match_serviceDict    键 game match service 至少包含一个

    :return: 返回  (游戏目录,port)
    '''
    section = 'Server'
    port = 0
    game_match_serviceDict = {}

    configINI = configparser.SafeConfigParser()
    #configINI.read('..\Sconfig.ini')
    try:
        configINI.read('Sconfig.ini')
        soption = configINI.options(section)

        for s in soption:
            game_match_serviceDict.update({s:configINI.get(section,s)})
    except Exception as e:
        print('处理Sconfig.ini错误：')
        print(e)

    if 'port' in game_match_serviceDict:
        port = int (game_match_serviceDict.get('port'))
        del game_match_serviceDict['port']
        if len(game_match_serviceDict) == 0:
            print('Sconfig.ini 未定义任何目录参数')
            return
    else:
        print('Sconfig.ini 未定义port参数')
        return

    return game_match_serviceDict,port


#
# def oneCommand_check(str,secondList,currentGame):
#     '''
#     判断输入的数字或字符是否 在目录名中  返回目录名
#     :param kindid:
#     :param secondList: table[1]dd
#         msg = ('%s@%s' % ('currentGame', currentGame[0]))
#     else:
#         msg = ('%s@%s 匹配不到游戏目录，请重新输入---！' % ('print', str))
#     return msg


def command_ServerCheck(cmdList,serverGameInfo,game_match_serviceDict):
    '''

    :param cmdList:
    :param currentGame:
    :return:
    '''
    gamedir = game_match_serviceDict[cmdList[2]]
    mstype = ['match','service']
    currentGame = cmdList[1]
    cmdtype = cmdList[2]
    # 检测游戏目录是否匹配
    if currentGame in serverGameInfo[0]:
        pass
    else:
        msg = ['print','Server端没有这个游戏目录'+currentGame]
        return msg



    if cmdList[0] == 'start':
        if cmdtype == 'game':
            if ',' in cmdList[3]:
                room = cmdList[3].split(',')
            else:
                room = cmdList[3]
            msg = runServiceLoader(gamedir+'\\'+currentGame,room)
        elif cmdtype in mstype:
            msg = runMatchService(cmdList,game_match_serviceDict)
        else:
            msg = ['print','game、match、service类型输入错误！']

    elif cmdList[0] == 'stop':
        if cmdtype == 'game':
            msg = stop_cmd_server(gamedir,currentGame,cmdList[2],cmdList[3])
        elif cmdtype in mstype:
            msg = stopMatchService(cmdList,game_match_serviceDict)
        else:
            msg = ['print', 'game、match、service类型输入错误！']

    elif cmdList[0] == 'show':
        if cmdtype =='game':
            msg = show_cmd_server(gamedir,currentGame,cmdList[2])
        elif cmdtype in mstype:
            msg = showMatchServer(cmdList,game_match_serviceDict)
        else:
            msg = ['print', 'game、match、service类型输入错误！']

    elif cmdList[0] == 'get':
        if cmdtype =='game':
            # get ini 下载当前游戏 目录下的所有ini到桌面
            # get *** 下载明确的文件名
            # 1、检查目录中的  是否存在ini文件，或者具体文件名称是否存在
            # 2、
            msg = get_filter_File(currentGame,cmdList)
        elif cmdtype in mstype:
            # get file  get rt
            msg = get_match_File(cmdList,game_match_serviceDict)
        else:
            msg = ['print', 'game、match、service类型输入错误！']


    elif cmdList[0] == 'put':
        msg = put_check_server(gamedir,currentGame,cmdList)


    elif cmdList[0] == 'update':
        # update exe 升级servicesLoader
        # update dll 升级游戏dll
        # 升级前 建立备份目录  并备份被升级的文件
        if cmdtype == 'game':
            msg = update_cmd_server(gamedir,currentGame,cmdList)
        elif cmdtype in mstype:
            msg =
        else:
            msg = ['print', 'game、match、service类型输入错误！']




    elif cmdList[0] =='back':
        if cmdtype == 'game':
            msg = back_cmd_server(gamedir,currentGame,cmdList[2])
        elif cmdtype in mstype:
            msg =
        else:
            msg = ['print', 'game、match、service类型输入错误！']



    elif cmdList[0] == 'compare':
        if cmdtype == 'game':
            msg =compare_cmd_server(gamedir,currentGame,cmdList[2])
        elif cmdtype in mstype:
            msg =
        else:
            msg = ['print', 'game、match、service类型输入错误！']



    return msg




def compare_cmd_server(gamedir,currentGame,suffixal):
    '''
    比较 游戏服务器 和本地SVN的  文件最新修改时间
    :param gamedir:
    :param currentGame:
    :param suffixal:
    :return:
    '''
    msg = []
    compareFilePath= gamedir+currentGame+'\\'
    compareFileSuffixal = []
    compareFile = []
    dllfile = re.sub('^\\d{2,3}', '', currentGame) + '.dll'

    if suffixal == 'exe':
        compareFileSuffixal = ['.exe','.dll']
    elif suffixal == 'dll':
        compareFileSuffixal = ['.dll']
    else        :
        msg = ['print', 'compare ' + suffixal + ' 命令错误！']
    if len(compareFileSuffixal) == 1:

        if os.path.exists(compareFilePath+dllfile):
            compareFile.append([dllfile,time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(compareFilePath+dllfile)))])
            msg = ['compare',compareFile]
        else:
            msg = ['print','游戏目录中没有 '+dllfile+' 文件！']
    else:
        for file in os.listdir(compareFilePath):
            if file[-4:] in compareFileSuffixal and file != dllfile:
                compareFile.append([file,time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(compareFilePath+file)))])

        if len(compareFile) >0:
            msg = ['compare',compareFile]
        else:
            msg = ['print','游戏目录中没有 .dll 文件！']

    return msg



def back_cmd_server(gamedir,currentGame,suffixal):
    '''
    还原备份文件，还原最近一次备份
    :param gamedir:
    :param currentGame:
    :param suffixal: ini  dll  exe三种
    :return:
    '''
    msg = []
    log = ''
    back_source_dir = gamedir+currentGame+'\\backup\\'+suffixal
    print(back_source_dir)

    if os.path.exists(back_source_dir):
        file = os.listdir(back_source_dir)
        if len(file) == 0:
            log = '没有'+suffixal+' 的备份文件！'
        else:
            backdir = back_source_dir+'\\'+file.pop(-1)
            log = copyAllFileto(backdir,gamedir+currentGame)
    else:
        log = '没有'+suffixal+' 的备份文件！'

    msg = ['print',log]
    return msg



def copyAllFileto(sourceDir,targetDir):
    '''
    将目录下所有的还原到 游戏目录，并且删除目录
    :param sourceDir:备份目录，游戏目录
    :param targetDir:
    :return:
    '''
    msgList = []
    maxlen = 0
    backfile = os.listdir(sourceDir)
    if len(backfile) == 0:
        msg = sourceDir + '目录中没有文件,目录被删除！'
        shutil.rmtree(sourceDir)
    else:
        for file in backfile:
            try:
                shutil.copy2(sourceDir+'\\'+file,targetDir)
                width = len(file)
                if width>maxlen:
                    maxlen = width
                msgList.append([file,time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(sourceDir+'\\'+file))),'还原成功!'])
                os.remove(sourceDir + '\\' + file)
            except Exception as e:
                print(e)
                msgList.append([file,'',e])
        if len(os.listdir(sourceDir)) == 0:
            shutil.rmtree(sourceDir)
        msg = format_printMSG(msgList,1,maxlen)
    return msg





def update_cmd_server(gamedir,currentGame,cmdList):
    '''
    更新 exe   dll  命令
    :param gamedir:
    :param currentGame:
    :param file_str:
    :return:
    '''
    source_target_list = []
    rev_update_cmd = cmdList[3]
    source_dir = cmdList[2]
    len_rev_cmd = len(rev_update_cmd)
    msg = ''
    if  len_rev_cmd == 1:
        # 只有一个文件  备份并更新dll
        msg = backup_file(gamedir,currentGame,rev_update_cmd,'dll')
    elif len_rev_cmd > 0:
        # 多个文件 备份并更新ServiceLoader
        msg = backup_file(gamedir, currentGame, rev_update_cmd, 'exe')

    # 传输 源目录 目标目录
    for file in rev_update_cmd:
        targetClient = '\\'+currentGame+'\\'+file
        sourceServer = source_dir + file
        source_target_list.append([sourceServer,targetClient])

    msg.insert(0,source_target_list)
    msg.insert(0,'update')
    return msg


def get_match_File(cmdList,game_match_serviceDict):
    '''
    返回 下载的文件目录，消息
    :param cmdList:
    :param game_match_serviceDict:
    :return:['print',消息]  ['get',[source,target],[source1,target1]....]
    '''
    gamedir  = game_match_serviceDict[cmdList[]]

    fileList = ['get']
    sourceList = []
    targetList = []

    if cmdList[2] == 'match':
        if cmdList[4] in ['ini','gateway.ini','gateway','config.ini','config']:
            if cmdList[4] in ['ini','config.ini','config']:
                sourceServer1 = gamedir + cmdList[1] + '\\MS\\config.ini'
                sourceList.append(sourceServer1)
                targetClient1 = cmdList[3] + cmdList[1] + '\\config.ini'
                targetList.append(targetClient1)
                if cmdList[4] == 'config.ini':
                    if os.path.exists(sourceServer1):
                        fileList.append([sourceServer1,targetClient1])

            sourceServer2 = gamedir + cmdList[1] + '\\MS\\gateway.ini'
            sourceServer3 = gamedir + cmdList[1] + '\\MS\\Gate1\\gateway.ini'
            sourceServer4 = gamedir + cmdList[1] + '\\MS\\Gate2\\gateway.ini'
            sourceList.append(sourceServer2)
            sourceList.append(sourceServer3)
            sourceList.append(sourceServer4)
            targetClient2 = cmdList[3] + cmdList[1] + '\\gateway.ini'
            targetClient3 = cmdList[3] + cmdList[1] + '\\MS\\Gate1\\gateway.ini'
            targetClient4 = cmdList[3] + cmdList[1] + '\\MS\\Gate1\\gateway.ini'
            targetList.append(targetClient2)
            targetList.append(targetClient3)
            targetList.append(targetClient4)

            for i in range(len(sourceList)):
                if os.path.exists(sourceList[i]):
                    fileList.append([sourceList[i],targetList[i]])

            if len(fileList) > 1:
                return fileList
            else:
                msg = ''
                for i in sourceList:
                    msg += i +' '
                return ['print', msg + '下载文件未找到！']

        elif cmdList[4] in ['rt','server.rt']:
            sourceServer1 = gamedir + cmdList[1]+'\\MS\\server.rt'
            targetClient1 = cmdList[3] + cmdList[1] + '\\server.rt'
            if os.path.exists(sourceServer1):
                fileList.append([sourceServer1,targetClient1])
                return fileList
            else:
                return ['print',sourceServer1 + '  下载文件未找到！']

        else:
            sourceServer1 = gamedir + cmdList[1] + '\\MS\\' + cmdList[4]
            if os.path.exists(sourceServer1):
                targetClient1 = cmdList[3] + cmdList[1] + '\\MS\\' + cmdList[4]
                fileList.append([sourceServer1,targetClient1])
                return fileList
            else:
                return ['print',sourceServer1 + '  下载文件未找到！']

    elif cmdList[2] == 'service':
        if cmdList[4] in ['config','config.ini']:
            sourceServer1 = gamedir + cmdList[1] + '\\config.ini'
            targetClient1 = cmdList[3] + cmdList[1] + '\\config.ini'
        else:
            sourceServer1 = gamedir + cmdList[1] + '\\' + cmdList[4]
            targetClient1 = cmdList[3] + cmdList[1] + '\\' + cmdList[4]

        if os.path.exists(sourceServer1):
            fileList.append([sourceServer1,targetClient1])
            return fileList
        else:
            return ['print', sourceServer1 + ' 下载文件未找到']




def get_filter_File(currentGame,getMSG):
    '''                                      固定桌面目录
    get ini 用，获取游戏目录下 特定后缀 文件
    :param gamedir: 游戏总目录
    :param currentGame: 游戏下  单个游戏目录
    :param get: 文件后缀 'ini' 返回所有ini文件   其他****   返回****文件
    :return:
    '''
    global gamedir
    desktop_dir = getMSG[2]
    get_fuzzy = getMSG[3]
    msg = []
    filelist = []
    gamefile = os.listdir(gamedir+'\\'+currentGame)
    if get_fuzzy.lower() == 'ini':
        for file in gamefile:
            if file[-3:].lower() == 'ini':
                sourceServer ='\\'+currentGame + '\\' + file
                targetClient = desktop_dir+currentGame+'\\'+file
                filelist.append([sourceServer,targetClient])
    else:
        status = True
        for file in gamefile:
            if get_fuzzy.lower() == file.lower():
                sourceServer = '\\' + currentGame + '\\' + file
                targetClient = desktop_dir + currentGame + '\\' + file
                filelist.append([sourceServer, targetClient])
                status = False
                break
        if status:
            msg = ['print', get_fuzzy+'在游戏目录'+currentGame+'  中未找到！']
            return msg
    print(filelist)
    msg = ['get',filelist]
    print('----------------')
    print(msg)
    return msg


def put_check_server(gamedir,currentGame,cmdList):
    '''
    put  上传用，判断目录是否存在，上传做备份
    :param gamedir:
    :param currentGame:
    :param get_fuzzy:
    :return:  返回msg  msg1     msg print备份消息     msg1 put消息
    '''
    msg=[]
    source_target_list = []
    backupfile = []

    if cmdList[3] == 'match':
        desktop_dir = cmdList[4]
        filelist = cmdList[6]
        sourceFileList = cmdList[5]

        msfile = os.listdir(gamedir+'\\'+currentGame+'\\MS')
        gsfile = os.listdir(gamedir+'\\'+currentGame+'\\GS')
        for file in filelist:
            if file[0] == 'MS' and file[1] in msfile:
                backupfile.append(['MS',filep[1]])
            if file[0] == 'GS' and file[1] in gsfile:
                backupfile.append(['GS',file[1]])


    # game service
    else:
        desktop_dir =cmdList[3]
        filelist =cmdList[4]

        gamefile = os.listdir(gamedir + '\\' + currentGame)
        for file in filelist:
            if file in gamefile:
                backupfile.append(file)

    print('gamedir:',end='')
    print(gamedir)
    print('currentGame:',end='')
    print(currentGame)


    if len(backupfile) >0:
        if cmdList['3'] == 'match':
            msg = backup_file(gamedir,currentGame,backupfile,'match')
        else:
            msg = backup_file(gamedir,currentGame,backupfile,backupfile[0][-3:])
        # print@......+put@..... client 接收后   split'+'

    # 传输 源目录 目标目录
    for file in filelist:
        targetClient ='\\'+currentGame + '\\' + file
        sourceServer = desktop_dir+currentGame+'\\'+file
        source_target_list.append([sourceServer,targetClient])

    msg.insert(0,source_target_list)
    msg.insert(0,'put')

    return msg




def backup_file(gamedir,currentGame,fileList,folder):
    '''
    升级文件  ini 时   备份文件用
    :param gamedir:
    :param currentGame:
    :param fileList:
    :param folder:  备份根目录backup的下一级目录  ini  dll  serviceLoader
    :return:
    '''
    # 游戏目录备份 根目录   例E:\Game\24StandLand3renServer\backup
    backup_dir = gamedir+'\\'+currentGame+'\\backup'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # 游戏目录  备份目录例E:\Game\24StandLand3renServer\backup\ini
    # match目录         E:\Match\DDZ\back
    if folder == 'match':
        backup_folder = backup_dir
    else:
        backup_folder = backup_dir+'\\'+folder
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)


    # 根据当前日期时间 创建备份子目录
    newfolder = time.strftime('%Y-%m-%d %H %M %S',time.localtime(time.time()))
    backup_path = backup_folder + '\\'+newfolder+'\\'
    os.makedirs(backup_path)

    msglist = []
    maxlen = 0
    if folder in ['ini','dll','exe']:
        for file in fileList:
            file_length = len(file)
            shutil.copy2(gamedir+'\\'+currentGame+'\\'+file,backup_path)
            if file_length > maxlen:
                maxlen = file_length
            msglist.append(['被覆盖文件',file,' 已备份！'])

    elif folder == 'match':
        for file in fileList:
            file_length = len(file[1])
            shutil.copy2(gamedir+'\\'+currentGame+'\\'+file[0]+'\\'+file[1],backup_path+file[0]+'\\'+file(1))
            if file_length > maxlen:
                maxlen = file_length
            msglist.append(['被覆盖文件'+file[0]+'\\',file[1],' 已备份！'])
    else:
        msg=['print','saction.py  backup_file方法错误，请检查代码！']

    msg = ['print',format_printMSG(msglist,2,maxlen)]
    return msg




def format_printMSG(plist,align_column_int,align_column_maxlen):
    '''
    对返回的 print消息 格式化列
    :param plist:打印消息的list
    :param align_column_int:  要对齐的列
    :return: 格式化后的输出消息

    [['第一列', '第二列231', '三'], ['第一列', '第二列2啊啊啊啊31', '三'], ['第一列', '第二列2', '三']]   2
                    ↓↓  ↓↓  ↓↓
    第一列         第二列231                三
    第一列         第二列2啊啊啊啊31         三
    第一列         第二列2                  三
    '''
    # 定义format  正则表达式
    def_format = ''
    length = len(plist[0])
    n=0
    plistlen = len(plist)
    listnum = 0
    while length > 0:
        def_format += '{'+str(n)+':'
        if align_column_int-1 == n:
            n += 1
            def_format +='{'+str(n)+'}}'
        else:
            if plistlen > 1:
                def_format += str(chinese(plist[1][listnum],2)+4)+'}'
            else:
                def_format += str(chinese(plist[0][listnum], 2) + 4) + '}'
        n += 1
        listnum += 1
        length -= 1

    msgStr = ''
    # print('max',end='')
    # print(align_column_maxlen)
    for i in plist:
        i.insert(align_column_int,align_column_maxlen+8-chinese(i[align_column_int-1]))
        # print(align_column_maxlen+8-chinese(i[align_column_int-1]))
        # print(i)
        msgStr += def_format.format(*i)+'\n'
    # print(def_format)
    return msgStr[:-1]



def show_cmd_server(gamedir,currentGame,info):
    '''
    显示游戏目录  文件，房间列表 等等
    :param gamedir: 游戏根目录
    :param currentGame: 游戏目录
    :param info: 显示的内容  room 房间(包括是否启用）   file  文件(包括修改时间)
    :return: 返回打印的消息
    '''
    msg = ''
    msgList = []
    maxlen = 0
    if info == 'room':
        path = gamedir+currentGame+'\\run'
        if os.path.exists(path):
            run_folder_files = os.listdir(path)
            xmlfile = []
            for i in run_folder_files:
                if i[-4:] =='.xml':
                    xmlfile.append(i)
            if len(xmlfile)>0:
                for i in xmlfile:
                    n='=====未启用！'
                    whidth = chinese(i,2)
                    if whidth>maxlen:
                        maxlen=whidth

                    if portISopen(getPortFromXML(i)):
                        # 端口状态，端口被占用 n='1'
                        n='>>>>>已启用！'
                    msgList.append([i,n])
                msg = format_printMSG(msgList,1,maxlen)
            else:
                msg = '游戏目录 ' + path + '中没有房间配置文件！'
        else:
            msg = '目录 ' + path + '不存在！'
    elif info == 'file':
        path = gamedir+currentGame
        if os.path.exists(path):
            game_folder_files = os.listdir(path)
        if len(game_folder_files)>0:
            for file in game_folder_files:
                whidth = chinese(file,2)
                if whidth > maxlen:
                    maxlen = whidth
                msgList.append([file,time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(path+'\\'+file)))])
                # msg += file + '    ' +time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(path+'\\'+file))) +'\n'
            msg = format_printMSG(msgList,1,maxlen)
        else:
            msg = '游戏目录 ' + path + '中没有文件！'
    else:
        msg = '命令不正确,参考：\nshow room 显示房间\nshow file 显示文件'
    return ['print',msg]





def chinese(data,mode=1):
    '''
    mode=1 默认返回str 中文字符个数，mode=2返回字符串宽度   中文占2，其他占1
    :param data:str
    :param mode:
    :return:返回字符串宽度
    '''
    count = 0
    if mode == 1:

        for s in data:
            if ord(s) > 127:
                count += 1
    elif mode == 2:
        for s in data:
            if ord(s) >127:
                count += 2
            else:
                count += 1
    return count



def portISopen(port):
    '''
    判断本地端口是否占用
    :param port:端口是否被占用
    :return:   True占用   False未占用
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.1)
    try:
        ADDR = ('127.0.0.1', port)
        s.connect(ADDR)
        s.shutdown(2)
        return True
    except Exception as e:
        print(e)
        return False


def getPortFromXML(xmlName):
    return int(xmlName[-9:][:5])





#》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》》  stop相关功能
def stop_cmd_server(gamedir,currentGame,info,stopSEC):
    '''
    关闭房间
    :param gamedir:
    :param currentGame:
    :param info:
    :return:
    '''
    # 检查 关闭 房间端口的合格     房间端口是否存在，房间端口是否开着
    if ',' in info:
        xml = info.split(',')
    else:
        xml = info

    path = gamedir + '\\' + currentGame

    xml_list_getgamexml,error_msg_1 = get_gamexmlANDport(path,xml)
    xml_list,return_msg = check_xml_port_open(xml_list_getgamexml,'stop')
    return_msg.extend(error_msg_1)

    msg_stopAction,stopSYC = stopFileCreate(path,xml_list,stopSEC)
    return_msg.extend(msg_stopAction)

    return_msg_str = msgList_2_msgStr(return_msg)


    return_msg = []
    if stopSYC:
        return_msg.append('stopRoom')
    else:
        return_msg.append('print')
    return_msg.append(return_msg_str)

    print('stop_cmd_server  end:')
    print(return_msg)
    return return_msg


def stopFileCreate(dir,info,stopSEC):
    '''
    创建  关闭房间的文件

    程序对端   检测游戏目录下   shut *****文件   *****为端口     内容为 关闭时间  单位秒


    :param dir:  游戏目录
    :param info:  [3,[ '疯狂跑得快新手场12601.xml' , '疯狂跑得快初级场12611.xml' , '疯狂跑得快顶级场12631.xml'],[ 12601 , 12611 , 12631]]
    :param sec:  关闭的时间
    :return:
    '''
    global timerState,timerList,timerLock
    state = False
    msg = []
    for i in range(len(info[2])):
        if os.path.exists('shut '+info[2][i]):
            msg.append(info[1][i] + ' 已经在关闭过程中！')
        else:
            shutDefault = dir + '\\shut'
            shutFile = dir + '\\shut ' + info[2][i]
            try:
                f = open(shutDefault,'w+')
                f.write(str(stopSEC))
                f.close()
                os.rename(shutDefault,shutFile)
                state = True
            except Exception as e:
                msg.append(info[1][i])
                msg.append(e)

            # 全局list操作
            timerLock.acquire()
            timerState = False
            timerList.append([info[1][i],shutFile+' result',stopSEC])
            timerLock.release()

    # 启动定时器
    if state:
        fun_timer()

    return msg,state


def fun_timer():
    '''
    定时器
    :return:
    '''
    global timerState,timerList,timer,timerLock,timerMsg
    if timerState:
        timer.cancel()
        return

    print('timerList',timerList)
    if timerList == []:
        timerLock.acquire()
        timerState = True
        timerLock.release()
        return
    for i in timerList[:]:
        removeState = False
        if os.path.exists(i[1]):
            timerMsg.append(i[0] + '   房间已关闭!')
            removeState = True
        else:
            i[2] -= 3
            if i[2] < -12:
                timerMsg.append(i[0] + '  房间关闭超时，请登录服务器检查！')
                removeState = True

        if removeState:
            timerLock.acquire()
            timerList.remove(i)
            timerLock.release()

    timer = threading.Timer(3,fun_timer)
    timer.start()


def checkMSG_Server():
    '''
    检查服务器 是否有 定时器检查的  关闭房间的消息
    :return:['None'] 没有定时器  ['Wait'] 有消息在等待
    '''
    global timerLock,timerMsg,timerState
    msg = []
    timerLock.acquire()
    if timerMsg == []:
        print('timerState',timerState)
        if timerState:
            msg = ['None']
        else:
            msg = ['Wait']
    else:
        msg = timerMsg
        timerMsg = []
    timerLock.release()
    return msg




def closeWindowAction(window,type='stop'):
    '''
    关闭窗口
    :return:
    '''

    # 显示窗口
    win32gui.ShowWindow(window, win32con.SW_RESTORE)
    # 获取窗口焦点
    win32gui.SetForegroundWindow(window)

    if type =='stop':
        win32api.keybd_event(17, 0, 0, 0)
        win32api.keybd_event(67, 0, 0, 0)
        win32api.keybd_event(17, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(67, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.1)
        win32api.keybd_event(17, 0, 0, 0)
        win32api.keybd_event(67, 0, 0, 0)
        win32api.keybd_event(17, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(67, 0, win32con.KEYEVENTF_KEYUP, 0)
    elif type == 'close':
        win32api.keybd_event(13, 0, 0, 0)
        win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)

    # # 回车
    # win32api.keybd_event(13, 0, 0, 0)
    # win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
    # # shutdown
    # win32api.keybd_event(83, 0, 0, 0)
    # win32api.keybd_event(83, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(72, 0, 0, 0)
    # win32api.keybd_event(72, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(85, 0, 0, 0)
    # win32api.keybd_event(85, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(84, 0, 0, 0)
    # win32api.keybd_event(84, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(68, 0, 0, 0)
    # win32api.keybd_event(68, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(79, 0, 0, 0)
    # win32api.keybd_event(79, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(87, 0, 0, 0)
    # win32api.keybd_event(87, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(78, 0, 0, 0)
    # win32api.keybd_event(78, 0, win32con.KEYEVENTF_KEYUP, 0)
    # # 回车
    # win32api.keybd_event(13, 0, 0, 0)
    # win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(13, 0, 0, 0)
    # win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
    # win32api.keybd_event(13, 0, 0, 0)
    # win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)


# --------------------------------------------------------------启动 停止 显示match Service-----------------------------------------------------
def runMatchService(cmdList,game_match_serviceDict,status='check'):
    # 判断是否已经开启
    isopen,infoList = checkMatchServer(cmdList,game_match_serviceDict)
    startNum = 0
    msgList = []
    if isopen == False:
        # 启动exe
        for i in infoList:
            a = subprocess.run(i,shell=True)
            startNum += 1
        msgList.append('print')
        msgList.append(startNum + '个服务已经启动！')
        return msgList
    else:
        infoList.insert(0,'print')
        return infoList

def showMatchServer(cmdList,game_match_serviceDict):
    if cmdList[3] == 'match':
        return checkMatchServer(cmdList,game_match_serviceDict,statue='show')
    else:
        return ['print','show '+ cmdList[3] +'命令无法识别！ 请参考 help show']


def checkMatchServer(cmdList,game_match_serviceDict,statue='check'):
    '''
    判断match 或者service 是否启用
    :param cmdList: status   True  检查已经启动   False 检查没有启动
    :return:
    '''

    msgList = []
    nameList,infoList = getNameMatchServer(cmdList,game_match_serviceDict)
    # 列出所有的顶级窗口
    if nameList == True:
        return True,infoList
    isopen = False
    hWndList = []
    win32gui.EnumWindows(lambda hWnd, param: param.append(hWnd), hWndList)
    # 检查窗口名称是否存在
    for h in hWndList:
        num = len(nameList)
        if num <= 0 :
            break
        for i in nameList[:]:
            if i in win32gui.GetWindowText(h):
                msgList.append(i+'已经启动！')
                nameList.remove(i)
                isopen = True
    if statue == 'check' and isopen:
        return True,msgList
    elif statue == 'show':
        for i in nameList:
            msgList.append(i+'  未启动！')
            msgList.insert(0,'print')
        return msgList
    else:
        return False,infoList




def getNameMatchServer(cmdList,game_match_serviceDict):
    '''
    获取 match service 窗口名称列表
    :param cmdList:
    :param game_match_serviceDict:
    :return:  nameList,msgList
    1   nameList['***','***']   conf_dir['****\\config.ini', ...]
    2   name[True]             msgList['***','***']
    '''
    # 窗体名称目录
    nameList = []
    msgList = []
    conf_dir = []
    exeList = []
    # 拿到需要config.ini的路径
    if cmdList[3] == 'match':
        conf_match =  game_match_serviceDict['match'] + cmdList[1] +'\\MS\\config.ini'
        conf_gateway = game_match_serviceDict['match'] + cmdList[1] +'\\MS\\gateway.ini'
        conf_gateway1 = game_match_serviceDict['match'] + cmdList[1] +'\\MS\\Gate1\\gateway.ini'
        conf_gateway2 = game_match_serviceDict['match'] + cmdList[1] +'\\MS\\Gate2\\gateway.ini'

        exe_match = game_match_serviceDict['match'] + cmdList[1] +'\\MS\\matchserver_x64_r.exe'
        exe_gateway = game_match_serviceDict['match'] + cmdList[1] +'\\MS\\gateway_x64_release.exe'
        exe_gateway1 = game_match_serviceDict['match'] + cmdList[1] + '\\MS\\Gate1\\gateway_x64_release.exe'
        exe_gateway2 = game_match_serviceDict['match'] + cmdList[1] + '\\MS\\Gate2\\gateway_x64_release.exe'
        if os.path.exists(conf_match) and os.path.exists(exe_match):
            conf_dir.append(conf_match)
            exeList.append(exe_match)
        else:
            msgList.append('未在'+cmdList[1]+'中找到config.ini或exe 文件！')
            return True,msgList
        # gateway config.ini文件检查
        if os.path.exists(conf_gateway) and os.path.exists(exe_gateway):
            conf_dir.append(conf_gateway)
            exeList.append(exe_gateway)
        elif os.path.exists(conf_gateway1) and os.path.exists(conf_gateway2) and os.path.exists(exe_gateway1) and os.path.exists(exe_gateway2):
            conf_dir.append(conf_gateway1)
            conf_dir.append(conf_gateway2)
            exeList.append(exe_gateway1)
            exeList.append(exe_gateway2)
        else:
            msgList.append('未在'+cmdList[1]+'的Gate1和Gate2文件夹中 找到 config.ini或exe文件！')
            return True,msgList

    elif cmdList[3] == 'service':
        conf_service = game_match_serviceDict['service'] + cmdList[1] +'\\config.ini'
        if os.path.exists(conf_service):
            conf_dir.append(conf_service)
        else:
            msgList.append('未找到'+ cmdList[1]+'的 config.ini文件！')
            return True,msgList
    else:
        msgList.append('cmdtype错误 非match或service 无法继续,请检查程序！')
        return True,msgList

    # 从config.ini中获取application name 窗口模糊名称
    for config in conf_dir:
        cf = configparser.SafeConfigParser()
        try:
            cf.read(config)
            nameList.append(cf.get('Application','name'))
        except Exception as e:
            msgList.append(e)
            return True,msgList
    return nameList,exeList


def stopMatchService(cmdList,game_match_serviceDict):
    # 判断是否已经开启
    isopen,infoList = getNameMatchServer(cmdList,game_match_serviceDict)
    msgList = []
    if isopen == True:
        msgList = infoList
    else:
        msgList = stopMatch(isopen)
    msgList.insert(0,'print')
    return msgList
# --------------------------------------------------------------启动 停止match Service end-----------------------------------------------------



def stopMatch(nameList_gateway_match):
    '''
    关闭比赛
    :param nameList_match_gateway:   gateway 和 match 的窗口名称       List末尾的match  末尾前面的都是gateway
    :return: 返回关闭 比赛和网关的消息
    '''

    # 列出所有的顶级窗口
    hWndList = []
    win32gui.EnumWindows(lambda hWnd, param: param.append(hWnd), hWndList)

    # match
    matchName = nameList_gateway_match.pop()
    # gateway
    numGateWay = len(nameList_gateway_match)
    msg = []
    msgsuccess = []
    ophWndList = []
    count = 0
    breakTab = 0

    for h in hWndList:
        if not h:
            return 0
        # gateWay窗口都关闭  +1   match找到 +3
        if breakTab == 3 + numGateWay:
            break

        if matchName in win32gui.GetWindowText(h):
            ophWndList.insert(0,h)
            breakTab += 3
            continue

        for nameGateway in nameList_gateway_match[:]:
            if count == numGateway:
                break
            if nameGateway in win32gui.GetWindowText(h):
                # 关闭窗口
                closeWindowAction(h)
                ophWndList.append(h)
                msgsuccess.append(nameGateway+' 关闭成功！')
                nameList_gateway_match.remove(nameGateway)
                count += 1

    if breakTab > 2:
        time.sleep(0.1)
        closeWindowAction(ophWndList[0])
        msgsuccess.append(matchName + ' 关闭成功！')

    else:
        msg.append('未找到可关闭的' + matchName)

    for gateway in nameList_gateway_match:
        msg.append( '未找到可关闭的' + gateway)


    # 启动 定时器 做最后的关闭   ？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？？   待修改
    for wnd in ophWndList:
        closeWindowAction(wnd,'close')






















