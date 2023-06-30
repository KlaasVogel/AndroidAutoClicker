from tkinter import Tk, IntVar, StringVar, Label, Text, Misc
from tkinter.ttk import Frame, LabelFrame, Button, Checkbutton, Entry, OptionMenu
from dataclasses import dataclass, field
from tasks import Tasks, Tasklist, TempTask
from json_tools import JSONs
from templates import loadTemplates
from adb import Adb_Device

IMAGE_DIR = "ID_images"

@dataclass
class Distiller(LabelFrame):
    parent: Misc
    device: Adb_Device

    def __post_init__(self):
        super().__init__(self.parent, text="Distiller")
        # self.logger=MyLogger('DeepTown', LOG_LEVEL=logging.DEBUG)
        self.resolution = self.device.get_resolution()
        self.configs = JSONs("data_ID", self.resolution)
        self.tasklist=Tasklist(self,row=6,column=1,columnspan=3, sticky='w')
        self.tasks=Tasks(self, self.device, self.tasklist, self.configs)
        self.tasks.grid(row=1, column=1, rowspan=5,columnspan=2, sticky='w')
        self.templates=loadTemplates(IMAGE_DIR, self.resolution, "general")
        self.bonus_templates = loadTemplates(IMAGE_DIR, self.resolution, "bonus")
        print(self.templates)

    def build(self):
        print("build")

    def check_bonus():
        return False

    def collect_bonus_money(self):
        print("collect money")
        if not self.check_bonus():
            ...
