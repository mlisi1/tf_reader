from tkinter import ttk
import tkinter as tk
from functools import partial
from toplevels import InfoWindow
import numpy as np

#====================LOADED SCALAR====================
#Represents every loaded scalar an its associated label.
#Has a reference to the data, the lines plotted, the color and
#the parameters 
class LoadedScalar:

	#Existing instances of the class
	instances = []

	def __init__(self, scalar, params, scalar_name, container, update_functions):

		#Initialize attributes
		self.scalar = scalar
		self.params = params
		self.scalar_name = scalar_name		
		self.lines = {}
		self.points = None
		self.color = None
		self.max_value = None
		self.data = {}
		self.update_functions = update_functions

		#Instantiate ScalarLabel class
		self.label = ScalarLabel(container, self.scalar_name, self)

		LoadedScalar.instances.append(self)

		self.get_max(None)

	#Forgets every line in the dict
	def clear_all_lines(self):

		del self.lines
		self.lines = {}

	#Destroy method; removes itself from the instances list
	def destroy(self):

		self.label.destroy()
		LoadedScalar.instances.remove(self)

	#Load data with specific tag
	def update_data_dict(self, scalar_choice):

		if type(scalar_choice) == list:

			data = [self.scalar[self.scalar['tag'] == scalar_choice[j]] for j in range(len(scalar_choice))]
			self.data[scalar_choice[0]] = data  

		else:	
			 
			data = self.scalar[self.scalar['tag'] == scalar_choice]   
			self.data[scalar_choice] = data   

		#Create entry for points
		if "[Point]" not in self.data.keys():

			point_tag = [tag for tag in self.scalar['tag'] if '[Point]' in tag]
			
			if len(point_tag)>0:

				data = self.scalar[self.scalar['tag'] == point_tag[0]]
				self.data['[Point]'] = data

	@classmethod
	#Used to retrive by other classes all existing loaded scalars
	def get_loaded_scalars(self):

		return LoadedScalar.instances 

	#Deletes a specific line from the line dict
	def clear_lines(self, scalar_choice):

		if type(scalar_choice) == list:

			if scalar_choice[0] in self.lines.keys():

				del self.lines[scalar_choice[0]]

		else: 

			del self.lines[scalar_choice]

	#Adds line(s) to the line dict
	def add_line(self, scalar_choice, line):

		if scalar_choice in self.lines.keys():

			#The '+' if for multiple plots of the same tag
			self.lines[scalar_choice+'+'] = line

		else:

			self.lines[scalar_choice] = line

	#Updates self.max_value based on the tag (order_choice)
	# >It's thought for plots of average values, so the value
	#  considered max is the one belonging to the last epoch
	def get_max(self, order_choice):


		for j, tag in enumerate(self.scalar['tag']):

			if order_choice == None:

				if "Avg" in tag and "Network" in tag and "Test" in tag and not "Best" in tag:

					x = self.scalar[self.scalar['tag'].values == tag]
					max_value = x['value'].values[-1]
					break

				#Handles when the tag is not found
				#>could be caused by a training never finished
				else:
					
					if j == len(self.scalar['tag']) - 1:                        

						max_value = -1000

			else:

				if '(3)' in order_choice:

					new_key = order_choice.strip(' (3)') 
					key = [(new_key + f' - {i}:') for i in range(1,4)][0]
					

				else:
							      
					key = order_choice

				x = self.scalar[self.scalar['tag'].values == key]

				if len(x) > 0:

					max_value = x['value'].values[-1]
					break

				else:

					max_value = -1000
					break

		self.max_value = max_value
		return self.max_value

	#Detaches its label GUI element from root 
	def remove_gui(self):

		self.label.grid_remove()
		self.label.info_button.grid_remove()
		self.label.remove_button.grid_remove()

	#Places GUI element associated to its label
	def restore_gui(self, row):

		self.label.grid(row = row, column = 0)
		self.label.info_button.grid(row = row, column = 1)
		self.label.remove_button.grid(row = row, column = 2)

	#Fast update method; redraws plot canvas
	def fast_update(self):

		plot_container = self.label.master.master.master.master.plot_container
		plot_container.fast_update()


	#Bringup Info window if there is no toplevel already; instantiated by every Info button
	def info_win_bringup(self, params, scalar_name):

		toplevel = self.label.master.master.master.master.toplevel

		if toplevel == None:

			toplevel = InfoWindow(self, params, scalar_name)

		else:

			toplevel.lift()





#======================== SCALAR LABELS ======================
#Conveniently defined labels with hover methods
class ScalarLabel(ttk.Label):

	def __init__(self, container, label, parent):

		font = ("Verdana", 9)
		super().__init__(container, text = label, font = font)
		self.parent = parent
		self.rm_icon = tk.PhotoImage(file = './icons/minus.gif')

		self.configure(foreground = self.parent.color if not self.parent.color == None else '#000000')

		self.bind("<Enter>", self.on_enter)       
		self.bind("<Leave>", self.on_leave)

		info = partial(self.parent.info_win_bringup, self.parent.params, label)

		self.info_button = ttk.Button(container, text = "Info", width = 4, command = info)
		self.remove_button = ttk.Button(container, image = self.rm_icon, width = 5, command = self.remove_lines)


	#Hover functions
	def on_enter(self, event):

		self.configure(foreground = '#000000')
		for i, key in enumerate(self.parent.lines.keys()):


			if key == '[Point]':

				continue

			value = self.parent.lines[key]

			if not value == None:

				if type(value) == list:

					for line in value:

						line.set_linewidth(3)

				else:

					value.set_linewidth(3)

		self.parent.fast_update()


	#Hover functions
	def on_leave(self, event):

		self.configure(foreground = self.parent.color)
		for i, key in enumerate(self.parent.lines.keys()):


			if key == '[Point]':

				continue

			value = self.parent.lines[key]

			if not value == None:

				if type(value) == list:

					for line in value:
			
						line.set_linewidth(1)

				else:

					value.set_linewidth(1)

			

		self.parent.fast_update()



	#Removes this scalar label's lines
	def remove_lines(self):

		#Undraw lines
		for i, key in enumerate(self.parent.lines.keys()):

			value = self.parent.lines[key]
		
			if key == '[Point]':

				value.remove()
				continue
			

			if not value == None:

				if type(value) == list:

					for line in value:

						line.remove()

				else:

					value.remove()

		self.parent.fast_update()

		self.info_button.destroy()
		self.remove_button.destroy()		
		self.parent.destroy()

	