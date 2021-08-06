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
from tools import getName

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
class StationType():
    name: str
    boostable: int
    def __post_init__(self):
        if self.boostable:
            self.boost=IntVar(name=self.name)

class Station(Frame):
    def __init__(self, parent, type, lvl, area, boost=False):
        self.type=StringVar(value=type)
        self.lvl=StringVar(value=f"[{lvl}]    ")
        self.area=IntVar(value=area)
        self.boost=IntVar(0)
        self.boost.set(1) if boost else self.boost.set(0)
        Frame.__init__(self, parent)
        self.labels=[]
        self.labels.append(Checkbutton(parent, textvariable=self.area, variable=self.boost, onvalue=1))
        self.labels.append(Label(parent, textvariable=self.type))
        self.labels.append(Label(parent, textvariable=self.lvl))
        self.boost.trace_add("write",self.update)

    def show(self,row,column):
        for idx,label in enumerate(self.labels):
            col=column+idx
            label.grid(row=row, column=col, sticky='nesw')

    def update(self,*args):
        print(f"saving boosts: {args}")
        data=[]
        json_file=path.join("data","boosted.json")
        data=loadJSON(json_file)
        area=self.area.get()
        if self.boost.get() and area not in data:
            data.append(area)
        if not self.boost.get() and area in data:
            data.remove(area)
        saveJSON(data,json_file)

    def delete(self):
        for label in self.labels:
            label.grid_forget()
        self.destroy()

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
        self[image]=StationType(name, boostable)


