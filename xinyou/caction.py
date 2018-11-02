#encoding: utf-8

import re
import configparser
import os
import json
import time
import paramiko
import threading

from xinyou import saction
global cmdaction,desktop_dir


cmdaction = ['start','stop','update','get','put','show','back','compare','mode']
desktop_dir = ''
cmdtype = 'game'
svnServiceLoader_dir = ''
dlls_dir = ''
timerList = []
timerLock = threading.Lock()


def getServerIpPort():
    '''
    从config.ini文件获取要连接服务器的 IP和端口    初始化桌面目录  svn目录  dll目录
    :return: [['GameServer 扑克服务器', ('192.168.0.1', '8001')], ['GameServer 麻将服务器', ('192.168.0.2', '8002')]]
    '''
    global desktop_dir,svnServiceLoader_dir,dlls_dir
    nameIpPortList = []
    cf = configparser.SafeConfigParser()
    cf.read('config.ini')
    s = cf.sections()
    for i in s:
        try:
            nameIpPortList.append([i,(cf.get(i,'ip'),int(cf.get(i,'port')))])
        except Exception as e:
            pass

    try:
        desktop_dir = cf.get('info','desktop_path')
    except Exception as e:
        print('请在config.ini配置 桌面目录地址！格式如下')
        print('[info]')
        print('desktop_path=')
        return False
    try:
        svnServiceLoader_dir = cf.get('info','svnServiceLoader_path')
    except Exception as e:
        print('请在config.ini配置 Serviceoader目录地址！格式如下')
        print('[info]')
        print('svnServiceLoader_path =')
        return False
    try:
        dlls_dir = cf.get('info','svnDll_path')
    except Exception as e:
        print('请在config.ini配置 svn单款dll目录地址！格式如下')
        print('[info]')
        print('svnDll_path=')
        return False


    return nameIpPortList


# 待测试~~~~~~~~~~~~~~~~~
def printGameDir(gameDirList,cmdtype):
    '''
    打印 所有游戏目录
    :param gameDirList:
    :return:
    '''
    if cmdtype[0] in gameDirList:
        for i in gameDirList[cmdtype[0]]:
            for id in i[0]:
                print(id)
    else:
        print('消息列表中没有 ',cmdtype[0])


def idSearching(id,gameInfo,currentGame,cmdtype,clientDict):
    '''
    检索输入的 单个字符串 是否在 game目录上
    :param id: 输入的  命令
    :param gameInfo: 游戏Server info
    :return:   currentGame 重新赋值   True 匹配到ID  False 未匹配到
    '''

    if cmdtype[0] in gameInfo:
        info = gameInfo[cmdtype[0]]
    else:
        print('isSearching 未查找到',cmdtype[0])


    status = False
    id = id.upper()
    for i in info:
        for m in i[0]:
            if id in m.upper():
                if len(currentGame) == 3:
                    currentGame.pop()
                    currentGame.pop()
                    currentGame.pop()
                clientGroup = clientDict[i[1]]
                currentGame.append(clientGroup[0])
                currentGame.append(clientGroup[1])
                currentGame.append(m)
                status = True
                break
        if status:
            break

    return status


