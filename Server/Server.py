import socket
import tkinter as tk
import os, signal
from PIL import ImageGrab
import json
import subprocess
import threading
import winreg

import appController
import processController
import ftpController
import keyboardController
import macAddress
import powerController
import streamingServer

PORT = 5000

class Server(tk.Frame):
    def __init__(self, master = None):
        self.__running = False
        self.__host = ''
        self.__port = PORT
        self.__client = None
        self.__serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__serverSocket.bind((self.__host, self.__port))

        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.createWidgets()

    #DESIGN
    def createWidgets(self):      
        #Button1
        self.butConnect = tk.Button(self,text = "Open server", relief="groove")
        self.butConnect["command"] = self.buttonClick
        self.butConnect.place(x=50, y=15, height=70, width=100) 

    def Shutdown(self):
        os.system("shutdown /s /t 60")

    def Screenshot(self):
        while True:
            buffer = ""
            buffer = self.__client.recv(1024).decode("utf-8")
            if not buffer:
                break
            if buffer == "Take":
                img = ImageGrab.grab()
                imgToSend = img.tobytes()
                size = len(imgToSend)
                self.__client.send(str(size).encode('utf-8'))
                check = self.__client.recv(10)
                self.__client.send(str(img.size[0]).encode('utf-8'))
                check = self.__client.recv(10)
                self.__client.send(str(img.size[1]).encode('utf-8'))
                check = self.__client.recv(10)
                self.__client.send(imgToSend)
            else:
                break        

    def BaseRegistryKey(self,link):
        a = None
        if link.find("\\")>=0 :
            key = link[:link.find("\\")]
            if key == "HKEY_CLASSIES_ROOT": a = winreg.HKEY_CLASSES_ROOT
            elif key == "HKEY_CURRENT_USER": a = winreg.HKEY_CURRENT_USER
            elif key == "HKEY_LOCAL_MACHINE": a = winreg.HKEY_LOCAL_MACHINE
            elif key == "HKEY_USERS": a = winreg.HKEY_USERS
            elif key == "HKEY_CURRENT_CONFIG": a = winreg.HKEY_CURRENT_CONFIG
            else: a = None
        return a   
        
    def SubKey(self,link):
        a = None
        if link.find("\\")>=0 :
            a = link[link.find("\\")+1:]
        return a

    def Value2String(self,value,typeValue):
        if typeValue == winreg.REG_SZ: 
            return value
        elif typeValue == winreg.REG_MULTI_SZ:
            return " ".join(value)
        elif typeValue ==  winreg.REG_EXPAND_SZ:
            return value
        elif typeValue == winreg.REG_BINARY:
            temp = bytearray(value)
            temp = [str(i) for i in temp]
            return " ".join(temp)
        elif typeValue == winreg.REG_DWORD:
            return str(value)
        elif typeValue == winreg.REG_QWORD:
            return str(value)
        else:
            return str(value)
    def String2Value(self,stringValue,typeValue):
        try:
            if typeValue == winreg.REG_SZ: 
                return stringValue
            elif typeValue == winreg.REG_MULTI_SZ:
                return stringValue.split("\n")
            elif typeValue ==  winreg.REG_EXPAND_SZ:
                return stringValue
            elif typeValue == winreg.REG_BINARY:
                temp = bytes()
                for  i in stringValue.split():
                    try:
                        temp += bytes([int(i)])
                    except:
                        temp += bytes([int(i,16)])
                return temp
            elif typeValue == winreg.REG_DWORD:
                return int(stringValue)
            elif typeValue == winreg.REG_QWORD:
                return int(stringValue)
            else:
                return stringValue
        except:
            return None


    def getValue(self,aKey,subKey,valueName):
        try:
            key = winreg.OpenKey(aKey,subKey,0, winreg.KEY_ALL_ACCESS)
            if not key:return "Error"
        except:
            return "Error"

        try: 
            value = winreg.QueryValueEx(key, valueName)
            stringValue = self.Value2String(value[0], value[1])
            return stringValue
        except:
            return "Error"
    
    def setValue(self,aKey,subKey,valueName, value, typeValue):
        try:
            key = winreg.OpenKey(aKey,subKey,0, winreg.KEY_ALL_ACCESS)
            if not key:return "Error"
        except:
            return "Error"
        
        kind = None
        if typeValue == "Binary": kind = winreg.REG_BINARY 
        elif typeValue == "DWORD": kind = winreg.REG_DWORD
        elif typeValue == "QWORD": kind = winreg.REG_QWORD
        elif typeValue == "String": kind = winreg.REG_SZ
        elif typeValue == "Multi-String": kind = winreg.REG_MULTI_SZ
        elif typeValue == "Expandable String": kind = winreg.REG_EXPAND_SZ
        else: return "Error"

        try:
            tempValue = self.String2Value(value,kind)
            winreg.SetValueEx(key,valueName,0,kind,tempValue)
        except:
            return "Error"
        return "Success"

    def deleteValue(self,aKey,subKey,valueName):
        try:
            key = winreg.OpenKey(aKey,subKey,0, winreg.KEY_ALL_ACCESS)
            if not key:return "Error"
        except:
            return "Error"
        try:
            winreg.DeleteValue(key,valueName)
        except:
            return "Error"
        return "Success"
    
    def Registry(self):
        while True:
            buffer = ""
            buffer = self.__client.recv(1024).decode("utf-8")
            if not buffer:
                break
            if buffer=="Reg":
                data = self.__client.recv(4096).decode("utf-8")
                f = open("fileReg.reg","w")
                f.write(data)
                f.close()
                test = True
                s = None
                try:
                    subprocess.call(["reg", "import", "fileReg.reg"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except:
                    test = False    
                if test: s = "Successful edit"
                else: s = "Edit failure"
                self.__client.send(s.encode("utf-8"))
            elif buffer =="Send":
                self.__client.send("OK".encode("utf-8"))

                option = self.__client.recv(1024).decode("utf-8")
                self.__client.send("OK".encode("utf-8"))

                link = self.__client.recv(1024).decode("utf-8")
                self.__client.send("OK".encode("utf-8"))

                valueName = self.__client.recv(1024).decode("utf-8")
                self.__client.send("OK".encode("utf-8"))

                value = self.__client.recv(1024).decode("utf-8")
                self.__client.send("OK".encode("utf-8"))

                typeValue = self.__client.recv(1024).decode("utf-8")
                s = None
                aKey = self.BaseRegistryKey(link)
                subKey = self.SubKey(link)
                if option == "Create key":
                    try:
                        winreg.CreateKey(aKey,subKey)
                        s = "Success"
                    except:
                        s = "Error"
                elif option == "Delete key":
                    try:
                        winreg.DeleteKey(aKey,subKey)
                        s = "Success"
                    except:
                        s = "Error"
                elif option == "Get value": 
                    s = self.getValue(aKey,subKey,valueName)
                elif option == "Set value":
                    s = self.setValue(aKey,subKey,valueName,value,typeValue)
                elif option == "Delete value":
                    s = self.deleteValue(aKey,subKey,valueName)
                else:
                    s = "Error"
                
                self.__client.send(s.encode("utf-8"))
            else:
                return 

    def process2List(self,processes):
        a = processes.decode().strip()
        b = a.split("\r\n")
        b = [" ".join(x.split()) for x in b]
        c = [x.split() for x in b][2:]
        return c

    def AppRunning(self):
        Apps = []      
        while True:
            buffer = ""
            buffer = self.__client.recv(1024).decode("utf-8")
            if not buffer:
                break

            if buffer == "View":
                s = subprocess.check_output("powershell gps | where {$_.MainWindowTitle} | select Name,Id,@{Name='ThreadCount';Expression={$_.Threads.Count}}", stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                Apps = self.process2List(s)
                dataToSend = json.dumps(Apps).encode('utf-8') 
                size = len(dataToSend)
                self.__client.send(str(size).encode('utf-8'))
                check = self.__client.recv(10)
                self.__client.send(dataToSend)
            elif buffer == "Kill":
                while True:
                    buffer2 = ""
                    buffer2 = self.__client.recv(1024).decode("utf-8")
                    if buffer2 == "KillID":
                        IDtoKill = self.__client.recv(10).decode('utf-8')
                        test = False
                        for app in Apps:
                            if IDtoKill==app[1]:
                                try:
                                    os.kill(int(IDtoKill), signal.SIGTERM) 
                                    s = "Success"
                                    self.__client.send(s.encode('utf-8'))
                                except:
                                    s = "Error"
                                    self.__client.send(s.encode('utf-8'))
                                test = True
                        if test==False:
                            s = "No App Found"
                            self.__client.send(s.encode('utf-8'))
                    else:
                        break 
            elif buffer == "Start":
                while True:
                    buffer2 = ""
                    buffer2 = self.__client.recv(1024).decode("utf-8")
                    if buffer2 == "StartID":
                        AppToStart = self.__client.recv(1024).decode('utf-8') + ".exe"
                        try:
                            PathApp= os.path.relpath(AppToStart)
                            os.startfile(PathApp)
                            s = "Success"
                            self.__client.send(s.encode('utf-8'))
                        except:
                            s = "Error"
                            self.__client.send(s.encode('utf-8'))
                    else:
                        break
            else: #Quit
                return
    
    def ProcessRunning(self):
        Processes = []

        while True:
            buffer = ""
            buffer = self.__client.recv(1024).decode("utf-8")
            if not buffer:
                break

            if buffer == "View":
                s = subprocess.check_output("powershell gps | select Name,Id,@{Name='ThreadCount';Expression={$_.Threads.Count}}",stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                Processes = self.process2List(s)

                dataToSend = json.dumps(Processes).encode('utf-8') 
                size = len(dataToSend)
                self.__client.send(str(size).encode('utf-8'))
                check = self.__client.recv(10)
                self.__client.send(dataToSend)
            elif buffer == "Kill":
                while True:
                    buffer2 = ""
                    buffer2 = self.__client.recv(1024).decode("utf-8")
                    if buffer2 == "KillID":
                        IDtoKill = self.__client.recv(10).decode('utf-8')
                        test = False
                        for process in Processes:
                            if IDtoKill == process[1]:
                                try:
                                    os.kill(int(IDtoKill),signal.SIGTERM)
                                    s = "Success"
                                    self.__client.send(s.encode('utf-8'))
                                except:
                                    s = "Error"
                                    self.__client.send(s.encode('utf-8'))
                                test = True
                        if test == False:
                            s = "Error"
                            self.__client.send(s.encode('utf-8'))
                    else:
                        break 
            elif buffer == "Start":
                while True:
                    buffer2 = ""
                    buffer2 = self.__client.recv(1024).decode("utf-8")
                    if buffer2 == "StartID":
                        ProcessToStart = self.__client.recv(1024).decode('utf-8') + ".exe"
                        try:
                            PathProcess = os.path.relpath(ProcessToStart)
                            os.startfile(PathProcess)
                            s = "Success"
                            self.__client.send(s.encode('utf-8'))
                        except:
                            s = "Error"
                            self.__client.send(s.encode('utf-8'))
                    else:
                        break
            else: #Quit
                return

    def KeyStroke(self):
        self.keyController.startListening()
        
    def buttonClick(self):
        self.__serverSocket.listen(5)
        print("Waiting for connection...")
        self.__client, addr = self.__serverSocket.accept()

        self.appController = appController.AppController(self.__client)
        self.processController = processController.ProcessController(self.__client)
        self.ftpController = ftpController.FtpController(self.__client)
        self.keyboardController = keyboardController.KeyboardController(self.__client)
        self.macAddress = macAddress.MacAddress(self.__client)
        self.powerController = powerController.PowerController(self.__client)
        self.streamingServer = streamingServer.StreamingServer(self.__client)

        while True:
            buffer = ""
            buffer = self.__client.recv(1024)
            
            if not buffer:
                break
            message = buffer.decode('utf-8')
            if message == "POWER":
                self.powerController.startListening()
            elif message == "KEYBOARDCONTROLLER":
                self.keyboardController.startListening()
            elif message == "MACADDRESS":
                self.macAddress.startListening()
            

            elif message == "SCREENSHOT":
                self.Screenshot()
            elif message == "REGISTRY":
                self.Registry()
            elif message == "APP":
                self.AppRunning()
            elif message == "PROCESS":
                self.ProcessRunning()
            elif message == 'EXIT':
                root.destroy()
                break
            else:
                break
        self.__serverSocket.close()
        

def CloseButton(root):
    root.destroy()

root = tk.Tk()
root.protocol('WM_DELETE_WINDOW', lambda: CloseButton(root))
app = Server(root)
app.master.title("Server")
app.master.minsize(210, 100)
app.mainloop()


