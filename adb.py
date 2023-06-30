from os import path
from math import isclose,sqrt
from time import sleep
import cv2
import numpy as np
from ppadb.client import Client

RESOLUTION = [1600,900] #"900x1600"

class ShowOutput():
    def __init__(self):
        self.img=None
    @staticmethod
    def show():
        return False
    def update(self,img):
        self.img=img
        if self.show():
            cv2.imshow('Example - Show image in window',self.img)
            cv2.waitKey(0)
        cv2.destroyAllWindows() # destroys the window showing image


class Adb_Device():
    device=None
    touch="/dev/input/event6"
    res_x, res_y = RESOLUTION
    max=32767
    output=ShowOutput()
    lastscreen=None

    def __init__(self):
        # self.log=MyLogger('ADB', LOG_LEVEL=logging.INFO)
        client=Client(host='127.0.0.1', port=5037)
        # self.log.debug(client.version())
        devices = client.devices()
        if len(devices) == 0:
            # self.log.debug("no devices")
            quit()
        print(devices)
        for device in devices:
            print(device.shell('wm size'))
            if self.get_resolution() in device.shell('wm size'):
                print('yes')
                self.device=device
        if not self.device:
            exit("geen device gevonden")
            # print (device.shell('getevent -p'))
        # self.device=devices[0]
        # self.log.debug(f'updating info for {self.device}')
        number=5
        touch_id=0
        lines=self.device.shell('getevent -p').split("\n")
        for line in lines:
            if "/dev/input" in line:
                number=line[-1]
            if "Touch" in line:
                touch_id=number
                touch=f"sendevent /dev/input/event{number}"
            if "max" in line and "ABS" in line and number==touch_id:
                values=line.split(', ')
                for value in values:
                    if "max" in value:
                        max=int(value[4:])
                        print(f"found max: {max} - touch_id = {touch_id}")
        self.printScreen()

    def get_resolution(self) -> str:
        return f"{self.res_y}x{self.res_x}"

    @staticmethod
    def correct(list1,list2):
        newlist=[]
        dx=list2[0][0]-list1[0][0]
        dy=list2[0][1]-list1[0][1]
        for x,y in list1:
            newlist.append([x+dx,y+dy])
        return newlist

    @staticmethod
    def getClosest(list,vector):
        x_target, y_target = vector
        winner=list[0]
        score=99999
        for loc in list:
            x,y=loc
            newscore=(x_target-x)**2+(y_target-y)**2
            if newscore<score:
                winner=[x,y]
                score=newscore
        return winner

    @staticmethod
    def checkClose(x1,y1, list, tol_x=30, tol_y=16):
        for location in list:
            x2,y2=location
            if (isclose(x1, x2, abs_tol=tol_x) and isclose(y1, y2, abs_tol=tol_y)):
                return True
        else:
            return False

    @staticmethod
    def getClose(list,x1,y1,tol_x,tol_y):
        newlist=[]
        for vector in list:
            x2,y2=vector
            if (isclose(x1, x2, abs_tol=tol_x) and isclose(y1, y2, abs_tol=tol_y)):
                newlist.append(vector)
        return newlist

    def getApplist(self,log=False):
        if log:
            # self.log.info(self.device.shell('dumpsys window a'))
            pass
        result=self.device.shell('dumpsys window a | grep "/" | cut -d "{" -f2 | cut -d "/" -f1 | cut -d " " -f2')
        # self.log.info(result)
        return result

    def closeApp(self, appname):
        applist=self.getApplist()
        apps=applist.split()
        namelist=[appname,"AdActivity","vending","ChromeTabbedActivity","Chrome"]
        for app in apps:
            for name in namelist:
                if name in app:
                    # self.log.info(f"closing: {app}")
                    self.device.shell(f"am force-stop {app}")

    def startApp(self, appname, activity="none"):
        if appname and activity:
            shellcmd=f"am start -n {appname}/{appname}.{activity}"
            self.device.shell(shellcmd)

    def restartApp(self, appname, activity="none"):
        self.closeApp(appname)
        sleep(.5)
        self.startApp(appname, activity)
        self.getApplist(True)

    def release_all(self):
        shellcmd= f"{self.touch} 3 57 -1  && {self.touch} 0 2 0 && {self.touch} 0 0 0"
        self.device.shell(shellcmd)

    def resize_screen(self):
        density=int(self.device.shell("wm density")[-4:])
        newdensity=int(density/2)
        self.device.shell(f"wm density {newdensity}")
        sleep(.5)
        self.device.shell(f"wm density {density}")

    def zoom_out(self):
        y=0.35
        x_c=.5
        dx=0.25
        steps=[]
        for i in range(10):
            x1=x_c-dx*(10-i)/11
            x2=x_c+dx*(10-i)/11
            steps.append(f"{self.touch} 3 57 0")
            steps.append(f"{self.touch} 3 53 {int(x1*self.max)}")
            steps.append(f"{self.touch} 3 54 {int(y*self.max)}")
            steps.append(f"{self.touch} 0 2 0")
            steps.append(f"{self.touch} 3 57 1")
            steps.append(f"{self.touch} 3 53 {int(x2*self.max)}")
            steps.append(f"{self.touch} 3 54 {int(y*self.max)}")
            steps.append(f"{self.touch} 0 2 0")
            steps.append(f"{self.touch} 0 0 0")
        shellcmd=" && ".join(steps)
        self.device.shell(shellcmd)
        self.release_all()
        self.release_all()
        sleep(.1)
        # cmd=f"{self.touch} 3 57 2 && {self.touch} 3 53 {int((x_c-dx)*self.max)} && {self.touch} 3 54 {int(y*self.max)}"
        # self.device.shell(cmd)
        # self.device.shell(f"input swipe {(x_c+dx)*self.res_x} {(y)*self.res_y} {(x_c-dx)*self.res_x} {(y)*self.res_y} 2000")
        # self.release_all()
        # self.release_all()
    def printLast(self):
        screencap = self.lastscreen
        screenshot_file=path.join('images','screen.png')
        with open(screenshot_file, 'wb') as f:
            f.write(screencap)

    def printScreen(self):
        screencap = self.device.screencap()
        screenshot_file=path.join('images','screen.png')
        with open(screenshot_file, 'wb') as f:
            f.write(screencap)

    def tap(self, x=-1, y=-1):
        self.device.shell(f'input tap {x} {y}')
        # sleep(.03)

    def go_back(self):
        self.device.shell('input keyevent 4')

    def trace(self, waypoints, size=0, pressure=0):
        eventlist=[]
        for waypoint in waypoints:
            x,y=waypoint
            eventlist.append(f"{self.touch} 3 57 0")
            eventlist.append(f"{self.touch} 3 53 {int(x*self.max/self.res_x)}")
            eventlist.append(f"{self.touch} 3 54 {int(y*self.max/self.res_y)}")
            if size:
                eventlist.append(f"{self.touch} 3 48 {size}")
            if pressure:
                eventlist.append(f"{self.touch} 3 58 {pressure}")
            eventlist.append(f"{self.touch} 0 2 0")
            eventlist.append(f"{self.touch} 0 0 0")
        # for event in eventlist:
        #     self.device.shell(event)
        shellcmd=" && ".join(eventlist)
        self.device.shell(shellcmd)
        self.release_all()
        # self.device.shell(shellcmd)

    def move(self, x, y):
        # self.log.debug('moving')
        border_x=self.scale_X(500)
        border_y=self.scale_Y(300)
        center_x=self.scale_X(800)
        center_y=self.scale_Y(450)
        while (x or y):
            if x<0:
                dx=x if x>-border_x else -border_x
            else:
                dx=x if x<border_x else border_x
            if y<0:
                dy=y if y>-border_y else -border_y
            else:
                dy=y if y<border_y else border_y
            self.swipe(self.res_x/2+dx,self.res_y/2+dy, center_x, center_y, 500)
            x=x-dx
            y=y-dy

    def swipe(self, x1, y1, x2, y2, speed=300):
        self.device.shell(f'input swipe {x1} {y1} {x2} {y2} {speed}')
        sleep(.3)

    def center(self,x,y):
        self.swipe(x,y,self.res_x/2, self.res_y/2, 500)

    def load_screen_img(self):
        screenshot_file=path.join('images','screen.png')
        return cv2.imread(screenshot_file)

    @staticmethod
    def show_img(img):
        cv2.imshow('Test', img)
        cv2.waitKey(0) # waits until a key is pressed
        cv2.destroyAllWindows() # destroys the window showing image

    def load_screenCap(self):
        screencap = self.device.screencap()
        img_bytes=bytes(screencap)
        self.lastscreen=cv2.imdecode(np.fromstring(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        # self.show_img(img)
        return self.lastscreen
        # screenshot_file=path.join('images','screen.png')
        # with open(screenshot_file, 'wb') as f:
        #     f.write(screencap)
        # sleep(.1)
        # return cv2.imread(screenshot_file)

    def get_match(self, template, img, threshold, margin):
        loc=[]
        if len(template.data):
            result = cv2.matchTemplate(img, template.data, cv2.TM_CCOEFF_NORMED)
            max=np.max(result)
            # self.log.debug(template.file)
            # self.log.debug(f"offset: {template.offset}")
            # self.log.debug(f"max: {max}")
            if (max>=threshold):
                min=max-margin if (max-margin >= threshold) else threshold
                loc=np.where(result >= min)
        return loc

    def check_present(self, template_dict,threshold=0.75,margin=0.05):
        img=self.load_screenCap()
        list=[]
        for name,template in template_dict.items():
            if len(self.get_match(template, img, threshold, margin)):
                list.append(name)
        return list


    #calculate new x or y, if device has an other resolution than 1600:900
    def scale_X(self,x):
        return x*self.res_x/1600

    def scale_Y(self,y):
        return y*self.res_y/900

    #calculate a new location based on location and the given vector
    #vector[x,y]=[0,1]=NE  -> -X (screen) and -Y (screen)
    #vector[1] positive = NW  -> dx = positive, dy= negative
    def getPos(self, vector, location=[0,0], multiplier=1):
        x,y=location
        dx=int(self.scale_X(47)*(vector[0]-vector[1])*multiplier)
        dy=int(self.scale_Y(23.5)*-(vector[0]+vector[1])*multiplier)
        return[x+dx, y+dy]

    #get color of pixel on this location
    def getColor(self,location):
        x,y=location
        img=self.lastscreen
        (b,g,r) = img[y,x]
        return [r,g,b]

    def getRow(self,row,last=True):
        img_base=self.lastscreen if last else self.load_screenCap()
        rows,cols,colors=img_base.shape
        # rows, cols=img_base.shape
        result=[]
        for col in range(cols):
            (b,g,r)=img_base[row,col]
            result.append([r,g,b])
        return result

    def locate_item(self,templates,threshold=0.75,margin=0.05,one=False,offset=[30,16],last=False, show=False):
        result_file=path.join('images','result.png')
        img_base=self.lastscreen if last else self.load_screenCap()
        img_result=img_base
        loclist=[]
        for template in templates:
            # self.log.debug(template)
            loc=self.get_match(template, img_base, threshold, margin)
            if len(loc) and len(loc[0]):
                for pt in zip(*loc[::-1]):  # Switch collumns and rows
                    cv2.rectangle(img_result, pt, (pt[0] + template.w, pt[1] + template.h), (0, 0, 255), 2)
                    x,y=np.add(pt,template.offset).astype(int)
                    if not self.checkClose(x,y,loclist,*offset):
                        # self.log.debug(f"found on {x},{y} ")
                        # self.log.debug(f"point={pt}")
                        cv2.rectangle(img_result, pt, (pt[0] + template.w, pt[1] + template.h), (255, 0, 255), 2)
                        loclist.append([x,y])
                for vector in loclist:
                    x,y=vector
                    cv2.circle(img_result, (x,y), 10, (0,255,0), -1)
        if show:
            cv2.imwrite(result_file, img_result)
        self.output.update(img_result)
        if one and len(loclist):
            target=[self.res_x, self.res_y/2]
            loclist=self.getClosest(loclist, target)
        return loclist
