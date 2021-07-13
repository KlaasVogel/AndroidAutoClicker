from tkinter import Tk, IntVar, StringVar, Label
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
from time import time

def build_dir(map):
    if not path.isdir(map):
        mkdir(map)
    return path.join(getcwd(),map)

def loadJSON(file):
    try:
        if path.isfile(file):
            with open(file) as json_file:
                data = json.load(json_file)
    except Exception as e:
        # self.logger.debug("ERROR")
        # self.logger.debug(e)
        traceback.print_exc()
        data=[]
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
    def __init__(self,parent):
        self.log=parent.logger
        self.parent=parent
        self.paused=True
        self.busy=False

    def start(self):
        self.paused=False
        self.thread=Thread(target=self.run, daemon=True).start()
    def pause(self):
        self.paused=True

    def addTask(self, name, check, job, waittime):
        # self.log.debug(f'\n adding job for {name}')
        task=Task(name, check, job, waittime)
        self.setTask(task, True)

    def setTask(self,task, firsttime=False):
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
                    print(task)
                    if getattr(self.parent, task.check):
                        self.busy=True
                        task.job()
                        self.busy=False
                        self.setTask(task)
            sleep(5)

class DeepTown(LabelFrame):
    def __init__(self, parent, device):
        self.logger=MyLogger('DeepTown', LOG_LEVEL=logging.DEBUG)
        self.parent=parent
        self.device=device
        self.scanned={}
        self.tasklist=Tasklist(self)
        LabelFrame.__init__(self, parent, text="Deep Town")
        self.frames=[]
        for i in range(4):
            self.frames.append(Frame(self.parent))
            self.frames[-1].grid(row=1, rowspan=10, column=i+1)
        self.dir_images=build_dir("DT_images")
        self.loadTemplates(self.dir_images)
        self.buttons=self.build_buttons()


    def loadTemplates(self, map):
        self.templates=DT_Images()
        filelist=glob(path.join(map,"*.png"))
        for file in filelist:
            self.templates.addTemplate(file)

        # datafile=path.join(map,'image_list.json')
        # data=loadJSON(datafile)
        # for name in data:
        #     file = findFile(name, filelist)
        #     if file:
        #         self.templates.addTemplate(name,file)

    def build_label_button(self, name, check, button, command, time=5):
        dict={"lbl": Label(self, text=f"{name}:"),
              "btn": Button(self, text="Start", command=lambda: self.trigger(name,check,button,command,time))}
        return dict

    def build_buttons(self):
        list={}
        list['prntscr']={"btn":Button(self, text="Print Screen", command=self.device.printScreen)}
        list['areas']={"btn":Button(self, text="Areas")}
        list['resources']={"btn":Button(self, text="Resources")}
        list['running']={'btn':Button(self, text="Start Tasks", command=self.start_tasks)}
        list['collect']=self.build_label_button("Collect", "collecting", "collect", self.collect,time=4)
        list['pump']=self.build_label_button("Pump", "collecting oil", "pump", self.pump,time=7)
        list['explore']=self.build_label_button("Explore", "exploring", "explore", self.explore,time=60.1)
        list['boost']=self.build_label_button("Boost", "boosting", "boost", self.boost,time=2)
        list['boost_prod']=self.build_label_button("Boost Production", "boosting_production", "boost_prod", self.boost_product,time=5.05)
        list['cc']=self.build_label_button("Check Chests", "checking_chests", "cc", self.openChests,time=10)
        list['ca']=self.build_label_button("Check Ads", "checking_ads","ca",self.searchAds,time=6.01)
        i = 1
        for dict in list.values():
            i+=1
            if "lbl" in dict:
                dict["lbl"].grid(row=i, column=1)
                dict["btn"].grid(row=i, column=2)
            else:
                dict["btn"].grid(row=i, column=1, columnspan=2)
        return list

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
            for type in ["Collect", "Pump", "Boost"]:
                if (name==type):
                    self.scanned[type]=0

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
        self.device.restartApp("deeptown","AndroidLauncher")
        sleep(20)
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

    def upgrade_mines(self):
        self.drones=True
        images=["main_down", "mine_up", "mine_upgrade", "upgrade", "red_cross"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",1.5)
            count=0
            while (not self.tap("main_up")) and count<50 and (self.drones):
                self.tap("mine_up")
                if self.tap("mine_upgrade"):
                    if self.tap("upgrade"):
                        # self.logger.debug("whoot")
                        sleep(5)
                    else:
                        self.device.go_back()

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

    def collect(self):
        images=["main_down", "mine_claim", "mine_up", "tower_down"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",3)
            if self.scanned.get("Collect",0)<time():
                self.scanned['Collect']=time()+45*60
                self.drilllist=[]
                while (not self.tap("main_up")):
                    self.tap("mine_up",1)
                    val = True if self.tap("mine_claim",.1) else False
                    self.drilllist.append(val)
                    # self.logger.debug(val)
            else:
                location=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
                if len(location):
                    for collect in self.drilllist:
                        self.device.tap(*location)
                        sleep(.3)
                        if collect:
                            self.tap("mine_claim",.1)
                    count=0
                    while (not self.tap("main_up") and count<10):
                        self.tap("mine_up")
                        count+=1
            self.tap("tower_down")
            self.tap("mine_claim",.1)
            self.move_home()

    def pump(self):
        images=["main_down", "oil_claim", "mine_up"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",3)
            if self.scanned.get("Pump",0)<time():
                self.scanned['Pump']=time()+45*60
                self.oillist=[]
                while (not self.tap("main_up")):
                    if not self.tap("mine_up"):
                        break
                    val = True if self.tap("oil_claim",.1) else False
                    self.oillist.append(val)
                    # self.logger.debug(val)
            else:
                location=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
                if len(location):
                    for collect in self.oillist:
                        self.device.tap(*location)
                        sleep(.3)
                        if collect:
                            self.tap("oil_claim",.1)
                    count=0
                    while (not self.tap("main_up") and count<10):
                        self.tap("mine_up")
                        count+=1
            self.move_home()

    def boost(self):
        images=["main_down", "mine_boost", "boost_play", "mine_up", "exit_boost"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",3)
            if self.scanned.get("Boost",0)<time():
                self.scanned['Boost']=time()+60*60
                self.boostlist=[]
                self.boosted=[]
                while (not self.tap("main_up")):
                    if not self.tap("mine_up"):
                        break
                    val = True if self.device.locate_item([self.templates["mine_boost"]],.8,one=True) else False
                    self.boostlist.append(val)
                    self.boosted.append(False)
                self.move_home()
                self.tap("main_down",3)
            count=0
            location=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
            if len(location):
                for idx,collect in enumerate(self.boostlist):
                    self.device.tap(*location)
                    sleep(.3)
                    if collect and not self.boosted[idx]:
                        self.tap("mine_boost",.1)
                        self.boosted[idx]=True
                        playbutton=self.device.locate_item([self.templates["boost_play"]],.8,one=True)
                        if playbutton:
                            self.watchAd(playbutton,"exit_boost")
                            count+=1
                            # sleep(2)
                        self.tap("exit_boost",.2)
                    if count>=5:
                        break
                else:
                    for i in range(len(self.boosted)):
                        # self.logger.debug("resetting counter for Boosts")
                        self.boosted[i]=False
            self.move_home()

    def boost_product(self):
        images=["main_up", "production_boost", "boost_play", "tower_down", "exit_boost"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_up")
            button_dwn=self.device.locate_item([self.templates["tower_down"]],.8,one=True)
            while len(button_dwn):
                self.device.tap(*button_dwn)
                sleep(.3)
                self.tap("production_boost",.5,.6)
                playbutton=self.device.locate_item([self.templates["boost_play"]],.7,one=True)
                if playbutton:
                    # print("found play-button")
                    self.watchAd(playbutton,"exit_boost")
                self.tap("exit_boost",.2)
                button_dwn=self.device.locate_item([self.templates["tower_down"]],.8,one=True)
        self.move_home()


    def openChests(self):
        images=["return","free_chest","chest_available","menu_chest","closed_chest_small","closed_chest_big","open_chest_big"]
        if self.checkTemplates(images):
            if self.move_home() and self.tap("chest_available"):
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

    def watchAd(self, location, exit):
        images=["close_video"]
        if self.checkTemplates(images):
            # print("watching Ad")
            # print(location)
            # self.logger.debug("watching Ad")
            self.device.tap(*location)
            wait=random.randrange(35, 40)
            sleep(wait)
            self.device.go_back()
            sleep(2)
            if not self.device.locate_item([self.templates[exit]],.8, one=True):
                # self.logger.debug("Stuck on Ad?")
                self.device.go_back()
                cross_list=[]
                for cross in images:
                    cross_list.append(self.templates[cross])
                newlocation=[300,300]
                newlocation=self.device.locate_item(cross_list,.65, one=True)
                if newlocation:
                    # self.logger.debug("found Cross")
                    self.device.tap(*newlocation)
                    sleep(1)
                    self.device.go_back()
                    # self.device.go_back()

    def searchAds(self):
        images=["return","store","store2","watch_free","claim"]
        if self.checkTemplates(images):
            self.move_home()
            # if self.move_home() and self.tap("free_chest"):
            #     count=0
            #     for image in ["watch_free", ""]
            #     location=self.device.locate_item([self.templates["watch_free"]],.75,one=True)
            #     while location and count<5:
            #         self.watchAd(location, "return")
            #         count+=1
            #         location=self.device.locate_item([self.templates["watch_free"]],.75,one=True)
            #     location=self.device.locate_item([self.templates["watch"]],.75,one=True)
            #     while location and count<5:
            #         self.watchAd(location, "return")
            #         count+=1
            #         location=self.device.locate_item([self.templates["watch"]],.75,one=True)
            #     self.tap("return")
            # # self.logger.debug("checking store")
            if self.tap("store") or self.tap("store2"):
                count=0
                for image in ["watch_free","claim"]:
                    location=self.device.locate_item([self.templates[image]],.75,one=True)
                    while (location and count<5):
                        self.watchAd(location, "return")
                        sleep(2)
                        count+=1
                        location=self.device.locate_item([self.templates[image]],.75,one=True)
                self.tap("return")
