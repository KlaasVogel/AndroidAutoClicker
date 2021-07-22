from tkinter import Tk, IntVar, StringVar, Label, Text
from tkinter.ttk import Frame, LabelFrame, Button, Checkbutton, Entry, OptionMenu
from dataclasses import dataclass, field
from os import path, getcwd, mkdir
from json_tools import loadJSON, saveJSON
from tools import printtime
import traceback
from time import time, sleep, localtime, strftime
from threading import Thread

# @dataclass
# class Task():
#     name: str
#     check: str
#     job: str = field(repr=False)
#     time: float


class Tasklist(dict):
    def __init__(self,parent,**kwargs):
        self.parent=parent
        self.log=parent.logger
        self.parent.behind=False
        self.frame=LabelFrame(self.parent, text="Taskslist:")
        self.frame.grid(**kwargs)
        self.textList=Text(self.frame,height=7)
        self.stringTask=StringVar()
        self.labelTask=Label(self.frame, textvariable=self.stringTask)
        # self.textConsole=Text(frame,height=7)
        self.textList.grid(row=2, column=1)
        self.labelTask.grid(row=1, column=1, sticky='w')
        # self.textConsole.grid(row=3, column=1)
        # self.tasklist=Tasklist(self,self.textList,self.stringTask,self.textConsole)
        # self.console=output3
        self.paused=True
        self.busy=False
        self.lasttask=None
        self.update()

    def start(self):
        self.paused=False
        self.thread=Thread(target=self.run, daemon=True).start()
    def pause(self):
        self.paused=True

    def addTask(self, task):
        self.setTask(task, True)

    def setTask(self,task, firsttime=False):
        if task.time.get() or firsttime:
            # self.log.debug(f'\n resetting job for {task.name}')
            multiplier = 3600 if task.unit.get()=="hour" else 60
            new_time=int(time()) if firsttime else int(time())+task.time.get()*multiplier
            while new_time in self:
                new_time+=1
            self[new_time]=task

    def removeTask(self, task):
        name=""
        for tasktime in self:
            if self[tasktime]==task:
                name=tasktime
        if name:
            self.pop(name)

    def run(self):
        print(self)
        while not self.paused:
            cur_time=int(time())
            if len(self):
                firsttask=sorted(self)[0]
                if firsttask<=cur_time and not self.busy:
                    self.parent.behind=True if cur_time-firsttask>20 else False
                    task=self.pop(firsttask)
                    self.stringTask.set(f"Current Task: {task.name} [started at {strftime('%H:%M:%S',localtime())}]")
                    if task.status.get():
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
            self.textList.delete("1.0","end")
            for line in data:
                self.textList.insert("end",str(line)+"\n")
        except Exception as e:
            traceback.print_exc()
        finally:
            self.parent.after(1000, self.update)


class TempGet():
    def get(self):
        return True

class TempTime():
    def get(self):
        return 0

@dataclass
class TempTask():
    name: str
    job: str
    def __post_init__(self):
        self.time=TempTime()
        self.unit=TempTime()
        self.status=TempGet()


@dataclass
class Task():
    parent: str
    row: int
    name: str
    time: float
    unit: str
    method: str
    status: int
    def __post_init__(self):
        status=self.status
        self.status=IntVar(name=self.name)
        self.status.set(status)
        self.job=getattr(self.parent.master,self.method,self.emptymethod)
        time=self.time
        self.time=IntVar()
        self.timeBox=Entry(self.parent,textvariable=self.time,width=3)
        self.timeBox.grid(column=2, row=self.row)
        self.time.set(time)
        self.time.trace_add('write', self.parent.save)
        unit=self.unit
        self.unit=StringVar()
        self.menu=OptionMenu(self.parent,self.unit,*["min","hour"])
        self.menu.grid(row=self.row, column=3, sticky='w')
        self.unit.set(unit)
        self.unit.trace_add('write', self.parent.save)
        if status:
            self.parent.tasklist.addTask(self)
        self.status.trace_add('write', self.toggle)
        self.button=Checkbutton(self.parent, text=self.name, variable=self.status, onvalue=1)
        self.button.grid(column=1, row=self.row, sticky='w')

    def toggle(self,*args):
        print(args)
        self.parent.tasklist.removeTask(self)
        if self.status.get():
            self.parent.tasklist.addTask(self)
        self.parent.save()

    def emptymethod(self):
        print("doing nothing")

    def get(self):
        try:
            time=self.time.get()
        except:
            time=0
        data={ "time":time,
               "unit":self.unit.get(),
               "method":self.method,
               "status":self.status.get()
             }
        return [self.name,data]

class Tasks(LabelFrame):
    def __init__(self, parent, tasklist, **kwargs):
        self.master=parent
        self.tasklist=tasklist
        LabelFrame.__init__(self, parent, text="Tasks:")
        self.fields=[]
        self.grid(**kwargs)
        self.json_file=path.join("data","tasks.json")
        self.print_button=Button(self, text="Print Screen", command=parent.device.printScreen)
        self.print_button.grid(row=0, column=1)
        self.start_button=Button(self, text="Start Tasks", command=self.start_tasks)
        self.start_button.grid(column=2, columnspan=2, row=0)
        self.build(loadJSON(self.json_file))

    def start_tasks(self):
        if self.tasklist.paused:
            self.start_button.configure(text="Pause")
            self.tasklist.start()
        else:
            self.start_button.configure(text="Start Tasks")
            self.tasklist.pause()

    def build(self, data):
        print(data)
        for idx, name in enumerate(data.keys()):
            try:
                self.fields.append(Task(self, idx+1, name, **data[name]))
            except:
                traceback.print_exc()

    def save(self,*args):
        alldata={}
        for task in self.fields:
            name,data=task.get()
            alldata[name]=data
        saveJSON(alldata,self.json_file)