def command_simpleCheck(cmd,gameInfo,currentGame,cmdtype,clientDict):
    '''
    命令处理
    :param cmd:
    :param gameInfo:
    :param currentGame:
    :param cmdtype:
    :return:
    '''
    global cmdaction,desktop_dir

    if cmd =='':
        return False

    if gameInfo == {}:
        print('没有可连接的服务器！')
        return 1

    cmdList = cmd.split()
    # 假设是单命令，保留命令字符串
    id = cmdList[0]
    cmdList[0] = cmdList[0].lower()

    # 单命令
    if len(cmdList) == 1:
        if cmdList[0] =='id':
            printGameDir(gameInfo,cmdtype)
            return False
        elif cmdList[0] in ['game','match','service']:
            cmdtype.pop()
            cmdtype.append(cmdList[0])
            return False
        elif cmdList[0] =='help':
            help()
            return False
        elif cmdList[0] =='cls':
            os.system('cls')
            return False
        elif cmdList[0] == 'exit':
            return 1
        else:
            # 检查输入的游戏id  是否可以匹配到
            if not idSearching(cmdList[0],gameInfo,currentGame,cmdtype,clientDict):
                print(id,' 匹配不到游戏目录，请重新输入！  id 命令查看游戏目录')
            return False


    # 超过2个命令
    if len(cmdList)>2:
        print('错误!!!  命令数超过2个,使用help查看帮助文档！')
        return False

    # 2个命令
    if len(cmdList)==2:
        if cmdList[0] =='help':
            help(cmdList[1])
            return False

        if currentGame[2] == '':
            print('请先选择目录:')
            printGameDir(gameInfo,cmdtype)
            return False

        if not cmdList[0] in cmdaction:
            print('错误!!!   '+ cmdList[0] +'  命令动作不存在,使用help命令查询！')
            return False
        elif cmdList[0] == 'help':
            help(cmdList[1])
            return False
        elif cmdList[0] == 'start':
            return start_check(cmdList,cmdtype)
        elif cmdList[0] == 'stop':
            return stop_check(currentGame[2],cmdList,cmdtype)
        elif cmdList[0] == 'get':
            return get_check(currentGame[2],desktop_dir,cmdList)
        elif cmdList[0] == 'put':
            # 判断桌面目录是否存在  上传的文件是否存在
            return put_check(currentGame[2],cmdList[1],cmdtype)
        elif cmdList[0] == 'update':
            # 判断上传的文件是否存在
            return update_check(currentGame[2],cmdList[1],cmdtype)
        elif cmdList[0] == 'show':
            return show_check(currentGame[2],cmdList)
        elif cmdList[0] == 'back':
            if not cmdList[1] in ['ini','exe','dll']:
                print('back 命令错误help back 查询命令的使用方法！')
                return False
            else:
                return cmdList
        elif cmdList[0] == 'compare':
            if not cmdList[1] in ['exe','dll']:
                print('compare 命令错误 help compare 查询命令的使用方法')
                return False
            else:
                return cmdList
        else:
            print('客户端 命令无法识别！')
            print(cmdList)
    return True



def start_check(cmdList,cmdtype):
    '''
    start 命令  client端 合理性检查
    :param cmdList:
    :param cmdtype: game  match  service
    :return:
    '''
    if cmdtype == 'match':
        if cmdList[1] != 'match':
            print('start '+ cmdList[1] + '命令错误 help start查询！')
            return False
    elif cmdtype == 'service':
        if cmdList[1] != 'service':
            print('start ' + cmdList[1] + '命令错误 help start查询！')
            return False
    return cmdList


def stop_check(currentGame,cmd,cmdtype):
    '''
    stop 命令  client端  合理性检查
    :param currentGame:
    :param cmd:
    :param cmdtype: game match service
    :return:
    '''
    if cmdtype == 'game':
        cf = configparser.SafeConfigParser()
        cf.read('config.ini')
        try:
            stopsec = cf.get('stopSEC', currentGame)
        except Exception as e:
            print('配置文件config.ini 中，未配置  ' + currentGame+' 的默认停止时间！')
            return False
        cmd.insert(2,int(stopsec))
        return cmd
    elif cmdtype == 'match':
        if cmdList[1] != 'match':
            print('stop '+ cmdList[1] + '命令错误 help start查询！')
            return False
    elif cmdtype == 'service':
        if cmdList[1] != 'service':
            print('stop '+ cmdList[1] + '命令错误 help start查询！')
            return False
    else:
        print('stop_check函数  获取的cmdtype参数错误！')
        return False



def get_check(currentGame,desktop_dir,cmdList):
    cmdList.insert(1,desktop_dir)
    return cmdList


