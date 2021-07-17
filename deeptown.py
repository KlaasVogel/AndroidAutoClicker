from tkinter import Tk, IntVar, StringVar, Label, Text
from tkinter.ttk import Frame, LabelFrame, Button, Checkbutton, Entry
from dataclasses import dataclass, field
from os import path, getcwd, mkdir
from adb import Template
from glob import glob
from time import sleep
from threading import Thread
from logger import MyLogger, logging
import json
import traceback
import random
from time import time, localtime, strftime
import numpy as np

def build_dir(map):
    if not path.isdir(map):
        mkdir(map)
    return path.join(getcwd(),map)

def loadJSON(file):
    data=[]
    try:
        if path.isfile(file):
            with open(file) as json_file:
                data = json.load(json_file)
    except Exception as e:
        # self.logger.debug("ERROR")
        # self.logger.debug(e)
        traceback.print_exc()
    finally:
        return data

def getName(file):
    filename=f"{path.splitext(path.split(file)[1])[0]}"
    for str in ["_C_","_C","_T","_B","L_","R_"]:
        if str in filename:
            filename=filename.replace(str,"")
    return filename

def findFile(name, filelist):
    for file in filelist:
        filename=path.splitext(path.split(file)[1])[0]
        if name in filename:
            return file
    else:
        return False

def printtime(seconds):
    if seconds <= 60:
        return f"{int(seconds)} seconds"
    if seconds <= 60*60:
        min=int(seconds/60)
        sec=int(seconds%60)
        return f"{min} minute(s) and {sec} seconds"
    hour=int(seconds/3600)
    min=int((seconds%3600)/60)
    sec=int(seconds%60)
    text=f"{hour} hour(s)"
    sep=", " if (min and sec) else " and "
    text=text+sep
    if min:
        text=text+f"{min} minute(s)"
    if sec:
        text=text+f" and {sec} seconds"
    return text

def clearEnd(list):
    for i in range(1,len(list)):
        if list[-i]:
            if i>1:
                list=list[0:-(i-1)]
            break
    return list

@dataclass
class DT_Resource():
    name: str
    folder: str = field(repr=False)
    image: str = field(init=False)
    templateS: Template = field(init=False)
    templateL: Template = field(init=False)
    def __post_init__(self):
        filelist=glob(path.join(self.folder,"*_big*.png"))
        file=findFile(name, filelist)
        if file:
            self.image=file
            self.templateL=Template(file)
        filelist=glob(path.join(self.folder,"*_small*.png"))
        file=findFile(name, filelist)
        if file:
            self.templateS=Template(file)
        # self.logger.debug(self)

class DT_Resources(dict):
    def __init__(self):
        folder=build_dir("resources")
        self.datafile=path.join(folder, "list.json")
        data=loadJSON(self.datafile)
        for resource in data:
            self[resource]=DT_Resource(resource,folder)

class DT_Images(dict):
    def addTemplate(self, fullpath):
        name=getName(fullpath)
        self[name]=Template(fullpath)

@dataclass
class Task():
    name: str
    check: str
    job: str = field(repr=False)
    time: float

