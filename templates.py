import os
import cv2
from glob import glob

def build_dir(map):
    if not os.path.isdir(map):
        os.mkdir(map)
    return os.path.join(os.getcwd(),map)

def getName(file):
    filename=f"{os.path.splitext(os.path.split(file)[1])[0]}"
    for str in ["_C_","_C","_T","_B","L_","R_"]:
        if str in filename:
            filename=filename.replace(str,"")
    return filename


class Template:
    def __init__(self, template_file):
        self.offset=[0.0,0.0]
        self.w,self.h=[0,0]
        self.data=[]
        if os.path.isfile(template_file):
            self.file=os.path.split(template_file)[-1]
            self.data= cv2.imread(template_file)
            self.h,self.w = self.data.shape[:-1]
            if "_C" in template_file:
                # self.log.debug("C")
                self.offset=[self.w/2,self.h/2]
            if "R_" in template_file:
                # self.log.debug("R")
                self.offset[0]=0
            if "L_" in template_file:
                # self.log.debug(f"L {self.w}")
                self.offset[0]=self.w
            if "_T" in template_file:
                # self.log.debug("T")
                self.offset[1]=self.h
        # self.log.debug(self.offset)
        # savedata={"name":self.file, "data":self.data.tolist(), "shape":[self.h, self.w], "offset":self.offset}
        # name=getName(template_file)
        # json_file=path.join("templates",name)
        # saveJSON(savedata,json_file)
    def __repr__(self):
        return f"Template({self.file}, offset={self.offset})"


class Templates(dict[str, Template]):
    def addTemplate(self, fullpath):
        name=getName(fullpath)
        self[name]=Template(fullpath)

def loadTemplates(*dirs):
    templates=Templates()
    map = os.path.join(*dirs)
    build_dir(map)
    filelist=glob(os.path.join(map,"*.png"))
    for file in filelist:
        templates.addTemplate(file)
    return templates