def put_check(currentGame,get_fuzzy,cmdtype):
    '''
    上传文件时，先判断要上传的文件是否存在
    :param currentGame:
    :return: False 文件不存在
    文件存在  返回
                ['put',desktop_dir,源地址,文件列表list]  game service
                ['put','match',desktop_dir,[文件带目录list] ,[[GS,文件list],[MS,文件]...]  ]  match
    '''
    global desktop_dir
    if not os.path.exists(desktop_dir+currentGame) and cmdtype in ['game','service']:
        os.makedirs(desktop_dir + currentGame)
        print(desktop_dir + currentGame + '   目录不存在，创建成功,请将文件放入此文件夹后再操作！')
        return False

    if cmdtype == 'match':
        msPath = desktop_dir+currentGame+'\\MS'
        gsPath = desktop_dir+currentGame+'\\GS'
        if not os.path.exists(msPath) and not os.path.exists(gsPath):
            os.makedirs(msPath)
            print(msPath,'   目录不存在，创建成功,请将文件放入此文件夹后再操作！')
            return False

    status= True
    putfile_list = []
    if cmdtype in ['game','service']:
        # filelist = []
        gamefile = os.listdir(desktop_dir+'\\'+currentGame)
        if get_fuzzy == 'ini':
            for file in gamefile:
                if file[-3:] == 'ini':
                    # temp = True
                    status = False
                    putfile_list.append(file)
                    # target ='\\'+currentGame + '\\' + file
                    # source = desktop_dir+currentGame+'\\'+file
                    # filelist.append([source,target])
        else:
            for file in gamefile:
                if get_fuzzy.lower() == file.lower():
                    putfile_list.append(file)
                    status = False
                    break
        if status:
            print('桌面文件夹 ' + currentGame + ' 中没有 ' + get_fuzzy + ' 文件！')
            return False

        return ['put',desktop_dir,putfile_list]
    # ['put',match]
    elif cmdtype == 'match':
        fileList = []
        if get_fuzzy =='ini':
            if os.path.exists(msPath):
                msFile = os.listdir(msPath)
                for file in msFile:
                    if file[-3:] == 'ini':
                        status= False
                        fileList.append(['MS',file])
                        putfile_list.append(msPath+'\\'+file)
            if os.path.exists(gsPath):
                gsFile = os.listdir(gsPath)
                for file in gsFile:
                    if file[-3:] == 'ini':
                        temp = False
                        fileList.append(['GS',file])
                        putfile_list.append(gsPath+'\\'+file)
        if get_fuzzy in ['rt','server.rt']:
            rt = msPath+'\\server.rt'
            if os.path.exists(rt):
                temp = False
                putfile_list.append(rt)

        if status:
            print('桌面文件夹 ' + currentGame + ' 中没有 ' + get_fuzzy + ' 文件！')
            return False

        return ['put','match',desktop_dir,putfile_list,fileList]



def show_check(currentGame,cmd):
    if cmd[1] in ['room','file']:
        return cmd
    else:
        print('show '+cmd[1]+'命令错误！')
        print('使用help show 参考命令使用方法！')
        return False



def update_check(currentGame,cmd_1,cmdtype):
    '''
    update 语句检查
    update exe  更新serviceLoader文件   确认目录是否存在，确认目录下是否有文件
    update dll  更新dll文件             确认目录是否存在，目录下是否有当前 游戏名称的dll
    :param currentGame:
    :param cmd_1:
    :return: False 不通过
    通过： 返回

    '''
    global svnServiceLoader_dir
    global dlls_dir

    exe_file = []
    if currentGame == '':
        print('请先选择 游戏目录！')
        return False

    if cmd_1 == 'exe':
        if os.path.exists(svnServiceLoader_dir):
            file = os.listdir(svnServiceLoader_dir)
            # print(file)
            if len(file) == 0:
                print(svnServiceLoader_dir+' 下没有更新文件！')
            else:
                for f in file[:]:
                    if not os.path.isdir(svnServiceLoader_dir+f):
                        flist = os.path.splitext(f)
                        if flist[1] == '.dll':
                            exe_file.append(f)
                exe_file.append('ServiceLoader.exe')
                # print(exe_file_str)
                return ['update',svnServiceLoader_dir,exe_file]
        else:
            print('本地目录 '+svnServiceLoader_dir+' 不存在！')
    elif cmd_1 == 'dll':
        dll_name = re.sub('^\\d{2,3}','',currentGame)+'.dll'
        dll_dir =dlls_dir + dll_name
        if os.path.exists(dll_dir):
            # 返回上传的dll文件
            return ['update',dlls_dir,[dll_name]]
        else:
            print('文件或目录 '+dlls_dir+' 不存在，请检查！')
            print('Tip：游戏目录命名规则  kindID+dll名称   例：22CrazyLand3renServer\n'
                  '     update dll 命令会根据  22CrazyLand3renServer 到dll文件夹寻找 CrazyLand3renServer.dll 文件！')
    else:
        print('update '+cmd_1+'  命令不正确！')
        print('命令帮助  help update')

    return False




