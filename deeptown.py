from tkinter import Tk, IntVar, StringVar, Label
from tkinter.ttk import Frame, LabelFrame, Button, Checkbutton, Entry
from dataclasses import dataclass, field
from os import path, getcwd, mkdir
from adb import Template
from glob import glob
from time import sleep
from threading import Thread
import json
import traceback
import random
from time import time

def build_dir(map):
    if not path.isdir(map):
        mkdir(map)
    return path.join(getcwd(),map)

def build_label_button(parent, name, check, button, command, time=5):
    dict={"lbl": Label(parent, text=f"{name}:"),
          "btn": Button(parent, text="Start", command=lambda: parent.trigger(name,check,button,command,time))}
    return dict

def loadJSON(file):
    try:
        if path.isfile(file):
            with open(file) as json_file:
                data = json.load(json_file)
    except Exception as e:
        print("ERROR")
        print(e)
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
        print(self)

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

class DeepTown(LabelFrame):
    def __init__(self, parent, device):
        self.parent=parent
        self.device=device
        self.busy=False
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

    def build_buttons(self):
        list={}
        list['prntscr']={"btn":Button(self, text="Print Screen", command=self.device.printScreen)}
        list['areas']={"btn":Button(self, text="Areas")}
        list['resources']={"btn":Button(self, text="Resources")}
        list['collect']=build_label_button(self, "Collect", "collecting", "collect", self.collect,time=5)
        list['explore']=build_label_button(self, "Explore", "exploring", "explore", self.explore,time=60)
        list['cc']=build_label_button(self, "Check Chests", "checking_chests", "cc", self.openChests,time=10)
        list['ca']=build_label_button(self, "Check Ads", "checking_ads","ca",self.searchAds,time=6)
        i = 1
        for dict in list.values():
            i+=1
            if "lbl" in dict:
                dict["lbl"].grid(row=i, column=1)
                dict["btn"].grid(row=i, column=2)
            else:
                dict["btn"].grid(row=i, column=1, columnspan=2)
        return list

    def trigger_resources(self):
        pass

    def checkTemplates(self, list):
        checklist=[]
        for image in list:
            if image not in self.templates:
                checklist.append(image)
        if len(checklist):
            print("need images:")
            print(checklist)
            print(self.templates)
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
            self.start_task(name, check, task, time)


    def tap(self,name,wait=.5):
        print(f"locating: {name}")
        try:
            location=self.device.locate_item([self.templates[name]],.8,one=True)
            if not location:
                raise Exception(f"Image ({name}) not found on screen")
            self.device.tap(*location)
            sleep(wait)
            return True
        except Exception as e:
            # print("ERROR")
            print(e)
            # traceback.print_exc()
            return False

    def move_home(self):
        images=["return", "surface", "tower_bottom", "main_down"]
        if self.checkTemplates(images):
            self.tap("return")
            self.tap("surface")
            self.tap("tower_bottom")
            if self.device.locate_item([self.templates["main_down"]],.75,one=True):
                return True
        return False

    def start_task(self, name, check, task, time):
        if getattr(self, check):
            if not self.busy:
                timer=time*60*1000
                self.thread=Thread(target=task, daemon=True).start()
            else:
                timer=30*1000
            print(f"setting timer for {name} ({timer})")
            self.parent.after(timer,lambda: self.start_task(name, check, task, time))
        elif (name=="Collect"):
            self.scanned=0

    def upgrade_mines(self):
        self.busy=True
        self.drones=True
        images=["main_down", "mine_up", "mine_upgrade", "upgrade", "red_cross"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",1.5)
            count=0
            while (not self.tap("main_up")) and count<50 and (self.drones):
                self.tap("mine_up")
                if self.tap("mine_upgrade"):
                    if self.tap("upgrade"):
                        print("whoot")
                        sleep(5)
                    else:
                        self.device.go_back()
        self.busy=False

    def explore(self):
        self.busy=True
        print("Expedition")
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
                        print("  --> next chapter")
                        check=True
                    if self.tap("expedition_claim",1):
                        print("claiming Price")
                        check=True
                        sleep(2)
                    if self.tap("expedition_start",1):
                        print(" --> staring next exploration")
                        check=True
                    if check:
                        break
            self.move_home()
        self.busy=False

    def collect(self):
        self.busy=True
        images=["main_down", "mine_claim", "mine_up", "tower_down"]
        if self.checkTemplates(images) and self.move_home():
            self.tap("main_down",3)
            if not hasattr(self, "scanned") or self.scanned<time():
                self.scanned=time()+45*60
                self.drilllist=[]
                while (not self.tap("main_up")):
                    self.tap("mine_up")
                    val = True if self.tap("mine_claim",.1) else False
                    self.drilllist.append(val)
                    print(val)
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
        self.busy=False

    def openChests(self):
        self.busy=True
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
            else:
                print("no")
        self.busy=False

    def watchAd(self, location):
        images=["cross_1", "cross_2", "cross_3"]
        if self.checkTemplates(images):
            print("watching Ad")
            self.device.tap(*location)
            wait=random.randrange(45, 50)
            sleep(wait)
            self.device.go_back()
            sleep(.5)
            if not self.device.locate_item([self.templates["return"]],.8, one=True):
                print("Stuck on Ad?")
                sleep(5)
                cross_list=[]
                for cross in images:
                    cross_list.append(self.templates[cross])
                newlocation=[300,300]
                newlocation=self.device.locate_item(cross_list,.65, one=True)
                if newlocation:
                    print("found Cross")
                    self.device.tap(*newlocation)
                    sleep(1)
                    self.device.go_back()
                    # self.device.go_back()

    def searchAds(self):
        self.busy=True
        images=["return","store","store2","free_chest","watch_free","claim"]
        if self.checkTemplates(images):
            if self.move_home() and self.tap("free_chest"):
                location=self.device.locate_item([self.templates["watch_free"],self.templates["watch"]],.75,one=True)
                count=0
                while location and count<10:
                    self.watchAd(location)
                    count+=1
                    location=self.device.locate_item([self.templates["watch_free"],self.templates["watch"]],.75,one=True)
                self.tap("return")
            print("checking store")
            if self.tap("store") or self.tap("store2"):
                location=self.device.locate_item([self.templates["claim"],self.templates["watch"]],.75,one=True)
                count=0
                while location and count<10:
                    self.watchAd(location)
                    count+=1
                    location=self.device.locate_item([self.templates["claim"],self.templates["watch"]],.75,one=True)
                self.tap("return")
        self.busy=False