class Tasklist(dict):
    def __init__(self,parent,output1, output2, output3):
        self.parent=parent
        self.log=parent.logger
        self.listOutput=output1
        self.taskOutput=output2
        self.console=output3
        self.paused=True
        self.busy=False
        self.lasttask=None
        self.update()

    def start(self):
        self.paused=False
        self.thread=Thread(target=self.run, daemon=True).start()
    def pause(self):
        self.paused=True

    def addTask(self, name, check, job, waittime):
        # self.log.debug(f'\n adding job for {name}')
        task=Task(name, check, job, waittime)
        self.setTask(task, True)
        if not hasattr(self.parent, check):
            setattr(self.parent, check, True)

    def setTask(self,task, firsttime=False):
        if task.time or firsttime:
            # self.log.debug(f'\n resetting job for {task.name}')
            new_time=0 if firsttime else int(time())+task.time*60
            while new_time in self:
                new_time+=1
            self[new_time]=task

    def run(self):
        print(self)
        while not self.paused:
            cur_time=int(time())
            if len(self):
                firsttask=sorted(self)[0]
                if firsttask<=cur_time and not self.busy:
                    task=self.pop(firsttask)
                    self.taskOutput.set(f"Current Task: {task.name} [started at {strftime('%H:%M:%S',localtime())}]")
                    if getattr(self.parent, task.check):
                        self.busy=True
                        task.job()
                        self.busy=False
                        self.setTask(task)
            sleep(1)

    def getData(self):
        data=[]
        timelist=sorted(self)
        cur_time=int(time())
        # data.append(strftime("%H:%M:%S",localtime()))
        for tasktime in timelist:
            remaining_time=tasktime-cur_time
            task=self[tasktime]
            data.append(f"{task.name} in {printtime(remaining_time)}")
        return data

    def update(self):
        try:
            data=self.getData()
            self.listOutput.delete("1.0","end")
            for line in data:
                self.listOutput.insert("end",str(line)+"\n")
        except Exception as e:
            traceback.print_exc()
        finally:
            self.parent.after(1000, self.update)

@dataclass
class Station():
    name: str
    boostable: int
    def __post_init__(self):
        if self.boostable:
            self.boost=IntVar()

class Stations(dict):
    def __init__(self, data):
        try:
            for name in data:
                image=data[name]["image"]
                boostable=data[name]["boost"]
                self.add(image, name, boostable)
        except:
            traceback.print_exc()
    def add(self, image, name, boostable=True):
        self[image]=Station(name, boostable)

class Boosts(LabelFrame):
    def __init__(self, parent):
        LabelFrame.__init__(self,parent, text="Boosts:")
        self.pack(side='top')
        self.tower_name_list=Stations(loadJSON(path.join("data","towerlist.json")))
        self.shaft_name_list=Stations(loadJSON(path.join("data","shaftlist.json")))
        self.items=[]
        for name,list in {"Tower:":self.tower_name_list, "Shaft:":self.shaft_name_list}.items():
            self.items.append(Label(self, text=name))
            for station in list.values():
                if station.boostable:
                    self.items.append(Checkbutton(self, text=station.name, variable=station.boost, onvalue=1))
        for idx,item in enumerate(self.items):
            item.grid(row=idx+1,column=1, sticky='w')

    def get(self, item):
        list=self.shaft_name_list if item=="shaft" else self.tower_name_list
        result=[]
        for idx, station in enumerate(list.values()):
            if station.boostable and station.boost.get():
                result.append(idx+1)
        print(f"get {item}: {result}")
        return result

