from tkinter import Tk, IntVar, StringVar, Label, Text
from tkinter.ttk import Frame, LabelFrame, Button, Checkbutton, Entry, OptionMenu
from dataclasses import dataclass, field
from os import path, getcwd, mkdir
from adb import Template
from glob import glob
from time import sleep
from logger import MyLogger, logging
from json_tools import loadJSON, saveJSON
from tasks import Tasks, Tasklist, TempTask
import traceback
import random
from time import time, localtime, strftime
import numpy as np

def build_dir(map):
    if not path.isdir(map):
        mkdir(map)
    return path.join(getcwd(),map)

def loadTemplates(map):
    templates=DT_Images()
    filelist=glob(path.join(map,"*.png"))
    for file in filelist:
        templates.addTemplate(file)
    return templates

class DT_Images(dict):
    def addTemplate(self, fullpath):
        name=getName(fullpath)
        self[name]=Template(fullpath)

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

def clearEnd(list):
    for i in range(1,len(list)+1):
        if list[-i]:
            if i>1:
                list=list[0:-(i-1)]
            break
    return list

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
    def __init__(self, parent, **kwargs):
        LabelFrame.__init__(self,parent, text="Boosts:")
        self.grid(**kwargs)
        self.parent=parent
        self.json_file=path.join("data","boosts.json")
        boostlist=loadJSON(self.json_file)
        self.items=[]
        for name,list in {"Tower:":parent.tower_stations, "Shaft:":parent.shaft_stations}.items():
            self.items.append(Label(self, text=name))
            for station in list.values():
                if station.boostable:
                    self.items.append(Checkbutton(self, text=station.name, variable=station.boost, onvalue=1))
                    if station.name in boostlist and boostlist[station.name]:
                        station.boost.set(1)
                    station.boost.trace_add('write',self.save)
        for idx,item in enumerate(self.items):
            item.grid(row=idx+1,column=1, sticky='w')

    def get(self, item):
        list=self.parent.shaft_stations if item=="shaft" else self.parent.tower_stations
        result=[]
        for idx, station in enumerate(list.values()):
            if station.boostable and station.boost.get():
                result.append(idx+1)
        print(f"get {item}: {result}")
        return result

    def save(self,*args):
        data={}
        for list in [self.parent.tower_stations,self.parent.shaft_stations]:
            for station in list.values():
                if station.boostable:
                    data[station.name]=station.boost.get()
        saveJSON(data, self.json_file)

class Request(LabelFrame):
    def __init__(self, parent, **kwargs):
        LabelFrame.__init__(self, parent, text="Request:")
        self.grid(**kwargs)
        self.json_file=path.join("data","request.json")
        self.label=Label(self,text="Request Item:")
        self.label.grid(row=0,column=0)
        self.choosen=StringVar()
        options=["----"]
        options.extend(parent.temp_req.keys())
        self.menu=OptionMenu(self,self.choosen,*options)
        self.load(options)
        self.menu.grid(row=0, column=1)
        self.choosen.trace_add('write',self.save)

    def load(self,list):
        name=loadJSON(self.json_file)
        if len(name) and name in list:
            self.choosen.set(name)

    def save(self,*args):
        saveJSON(self.choosen.get(),self.json_file)

