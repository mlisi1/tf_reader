import tkinter as tk
from tkinter import ttk

import numpy as np
import os
import copy
import re

#Matplotlib plot utilities and tk wrapper
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib
matplotlib.use("TkAgg")
try:
	from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
except ImportError:
	from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg

import cv2


#================ TOOLBAR ===================
# A custom class for NavigationToolbar2TkAgg; 
# Adds the possibility to be resized to a smaller version with smaller icons
class Toolbar(NavigationToolbar2TkAgg):

	def __init__(self, plot, master, pack_toolbar = True, default = True):

		#Initialize super class
		super().__init__(plot, master, pack_toolbar = pack_toolbar)
		
		#Toolbar small icons paths
		self.icon_names = ['./icons/home.gif', './icons/left_arrow.gif', './icons/right_arrow.gif', './icons/move.gif', './icons/zoom.gif',
							'./icons/config.gif', './icons/save.gif']

		#Default icons and size
		self.default_icons = [widget.cget('image') for widget in self.winfo_children() if isinstance(widget, (tk.Button, tk.Checkbutton))]
		self.default_hw = (self.winfo_children()[0].cget('height'), self.winfo_children()[0].cget('width'))

		self.icons = []

		#The coordinates label is removed and placed elsewhere
		self._message_label.pack_forget()
		self._load_icons()      

	#Loads the small icons
	def _load_icons(self):

		for i, icon in enumerate(self.icon_names):
			self.icons.append(tk.PhotoImage(file = icon))

	#Changes the toolbar to its smaller version
	def change_icons(self, default):

		#Delete all existing buttons
		self.place_forget()
		i = 0
		for widget in self.winfo_children():            

			if isinstance(widget, (tk.Button, tk.Checkbutton)):               

				#Create new buttons and checkbuttons according to the requested size
				widget.config(height = self.default_hw[0] if default else 17, 
								image = self.default_icons[i] if default else self.icons[i], 
								width = self.default_hw[1] if default else 17)

				if isinstance(widget, tk.Checkbutton):
					widget.config(selectimage = self.default_icons[i] if default else self.icons[i])
				i+=1

		self.place(height = 50 if default else 30)


