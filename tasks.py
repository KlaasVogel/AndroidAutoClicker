from tkinter import Tk, IntVar, StringVar, Label, Text
from tkinter.ttk import Frame, LabelFrame, Button, Checkbutton, Entry
from dataclasses import dataclass, field
from os import path, getcwd, mkdir
from json_tools import loadJSON, saveJSON

@dataclass
class Task():
    name: str
    check: str
    job: str = field(repr=False)
    time: float




class Tasklist(dict):
    def __init__(self,parent,**kwargs):
        self.parent=parent
        self.log=parent.logger
        self.parent.behind=False
        self.frame=LabelFrame(self.parent, text="Taskslist:")
        self.frame.grid(**kwargs)
        self.textList=Text(frame,height=7)
        self.stringTask=StringVar()
        self.labelTask=Label(frame, textvariable=self.stringTask)
        # self.textConsole=Text(frame,height=7)
        self.textList.grid(row=2, column=1)
        self.labelTask.grid(row=1, column=1, sticky='w')
        # self.textConsole.grid(row=3, column=1)
        self.tasklist=Tasklist(self,self.textList,self.stringTask,self.textConsole)

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
            new_time=int(time()) if firsttime else int(time())+task.time*60
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
                    self.parent.behind=True if cur_time-firsttask>20 else False
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
class TaskField():
    parent: str
    row: int
    name: str
    time: int
    unit: str
    method: str
    def __post_init__(self):
        print(self)

class Tasks(LabelFrame):
    def __init__(self, parent, **kwargs):
        self.parent=parent
        LabelFrame.__init__(self, parent, text="Tasks:")
        self.fields=[]
        self.grid(**kwargs)
        self.build(loadJSON(path.join("data","tasks.json")))

    def build(self, data):
        print(data)
        for idx, name in enumerate(data.keys()):
            try:
                self.fields.append(TaskField(self, idx, name, data[name]))
            except:
                traceback.print_exc()
