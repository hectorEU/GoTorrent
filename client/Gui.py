
from Tkinter import *
from ttk import Progressbar

class Gui(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.scrollbar = Scrollbar(self)
        self.scrollbar.pack(side = RIGHT, fill=Y)
        self.list = Listbox(self, yscrollcommand=self.scrollbar.set, listvariable=Torrent)
        self.list.pack(side=LEFT, fill=BOTH)
        self.scrollbar.config(command=self.list.yview)
        self.update()

    def add_torrent(self, torrent):
        self.list.insert(END, Torrent(self.list, torrent))

    def update(self):
        for row in self.list.get(0, last=END):
            print row.get()
        self.after(1000, self.update)

class Torrent(object):
    def __init__(self, parent, torrent):
        self.torrent = torrent
        self.widgets = [Label(parent, text=torrent.file.name, relief=RIDGE, width=15),
                   Progressbar(parent),
                   Label(parent, text=str(len(torrent.peers)))]

        for widget in self.widgets:
            widget.pack(side=LEFT)

        self.update()


    def update(self):
        self.widgets[1]["value"] = self.torrent.file.downloaded * 100 / self.torrent.file.size