#=============== PLOT CONTAINER ====================
#Frame used to contain Matplotlibs tk wrapper; handles low level plot functions
class PlotContainer(ttk.Frame):

	def __init__(self, container, scalars, scalar_choice, **args):

		#Initialize frame and figure
		tk.Frame.__init__(self, container, **args)
		self.fig, self.ax = plt.subplots()  
		self.ax.grid(True)   

		#Initialize Matplotlib wrappers and place them
		self.canvas = FigureCanvasTkAgg(self.fig, master = self)
		self.canvas.draw()
		self.canvas.get_tk_widget().pack(side=tk.BOTTOM)       
		self.canvas._tkcanvas.pack(side=tk.TOP, expand =True)
		self.title = ""       

		self.tool_frame = tk.Frame(self)
		self.toolbar = Toolbar(self.canvas, self.tool_frame)
		self.toolbar.update()
		self.tool_frame.pack(fill = tk.X)
		self.coord = self.toolbar.message

		#Initialize scalar defining arrays
		self.scalars = scalars
		self.scalar_name = scalar_choice
		self.line = []
		self.colors = []
		self.data = []  

		#Translate scalars to arrays
		self.data_from_scalar() 


	#Smooth function; implemented after the analog Tensorboard feature
	def smooth(self, scalars, weight):
		#check for NaN
		last = scalars[0] if np.isfinite(scalars[0]) else 0.0
		smoothed = np.convolve(np.ones(len(scalars)), scalars, mode='same') / len(scalars)
		smoothed[0] = last
		for i in range(1, len(scalars)):
			#smooth if not NaN; else use last value
			if not np.isfinite(scalars[i]):
				smoothed[i] = smoothed[i-1]
			else:
				smoothed[i] = last * weight + (1 - weight) * scalars[i]
				last = smoothed[i]
		return smoothed

	#Clears the plot
	def clear(self):

		#Clear plot and draw it
		self.ax.clear()
		self.canvas.draw()

		#Reset scalar choices arrays
		self.scalars = []
		self.colors = []

	#Gets data from scalars
	def data_from_scalar(self):

		#Delete previous data
		del self.data
		self.data = []  


		#Gather correct values
		for i in range(len(self.scalars)):

			if type(self.scalar_name) == list:

				data = [self.scalars[i][self.scalars[i]['tag'] == self.scalar_name[j]] for j in range(len(self.scalar_name))]
				self.data.append(data)  

			else:	
				 
				data = self.scalars[i][self.scalars[i]['tag'] == self.scalar_name]   
				self.data.append(data)    


	#Updates the plot with the scalars data
	def update_plot(self, smooth_value):

		#Initialize min/max values
		min_x = 0
		max_x = 0
		min_y = 0
		max_y = 0

		#Clear plot and reset plot relative arrays
		self.ax.clear()
		self.line = []
		self.colors = []       


		for i in range(len(self.scalars)):

			#Gather plot data
			self.data_from_scalar()
			if len(self.data[i]) > 0:

				if type(self.data[i]) == list:

					style = ['-', '--', ':']
					color = None
					title = self.title.strip('(3)')
					triple_lines = []

					for j, data in enumerate(self.data[i]):

						x = data['step']
						y = self.smooth(data['value'].values, smooth_value)

						p, q,  r, s = np.min(x), np.max(x), np.min(y), np.max(y)
					
						#Update plot limit values
						if p < min_x:
							min_x = p
						if q > max_x:
							max_x = q
						if r < min_y:
							min_y = r
						if s > max_y:
							max_y = s

						

						if color == None:

							#Draw line and store color for the first entry
							tmp, = self.ax.plot(x, y, linestyle=style[j])
							color = tmp.get_color()

						else:

							#Draw line
							tmp, = self.ax.plot(x, y, linestyle=style[j], color = color)

						triple_lines.append(tmp)

					#Add legend to plot
					self.ax.legend(labels=[f'{title}- 1', f'{title}- 2', f'{title}- 3'], loc='upper left')
					self.line.append(triple_lines)
					self.colors.append(color)




				else:

					x = self.data[i]['step']
					y = self.smooth(self.data[i]['value'].values, smooth_value)
					p, q,  r, s = np.min(x), np.max(x), np.min(y), np.max(y)
					
					#Update plot limit values
					if p < min_x:
						min_x = p
					if q > max_x:
						max_x = q
					if r < min_y:
						min_y = r
					if s > max_y:
						max_y = s

				   
					#Draw line and store color
					tmp, = self.ax.plot(x, y)
					self.line.append(tmp)
					self.colors.append(self.line[i].get_color())

			#The scalar has no valid data
			else:

				self.line.append(None)
				self.colors.append(None)

		
		#Set plot limits, title and grid and draw
		self.ax.set_xlim(min_x-10, max_x+10)
		self.ax.set_ylim(min_y-10, max_y+50)   
		self.ax.grid(True) 
		self.ax.set_title(self.title)    
		self.canvas.draw()

	#Fast update method; it only redraws the plot;
	#>used when the scalars haven't changed but plot needs to be redrawn
	def fast_update(self):

		self.canvas.draw()


#===================== SCROLLABLE FRAME ===============
#Frame with scrollbar
class ScrollableFrame(ttk.Frame):

	def __init__(self, container, row, column, height, width,  *args, **kwargs):

		#Initialize frame
		super().__init__(container, *args, **kwargs)

		#Initialize canvas and scrollbar, both attached to the frame
		self.canvas = tk.Canvas(self, height = height, width = width)
		scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

		#Scrollable frame where widgets will be attached
		self.scrollable_frame = ttk.Frame(self.canvas)
		self.scrollable_frame.columnconfigure(row)
		self.scrollable_frame.rowconfigure(column)

		#Configure scrollbar and scrollbar frame
		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(
				scrollregion=self.canvas.bbox("all")
			)
		)
		self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		self.canvas.configure(yscrollcommand=scrollbar.set)

		#Place items
		self.canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")