def transfer_File(currentGame,fileList_Info,mode='put'):
    '''
    上传文件到游戏服务器
    :param host: 游戏服务器ip   str
    :param fileList_Info: 上传文件路径 和 目的文件路径(含文件名)  [['上传路径','目的路径']['','']['','']['','']]
    :param mode:   put 上传   get 下载
    :return: 执行在client端  消息直接打印
    '''
    host = currentGame[0].host
    gamePath = currentGame[2]
    transport  = paramiko.Transport(host,22)
    transport.connect(username='xinyou',password='EVxBhaTCWxUt')

    # 上传或下载前检查  桌面是否有currentGame目录 没有目录 默认创建
    if mode == 'get':
        if not os.path.exists(desktop_dir+gamePath):
            os.makedirs(desktop_dir+gamePath)
            print(desktop_dir+gamePath+'   目录不存在，创建成功！')
    if len(fileList_Info) != 0:
        try:
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            print(e)
        # 打印sftp 传输的 文件源和目标地址list
        # print('filelist:',end='')
        # print(fileList_Info)

        msgList = []
        maxlen = 0
        for filelist in fileList_Info:
            # 传输的文件名称
            filename = filelist[0].split('\\')[-1]
            filelen = len(filename)
            if filelen > maxlen:
                maxlen = filelen
            try:
                if mode == 'put':
                    sftp.put(filelist[0],filelist[1])
                    sftp.utime(filelist[1],(os.path.getatime(filelist[0]),os.path.getmtime(filelist[0])))
                    msgList.append(['文件',filename,'上传成功！'])
                    # print('文件 '+filelist[0].split('\\')[-1]+' 上传成功！')
                elif mode == 'get':
                    print('进入get')
                    print(filelist)
                    sftp.get(filelist[0],filelist[1])
                    a = paramiko.sftp_attr.SFTPAttributes.from_stat(sftp.stat(filelist[0]))
                    os.utime(filelist[1],(a.st_atime,a.st_mtime))
                    msgList.append(['文件', filename, '成功下载到桌面目录！'])
                    # print('文件   '+filelist[0].split('\\')[-1]+'  成功下载到桌面目录!')
                elif mode == 'update':
                    sftp.put(filelist[0], filelist[1])
                    sftp.utime(filelist[1], (os.path.getatime(filelist[0]), os.path.getmtime(filelist[0])))
                    msgList.append(['文件',filename, '更新成功！'])
                    # print('文件   '+filelist[0].split('\\')[-1]+'  更新成功！')
                else:
                    print(mode + ' transfe rFile 模式错误！')
            except Exception as e:
                print(filelist[0],end='')
                print(filelist[1],end='')
                print(e)

        msg = saction.format_printMSG(msgList,2,maxlen)
        print(msg)
    else:
       print('上传文件列表为空！')


def compare_cmd_client(currentGame,cmd_1):
    '''
    将服务器返回的  文件 修改日期，和SVN的 修改日期整合
    :param currentGame:
    :param cmd_1:
    :return:
    '''
    global svnServiceLoader_dir
    global dlls_dir

    maxlen = 0
    msg = ''
    compareFile = cmd_1
    print(compareFile)
    # print(compareFile)
    # 列表长度为1时候  游戏.dll   >1的时候  serviceLoader.exe   .. .dll
    num = len(compareFile)
    print(num)
    if num == 1:
        # 去除name 开头2-3位数字
        dllname = re.sub('^\\d{2,3}','',currentGame)+'.dll'
        dllpath = dlls_dir+dllname
        if os.path.exists(dllpath):
            maxlen = len(dllname)
            compareFile[0].append(time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(dllpath))))
        else:
            compareFile[0].append('')
    else:
        # 统计svn目录下的 dll 和exe文件
        svnFile = []
        for file in os.listdir(svnServiceLoader_dir):
            if file[-4:] == '.dll':
                svnFile.append(file)
        svnFile.append('ServiceLoader.exe')

        for x in range(num):
            length = len(compareFile[x][0])
            if length > maxlen:
                maxlen = length


            status = False
            removeObj = ''
            for file in svnFile:
                if compareFile[x][0] == file:
                    compareFile[x].append(time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(svnServiceLoader_dir+file))))
                    status = True
                    removeObj = file
                    break
            if status:
                svnFile.remove(removeObj)
            else:
                compareFile[x].append('')

        if len(svnFile) >0:
            for file in svnFile:
                length = len(file)
                if length > maxlen:
                    maxlen = length
                compareFile.append([file,'',time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(os.path.getmtime(svnServiceLoader_dir+file)))])

    compareFile.insert(0,['File','Using','SVN'])

    msg = saction.format_printMSG(compareFile,1,maxlen)
    print(msg)



