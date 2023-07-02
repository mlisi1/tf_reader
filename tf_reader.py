import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import re
from functools import partial
import datetime
import numpy as np
import copy

#GUI
import tkinter as tk
from tkinter import ttk

#local imports
from sessionloader import SessionLoader
from scalar_widgets import ScrollableFrame, ScalarLabel, PlotHandler
from toplevels import InfoWindow, SelectScalarWin




#Main application class
class TFReaderWin(tk.Tk):

	def __init__(self, workdir):

		#Main window initialization
		self.running = True
		tk.Tk.__init__(self)
		tk.Tk.wm_title(self, "TF Reader")
		self.tk.call("source", "azure.tcl")
		self.tk.call("set_theme", "light")
		self.geometry("950x650")
		self.protocol('WM_DELETE_WINDOW', self.on_destroy)
		self.grid_rowconfigure(0, weight=20)
		self.grid_columnconfigure(0, weight = 30)

		self.rm_icon = tk.PhotoImage(file = './icons/minus.gif')

		self.root_dir = os.getcwd()

		self.menu_bar = tk.Menu(self)
		self.file_menu = tk.Menu(self.menu_bar, tearoff = 0)
		self.file_menu.add_command(label = "Add single training folder", command = self.add_training_dir_bringup)
		self.file_menu.add_command(label = "Add tag folder", command = self.add_tag_dir_bringup)

		self.menu_bar.add_cascade(labe = "File", menu = self.file_menu)
		self.config(menu = self.menu_bar)


		#Scalar list frame initialization
		self.scalar_container = ScrollableFrame(self, 20, 2, width = 300, height = 400)
		self.scalar_container.grid(row = 0, column = 2, sticky = "E", pady = (100, 20), padx = (0, 10))         

		#Save button
		self.save_butt = ttk.Button(self, text = "Save scalar data", command = self.save_scalar_data)
		self.save_butt.state(["disabled"])
		self.save_butt.grid(row = 0, column = 2, pady = 30, sticky = "SE", padx = (20, 20))

		#Array of scalars and their relative parameters
		self.scalars = []
		self.params = []
		self.max_values = []

		#SessionLoader; handles workdir scanning and file loading/parsing
		self.loader = SessionLoader(workdir)
		self.loader.parse_sessions()
		self.loader.update_size_dict()

		#Model choice variables
		self.available_models = copy.copy(self.loader.model_tags)
		self.available_models.append("All")
		self.model_choice = tk.StringVar()
		self.model_choice.set(self.available_models[0])

		#Size choice variables
		self.sizes = copy.copy(self.loader.size_tags)
		self.sizes.append("All")
		self.size_choice = tk.StringVar()
		self.size_choice.set(self.sizes[0])
	
		#Reward choice variables
		self.available_rewards = copy.copy(self.loader.reward_tags)
		self.available_rewards.append("All")        
		self.reward_choice = tk.StringVar()
		self.reward_choice.set(self.available_rewards[0])

		#Scalar list GUI arrays
		self.scalar_labels = []
		self.scalar_buttons = []
		self.remove_buttons = []
		self.scalar_names = []

		#Button to add scalars initialization
		self.add_scalar_button = ttk.Button(self, text = "Add Scalar", command = self.add_scalar_fn)
		self.add_scalar_button.grid(row = 0, column = 2, sticky = "NE", pady = 100, padx = (0,180))

		#Button to clear the plot
		self.clear_button = ttk.Button(self, text = "Clear", command = self.clear)
		self.clear_button.grid(row = 0, column = 2, sticky = "NE", pady = 100, padx = (0,50))

		#Toplevel variable; used to only allow one additional window at a time
		self.toplevel = None
		
		#calls the SessionLoader to attempt a first load for initialization purposes
		self.frame = None
		self.plot_container = None
		  

		#Model tag choice variables initialization
		self.tags = [""]
		self.full_tags = [""]

		#Plot Handler class; hadles plot adding, removing and rescaling
		self.plot_container = PlotHandler(self, self.tags, self.full_tags)
		self.plot_container.grid(row = 0, column = 0, sticky = "NW") 


		self.save_plots_button = ttk.Button(self, text = "Save Plots", command = self.plot_container.save_multiple_plots)
		self.save_plots_button.grid(row = 0, column = 2, padx = (0, 170), sticky = "SE", pady = 30)       

		#Smooth variable and slider initialization
		self.smooth_value = tk.DoubleVar()
		self.smooth_value_label = ttk.Label(self, text = str(self.get_smooth_value))
		self.smooth_value_label.grid(row = 0, column = 2, sticky = "NE", pady = 20, padx = (0,170))
		self.slider_label = ttk.Label(self, text = "Smooth Value:")
		self.slider_label.grid(row = 0, column = 2, sticky = "NE", pady = 20, padx = (0,200))
		self.slider = ttk.Scale(self, from_ = 0.0, to = 0.99, variable = self.smooth_value,
						orient = tk.HORIZONTAL, command = self.update_plot, length = 200)
		self.slider.grid(row = 0, column = 2, sticky = "NE", pady = 60, padx = (0,70))

		#Bind resizing function
		self.bind("<Configure>", self.on_resize) 
		self.previous_size = (950, 650)

		#Attempt a first resize to inizialize some values      
		self.on_resize(None)
 



	#======GETTER AND SETTERS=========== 
	#Retrieves the set of tags found in the scalar
	def get_tags(self):

		self.tags = []
		self.full_tags = []

		for tag in self.scalars[0]['tag']:

			short_tag = tag[7:-1]

			if short_tag not in self.tags:
				
				self.tags.append(short_tag)
				self.full_tags.append(tag)
   
	#Gets the chosen smooth value from the slider widget
	@property
	def get_smooth_value(self):
		return float(self.smooth_value.get())

	#Setter for the slider; never used   
	def set_smooth_value(self, value):
		self.smooth_value.set(value)

	#Gets the chosen size
	@property
	def get_size_choice(self):
		if self.size_choice.get() == "All":
			return (0, 0)
		sizes = re.findall(r'\w+', self.size_choice.get())
		return (int(sizes[0]), int(sizes[1]))

	#===========TK WINDOW FUNCTIONS===========
	#Used when quitting main window; self.running is used to stop the main loop
	def on_destroy(self):
		if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
			self.destroy()
			self.quit()
			self.running = False

	#Just a convenient gruping for tkinter update functions; to be used instead of mainloop()
	def update_gui(self):

		#Check if new scalars are added to update tags choice menu entries
		if self.loader.entries_update:
			self.update_menu_entries()
		#Checks if a label has been triggered for removal
		if len(self.scalar_labels)>1:
			for i, label in enumerate(self.scalar_labels):
				if label.removed:
					self.on_line_remove(i)
					break
		#If there is only one line, simply clear all
		elif len(self.scalar_labels)==1:
			if self.scalar_labels[0].removed:
				self.clear()

		#If there are no plots, disable save plot button
		if len(self.plot_container.plots) == 0:
			self.save_plots_button.state(["disabled"])
		else:
			self.save_plots_button.state(["!disabled"])

		if self.plot_container is not None:
			if self.plot_container.need_to_update:
				self.update_plot(self.get_smooth_value)
				self.plot_container.need_to_update = False
				self.update_scalar_labels()
		self.update_idletasks()
		self.update()

	#Calls the PlotHandler resize function and resizes Scrollable Frame
	def on_resize(self, event):

		#Update to get the current values
		self.update()
		curr_size = (self.winfo_width(), self.winfo_height())

		if self.previous_size != curr_size:

			self.plot_container.on_resize(curr_size)
			self.scalar_container.canvas.config(height = curr_size[1]-250)

		self.previous_size = curr_size

	#==============PLOT HIGH LEVEL FUNCTIONS===============
	#Clears the plot, scalar labels and resets attributes
	def clear(self):

		#Delete attributes and re-initialize them
		del self.scalars 
		del self.scalar_names
		del self.params 
		del self.max_values
		self.scalars = []
		self.scalar_names = []
		self.params = []
		self.max_values = []

		#Deactivate save button
		self.save_butt.state(["disabled"])

		#The low level clear function
		self.plot_container.clear()
		self.plot_container.flush_tags()

		#Clear the scalar labels
		self.update_scalar_labels()




	#Standard plot update method: redraws the plot and updates existing scalar label's line variable
	def update_plot(self, smooth_value):

		#Update smooth value label
		self.smooth_value_label.config(text = f'{self.get_smooth_value:.2f}')

		#Update plots
		self.plot_container.update_plots(self.get_smooth_value)        
		
		#Update scalar labels lines   
		for i in range(len(self.scalar_labels)):
			if len(self.plot_container.plots) > 0:
				lines = [plot.line[i] for plot in self.plot_container.plots]
				updates = [plot.fast_update for plot in self.plot_container.plots]

			else:

				lines = None
				updates = None

			self.scalar_labels[i].update_lines(lines, updates)

	#================GUI ELEMENT UPDATE FUNCTIONS================================
	#Updates the labes by destroying and recreating according to the scalars
	def update_scalar_labels(self):

		#If there are labels, destroy them
		if len(self.scalar_labels) > 0:            
			for i in range(len(self.scalar_labels)):
				self.scalar_labels[i].destroy()
				self.scalar_buttons[i].destroy()
				self.remove_buttons[i].destroy()
			self.scalar_labels = []
			self.scalar_buttons = []
			self.remove_buttons = []
		
		#index used if some scalars does not have valid data
		j = 0

		#If there are scalars, create labels and buttons
		if len(self.scalar_names) > 0:
			for i in range(len(self.scalar_names)):

				#Gather lines and correct update functions
				if len(self.plot_container.plots) > 0:
					lines = [plot.line[i] for plot in self.plot_container.plots]
					updates = [plot.fast_update for plot in self.plot_container.plots]

				else:

					lines = None
					updates = None

 
				#instantiate ScalarLabel class; uses fast update method instead of normal update
				tmp = ScalarLabel(self.scalar_container.scrollable_frame, text = f'{self.scalar_names[i]}', lines = lines, update_fns = updates)
				tmp.grid(column = 0, row = j, sticky = "NW")

				#create partial for instancing the Info window; for some reason lambda definition was not working
				cmd = partial(self.info_win_bringup, self.params[i], self.scalar_names[i])
				

				#instantiate Info Button                
				tmp_butt = ttk.Button(self.scalar_container.scrollable_frame, text = "Info", width = 4, command = cmd)              
				tmp_butt.grid(column = 1, row = j, padx = 5)

				tmp_rm = ttk.Button(self.scalar_container.scrollable_frame, image = self.rm_icon, width = 5, command = tmp.remove_lines)
				tmp_rm.grid(column = 2, row = j, padx = 5)

				#update button and labels list
				self.scalar_labels.append(tmp)
				self.scalar_buttons.append(tmp_butt)
				self.remove_buttons.append(tmp_rm)
				j+=1


	#Method called on line removal; clears variables and updates scalar labels
	def on_line_remove(self, index = 0):

		#Remove label
		self.scalar_labels[index].grid_remove()
		self.scalar_labels[index].destroy()
		self.scalar_labels.pop(index)

		#Remove Info button
		self.scalar_buttons[index].grid_remove()
		self.scalar_buttons[index].destroy()
		self.scalar_buttons.pop(index)

		#Remve remove buttons
		self.remove_buttons[index].grid_remove()
		self.remove_buttons[index].destroy()
		self.remove_buttons.pop(index)

		#Pop removed scalar values
		#>popping self.scalars[index] removes it also from PlotHandler.plots
		self.scalar_names.pop(index)
		self.params.pop(index)
		self.max_values = np.delete(self.max_values, index)
		self.scalars.pop(index)

		#Call other update functions
		self.plot_container.remove_line(index)
		self.update_plot(self.get_smooth_value)
		self.update_scalar_labels()



	def update_menu_entries(self):

		#Model choice variables
		self.available_models = copy.copy(self.loader.model_tags)
		self.available_models.append("All")

		#Size choice variables
		self.sizes = copy.copy(self.loader.size_tags)
		self.sizes.append("All")
	
		#Reward choice variables
		self.available_rewards = copy.copy(self.loader.reward_tags)
		self.available_rewards.append("All")        

		self.loader.entries_update = False
		





	#===================TOPLEVEL BRINGUP FUNCTIONS=========================
	#Bringup Select Scalar Window if there is no toplevel already
	def add_scalar_fn(self):

		if self.toplevel == None:

			self.toplevel = SelectScalarWin(self)

			#Add tracing for choice variables
			trace_id = self.model_choice.trace('w', self.toplevel.on_model_tag_change)
			self.toplevel.model_trace = trace_id
			trace_id = self.reward_choice.trace('w', self.toplevel.on_reward_tag_change)
			self.toplevel.reward_trace = trace_id

		else:

			self.toplevel.lift()

	#Bringup Info window if there is no toplevel already; instantiated by every Info button
	def info_win_bringup(self, params, scalar_name):

		if self.toplevel is None:

			self.toplevel = InfoWindow(self, params, scalar_name)

		else:

			self.toplevel.lift()

	#Bringup for path asking window; used to load external scalars
	def add_training_dir_bringup(self):

		folder_path = tk.filedialog.askdirectory(title = "Load scalar from directory",
						initialdir = self.root_dir,
						mustexist = True)

		#Append the new session if valid
		tmp = self.loader.generate_session(folder_path, from_gui = True)

		#SessionLoader.generate_session() returns -1 in case of any failure
		# while preprocessing data
		if tmp == -1:
			tk.messagebox.showerror("Error", "The selected folder does not contain a valid scalar.")


	def add_tag_dir_bringup(self):

		folder_path = tk.filedialog.askdirectory(title = "Load scalars from tag directory",
						initialdir = self.root_dir,
						mustexist = True)

		#Append the new session if valid
		try:
			self.loader.parse_sessions(folder_path)

		except Exception as e:

			tk.messagebox.showerror("Error", "The selected folder is not a valid tag directory.")

		#SessionLoader.generate_session() returns -1 in case of any failure
		# while preprocessing data
	  






	#======================LOAD FUNCTIONS =====================================
	#Load scalar from selected session(s) and update plot
	def append_scalar(self):

		#Trigger to remove corrupted or invalid scalars
		raise_err = False
		to_remove = []

		#Retrieve [scalars, scalar_name, params] from SessionLoader
		scalar_iter = self.loader.get_scalar_from_tags(self.model_choice.get(), self.reward_choice.get(), self.get_size_choice[1], self.get_size_choice[0])
		
		#Update scalar related variables      
		for tmp in scalar_iter:           
			
			if 'tag' in tmp[0].keys():

				self.scalars.append(tmp[0])
				self.scalar_names.append(tmp[1])
				self.params.append(tmp[2])     

			else:

				raise_err = True       

		if len(self.scalars) > 1:
			
			#Append max average reward during test for each scalar
			max_test_value = np.empty(0)
			for i in range(len(self.scalars)):
				
				for j, tag in enumerate(self.scalars[i]['tag']):

					if "Avg" in tag and "Network" in tag and "Test" in tag and not "Best" in tag:

						x = self.scalars[i][self.scalars[i]['tag'].values == tag]
						max_test_value = np.append(max_test_value, x['value'].values[-1])
						break

					#Handles when the tag is not found
					#>could be caused by a training never finished
					else:
						
						if j == len(self.scalars[i]['tag']) - 1:                        

							max_test_value = np.append(max_test_value, -1000)
			


			#Sort the array and get the indexes
			indexes = np.argsort(max_test_value)[::-1] 
			self.max_values = np.sort(max_test_value)[::-1]
				 
			self.scalars = [self.scalars[i] for i in indexes]
			self.scalar_names = [self.scalar_names[i] for i in indexes]
			self.params = [self.params[i] for i in indexes]   

			#Activate save button
			self.save_butt.state(["!disabled"])                   


		#Update plot
		if self.plot_container is not None:

			self.plot_container.scalars = self.scalars
			self.update_plot(self.get_smooth_value)
			self.update_scalar_labels()
			self.get_tags()
			self.plot_container.update_tags(self.tags, self.full_tags)


		return -1 if raise_err else 0




	#======================SAVE FUNCTIONS =====================================
	#Saves currently plotted scalars to a .txt file
	def save_scalar_data(self):

		#Use datetime for filename
		dt = datetime.datetime.now()     
		dt_str = dt.strftime("%Y-%m-%d-%H-%M-%S")
		filename = f"scalars-{dt_str}.txt"
		filepath = os.path.join(self.root_dir, 'saved_scalars')

		#If the dirs doesn't exist, create it
		if not os.path.isdir(filepath):
			os.mkdir(filepath)

		#Save dialog window
		file_path = tk.filedialog.asksaveasfilename(parent = self, initialdir = filepath, initialfile = filename, 
					filetypes=(("Text files", "*.txt"), ("All files", "*.*")), defaultextension = '.txt')
	  

		if len(self.scalars) > 1:

			with open(file_path, 'w') as f:

				#Write relevant infos
				f.write("Scalars Plotted:\n")      
				for i in range(len(self.scalars)):

					scalar_tag = re.sub(r'Ant-v4-', "",self.frame.scalar_name[i]).strip(':').strip('\n')
					name = self.scalar_names[i].split('\n')

					f.write(f'{name[0]}{name[1]}   Max Test Avg: {self.max_values[i]}   Scalar Tag: {scalar_tag}\n')


			

		







	