#======================== SCALAR LABELS ======================
#Conveniently defined labels with hover methods
class ScalarLabel(ttk.Label):

	def __init__(self, container, text, lines, update_fns):

		#Initialize label
		self.font = ("Verdana", 9)
		super().__init__(container, text = text, font = self.font)
		self.color = None

		#Get line and line color
		self.lines = lines
		if self.lines != None:

			for line in lines:

				if line != None:

					if type(line) == list:

						self.color = line[0].get_color()

					else:

						self.color = line.get_color()
		else:

			self.color = "#000000"

		self.removed = False

		#Assign the color to the label
		self.configure(foreground = self.color)
		
		#Reference to the update function (fast update)
		self.update_fns = update_fns

		# Bind the hover functions to the <Enter> and <Leave> events
		self.bind("<Enter>", self.on_enter)       
		self.bind("<Leave>", self.on_leave)

	#Method called externally; updates the assigned line if plot has changed
	def update_lines(self, lines, update_fns):
		
		self.lines = lines
		self.update_fns = update_fns
		if self.lines != None:
			for line in lines:
				if line != None:

					if type(line) == list:				

						self.configure(foreground = line[0].get_color())
						break

					else:

						self.configure(foreground = line.get_color())
						break
		else:
			
			self.configure(foreground = "#000000")

	#Hover functions
	def on_enter(self, event):

		#Highlight label and assigned line
		self.configure(foreground="black")
		if self.lines != None:
			for i, line in enumerate(self.lines):

				if line != None:

					if type(line) == list:

						for j in range(len(line)):

							line[j].set_linewidth(3)
					else:

						self.lines[i].set_linewidth(3)

					self.update_fns[i]()

	def on_leave(self, event):

		#Deselect label and line
		self.configure(foreground=self.color)
		if self.lines != None:
			for i, line in enumerate(self.lines):

				if line != None:

					if type(line) == list:

						for j in range(len(line)):

							line[j].set_linewidth(1)

					else:

						self.lines[i].set_linewidth(1)
					
					self.update_fns[i]()


	#Removes this scalar label's lines
	def remove_lines(self):

		#Undraw lines
		for i, line in enumerate(self.lines):

			if type(line) == list:

				for j in range(len(line)):

					line[j].remove()

			else:

				line.remove()

			self.update_fns[i]()

		#Call for a higher level update
		self.lines = None
		self.removed = True
	   