def sendMSG(msg,currentGame,cmdtype):
    '''
    发送消息  到对应的服务器 并接受反馈的消息
    :param msg:发送的  list
    :param currentGame:[client对象，当前管理游戏目录]
    :return: 反馈消息
    '''
    currentGame[0].connect()
    msg.insert(1,currentGame[2])
    msg.insert(2,cmdtype[0])
    msgstr = json.dumps(msg)
    currentGame[0].send(msgstr)
    revstr = currentGame[0].receive()
    currentGame[0].close()
    return json.loads(revstr)

def endAction(msg):
    '''
    接受服务器消息 进行相关操作
    :param msg:
    :return:
    '''



def pringMSG(msg):
    '''
    打印 服务器返回的 打印消息
    :param msg: 打印消息
    :return:
    '''
    pass

def stopRoomMSG_pre(returnMSG):
    '''
    stop命令 执行后的   当前的消息返回
    :param returnMSG:
    :return:
    '''
    lenMSG = len(returnMSG)
    if lenMSG>1:
        for i in range(lenMSG-1):
            print(returnMSG[i+1])

def stopSyc(client):
    global timerList,timerLock

    timerLock.acquire()
    timerList.append(client)
    timerLock.release()
    fun_timer()


def checkStopMSG(revList):
    if revList == ['Wait']:
        return False
    elif revList == ['None']:
        return True
    else:
        for i in revList:
            print(i)

def fun_timer():
    global timer,timerList,timerLock
    if timerList == []:
        timer.cancel()
        return

    msg = ['checkMSG']

    timerLock.acquire()
    for i in timerList[:]:
        msgstr = json.dumps(msg)
        i.connect()
        i.send(msgstr)
        revstr = i.receive()
        i.close()
        revMSG = json.loads(revstr)
        if checkStopMSG(revMSG):
            timerList.remove(i)
    timerLock.release()

    if timerList == []:
        return

    timer = threading.Timer(3,fun_timer)
    timer.start()


