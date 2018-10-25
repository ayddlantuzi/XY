from socket import *
import json


class gsClient:
    def __init__(self,GSname,addr,family = AF_INET,type = SOCK_STREAM,BUFSIZ = 4096):
        '''
        连接GameServer 的client类
        :param GSname:
        :param addr:
        :param family:
        :param type:
        :param BUFSIZ:
        '''
        self.GSname = GSname
        self.addr = addr
        self.host = addr[0]
        self.family = family
        self.type = type
        self.BUFSIZ = BUFSIZ
        self.status = False


    def connect(self):
        try:
            self.sock = socket(self.family, self.type)
            self.sock.connect(self.addr)
            self.status = True
            return True
        except Exception as e:
            # print(e)
            return False


    def close(self):
        try:
            self.sock.close()
            self.sock = None
        except Exception as e:
            print(e)

    def send(self,data):
        try:
            self.sock.send(data.encode())
        except Exception as e:
            print(e)

    def receive(self):
        try:
            data = self.sock.recv(self.BUFSIZ).decode()
            return data
        except Exception as e:
            print(e)

def getClientGroup(serverIpPortList):
    '''
    获得所有服务器连接
    :param serverIpPortList:[[name1,(ip,port)],[]]
    :return: 返回列表[[client1,client1备份][client2,client2备份]...]
    '''
    clientList = []

    for i in serverIpPortList:
        gsc = gsClient(i[0],i[1])
        gscc = gsClient(i[0],i[1])
        clientList.append([gsc,gscc])

    return clientList


def client_getServerGameInfo(clientgroup):
    '''
    连接所有clientgroup中的服务器，获取基础信息
    :param clientgroup: 所有连接[[c1,c1备份]，[c2,c2备份]，[c3,c3备份]....]
    :return: 返回 收集的服务器初始化消息 [[client对象,client对象,[消息，消息，消息]],[client对象，client对象,[消息，消息，消息]]]

    return : 修改后
            [{'game':['***','***'...],'match':['***','***'...] , 'service':['***','***'...] , 'client':[**,**]}
             {'game':['***','***'...],'match':['***','***'...] , 'service':['***','***'...] , 'client':[**,**]}
             {'game':['***','***'...],'match':['***','***'...] , 'service':['***','***'...] , 'client':[**,**]}
            ]

    return: 修改 finally
    {'game': [ [[***,***,***],n],[[***,***,***],n],'match':...  ,'service':...  ]}
    {n:[client1,client1_copy],n:[client2,client2_copy]...}
    '''

    unconnected_num = len(clientgroup)
    allGameInfo = []
    while unconnected_num > 0:
        for clientg in clientgroup[:]:
            client = clientg[0]
            if client.connect():
                # 发送消息获取 服务器初始消息
                client.send(json.dumps(['getinfo']))
                revdata = client.receive()
                print(revdata)
                print(type(revdata))
                info = json.loads(revdata)
                print(info)
                # if type(info) == list:
                #     info.insert(0,client)
                #     info.insert(1,clientg[1])
                #     allGameInfo.append(info)
                # else:
                #     print(client.GSname+'接收数据类型非List  请检查~')

                if type(info) == dict:
                    info.update({'client':clientg})
                    allGameInfo.append(info)
                else:
                    print(client.GSname + '接收数据类型非Dict  请检查~')
                print(client.GSname+'  连接成功√ √ √')

                client.close()
                clientgroup.remove(clientg)
            else:
                print(client.GSname+'  连接失败× × ×   查看服务器端是否开启！')
        # 判断是否有未连接 成功的client
        unconnected_num = len(clientgroup)
        if unconnected_num > 0:
            data = input('未连接的Server 是否尝试重连！  yes 尝试重连，任意字符 继续操作')
            if data.strip().lower() == 'yes':
                continue
            else:
                break
    # 消息整合处理

    return analyzeInfo(allGameInfo)


def analyzeInfo(allGameInfo):
    '''
    client端收集的初始消息整合
    :param allGameInfo:
    [{'game':['***','***'...],'match':['***','***'...] , 'service':['***','***'...] , 'client':[**,**]}
      {'game':[['***','***'...],[]],'match':['***','***'...] , 'service':['***','***'...] , 'client':[**,**]}
      {'game':[['***','***'...],[]],'match':['***','***'...] , 'service':['***','***'...] , 'client':[**,**]}
    ]
    :return:
    '''
    gameList = []
    matchList = []
    serviceList = []
    clientDict = {}

    n = 0
    for singleDict in allGameInfo:
        clientGroup = singleDict['client']
        clientDict.update({n:clientGroup})
        if 'game' in singleDict:
            gameList.append([singleDict['game'],n])
        if 'match' in singleDict:
            matchList.append([singleDict['match'],n])
        if 'service' in singleDict:
            serviceList.append([singleDict['service'],n])
        n += 1

    return {'game':gameList,'match':matchList,'service':serviceList},clientDict





