from dataclasses import dataclass, field
from os import path, getcwd, walk, stat
from adb import Template
from glob import glob
from time import sleep
import traceback
from time import time, localtime, strftime
import cv2
import numpy as np
from tools import getName
from database import MyDB

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

def load_screen_img(file):
    return cv2.imread(file)

def get_match(template, img, threshold=.97, margin=.03):
    loc=[]
    if len(template.data):
        result = cv2.matchTemplate(img, template.data, cv2.TM_CCOEFF_NORMED)
        max=np.max(result)
        if (max>=threshold):
            min=max-margin if (max-margin >= threshold) else threshold
            loc=np.where(result >= min)
    return loc

def getRow(row,img):
    rows,cols,colors=img.shape
    print(rows, cols, colors)
    result=[]
    for col in range(cols):
        (b,g,r)=img[row,col]
        result.append([r,g,b])
    return result

def getPixel(row,img):
    pixel=610
    row=getRow(row,img)
    for idx,(r,g,b) in enumerate(row):
        print(r,g,b)
        if idx>600 and idx<780:
            if r<35 and g>150 and b>220:
                pixel=idx
    return(pixel)

def getLevel(templates,img):
    for lvl,template in templates.items():
        location=get_match(template,img)
        if len(location):
            loc=location[::-1]
            y=int(loc[1]+template.offset[1])
            # print(f"img: {img} - level: {lvl}")
            pixel=getPixel(y,img)
            return [int(lvl),pixel]
    return [0,0]

temp_names=loadTemplates(path.join('images','guilds','names'))
temp_lvls=loadTemplates(path.join('DT_images','levels'))

datadirs=[]
datafiles=[]
search_path=path.join('images','guilds')
for root, dirs, files in walk(search_path):
    for dir in dirs:
        if root==search_path and dir!="names":
            datadirs.append(path.join(search_path,dir))

    for file in files:
        # print(root, file)
        if root in datadirs:
            datafiles.append(path.join(getcwd(),root,file))

for file in datafiles:
    db=MyDB()
    created=stat(file).st_ctime
    # result=db.query(f"SELECT FROM_UNIXTIME({created}) as `nu`")
    # date=result[0]
    # print(date)

    img_base=load_screen_img(file)
    for guild,template in temp_names.items():
        (guildID,name)=db.query(f"SELECT * FROM `guilds` WHERE `name`='{guild}'")[0]
        if not guildID:
            db.update(f"INSERT INTO `guilds` (name) VALUES ('{guild}')")
            guildID=db.lastID()
        if len(get_match(template,img_base)):
            # print(guild)
            level,pixel=getLevel(temp_lvls, img_base)
            # print(level, pixel)
            if level:
                print(f"{guild} - {guildID} - {created} - {level} - {pixel}")
                sql=f"INSERT INTO `pixels` (guildID, tijd, level, pixels) VALUES ({guildID},FROM_UNIXTIME({created}),{level},{pixel})"
                print(sql)
                print(db.update(sql))
            break
    db.close()






    # def spy(self):
    #     images=["menu_guild","guild_list"]
    #     if self.checkTemplates(images):
    #         # self.clearMem()
    #         db=MyDB()
    #         fullpath=build_dir(path.join("DT_Images","guilds"))
    #         templates=loadTemplates(fullpath)
    #         record={}
    #         for guild in templates:
    #             record[guild]=False
    #         print(record)
    #         if len(record) and self.tap("menu_guild"):
    #             sleep(2)
    #             self.tap("guild_list")
    #             count=0
    #             for x in range(3):
    #                 last=False
    #                 for guild in record:
    #                     if not record[guild]:
    #                         print(f"searching for {guild}")
    #                         guild_loc=self.device.locate_item([templates[guild]], last=last, one=True)
    #                         if len(guild_loc):
    #                             print(f"found at: {guild_loc}")
    #                             self.device.tap(*guild_loc)
    #                             sleep(1)
    #                             print("searching level")
    #                             level,pixel=self.getLevel()
    #                             if level:
    #                                 print(f"guild: {guild} - level: {level} - pixel: {pixel}")
    #                                 guildID=db.query(f"SELECT * FROM `guilds` WHERE `name`='{guild}'")
    #                                 if not guildID:
    #                                     db.update(f"INSERT INTO `guilds` (name) VALUES ('{guild}')")
    #                                     guildID=db.lastID()
    #                                 if db.update(f"INSERT INTO `pixels` (guildID, level, pixels) VALUES ({guildID},{level},{pixel})"):
    #                                     record[guild]=True
    #                             self.device.go_back()
    #                             sleep(2)
    #                             last=False
    #                         else:
    #                             last=True
    #                 self.device.swipe(777,1530,777,800,speed=1200)
    #                 sleep(2)
    #             self.device.go_back()
    #
    #         db.close()
