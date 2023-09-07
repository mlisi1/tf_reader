import tkinter as tk
from tkinter import ttk
import re
import copy

#==========INFO WINDOW=============
#Window with info on the scalar parameters 
class InfoWindow(tk.Toplevel):

	def __init__(self, parent, params, scalar_name):

		#Initialize toplevel
		self.parent = parent
		tk.Toplevel.__init__(self)
		self.protocol('WM_DELETE_WINDOW', self.on_destroy)
		self.wm_title('Session Info')
		self.geometry('225x605')
		self.resizable(tk.FALSE, tk.FALSE)


		self.scalar_name = scalar_name

		#Scalar name label
		self.name_label = ttk.Label(self, text = self.scalar_name, justify = tk.LEFT, anchor = tk.NW)
		self.name_label.place(x = 10, y = 10)
		self.separator = ttk.Separator(self,orient='horizontal')
		self.separator.place(x = 10, y = 55, width=200, height=2)

		#Initialize labels' values
		self.params = params
		self.strings = []
		self.get_strings()

		#Draw labels
		self.labels = []
		self.draw_info()

	#Method called on window closing
	def on_destroy(self):

		#Destroy every label
		for label in self.labels:

			label.destroy()

		#Reset parento toplevel and destroy
		self.parent.toplevel = None
		self.destroy()

	#Draw labels in the window
	def draw_info(self):

		for i in range(len(self.strings)):

			tmp = ttk.Label(self, text = self.strings[i], justify = tk.LEFT, anchor = tk.NW)
			tmp.place(x = 10, y = (60+20*i))

			self.labels.append(tmp)       

	#Retrieve strings from params dataclass
	def get_strings(self):

		#Dataclass method to get the string
		parameters = self.params.render_to_string().split(', ')

		for par in parameters:

			#Remove unnecessary characters and find matches
			par = par.strip('< ')
			par = par.strip(' >')
			match = re.search(r'(.+): (.+)', par)

			if match:

				#Create string
				attr_name, attr_value = match.groups()
				self.strings.append(f'{attr_name} : {attr_value}\n')


	