class Boosts(LabelFrame):
    def __init__(self, parent, **kwargs):
        LabelFrame.__init__(self,parent, text="Boosts:")
        self.grid(**kwargs)
        self.parent=parent
        self.json_file=path.join("data","boosts.json")
        boostlist=loadJSON(self.json_file)
        self.items=[]
        self.stations=[]
        for name,list in {"Tower:":parent.tower_stations, "Shaft:":parent.shaft_stations}.items():
            self.items.append(Label(self, text=name))
            for station in list.values():
                if station.boostable:
                    self.items.append(Checkbutton(self, text=station.name, variable=station.boost, onvalue=1))
                    if station.name in boostlist and boostlist[station.name]:
                        station.boost.set(1)
                    station.boost.trace_add('write',self.save_types)
        for idx,item in enumerate(self.items):
            item.grid(row=idx+1,column=1, sticky='ew')

    def load(self, shaftlist):
        json_file=path.join("data","boosted.json")
        maxlevel=len(shaftlist)
        for station in self.stations:
            station.delete()
        self.stations=[]
        boostlist=loadJSON(json_file)
        typenames=[]
        typelist=list(self.parent.shaft_stations.values())
        for type in typelist:
            typenames.append(type.name)
        print(typenames)
        for idx,(type,lvl) in enumerate(reversed(shaftlist)):
            if idx and type:
                typename=typenames[type-1]
                boost=True if idx in boostlist else False
                self.stations.append(Station(self, typename, lvl, idx, boost))
        self.showStations()

    def showStations(self):
        row,col=(1,4)
        for station in self.stations:
            station.show(row=row, column=col)
            row+=1
            if row>=14:
                row=1
                col+=4

    def getShaftList(self):
        result=[]
        boostlist=[]
        num_areas=len(self.parent.shaft)+1
        for station in self.stations:
            if station.boost.get():
                boostlist.append(station.area.get())
        return[num_areas-1, boostlist]
        # for x in range(1,num_areas+1):
        #     area=num_areas-x
        #     result.append(1) if area in boostlist else result.append(0)

        # return result

    def save_types(self,name,*args):
        print(args)
        data={}
        for station in self.parent.tower_stations.values():
            if station.boostable:
                data[station.name]=station.boost.get()
        for station in self.parent.shaft_stations.values():
            if station.boostable:
                boost=station.boost.get()
                data[station.name]=boost
                if station.name==name:
                    for item in self.stations:
                        if item.type.get()==name:
                            item.boost.set(boost)
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
        self.tasklist=Tasklist(self,row=6,column=1,columnspan=3, sticky='w')
        self.loaddata()
        self.boosts=Boosts(self,row=2,column=3,sticky='nw')
        self.boosts.load(self.shaft)
        self.tasks=Tasks(self, self.tasklist, row=1, column=1, rowspan=5,columnspan=2, sticky='w')
        self.templates=loadTemplates(build_dir("DT_images"))
        self.temp_req=loadTemplates(build_dir(path.join("DT_images","requests")))
        self.temp_don=loadTemplates(build_dir(path.join("DT_images","donations")))
        self.requests=Request(self,row=1,column=3, sticky='nw')

    def checkTemplates(self, list, templates=False):
        # print(f"checking: {list}")
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

    def getLoc(self,location,name):
        if not len(location):
            sleep(.6)
            location=self.device.locate_item([self.templates[name]],.8,one=True)
        return location

    def restart_app(self):
        print("restarting App")
        sleep(3)
        self.device.restartApp("com.rockbite.deeptown","AndroidLauncher")
        sleep(10)
        setattr(self, "lastRestart", int(time()))

    def extra(self):
        print("doing extra")
        self.device.resize_screen()

    def start_hack(self):
        for i in range(7):
            self.device.resize_screen()
            wait=8+i
            print(f"Waiting: {wait} seconds")
            sleep(wait)

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
        if len(location):
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
        print("**** Planning New Scan of Shaft ****")
        self.tasklist.addTask(TempTask('Scan Mineshaft',self.scan_shaft))
        self.reset_shaft=True

    def plan_scan_tower(self):
        print("**** Planning New Scan of Tower ****")
        self.tasklist.addTask(TempTask('Scan Tower',self.scan_tower))
        self.reset_tower=True

    def plan_get_free(self):
        self.tasklist.addTask(TempTask('Get Free Money',self.get_free))

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
                        print(station)
                        for i in range(9,0,-1):
                            if len(self.device.locate_item([self.templates[f"level_{i}"]],.96,one=True,last=True)):
                                result=[id+1,i]
                                break
                scanlist.append(result)
        saveJSON(scanlist,path.join("data","shaftdata.json"))
        self.shaft=scanlist
        self.boosts.load(self.shaft)

    def getDrillList(self,types):
        print("GET DRILLIST")
        arealist=[]
        num_areas=len(self.shaft)
        x=0
        for type,lvl in self.shaft:
            x+=1
            area=num_areas-x
            if type in types:
                arealist.append(area)
        return [num_areas, arealist]

    def getTowerBoosts(self):
        result=[]
        for idx, station in enumerate(self.tower_stations.values()):
            if station.boostable and station.boost.get():
                result.append(idx+1)
        return result

    def getTowerList(self, types=[]):
        if not len(types):
            types=self.getTowerBoosts()
        result=[]
        for type,lvl in self.tower:
            result.append(1) if type in types else result.append(0)
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
        for idx,item in enumerate(list):
            if item.name==name:
                type=idx+1
        return type

    def explore(self):
        pass
        # self.logger.debug("Expedition")
        # images=["main_down", "mine_up", "expedition_next", "expedition_claim", "expedition_start"]
        # movelist=clearEnd(self.getDrillList([4]))
        # if len(movelist):
        #     if self.checkTemplates(images) and self.move_home():
        #         self.tap("main_down",3)
        #         up_button=self.device.locate_item([self.templates["mine_up"]],.8,one=True)
        #         if len(up_button):
        #             for lvl in movelist:
        #                 self.device.tap(*up_button)
        #                 sleep(.3)
        #                 check=False
        #                 if lvl:
        #                     sleep(.3)
        #                     while (self.tap("expedition_next")):
        #                         # self.logger.debug("  --> next chapter")
        #                         check=True
        #                     if self.tap("expedition_claim",1):
        #                         # self.logger.debug("claiming Price")
        #                         check=True
        #                         sleep(2)
        #                     if self.tap("expedition_start",1):
        #                         # self.logger.debug(" --> staring next exploration")
        #                         check=True
        #                     break
        #         self.move_home()

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

    def clearMem(self):
        if not hasattr(self, "lastRestart"):
            setattr(self, "lastRestart", 0)
        last=self.lastRestart
        now=int(time())
        self.restart_app() if now-last>20*60 else self.move_home()

    def collect(self,type):
        print("COLLECT")
        images=["main_down", "mine_claim", "mine_up", "tower_down", "oil_claim"]
        claim="mine_claim" if type==1 else "oil_claim"
        current,collectlist=self.getDrillList([type])
        if len(collectlist) and self.checkTemplates(images):
            self.clearMem()
            self.tap("main_down",1)
            navigation=self.getNavigation()
            for area in collectlist:
                self.navigate(current, area, navigation)
                current = area
                if not self.tap(claim,.1,error=.7):
                    print("resetting mines")
                    self.plan_scan_shaft()
                    break
        self.move_home()

    def boost(self):
        print("BOOST")
        images=["main_down", "mine_boost", "boost_play", "exit_boost"]
        current,boostlist=self.boosts.getShaftList()
        max=2 if self.behind else 5
        if len(boostlist) and self.checkTemplates(images):
            self.clearMem()
            # self.restart_app()
            # self.move_home()
            self.tap("main_down")
            count=0
            if not hasattr(self, "boosted"):
                self.boosted=[]
            if len(self.boosted)!=len(self.shaft):
                for i in range(len(self.shaft)):
                    self.boosted.append(False)
            navigation=self.getNavigation()
            for area in reversed(boostlist):
                if not self.boosted[area]:
                    self.navigate(current, area, navigation)
                    current = area
                    if not self.tap("mine_boost",.1):
                        self.plan_scan_shaft()
                        break
                    self.boosted[area]=True
                    playbutton=self.device.locate_item([self.templates["boost_play"]],.8,one=True)
                    if playbutton:
                        if not self.watchAd(playbutton,"exit_boost"):
                            break
                        count+=1
                    self.tap("exit_boost",.5)
                    if count>=max:
                         break
            if area==boostlist[0]:
                for i in range(len(self.boosted)):
                    self.boosted[i]=False
        self.move_home()

    def getNavigation(self):
        sleep(2)
        nav=type('', (), {})()
        images=["mine_down", "mine_up", "level_down", "level_up"]
        if self.checkTemplates(images) and len(self.device.load_screenCap()):
            for image in images:
                setattr(nav,image,self.device.locate_item([self.templates[image]],.8,one=True,last=True))
        for image in images:
            if not hasattr(nav,image):
                return False
        return nav

    def navigate(self, current, target, navigation):
        print(f"NAVIGATE: from {current} to {target}")
        for x in range(9):
            level=109-12*x
            if target<=level<current and level+12<=current:
                self.device.tap(*navigation.level_up)
                sleep(.1)
                current=level
                # print(current)
        while target < current:
            self.device.tap(*navigation.mine_up)
            sleep(.1)
            current-=1
            # print(current)
        sleep(.5)

    def find_cross(self):
        print("trying to find cross")
        sleep(5)
        for image in self.templates:
            if "cross" in image and self.tap(image):
                sleep(1)
                return True
        print("could not find cross")
        return False

    def boost_product(self):
        if not self.behind:
            images=["main_up", "production_boost", "production_boost_2", "boost_play", "tower_down", "exit_boost"]
            boostlist=self.getTowerBoosts()
            if self.checkTemplates(images) and self.move_home():
                self.tap("main_up")
                button_dwn=self.device.locate_item([self.templates["tower_down"]],.8,one=True)
                for type,lvl in self.tower:
                    self.device.tap(*button_dwn)
                    sleep(.3)
                    print(type, lvl)
                    if type in boostlist:
                        sleep(.3)
                        if not (self.tap("production_boost",.5,.5) or self.tap("production_boost_2",.5,.5)):
                            print("could not find boostbutton")
                            self.plan_scan_tower()
                            break
                        playbutton=self.device.locate_item([self.templates["boost_play"]],.7,one=True)
                        if playbutton:
                            if not self.watchAd(playbutton,"exit_boost"):
                                break
                        while(self.tap("exit_boost",.3)):
                            print("closing menu's")
            self.move_home()


    def openChests(self):
        images=["return","inventory","menu_chest","closed_chest_small","closed_chest_big","magnifier"]
        max=25 if self.behind else 40
        loc_big_chest=[]
        loc_mag=[]
        loc_menu=[]
        if self.checkTemplates(images):
            if self.move_home() and self.tap("inventory"):
                loc_menu=self.getLoc(loc_menu,"menu_chest")
                self.tap("menu_chest")
                location=self.device.locate_item([self.templates["closed_chest_small"]],.8,one=True)
                count=0
                while location and count<max:
                    self.device.tap(*location)
                    loc_big_chest=self.getLoc(loc_big_chest,"closed_chest_big")
                    self.device.tap(*loc_big_chest)
                    sleep(.2)
                    loc_mag=self.getLoc(loc_mag,"magnifier")
                    self.device.tap(*loc_mag)
                    sleep(.1)
                    loc_menu=self.getLoc(loc_menu,"menu_chest")
                    self.device.tap(*loc_menu)
                    sleep(.4)
                    count+=1
                    location=self.device.locate_item([self.templates["closed_chest_small"]],.8,one=True)
                self.tap("return")

    def watchAd(self, location, exit, showActivity=False):
        images=["close_video"]
        if self.checkTemplates(images) and len(location):
            print("watching Ad")
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
                    self.logger.debug("Stuck on Ad?")
                    if not self.find_cross():
                        sleep(1)
                        self.device.go_back()
                        return False
                return True


    def searchAds(self):
        # max=1 if self.behind else 4
        max=6
        images=["return","store","store2","watch_free","claim"]
        if self.checkTemplates(images):
            store_button=self.device.locate_item([self.templates["store"],self.templates["store2"]],.75,one=True)
            if not len(store_button):
                print("ERROR: Store not found")
                return
            self.restart_app()
            self.start_hack()
            sleep(3)
            self.device.tap(*store_button)
            count=0
            sleep(2)
            if not len(self.device.locate_item([self.templates["claim"]],.65,one=True)):
                sleep(3)
                self.device.tap(*store_button)
                sleep(2)
            if len(self.device.locate_item([self.templates["watch_free"]],.65,one=True)):
                self.plan_get_free()
            location=self.device.locate_item([self.templates["claim"]],.65,one=True,last=True)
            while (location and count<max):
                self.watchAd(location, "return", False)
                sleep(2)
                count+=1
                self.tap("exit_boost")
                location=self.device.locate_item([self.templates["claim"]],.65,one=True)
            sleep(12)
            self.tap("return")
            self.restart_app()

    def get_free(self):
        images=["return","store","store2","watch_free"]
        max=5
        if self.checkTemplates(images):
            self.restart_app()
            self.start_hack()
            sleep(5)
            if self.tap("store") or self.tap("store2"):
                count=0
                location=self.device.locate_item([self.templates["watch_free"]],.75,one=True)
                while (location and count<max):
                    self.watchAd(location, "return", False)
                    sleep(10)
                    count+=1
                    self.tap("exit_boost")
                    location=self.device.locate_item([self.templates["watch_free"]],.75,one=True)
                self.tap("return")
            sleep(12)
            self.restart_app()

    def claim(self):
        images=["menu_guild","chat","request_claim"]
        if self.checkTemplates(images):
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
        images=["menu_guild","chat","request_big", "request_small","donate"]
        donations=["Alexandrite","Water"]
        if len(donations) and self.checkTemplates(images) and self.checkTemplates(donations, self.temp_don):
            templates=[]
            for name in donations:
                templates.append(self.temp_don[name])
            print(templates)
            self.clearMem()
            if self.tap("menu_guild"):
                self.tap("chat")
                sleep(2)
                for x in range(7):
                    donate_buttons=self.device.locate_item([self.templates["donate"]],.9)
                    if len(donate_buttons):
                        print(f"found: {donate_buttons}")
                        requests=self.device.locate_item(templates,.9, last=True)
                        if len(requests):
                            print(f"found request: {requests}")
                            for request in requests:
                                for button in donate_buttons:
                                    if abs(button[1]-request[1])<50:
                                        print(f"start donate! {button}")
                                        self.device.tap(*button)
                                        sleep(.5)
                                        bar=self.device.locate_item([self.templates["bar"]],.8, one=True)
                                        pen=self.device.locate_item([self.templates["pen"]],.8,last=True, one=True)
                                        ok=self.device.locate_item([self.templates["ok_donate"]],.8,last=True, one=True)
                                        if (len(bar) and len(pen) and len(ok)):
                                            self.device.swipe(*bar,*pen,speed=1400)
                                            sleep(.5)
                                            self.device.tap(*ok)
                                            sleep(1)
                                        else:
                                            self.device.go_back()
                    self.device.swipe(200,600,200,1200,speed=500)
                    sleep(.5)
                self.device.go_back()