#====================PLOT HANDLER====================
#Class capable of handling multiple instances of PlotContainer
#Chooses from the loaded scalars the correct tags
#Allows to create up to 6 plots
class PlotHandler(ttk.Frame):

	def __init__(self, container, tags, full_tags, **args):

		super().__init__(container, **args)

		self.root_dir = os.getcwd()
		self.icon = tk.PhotoImage(file = './icons/minus.gif')

		self.scalars = []

		self.scalar_tags = tags
		self.full_scalar_tags = full_tags 

		self.scalar_choice = tk.StringVar()
		self.scalar_choice.set(self.scalar_tags[0])

		self.root_size = None
		self.offset = (340, 220)      

 
		#Top frame used for the scalar tag choice and to add plots
		self.top_frame = ttk.Frame(self, height = 30)
		self.top_frame.grid(row = 0, column = 1, sticky = "NW", pady = 5, columnspan = 3)

		self.option_menu  = ttk.OptionMenu(self.top_frame, self.scalar_choice, self.scalar_tags[0], *self.scalar_tags)
		self.option_menu.config(width = 25)
		self.option_menu.grid(row = 0, column = 0, sticky  = "NW", padx = 20, pady = 5)

		self.add_butt = ttk.Button(self.top_frame, text = "Add", command = self.add_plot)
		self.add_butt.grid(row = 0, column = 1, padx = 10, pady = 5, sticky = "NE")

		self.remove_plots_button = ttk.Button(self.top_frame, text = "Remove all plots", command = self.remove_all_plots)
		self.remove_plots_button.grid(row = 0, column = 2, padx = 10, pady = 5, sticky = "NE")
		
		self.remove_plots_button.state(["disabled"])
		self.option_menu.state(["disabled"])
		self.add_butt.state(["disabled"])


		#Fixed grid positions for the plots
		self.positions = [(1,1), (2,1), (1,2), (2,2), (1,3), (2,3)]   

		self.frames = []
		self.plots = []
		self.labels = []
		self.remove_buttons = []

		#Variable used to trigger root update
		self.need_to_update = False


	#Self explainatory
	def remove_all_plots(self):

		for i in range(len(self.plots)):

			self.remove_plot(self.plots[0])


	#Clears remeved lines data
	def remove_line(self, index):

		for plot in self.plots:
			plot.line.pop(index)
			plot.colors.pop(index)
			plot.data.pop(index)

	 
	#Gets the correct plot sizes based on the window size
	@property
	def plot_size(self):

		if len(self.plots) == 1:

			height = self.root_size[1]-self.offset[1]
			width = self.root_size[0]-self.offset[0]
			return (width, height)

		if len(self.plots) == 2:

			height = self.root_size[1]-self.offset[1]
			width = self.root_size[0]-self.offset[0]
			height = height/2
			return (width, height)

		if len(self.plots) > 2 and len(self.plots) < 5:

			height = self.root_size[1]-self.offset[1]
			width = self.root_size[0]-self.offset[0]
			height = height/2
			width = width/2
			return (width, height)

		if len(self.plots) > 4:

			height = self.root_size[1]-self.offset[1]
			width = self.root_size[0]-self.offset[0]-20
			height = height/2
			width = width/3
			return (width, height)


	#Calls the update function for every plot
	def update_plots(self, smooth_value):

		for plot in self.plots:

			plot.scalars = self.scalars
			plot.update_plot(smooth_value)

	#Returns the full tag 
	@property
	def get_tag_choice(self):
		key = self.scalar_choice.get()
		index = self.scalar_tags.index(key) 

		#The '(3)' in the tag indicates there are 3 tags to be drawn together
		if '(3)' in key:

			new_key = self.full_scalar_tags[index].strip(' (3)') 
			triple_keys = [(new_key + f' - {i}:') for i in range(1,4)]
			return triple_keys

		else:
					      
			return self.full_scalar_tags[index]  

	#Add a plot
	def add_plot(self):

		#Initialize frame (container), plot, remove button, and coordinates label and place them in the frame
		new_frame = ttk.Frame(self)

		new_plot = PlotContainer(new_frame, self.scalars, self.get_tag_choice)
		new_plot.title = self.scalar_choice.get()
		new_plot.grid(row = 0, column = 0)

		new_button = tk.Button(new_frame, text = "-", image = self.icon, height = 17, width = 17, command = lambda: self.remove_plot(new_plot))
		new_button.grid(row = 1, column = 0, sticky = "NE", padx = 10)       

		new_label = tk.Label(new_frame, textvariable = new_plot.coord, justify=tk.RIGHT)
		new_label.grid(row = 1, column = 0, sticky = "NW", padx = 20)        

		self.frames.append(new_frame)
		self.plots.append(new_plot)
		self.labels.append(new_label)

		#Update
		self.update_sizes()
		self.update_grid()
		self.update_plots(0.0)
		self.need_to_update = True

		self.remove_plots_button.state(["!disabled"])

		#Max plot number is 6
		if len(self.plots) == 6:

			self.add_butt.state(["disabled"])


	#Update the plots to the correct sizes along with dpi and toolbar
	def update_sizes(self):


		for i, plot in enumerate(self.plots):
			plot.canvas.get_tk_widget().config(width=self.plot_size[0], height=self.plot_size[1])

			if len(self.plots) <=2:
				plot.fig.dpi = 100
				plot.toolbar.change_icons(True)
				plot.tool_frame.config(height = 50)

			else:
				plot.fig.dpi = 75
				plot.toolbar.change_icons(False)
				plot.tool_frame.config(height = 30)


	#Place the plots according to the fixes positions
	def update_grid(self):

		for i, frame in enumerate(self.frames):

			frame.grid_remove()
			frame.grid(row = self.positions[i][0], column = self.positions[i][1], sticky="NW", padx = 5, pady = 5)
		
			self.labels[i].grid_remove()
			self.labels[i].grid(row = 1, column = 0, sticky = "NW", padx = 20)



	#Remove plots
	def remove_plot(self, rm_plot):


		for i, plot in enumerate(self.plots):

			if plot == rm_plot:

				plt.close(plot.fig)
				self.plots[i].destroy()
				self.labels[i].destroy()
				self.frames[i].destroy()
				self.plots.pop(i)
				self.labels.pop(i)
				self.frames.pop(i)
				break

		self.update_sizes()
		self.update_grid()
		self.need_to_update = True
		self.add_butt.state(["!disabled"])

		if len(self.plots) == 0:
			self.remove_plots_button.state(["disabled"])

	#Calls the clear function for every plot
	def clear(self):
		
		del self.scalars
		self.scalars = []

		for plot in self.plots:
			plot.clear()

	#Resize function; adjusts plot size according to the window size
	def on_resize(self, win_size):

		self.update()        
		self.root_size = win_size       

		for plot in self.plots:
			
			plot.canvas.get_tk_widget().config(width = self.plot_size[0], height = self.plot_size[1])

	#Save all the displayed plots into a single image
	def save_multiple_plots(self):

		#copy the Figures to resize them beforehand (won't loose quality)
		images = []
		figs = [copy.deepcopy(plot.fig) for plot in self.plots]

		for fig in figs:

			#Modify height and width
			fig.set_figwidth(10)
			fig.set_figheight(10)

			#Cast to FigureCanvas
			canvas = FigureCanvasAgg(fig)
			canvas.draw()

			#Render to RGBA
			image = np.array(canvas.renderer.buffer_rgba())
			image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
			images.append(image)

		del figs

		#Initialize top and bottom image
		#> the plots are saved following this order:
		# 1 	2 	3 		-> top_image
		# 4 	5 	6 		-> bottom_image
		top_image = images[0]
		bottom_image = images[3] if len(images)>3 else None

		#Horizontally concatenate images
		for i, image in enumerate(images):

			if 0<i<3:
				top_image = cv2.hconcat([top_image, image])

			if i>3:
				bottom_image = cv2.hconcat([bottom_image, image])

		#Add bottom image to a canvas the same width of top_image to concatenate vertically
		if bottom_image is not None:
			canvas = np.full(top_image.shape, 255, dtype=np.uint8)
			canvas[:bottom_image.shape[0], :bottom_image.shape[1]] = bottom_image

		final_image = cv2.vconcat([top_image, canvas]) if bottom_image is not None else top_image


		#Save path file dialog
		filepath = os.path.join(self.root_dir, 'saved_scalars/plots')
		os.makedirs(filepath, exist_ok=True)

		filetypes = [("PNG Image File", "*.png"), ("Bitmap", "*.bmp"), ("JPEG File", "*.jpg"), ("All files", "*.*")]
		default_extension = '.png'

		file_path = tk.filedialog.asksaveasfilename(
			parent=None,
			initialdir=filepath,
			initialfile="plot.png",
			filetypes=filetypes,
			defaultextension=default_extension
		)

		if file_path:
			cv2.imwrite(file_path, final_image)		


	#Updates scalar tags listing them from the loaded ones
	#> Now tags with the same name followed by ' - 1:' will be grouped together 
	def update_tags(self, tags, full_tags):

		self.full_scalar_tags = full_tags   
		self.scalar_tags = tags 

		#Pattern to match multiple tags
		pattern = re.compile(r'.* - [123]$')

		triple_tags = []
		new_tags = []
		to_pop = []
		new_full_tags = []
		full_triple_tags = []

		#Search in every tag for matches and store tags and full tags in separate lists	
		for i, tag in enumerate(self.scalar_tags):

			if pattern.match(tag):

				triple_tags.append(tag)
				full_triple_tags.append(self.full_scalar_tags[i])
				to_pop.append(i)

		#Pop matching tas from original lists
		for i in reversed(to_pop):
			self.scalar_tags.pop(i)
			self.full_scalar_tags.pop(i)

		assert len(triple_tags) == len(full_triple_tags)

		#Create new entries for the OptionMenu
		for i in range(int(len(triple_tags)/3)):

			new_tags.append(triple_tags[i*3].strip(' - 1') + ' (3)')
			new_full_tags.append(full_triple_tags[i*3].strip(' - 1:') + ' (3)')

		#Extend the tag lists with the new entries and sort them in the same order
		#>the sort order is important for later retrieval
		self.scalar_tags.extend(new_tags)
		self.full_scalar_tags.extend(new_full_tags)

		sorted_indices = sorted(range(len(self.scalar_tags)), key=lambda i: self.scalar_tags[i])

		self.scalar_tags = [self.scalar_tags[i] for i in sorted_indices]
		self.full_scalar_tags = [self.full_scalar_tags[i] for i in sorted_indices]

		#Enable adding plots
		self.option_menu.state(["!disabled"])
		self.option_menu["menu"].delete(0,"end")
		self.add_butt.state(["!disabled"])

		#Load the new choices       
		for choice in tags:

			self.option_menu["menu"].add_command(label = choice, command=tk._setit(self.scalar_choice, choice))

		self.scalar_choice.set(self.scalar_tags[0])

	#Delete tags
	#>performed when loaded scalars are cleared
	def flush_tags(self):

		self.full_scalar_tags = []
		self.scalar_tags = []
		self.option_menu.state(["disabled"])
		self.add_butt.state(["disabled"])
		self.scalar_choice.set("")
		self.option_menu["menu"].delete(0,"end")
  





if __name__ == "__main__":

	root = tk.Tk()
	root.geometry('700x700')

	frame = ScrollableFrame(root, 20, 2, 300, 50)

	for i in range(50):
		ttk.Label(frame.scrollable_frame, text="Sample scrolling label").grid(column = 0,row =i)

	frame.pack()
	root.mainloop()