#================== SELECT SCALAR WINDOW =====================
#Window used to select scalar(s) to add to the plot
class SelectScalarWin(tk.Toplevel):

	def __init__(self, parent):

		#Initialize window
		self.parent = parent
		tk.Toplevel.__init__(self)
		self.protocol('WM_DELETE_WINDOW', self.on_destroy)
		self.wm_title('Select Scalar')
		self.resizable(tk.FALSE, tk.FALSE)

		#Variables used to show only available entries when selecting a model or a reward
		self.available_rewards = []
		self.available_sizes = []
		self.model_trace = None
		self.reward_trace = None
		self.updating_entries = False

	   
		#>All variables for the choice are handled in the caller to mantain persistency in different instances
		#Model Tag option Menu and Label
		self.model_option_label = tk.Label(self, text = "Model Tags:")
		self.model_option_label.grid(row = 0, column = 0, sticky = "NW", padx = 10, pady = 3)
		self.model_options = ttk.OptionMenu(self, variable = self.parent.model_choice)
		self.model_options.config(width = 23)
		self.model_options.grid(row = 1, column = 0, sticky = "NW", padx = 10, pady = 3)

		#Reward Tag option Menu and Label
		self.reward_option_label = tk.Label(self, text = "Reward Tags:")
		self.reward_option_label.grid(row = 2, column = 0, sticky = "NW", padx = 10, pady = 3)
		self.reward_options = ttk.OptionMenu(self, self.parent.reward_choice)
		self.reward_options.config(width = 23)
		self.reward_options.grid(row = 3, column = 0, sticky = "NW", padx = 10, pady = 3)   
		
		#Network size option Menu and Label initialization
		self.size_label = ttk.Label(self, text  = "Network Size:")
		self.size_label.grid(row = 4, column = 0, sticky = "NW", padx = 10, pady = 3)
		self.size_options = ttk.OptionMenu(self, self.parent.size_choice, command = self.choose_size)
		self.size_options.grid(row = 5, column = 0, sticky = "NW", padx = 10, pady = 3)
		self.size_options.config(width = 23)

		#Select Button
		self.select_butt = ttk.Button(self, text = "Select", command = self.select_scalar)
		self.select_butt.place(x = 80, y = 260)
		self.select_butt.grid(row = 6, column = 0, sticky = "NWES", padx = 70, pady = (30, 10))

		self.update_entries()
		self.on_model_tag_change()

	#Method called on window destroy
	def on_destroy(self):

		self.parent.toplevel = None
		self.destroy()

		#Remove variable trace function binding
		self.parent.model_choice.trace_remove('write', self.model_trace)
		self.parent.reward_choice.trace_remove('write', self.reward_trace)


	#Size choice handling function
	def choose_size(self, choice):


		if choice == "All":
			#Set [0,0] as "special" size to select All sizes
			self.parent.chosen_batch = 0
			self.parent.chosen_hid = 0

		else:

			#Cast the specified size in int
			sizes = choice.split(',')
			self.parent.chosen_batch = int(sizes[1])
			self.parent.chosen_hid = int(sizes[0])

	#Method for the Select Scalar button
	def select_scalar(self):

		#Add scalar to plot and destroy window
		e = self.parent.append_scalar()
		self.on_destroy()

		if e == -1:
			tk.messagebox.showerror("Error", "Some scalars have invalid data")



	#Update menu entries if a new scalar has been externally loaded
	def update_entries(self, from_model = False, from_reward = False):

		#Save last choice and reset options
		last_choice = self.parent.model_choice.get()
		self.parent.model_choice.set("")
		self.model_options["menu"].delete(0,"end")

		#Load the new choices       
		for choice in self.parent.available_models:
			self.model_options["menu"].add_command(label = choice, command=tk._setit(self.parent.model_choice, choice))

		#Find the "new" last choice and set it
		idx = [i for i, choice in enumerate(self.parent.available_models) if choice == last_choice][0]
		last_model_choice = self.parent.available_models[idx]
		self.parent.model_choice.set(last_model_choice)



		#Save last choice and reset options
		last_choice = self.parent.reward_choice.get()
		self.parent.reward_choice.set("")
		self.reward_options["menu"].delete(0,"end")   

		#Load the new choices 
		#>if from_model == True => load only available rewards  
		if from_model: 
			for choice in self.available_rewards:
				self.reward_options["menu"].add_command(label = choice, command=tk._setit(self.parent.reward_choice, choice))

			if last_choice != all(self.available_rewards):
				last_choice = self.available_rewards[0]
		else:
			for choice in self.parent.available_rewards:
				self.reward_options["menu"].add_command(label = choice, command=tk._setit(self.parent.reward_choice, choice))

		#Find the "new" last choice and set it
		idx = [i for i, choice in enumerate(self.parent.available_rewards) if choice == last_choice][0]
		last_reward_choice = self.parent.available_rewards[idx]
		self.parent.reward_choice.set(last_reward_choice)



		#Save last choice and reset options
		last_choice = self.parent.size_choice.get()
		self.parent.size_choice.set("")
		self.size_options["menu"].delete(0,"end")      

		#Load the new choices 
		#>if from_reward == True => load only available sizes
		if from_reward: 
			for choice in self.available_sizes:
				self.size_options["menu"].add_command(label = choice, command=tk._setit(self.parent.size_choice, choice))

			# if last_choice != all(self.available_sizes):
			last_choice = self.available_sizes[0]
		else:

			for choice in self.parent.sizes:
				self.size_options["menu"].add_command(label = choice, command=tk._setit(self.parent.size_choice, choice))
		
		self.parent.size_choice.set(last_choice)
		self.updating_entries = False

	#Trace binded function; changes the entries of the reward OptionMenu to the available
	# ones for the chosen model
	#>Gets called every time an entry from the model tag OptionsMenu is selected
	def on_model_tag_change(self, *args):

		#Chek if other updates are performed
		if self.updating_entries == False:

			self.updating_entries = True
			self.available_rewards = []

			#Get selected model tags
			choice = self.parent.model_choice.get()

			if choice != "All":

				choice = choice.strip("Ant ")

				#Retrieve available reward tags from SessionLoader dict
				for rew_tag in self.parent.loader.model_dict.get(choice):

					rew = rew_tag.split('|')[1]
					self.available_rewards.append(rew)

				self.available_rewards.append("All")

				#Update entries skipping model
				self.update_entries(from_model = True)

			else:

				self.update_entries()


	#Trace binded function; changes the entries of the size OptionMenu to the available
	# ones for the chosen model+rewards
	#>Gets called every time an entry from the reward tag OptionsMenu is selected
	def on_reward_tag_change(self, *args):

		#Check if other updates are performed
		if self.updating_entries == False:

			self.updating_entries = True
			self.available_sizes = []

			#Get selected reward choice
			choice = self.parent.reward_choice.get()

			if choice != "All":

				choice = self.parent.model_choice.get() + choice

				#Retrieve available sizes from SessionLoader dict
				for size_tag in self.parent.loader.size_dict.get(choice):

					entry = f"{size_tag[0]}, {size_tag[1]} ({size_tag[-1]})"
					self.available_sizes.append(entry)

				self.available_sizes.append("All")

				#Update entries skipping model and reward
				self.update_entries(from_reward = True)

			else:

				self.update_entries()



#================== PREFERENCES =====================
#Window used to hold and choose all the preferences
#>still in development
class Preferences(tk.Toplevel):

	def __init__(self, parent):

		super().__init__()
		tk.Tk.wm_title(self, "Preferences")
		self.protocol('WM_DELETE_WINDOW', self.close)
		self.resizable(tk.FALSE, tk.FALSE)
		self.geometry("250x150")

		self.parent = parent

		self.order_label = ttk.Label(self, text = "Order scalars based on tag:")
		self.order_label.grid(row = 0, column = 0, padx = 10, pady = 5)

		self.order_choice = tk.StringVar()
		self.scalar_tags = copy.deepcopy(self.parent.plot_container.full_scalar_tags)
		self.order_menu  = ttk.OptionMenu(self, self.order_choice, self.scalar_tags[0], *self.scalar_tags)
		self.order_menu.config(width = 23)
		self.order_menu.grid(row = 1, column = 0, padx = 20, pady = 5)


		self.save_butt = ttk.Button(self, text = "Save", command = self.save)
		self.save_butt.grid(row = 10, column = 0, padx = 15, pady = 10, sticky = "NW")

		self.close_butt = ttk.Button(self, text = "Close", command = self.close)
		self.close_butt.grid(row = 10, column = 0, padx = 15, pady = 10, sticky = "NE")

	#Apply preferences
	def save(self):

		if not self.order_choice.get() == '':
			
			self.parent.order_choice = self.order_choice.get()

		else:

			self.parent.order_choice = None

		self.parent.update_scalar_labels()

		self.close()

	def close(self):

		self.parent.toplevel = None

		self.destroy()