class DeepTown(LabelFrame):
    def __init__(self, parent, device):
        self.logger=MyLogger('DeepTown', LOG_LEVEL=logging.DEBUG)
        self.parent=parent
        self.device=device
        LabelFrame.__init__(self, parent, text="Deep Town")
        # self.buttons=Buttons(self,row=1,column=1,sticky='nw')
        self.tasklist=Tasklist(self,row=6,column=1,columnspan=3, sticky='w')
        self.loaddata()
        self.boosts=Boosts(self,row=2,column=3,sticky='nw')
        self.tasks=Tasks(self, self.tasklist, row=1, column=1, rowspan=5,columnspan=2, sticky='w')
        self.templates=loadTemplates(build_dir("DT_images"))
        self.temp_req=loadTemplates(build_dir(path.join("DT_images","requests")))
        self.requests=Request(self,row=1,column=3, sticky='nw')

    # def buildOutput(self,parent,**kwargs):
    #     self.textList=Text(frame,height=7)
    #     self.stringTask=StringVar()
    #     self.labelTask=Label(frame, textvariable=self.stringTask)
    #     self.textConsole=Text(frame,height=7)
    #     self.textList.grid(row=2, column=1)
    #     self.labelTask.grid(row=1, column=1, sticky='w')
    #     self.textConsole.grid(row=3, column=1)
    #     self.tasklist=Tasklist(self,self.textList,self.stringTask,self.textConsole)

    # def buildFrames(self):
    #     self.frames=[]
    #     for i in range(4):
    #         self.frames.append(Frame(self))
    #         self.frames[-1].grid(row=1, rowspan=10, column=i+1)

    # def build_label_button(self, frame, name, check, button, command, time=5):
    #     dict={"lbl": Label(frame, text=f"{name}:"),
    #           "btn": Button(frame, text="Start", command=lambda: self.trigger(name,check,button,command,time))}
    #     return dict
    #
    # def buildButtons(self,frame):
    #     self.buttons={}
    #     self.buttons['prntscr']={"btn":Button(frame, text="Print Screen", command=self.device.printScreen)}
    #     # self.buttons['areas']={"btn":Button(frame, text="Areas")}
    #         # self.buttons['resources']={"btn":Button(frame, text="Resources")}
    #
    #     i = 1
    #     for dict in self.buttons.values():
    #         i+=1
    #         if "lbl" in dict:
    #             dict["lbl"].grid(row=i, column=1)
    #             dict["btn"].grid(row=i, column=2)
    #         else:
    #             dict["btn"].grid(row=i, column=1, columnspan=2)

    def checkTemplates(self, list, templates=False):
        print(f"checking: {list}")
        if not templates:
            templates=self.templates
        checklist=[]
        for image in list:
            if image not in templates:
                checklist.append(image)
        if len(checklist):
            print("not found:")
            print(checklist)
            return False
        return True



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


    def tap(self,name,wait=.5, error=.8, templates=False):
        if not templates:
            templates=self.templates
        # self.logger.debug(f"locating: {name}")
        try:
            location=self.device.locate_item([templates[name]],error,one=True)
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

    def loaddata(self):
        self.reset_shaft=False
        self.shaft_stations=Stations(loadJSON(path.join("data","shaftlist.json")))
        self.shaft=loadJSON(path.join('data','shaftdata.json'))
        if not len(self.shaft):
            self.plan_scan_shaft()
        self.reset_tower=False
        self.tower_stations=Stations(loadJSON(path.join("data","towerlist.json")))
        self.tower=loadJSON(path.join('data','towerdata.json'))
        if not len(self.tower):
            self.plan_scan_tower()

    def plan_scan_shaft(self):
        self.tasklist.addTask(TempTask('Scan Mineshaft',self.scan_shaft))
        self.reset_shaft=True

    def plan_scan_tower(self):
        self.tasklist.addTask(TempTask('Scan Tower',self.scan_tower))
        self.reset_tower=True

    def scan_shaft(self):
        print("SCAN SHAFT")
        self.shaft=[]
        self.boosted=[]
        self.reset_shaft=False
        scanlist=[]
        stations=self.shaft_stations.keys()
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
                # if len(self.device.locate_item([self.templates["info"]],.8,one=True)):
                for id,station in enumerate(stations):
                    if len(self.device.locate_item([self.templates[f"text_{station}"]],.8,one=True)):
                        result=[id+1,0]
                        for i in range(8,0,-1):
                            if len(self.device.locate_item([self.templates[f"level_{i}"]],.95,one=True,last=True)):
                                result=[id+1,i]
                                break
                scanlist.append(result)
        saveJSON(scanlist,path.join("data","shaftdata.json"))
        self.shaft=scanlist


    def getShaftList(self,types):
        result=[]
        for type,lvl in self.shaft:
            result.append(1) if type in types else result.append(0)
        return result

    def getTowerList(self, types):
        result=[]
        print(self.tower)
        for type,lvl in self.tower:
            result.append(1) if type in types else result.append(0)
        print(result)
        return result

    def scan_tower(self):
        self.tower=[]
        scanlist=[]
        stations=self.tower_stations.keys()
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
        saveJSON(scanlist,path.join("data","towerdata.json"))
        self.tower=scanlist

    def getTowerType(self, name):
        type=0
        list=self.tower_stations.values()
        print(list)
        for idx,item in enumerate(list):
            if item.name==name:
                type=idx+1
        print(type)
        return type

    def explore(self):
        # self.logger.debug("Expedition")
        images=["main_down", "mine_up", "expedition_next", "expedition_claim", "expedition_start"]
        movelist=clearEnd(self.getShaftList([4]))
        if len(movelist):
            if self.checkTemplates(images) and self.move_home():
                self.tap("main_down",3)
                up_button=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
                if len(up_button):
                    for lvl in movelist:
                        self.device.tap(*up_button)
                        sleep(.3)
                        check=False
                        if lvl:
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
                            break
                self.move_home()

    def collect_ore(self):
        self.collect(1)

    def collect_oil(self):
        self.collect(3)

    def collect_water(self):
        print("COLLECT WATER")
        images=["tower_down", "mine_claim", "main_up"]
        type=self.getTowerType("Water Collector")
        if type:
            prodlist=clearEnd(self.getTowerList([type]))
            print(prodlist)
            if self.checkTemplates(images) and self.move_home():
                self.tap("main_up")
                button_dwn=self.device.locate_item([self.templates["tower_down"]],.8,one=True)
                for collect in prodlist:
                    self.device.tap(*button_dwn)
                    sleep(.3)
                    if collect:
                        sleep(.4)
                        if not self.tap("mine_claim",.1,error=.7):
                            print("resetting tower")
                            self.plan_scan_tower()
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
                        if not self.tap(claim,.1,error=.7):
                            print("resetting mines")
                            self.plan_scan_shaft()
                            break
                self.tap("surface")
                # self.tap("main_up")
            # self.tap("tower_down")
            # self.tap("mine_claim",.1)
            self.move_home()

    def boost(self):
        print("BOOST")
        images=["main_down", "mine_boost", "boost_play", "mine_up", "exit_boost"]
        boostlist=self.boosts.get("shaft")
        max=1 if self.behind else 4
        if len(boostlist) and self.checkTemplates(images) and self.move_home():
            self.tap("main_down",2)
            count=0
            shaftlist=clearEnd(self.getShaftList(boostlist))
            if not hasattr(self, "boosted"):
                self.boosted=[]
            if len(self.boosted)!=len(shaftlist):
                for i in range(len(shaftlist)):
                    self.boosted.append(False)
            location=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
            if len(location):
                for idx,collect in enumerate(shaftlist):
                    self.device.tap(*location)
                    sleep(.2)
                    if collect and not self.boosted[idx]:
                        sleep(.3)
                        if not self.tap("mine_boost",.1):
                            self.plan_scan_shaft()
                            break
                        self.boosted[idx]=True
                        playbutton=self.device.locate_item([self.templates["boost_play"]],.8,one=True)
                        if playbutton:
                            self.watchAd(playbutton,"exit_boost")
                            count+=1
                        self.tap("exit_boost",.2)
                    if count>=max:
                        break
                if idx==len(shaftlist)-1:
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
                sleep(.2)
                print(type, lvl)
                if type in boostlist:
                    sleep(.3)
                    if not self.tap("production_boost",.5,.5):
                        print("could not find boostbutton")
                        sleep(1)
                        self.plan_scan_tower()
                        break
                    playbutton=self.device.locate_item([self.templates["boost_play"]],.7,one=True)
                    if playbutton:
                        self.watchAd(playbutton,"exit_boost")
                    while(self.tap("exit_boost",.3)):
                        print("closing menu's")
        self.move_home()


    def openChests(self):
        images=["return","inventory","menu_chest","closed_chest_small","closed_chest_big","magnifier"]
        max=5 if self.behind else 15
        if self.checkTemplates(images):
            if self.move_home() and self.tap("inventory"):
                self.tap("menu_chest")
                location=self.device.locate_item([self.templates["closed_chest_small"]],.8,one=True)
                count=0
                while location and count<max:
                    self.device.tap(*location)
                    sleep(.5)
                    self.tap("closed_chest_big",.3)
                    self.tap("magnifier",.3)
                    self.tap("menu_chest",.3)
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
        max=1 if self.behind else 4
        images=["return","store","store2","watch_free","claim"]
        if self.checkTemplates(images):
            self.move_home()
            if self.tap("store") or self.tap("store2"):
                count=0
                for image in ["watch_free","claim"]:
                    location=self.device.locate_item([self.templates[image]],.75,one=True)
                    self.logger.info(f"Ads: {image}")
                    while (location and count<max):
                        showInfo = True if image=="watch_free" else False
                        # showInfo=True
                        self.watchAd(location, "return", showInfo)
                        sleep(2)
                        count+=1
                        location=self.device.locate_item([self.templates[image]],.75,one=True)
                self.tap("return")

    def claim(self):
        images=["menu_guild","chat","request_claim"]
        if self.checkTemplates(images):
            self.move_home()
            self.restart_app()
            if self.tap("menu_guild"):
                self.tap("chat")
                sleep(2)
                for x in range(5):
                    if self.tap("request_claim"):
                        print("Whooot!")
                    self.device.swipe(200,600,200,1200,speed=500)
                    sleep(.5)
                self.device.go_back()


    def request(self):
        images=["menu_guild","chat","request_big", "request_small"]
        request=self.requests.choosen.get()
        print(f"Requesting: {request}")
        if request and self.checkTemplates(images) and self.checkTemplates([request], self.temp_req):
            self.move_home()
            self.restart_app()
            if self.tap("menu_guild"):
                self.tap("chat")
                if self.tap("request_big"):
                    count=0
                    dcount=1
                    x=557
                    while not self.tap(request, templates=self.temp_req):
                        y=[970,400] if count<6 else [400,970]
                        self.device.swipe(x,y[0],x,y[1],speed=200)
                        sleep(.7)
                        count+=dcount
                        if count >= 10:
                            dcount=-1
                        if count<0:
                            print("could not find request")
                            self.move_home()
                            return
                    self.tap("request_small")
                    self.device.go_back()
                    self.move_home()

    def donate(self):
        pass
