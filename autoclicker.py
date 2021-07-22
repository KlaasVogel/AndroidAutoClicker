from adb import Adb_Device, ShowOutput
from tkinter import Tk, Frame, IntVar, StringVar, Text, Canvas, SUNKEN, Y, X, Label
from tkinter.ttk import Style, Frame, LabelFrame, Button, Checkbutton, Entry, OptionMenu
from crafting import Crafting
from deeptown import DeepTown

class EmptyFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.label=Label(self,text="Kies een programma")
        self.label.grid(row=1, column=1, padx=20, pady=15)


class MainApp(Tk):
    def __init__(self):
        self.root = Tk.__init__(self)
        self.device=Adb_Device()
        # self.frame=EmptyFrame(self)
        # self.frame.grid(row=2, column=1)
        self.games=["Geen","Crafting", "Deep Town"]
        self.option=StringVar(name="game")
        self.option.set(self.games[0])
        self.dropdown = OptionMenu(self, self.option, self.games[0], *self.games, command=self.display_selected)
        # self.dropdown.grid(row=1, column=1, columnspan=3)
        self.frame=DeepTown(self,self.device)
        self.frame.grid(row=2, column=1)


    def display_selected(self, option):
        print(option)
        self.frame.grid_forget()
        self.frame.destroy()
        for idx,game in enumerate(self.games):
            if game==option:
                if idx==1:
                    self.frame=Crafting(self,self.device)
                elif idx==2:
                    self.frame=DeepTown(self,self.device)
                else:
                    self.frame=EmptyFrame(self)
                break
        else:
            self.frame=EmptyFrame(self)
        self.frame.grid(row=2, column=1)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