class DeepTown(LabelFrame):
    def __init__(self, parent, device):
        self.logger=MyLogger('DeepTown', LOG_LEVEL=logging.DEBUG)
        self.parent=parent
        self.device=device
        LabelFrame.__init__(self, parent, text="Deep Town")
        self.buildFrames()
        self.buildButtons(self.frames[0])
        self.boosts=Boosts(self.frames[1])
        self.buildOutput(self.frames[2])
        self.plan_scan_shaft()
        self.plan_scan_tower()
        self.loadTemplates(build_dir("DT_images"))
        self.prod_boost_types=[2,3,6]

    def buildOutput(self,frame):
        self.textList=Text(frame,height=7)
        self.stringTask=StringVar()
        self.labelTask=Label(frame, textvariable=self.stringTask)
        self.textConsole=Text(frame,height=7)
        self.textList.grid(row=2, column=1)
        self.labelTask.grid(row=1, column=1, sticky='w')
        self.textConsole.grid(row=3, column=1)
        self.tasklist=Tasklist(self,self.textList,self.stringTask,self.textConsole)

    def buildFrames(self):
        self.frames=[]
        for i in range(4):
            self.frames.append(Frame(self))
            self.frames[-1].grid(row=1, rowspan=10, column=i+1)

    def loadTemplates(self, map):
        self.templates=DT_Images()
        filelist=glob(path.join(map,"*.png"))
        for file in filelist:
            self.templates.addTemplate(file)

    def build_label_button(self, frame, name, check, button, command, time=5):
        dict={"lbl": Label(frame, text=f"{name}:"),
              "btn": Button(frame, text="Start", command=lambda: self.trigger(name,check,button,command,time))}
        return dict

    def buildButtons(self,frame):
        self.buttons={}
        self.buttons['prntscr']={"btn":Button(frame, text="Print Screen", command=self.device.printScreen)}
        # self.buttons['areas']={"btn":Button(frame, text="Areas")}
        # self.buttons['resources']={"btn":Button(frame, text="Resources")}
        self.buttons['running']={'btn':Button(frame, text="Start Tasks", command=self.start_tasks)}
        self.buttons['collect']=self.build_label_button(frame,"Collect Ores", "collecting", "collect", lambda: self.collect(1),time=4)
        self.buttons['pump']=self.build_label_button(frame,"Pump Oil", "collecting oil", "pump", lambda: self.collect(3),time=7)
        self.buttons['boost']=self.build_label_button(frame,"Boost", "boosting", "boost", self.boost,time=2)
        self.buttons['boost_prod']=self.build_label_button(frame,"Boost Production", "boosting_production", "boost_prod", self.boost_product,time=2.5)
        self.buttons['cc']=self.build_label_button(frame,"Check Chests", "checking_chests", "cc", self.openChests,time=10)
        self.buttons['ca']=self.build_label_button(frame,"Check Ads", "checking_ads","ca",self.searchAds,time=6.01)
        self.buttons['explore']=self.build_label_button(frame,"Explore", "exploring", "explore", self.explore,time=60.1)
        i = 1
        for dict in self.buttons.values():
            i+=1
            if "lbl" in dict:
                dict["lbl"].grid(row=i, column=1)
                dict["btn"].grid(row=i, column=2)
            else:
                dict["btn"].grid(row=i, column=1, columnspan=2)

    def checkTemplates(self, list):
        checklist=[]
        for image in list:
            if image not in self.templates:
                checklist.append(image)
        if len(checklist):
            # self.logger.debug("need images:")
            # self.logger.debug(checklist)
            # self.logger.debug(self.templates)
            return False
        return True

    def start_tasks(self):
        if self.tasklist.paused:
            self.buttons['running']["btn"].configure(text="Pause")
            self.tasklist.start()
        else:
            self.buttons['running']["btn"].configure(text="Start Tasks")
            self.tasklist.pause()

    def trigger(self, name, check, button, task, time):
        if not hasattr(self, check):
            setattr(self, check, False)
        if getattr(self, check):
            setattr(self, check, False)
            self.buttons[button]["btn"].configure(text="Start")
        else:
            setattr(self, check, True)
            self.buttons[button]["btn"].configure(text="Stop")
            self.tasklist.addTask(name, check, task, time)


    def tap(self,name,wait=.5, error=.8):
        # self.logger.debug(f"locating: {name}")
        try:
            location=self.device.locate_item([self.templates[name]],error,one=True)
            if not location:
                raise Exception(f"Image ({name}) not found on screen")
            self.device.tap(*location)
            sleep(wait)
            return True
        except Exception as e:
            # # self.logger.debug("ERROR")
            # self.logger.debug(e)
            # traceback.print_exc()
            return False

    def restart_app(self):
        print("restarting App")
        self.device.restartApp("com.rockbite.deeptown","AndroidLauncher")
        sleep(10)
        if not self.move_home():
            quit()

    def move_home(self):
        images=["return", "surface", "tower_bottom", "main_down"]
        if self.checkTemplates(images):
            self.tap("close_video")
            self.tap("exit_boost")
            self.tap("return")
            self.tap("surface")
            self.tap("tower_bottom")
            if self.device.locate_item([self.templates["main_down"]],.75,one=True):
                return True
        self.device.go_back()
        self.restart_app()

    def check_images(self, image):
        result=False
        location=self.device.locate_item([self.templates[image]],.8,one=True)
        if len(up_button):
            return True
        return False

    def plan_scan_shaft(self):
        self.tasklist.addTask('Scan Mineshaft', 'scanning shaft', self.scan_shaft, 0)
        self.reset_shaft=True

    def plan_scan_tower(self):
        self.tasklist.addTask('Scan Tower', 'scanning tower', self.scan_tower, 0)
        self.reset_tower=True

    def scan_shaft(self):
        print("SCAN SHAFT")
        self.shaft=[]
        self.boosted=[]
        self.reset_shaft=False
        scanlist=[]
        stations=self.boosts.shaft_name_list.keys()
        images=[]
        for i in range(1,9):
            images.append(f"level_{i}")
        for station in stations:
            images.append(f"text_{station}")
        images.extend(["main_down", "mine_up", "info"])
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",2)
            while(self.tap("mine_up")):
                result=[0,0]
                if len(self.device.locate_item([self.templates["info"]],.8,one=True)):
                    for id,station in enumerate(stations):
                        if len(self.device.locate_item([self.templates[f"text_{station}"]],.8,one=True,last=True)):
                            result=[id+1,0]
                            for i in range(8,0,-1):
                                if len(self.device.locate_item([self.templates[f"level_{i}"]],.95,one=True,last=True)):
                                    result=[id+1,i]
                                    break
                scanlist.append(result)
        self.shaft=scanlist
        print(self.shaft)

    def getShaftList(self,types):
        result=[]
        for type,lvl in self.shaft:
            result.append(1) if type in types else result.append(0)
        print(result)
        return result

    def scan_tower(self):
        self.tower=[]
        scanlist=[]
        stations=self.boosts.tower_name_list.keys()
        images=[]
        for i in range(1,9):
            images.append(f"level_{i}")
        for station in stations:
            images.append(f"text_{station}")
        images.extend(["main_up", "tower_down", "info"])
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_up",2)
            while(self.tap("tower_down")):
                result=[0,0]
                if len(self.device.locate_item([self.templates["info"]],.8,one=True)):
                    for id,station in enumerate(stations):
                        if len(self.device.locate_item([self.templates[f"text_{station}"]],.8,one=True,last=True)):
                            result=[id+1,0]
                            for i in range(8,0,-1):
                                if len(self.device.locate_item([self.templates[f"level_{i}"]],.95,one=True,last=True)):
                                    result=[id+1,i]
                                    break
                print(result)
                scanlist.append(result)
            print(scanlist)
        self.tower=scanlist

    def explore(self):
        # self.logger.debug("Expedition")
        images=["main_down", "mine_up", "expedition_next", "expedition_claim", "expedition_start"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",3)
            up_button=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
            if len(up_button):
                while (not self.tap("main_up")):
                    check=False
                    self.device.tap(*up_button)
                    sleep(.5)
                    while (self.tap("expedition_next")):
                        # self.logger.debug("  --> next chapter")
                        check=True
                    if self.tap("expedition_claim",1):
                        # self.logger.debug("claiming Price")
                        check=True
                        sleep(2)
                    if self.tap("expedition_start",1):
                        # self.logger.debug(" --> staring next exploration")
                        check=True
                    if check:
                        break
            self.move_home()

    def collect(self,type):
        print("COLLECT")
        images=["main_down", "mine_claim", "mine_up", "tower_down", "oil_claim"]
        claim="mine_claim" if type==1 else "oil_claim"
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",3)
            self.drilllist=clearEnd(self.getShaftList([type]))
            location=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
            if len(location):
                for collect in self.drilllist:
                    self.device.tap(*location)
                    sleep(.3)
                    if collect:
                        sleep(.4)
                        if not self.tap(claim,.1,error=.7) and not self.reset_shaft:
                            print("resetting mines")
                            self.plan_scan_shaft()
                self.tap("surface")
                self.tap("main_up")
            self.tap("tower_down")
            self.tap("mine_claim",.1)
            self.move_home()

    def boost(self):
        print("BOOST")
        images=["main_down", "mine_boost", "boost_play", "mine_up", "exit_boost"]
        boostlist=self.boosts.get("shaft")
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",2)
            count=0
            shaftlist=clearEnd(self.getShaftList(boostlist))
            if not hasattr(self, "boosted"):
                self.boosted=[]
            if not len(self.boosted):
                for i in range(len(shaftlist)):
                    self.boosted.append(False)
            location=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
            if len(location):
                for idx,collect in enumerate(shaftlist):
                    self.device.tap(*location)
                    sleep(.3)
                    if collect and not self.boosted[idx]:
                        if not self.tap("mine_boost",.1) and not self.reset_shaft:
                            self.plan_scan_shaft()
                        self.boosted[idx]=True
                        playbutton=self.device.locate_item([self.templates["boost_play"]],.8,one=True)
                        if playbutton:
                            self.watchAd(playbutton,"exit_boost")
                            count+=1
                        self.tap("exit_boost",.2)
                    if count>=4:
                        break
                else:
                    for i in range(len(self.boosted)):
                        self.boosted[i]=False
            self.move_home()

    def boost_product(self):
        images=["main_up", "production_boost", "boost_play", "tower_down", "exit_boost"]
        boostlist=self.boosts.get("tower")
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_up")
            button_dwn=self.device.locate_item([self.templates["tower_down"]],.8,one=True)
            for type,lvl in self.tower:
                self.device.tap(*button_dwn)
                sleep(.3)
                print(type, lvl)
                if type in boostlist and self.tap("production_boost",.5,.6):
                    playbutton=self.device.locate_item([self.templates["boost_play"]],.7,one=True)
                    if playbutton:
                        self.watchAd(playbutton,"exit_boost")
                    self.tap("exit_boost",.2)
        self.move_home()


    def openChests(self):
        images=["return","inventory","menu_chest","closed_chest_small","closed_chest_big","open_chest_big"]
        if self.checkTemplates(images):
            if self.move_home() and self.tap("inventory"):
                self.tap("menu_chest")
                location=self.device.locate_item([self.templates["closed_chest_small"]],.8,one=True)
                count=0
                while location and count<10:
                    self.device.tap(*location)
                    sleep(.5)
                    self.tap("closed_chest_big", 5)
                    self.tap("open_chest_big")
                    count+=1
                    location=self.device.locate_item([self.templates["closed_chest_small"]],.8,one=True)
                self.tap("return")

    def watchAd(self, location, exit, showActivity=False):
        images=["close_video"]
        if self.checkTemplates(images):
            # print("watching Ad")
            # print(location)
            # self.logger.debug("watching Ad")
            self.device.tap(*location)
            sleep(3)
            if not self.tap("ok"):
                wait=random.randrange(31, 36)
                sleep(wait)
                if showActivity:
                    self.device.getApplist(True)
                self.device.go_back()
                sleep(2)
                if not self.device.locate_item([self.templates[exit]],.8, one=True):
                    # self.logger.debug("Stuck on Ad?")
                    self.device.go_back()
                    newlocation=[851,44]
                    self.device.tap(*newlocation)
                    sleep(1)
                    self.device.go_back()
                        # self.device.go_back()

    def searchAds(self):
        images=["return","store","store2","watch_free","claim"]
        if self.checkTemplates(images):
            self.move_home()
            if self.tap("store") or self.tap("store2"):
                count=0
                for image in ["watch_free","claim"]:
                    location=self.device.locate_item([self.templates[image]],.75,one=True)
                    self.logger.info(f"Ads: {image}")
                    while (location and count<3):
                        showInfo = True if image=="watch_free" else False
                        # showInfo=True
                        self.watchAd(location, "return", showInfo)
                        sleep(2)
                        count+=1
                        location=self.device.locate_item([self.templates[image]],.75,one=True)
                self.tap("return")
