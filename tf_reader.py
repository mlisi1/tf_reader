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
from loaded_scalar import LoadedScalar
from sessionloader import SessionLoader
from scalar_widgets import ScrollableFrame, PlotHandler
from toplevels import InfoWindow, SelectScalarWin, Preferences




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

		self.root_dir = os.getcwd()

		self.menu_bar = tk.Menu(self)
		self.file_menu = tk.Menu(self.menu_bar, tearoff = 0)
		self.file_menu.add_command(label = "Add single training folder", command = self.add_training_dir_bringup)
		self.file_menu.add_command(label = "Add tag folder", command = self.add_tag_dir_bringup)

		self.config_menu = tk.Menu(self.menu_bar, tearoff = 0)
		self.config_menu.add_command(label = "Preferences", command = self.preferences_bringup)

		self.order_choice = None		

		self.menu_bar.add_cascade(labe = "File", menu = self.file_menu)
		self.menu_bar.add_cascade(labe = "Config", menu = self.config_menu)

		self.config(menu = self.menu_bar)

		#Scalar list frame initialization
		self.scalar_container = ScrollableFrame(self, 20, 2, width = 300, height = 400)
		self.scalar_container.grid(row = 0, column = 2, sticky = "E", pady = (100, 20), padx = (0, 10))         

		#Save button
		self.save_butt = ttk.Button(self, text = "Save scalar data", command = self.save_scalar_data)
		self.save_butt.state(["disabled"])
		self.save_butt.grid(row = 0, column = 2, pady = 30, sticky = "SE", padx = (20, 20))

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

		#Button to add scalars initialization
		self.add_scalar_button = ttk.Button(self, text = "Add Scalar", command = self.add_scalar_fn)
		self.add_scalar_button.grid(row = 0, column = 2, sticky = "NE", pady = 100, padx = (0,180))

		#Button to clear the plot
		self.clear_button = ttk.Button(self, text = "Clear", command = self.clear)
		self.clear_button.grid(row = 0, column = 2, sticky = "NE", pady = 100, padx = (0,50))

		#Toplevel variable; used to only allow one additional window at a time
		self.toplevel = None		

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

		for scalar in LoadedScalar.get_loaded_scalars():		

			for tag in scalar.scalar['tag']:

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
	#Clears the plots and deletes scalar labels
	def clear(self):

		for i in range(len(LoadedScalar.get_loaded_scalars())):

			scalars = LoadedScalar.get_loaded_scalars()

			scalars[0].label.remove_lines()

		self.plot_container.flush_tags()

	#Standard plot update method: redraws the plot and updates existing scalar label's line variable
	def update_plot(self, smooth_value):

		#Update smooth value label
		self.smooth_value_label.config(text = f'{self.get_smooth_value:.2f}')

		#Update plots
		self.plot_container.update_plots(self.get_smooth_value)


	#================GUI ELEMENT UPDATE FUNCTIONS================================
	#Updates the labes by destroying and recreating according to the scalars
	def update_scalar_labels(self):

		max_values = [scalar.get_max(self.order_choice) for scalar in LoadedScalar.get_loaded_scalars()]
		indexes = np.argsort(max_values)[::-1]

		loaded_scalars = LoadedScalar.get_loaded_scalars()
		loaded_scalars = [loaded_scalars[i] for i in indexes]

		for i, scalar in enumerate(loaded_scalars):

			scalar.remove_gui()

			fns = [plot.fast_update for plot in self.plot_container.plots]
			scalar.swap_functions(fns)		

		
			scalar.restore_gui(i)

			scalar.label.on_leave(None)

	#Updtaes OptionMenu entries
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

	#Bringup for path asking window; used to load external tag folder (multiple trainings that only differ net sizes)
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

	#Bringup for preferences menu
	def preferences_bringup(self):

		if self.toplevel is None:

			self.toplevel = Preferences(self)

		else:

			self.toplevel.lift()  


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

				scalar, name, params = tmp    
				fns = [plot.fast_update for plot in self.plot_container.plots]
				new_scalar = LoadedScalar(scalar, params, name, self.scalar_container.scrollable_frame, fns)

			else:

				raise_err = True       
 
			#Activate save button
			self.save_butt.state(["!disabled"])                   


		#Update plot
		if self.plot_container is not None:

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
	  
		loaded_scalars = LoadedScalar.get_loaded_scalars()

		if len(loaded_scalars) > 1:

			with open(file_path, 'w') as f:

				criterion = "Max Test Avg:" if self.order_choice == None else f'Max {self.order_choice}'

				#Write relevant infos
				f.write("Scalars Plotted:\n")      
				for scalar in loaded_scalars:

					name = scalar.scalar_name.split('\n')
					max_value = scalar.max_value if scalar.max_value != -1000 else "NO DATA"

					f.write(f'{name[0]}|{name[1]}  			 {criterion} {max_value}\n')