def help(cmd=''):
    '''
    帮助命令
    :param cmd:   cmd不是action动作的时候 默认help帮助提示
    :return:
    '''
    actionCMD = ['start','stop','update', 'get', 'put', 'show', 'back', 'compare']
    if cmd == '' or cmd not in actionCMD:
        print('在选择游戏名称后  使用多命令进行管理\n\n'
              '单命令:\n'
              '输入的字符串 会优先匹配游戏目录，游戏目录使用了模糊匹配 \n'
              '如26CrazyRunFastServer 可以输入26  或者fast  当输入匹配多个游戏时，按顺序优先进入！\n'
              'cls 清楚界面消息\n'
              'exit 退出\n\n'
              '多命令:\n'
              'start   命令  启用游戏房间 支持单个、多个、所有\n'
              'update  命令  从本地更新游戏文件 更新游戏dll 或者ServiceLoader\n'
              'back    命令  使用update 或者 put  被覆盖的文件会自动备份，back可以回退到上一个版本的文件\n'
              'get     命令  从游戏目录下载指定文件 \n'
              'put     命令  从本地上传文件到游戏目录\n'
              'show    命令  显示当前游戏的 房间\n'
              'compare 命令  比对 游戏目录  和 SVN 中的文件日期\n'
              '以上 命令使用help+动作命令  获得更详细的帮助！例如 help start')
    elif cmd == 'start':
        print('start 命令 可以单个、多个、全部  启动当前管理游戏的房间\n'
              '进入游戏目录后 使用show room 可以查看游戏的房间配置文件\n'

              '例：\n'
              '26CrazyRunFastServer:>show room\n'
              '手机疯狂跑得快初级场12610.xml        =====未启用！\n'
              '疯狂跑得快中级场12621.xml            =====未启用！\n'
              '疯狂跑得快初级场12611.xml            =====未启用！\n'
              '疯狂跑得快新手场12601.xml            =====未启用！\n'
              '疯狂跑得快顶级场12631.xml            =====未启用！\n'

              '命令使用方法 start 12601     start 12601,12611    start all\n'
              '注意事项：游戏房间配置文件 命名规则    *******12601.xml  文件名最后5位为房间端口号！\n'
              '         端口号          命名规则    100+kindid**  最后两位编号\n'
              '         例： 跑得快  kindID 26     端口号应为126**  12601新手场  12611初级场  12621中级场')
    elif cmd == 'stop':
        print('stop 命令 可以单个、多个、全部  关闭当前管理游戏的房间\n'
              '进入游戏目录后  使用show room 可以查看当前游戏的房间 启动状态\n'
              '例：\n'
              '26CrazyRunFastServer:>show room\n'
              '手机疯狂跑得快初级场12610.xml        》》》》已启用！\n'
              '疯狂跑得快中级场12621.xml            》》》》已启用！\n'
              '疯狂跑得快初级场12611.xml            》》》》已启用！\n'
              '疯狂跑得快新手场12601.xml            》》》》已启用！\n'
              '疯狂跑得快顶级场12631.xml            =====未启用！\n'
              ''
              '命令使用方法 stop 12610     stop 12601,12611     stop all\n'
              '注意事项：游戏房间配置文件 命名规则    *******12601.xml  文件名最后5位为房间端口号！\n'
              '         端口号          命名规则    100+kindid**  最后两位编号\n'
              '         例： 跑得快  kindID 26     端口号应为126**  12601新手场  12611初级场  12621中级场')
    elif cmd == 'update':
        print('update 命令 用于更新游戏文件,文件从本地svn目录自动获取\n'
              'update dll  svn游戏单款dll 更新到游戏目录  旧的单款dll 文件会备份到 游戏目录back\dll中，使用back dll还原本次操作\n'
              'update exe  svn目录ServiceLoader文件  更新到游戏目录  旧的文件会备份到  游戏目录back\exe中，使用back exe还原本次操作'
              )

    elif cmd == 'back':
        print('back 命令用于 还原最近一次备份的文件\n'
              'back ini 还原最近一次备份的ini文件\n'
              'back exe 还原最近一次更新的ServiceLoader文件\n'
              'back dll 还原最近一次更新的单款dll')
    elif cmd == 'get':
        print('get 命令用于获取游戏中的文件,文件下载到本地桌面 以游戏名称命名的文件夹\n'
              '例：当前管理游戏 22CrazyLand3renServer'
              'get GameConfig.ini 将文件下载覆盖到 桌面22CrazyLand3renServer目录\n'
              'get ini 将所有ini文件下载覆盖到 桌面22CrazyLand3renServer目录'
              )
    elif cmd == 'put':
        print('put 命令用于上传桌面游戏目录中的文件到 游戏服务器'
              '例：当前管理游戏 22CrazyLand3renServer\n'
              'put GameConfig.ini 将本地桌面目录22CrazyLand3renServer的 GameConfig.ini 文件上传到游戏目录\n'
              'put ini 将所有将本地桌面目录22CrazyLand3renServer的 所有ini文件上传到游戏目录\n'
              '注意事项：被上传的文件会保留最后一次修改日期'
              )
    elif cmd == 'show':
        print('show 命令用于显示当前管理游戏的 房间或文件\n'
              '例：当前管理游戏 22CrazyLand3renServer\n'
              'show room 显示该游戏目录run文件夹下的 房间配置文件 和端口开启情况\n'
              'show file 显示该游戏目录下的所有文件信息')
    elif cmd == 'compare':
        print('compare 命令用于对比游戏目录下 ServiceLoader 和dll的时间对比\n'
              'compare dll对比游戏目录下的 单款dll 和SVN 单款dll日期\n'
              'compare exe对比游戏目录下的 ServiceLoader 和SVN 的ServiceLoader日期')

# if __name__ == '__main__':
    # print(getServerIpPort())
