from adb import Adb_Device, ShowOutput
from tkinter import Tk, Frame, IntVar, StringVar, Text, Canvas, SUNKEN, Y, X, Label
from tkinter.ttk import Style, Frame, LabelFrame, Button, Checkbutton, Entry
from dataclasses import dataclass, field


@dataclass
class clickLocation:
    source1_x: int = 0
    source1_y: int = 0
    source2_x: int = 0
    source2_y: int = 0
    upgrade_coord: int = field(default_factory=list)
    sell_coord: int = field(default_factory=list)

    def set(self, x, y):
        self.source1_coord = [x - 100, y - 40]
        self.source2_coord = [x - 100, y + 40]
        self.upgrade_coord = [x - 207, y - 56]
        self.sell_coord =    [x + 142, y - 55]

class EmptyFrame(Frame):
    def __init__(self):
        Frame.__init__()
        self.label=Label(text="Kies een programma")
        self.label.grid(row=1, column=1, padx=20, pady=15)

class Crafting(LabelFrame):
    def __init__(self, parent):
        self.parent=parent
        LabelFrame.__init__(self, parent, text="Crafting:")
        # self.clicker=clickLocation()
        self.main_x=IntVar()
        self.main_y=IntVar()
        self.source1=IntVar()
        self.source2=IntVar()
        self.upgrade=IntVar()
        self.main_x.trace_add('write', self.update)
        self.main_y.trace_add('write', self.update)
        self.label1=Label(self, text="MainClicker:")
        self.label1.grid(row=1, column=2)
        self.set_main_x=Entry(self, textvariable=self.main_x)
        self.set_main_y=Entry(self, textvariable=self.main_y)
        self.set_main_x.grid(row=1, column=3)
        self.set_main_y.grid(row=1, column=4)
        self.data=clickLocation()
        self.label2=Label(self, text="Source 1:")
        self.label2.grid(row=2, column=2)
        self.set_source1=Entry(self, textvariable=self.source1)
        self.set_source1.grid(row=2, column=3)
        self.label3=Label(self, text="Source 2:")
        self.label3.grid(row=3, column=2)
        self.set_source2=Entry(self, textvariable=self.source2)
        self.set_source2.grid(row=3, column=3)
        self.check_upgrade=Checkbutton(self, text="upgrade", variable=self.upgrade)
        self.check_upgrade.grid(row=4, column=2)
        self.but_start=Button(self, text="start", command=self.parent.start_crafting)
        self.but_stop=Button(self, text="stop", command=self.parent.stop_crafting)
        self.but_start.grid(row=5, column=2)
        self.but_stop.grid(row=5, column=3, columnspan=2)

    def update(self, var, indx, mode):
        print(f"Traced variable {var}")
        x=self.main_x.get()
        y=self.main_y.get()
        print(f"x,y = {x}, {y}")
        self.data.set(x,y)
        print(self.data)


class MainApp(Tk):
    def __init__(self):
        self.running=False
        self.root = Tk.__init__(self)
        self.device=Adb_Device()
        self.frame=EmptyFrame()
        self.frame.grid(row=2, column=1)
        self.games=["Crafting", "Deep Town"]
        self.option=StringVar()
        self.option.set(self.games[0])
        self.dropdown = OptionMenu(self, self.option, *self.games, command=display_selected)
        self.dropdown.grid(self, row=1, column=1, columnspan=3)

    def display_selected(self, option):
        print(option)
        # self.frame=Crafting(self)
        # self.frame.grid(row=2, column=1)

    def start_crafting(self):
        if not self.running:
            self.running=True
            self.click_crafting()

    def click_crafting(self):
        if self.running:
            sets={self.crafting.source1.get():self.crafting.data.source1_coord,
                  self.crafting.source2.get():self.crafting.data.source2_coord}
            for set,coord in sets.items():
                x,y=coord
                for i in range(set):
                    self.device.tap(x,y)
            for i in range(10):
                self.device.tap(self.crafting.main_x.get(), self.crafting.main_y.get())
            x,y=self.crafting.data.sell_coord
            self.device.tap(x,y)
            if self.crafting.upgrade.get():
                x,y=self.crafting.data.upgrade_coord
                self.device.tap(x,y)
            self.after(100, self.click)

    def stop_crafting(self):
        self.running=False


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
