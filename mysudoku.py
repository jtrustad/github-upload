from Tkinter import *
from solver import Box as SolverBox
from solver import *
import tkFont

box = []
hint_level = 0

class Puzzle(Frame):
	def __init__(self, master):
		Frame.__init__(self, master)
		for i in range(3):
			self.rowconfigure(i, weight=1)
			self.columnconfigure(i, weight=1)
			for j in range(3):
				r = Region(self, i, j)
				r.grid(row=i, column=j, sticky=NSEW)

class Region(Frame):
	def __init__(self, master, rrow, rcol):
		Frame.__init__(self, master, padx=2, pady=2, bg="black")
		for i in range(0, 3):
			for j in range(0, 3):
				b = Box(self, 3*rrow + i, 3*rcol + j)
				b.grid(row=i, column=j, sticky=NSEW)
		for i in range(6):
			self.rowconfigure(i, weight=1)
			self.columnconfigure(i, weight=1)
		
class Box(SolverBox, Frame):
	def shownumber(self, text):
		self.choice = int(text)
		update_displays()
		
	def undonumber(self, l):
		l.grid_remove()
		self.choice = 0
		update_displays()

	def makelabel(self, row, col, text, color):
		l = Label(self, text=text, fg=color)
		l.grid(row=row, column=col, sticky=NSEW)
		l.bind('<Control-Button-1>', lambda event: self.hidelabel(text, l))
		l.bind('<Button-1>', lambda event: self.shownumber(text))
		return l
		
	def hidelabel(self, text, l):
		x = int(text)
		n = 1 << x - 1
		self.maybe ^= n
		update_displays()

	def __init__(self, master, row, col):
		SolverBox.__init__(self, row, col)
		Frame.__init__(self, master, relief="groove",
			           bd=0, padx=2, pady=2, bg="gray")
		self.bigstate = 0
		self.biglabel = None
		self.labelcolor = ['pink', 'red', 'orange',
				         'green', 'blue', 'purple', 'dark green',
				         'navy', 'brown']
		self.labels = []
		for r in range(3):
			for c in range(3):
				i = 3*r + c
				self.labels.append(self.makelabel(r, c, i + 1, self.labelcolor[i]))
		for i in range(3):
			self.rowconfigure(i, weight=1)
			self.columnconfigure(i, weight=1)

	def update_display(self):
		if self.start != 0:
			if self.bigstate != self.start:
				if self.biglabel:
					self.biglabel.grid_remove()
				self.biglabel = Label(self, text=str(self.start), font=bigFont, fg='black')
				self.biglabel.grid(row=0, column=0, rowspan=3, columnspan=3, sticky=NSEW)
				self.bigstate = self.start
		elif self.choice != 0:
			if self.bigstate != self.choice + 9:
				if self.biglabel:
					self.biglabel.grid_remove()
				self.biglabel = Label(self, text=str(self.choice), font=bigFont, fg='blue')
				self.biglabel.grid(row=0, column=0, rowspan=3, columnspan=3, sticky=NSEW)
				self.biglabel.bind('<Button-1>', lambda event: self.undonumber(self.biglabel))
				self.bigstate = self.choice + 9
		else:
			if self.bigstate != 0:
				self.biglabel.grid_remove()
				self.biglabel = None
				self.bigstate = 0

		for i in range(9):
			fg = self.labelcolor[i]
			bg = "white"
			if (((self.hint & self.maybe) >> i) & 1) != 0:
				bg = "yellow"
			if ((self.hint >> i) & 1) == 0:
				fg = "white"
			self.labels[i].config(fg=fg, bg=bg)
				
def update_displays():
	show_hints()
	for i in box_list:
		i.update_display()
		
def none():
	global hint_level
	hint_level = 0
	update_displays()
			
def basic():
	global hint_level
	hint_level = 1
	update_displays()
	
def medium():
	global hint_level
	hint_level = 14
	update_displays()
	
def advan():
	global hint_level
	hint_level = 18
	update_displays()
	
def soln():
	global hint_level
	hint_level = 100
	update_displays()

def show_hints():
	reset_all_states()
	
	if hint_level >= 100:
		for b in box_list:
			b.hint = 1 << (b.solution-1)
		return
		
	h = hint_level
	while h > 8:
		update_all_hints(8)
		update_all_states()
		h -= 8
	update_all_hints(h)
	
def new_puzzle():
	global hint_level
	hint_level = 0
	n = select_puzzle()
	print("Puzzle Number", str(n))
	find_solution()
	print_puzzle("before mainloop")
	for b in box_list:
		b.maybe = 0
	update_displays()
	
def reset():
	global hint_level
	hint_level = 0
	for i in box_list:
		i.choice = 0
		i.maybe = 0
	update_displays()
	
def check_ans():
	for i in box_list:
		if i.choice != 0:
			if i.choice != i.solution:
				i.biglabel.config(bg='pink')

root = Tk()
bigFont = tkFont.Font(family="Times", size=22, weight="bold")
clear_board()
read_puzzle_file("puzzles.txt")

f = Frame(root)
f.grid()
p = Puzzle(f)
p.grid(row=0, column=0, sticky=NSEW)

g = Frame(f)
g.grid(row=1, column=0, sticky=NSEW)
lab = Label(g, text='Click an option to set box number\nControl-click --> highlights/unhighlights option\n')
lab.grid(row=0, column=0)
g.rowconfigure(0, weight=1)
g.columnconfigure(0, weight=1)
h = Frame(f)
h.grid(row=0, column=1, sticky=NSEW)
help = Label(h, text='Levels of Help:')
help.grid(row=0, column=0)
non = Button(h, text='None', command=none)
non.grid(row=1, column=0)
bas = Button(h, text='Basic', command=basic)
bas.grid(row=2, column=0)
med = Button(h, text='Medium', command=medium)
med.grid(row=3, column=0)
adv = Button(h, text='Advanced', command=advan)
adv.grid(row=4, column=0)
sol = Button(h, text='Solve Puzzle', command=soln)
sol.grid(row=6, column=0)
ch = Button(h, text='Check Answers', command=check_ans)
ch.grid(row=5, column=0)

h.rowconfigure(0, weight=1)
h.rowconfigure(1, weight=1)
h.rowconfigure(2, weight=1)
h.rowconfigure(3, weight=1)
h.rowconfigure(4, weight=1)
h.rowconfigure(5, weight=4)
h.rowconfigure(6, weight=4)
h.columnconfigure(0, weight=1)

k = Frame(f)
k.grid(row=1, column=1, sticky=NSEW)
res = Button(k, text='Reset Puzzle', command=reset)
res.grid(row=0, column=0)
new = Button(k, text='New Puzzle', command=new_puzzle)
new.grid(row=1, column=0)
k.rowconfigure(0, weight=1)
k.rowconfigure(1, weight=1)
k.columnconfigure(0, weight=1)

root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

n = select_puzzle()
print("Puzzle Number", str(n))
find_solution()

print_puzzle("before mainloop")
update_displays()

root.mainloop()
