import tkinter as tk
from tkinter import ttk
import re

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
       
        #>All variables for the choice are handled in the caller to mantain persistency in different instances
        #Model Tag option Menu and Label
        self.model_option_label = tk.Label(self, text = "Model Tags:")
        self.model_option_label.grid(row = 0, column = 0, sticky = "NW", padx = 10, pady = 3)
        self.model_options = ttk.OptionMenu(self, self.parent.model_choice, self.parent.model_choice.get(), *self.parent.available_models)
        self.model_options.config(width = 23)
        self.model_options.grid(row = 1, column = 0, sticky = "NW", padx = 10, pady = 3)

        #Reward Tag option Menu and Label
        self.reward_option_label = tk.Label(self, text = "Reward Tags:")
        self.reward_option_label.grid(row = 2, column = 0, sticky = "NW", padx = 10, pady = 3)
        self.reward_options = ttk.OptionMenu(self, self.parent.reward_choice, self.parent.reward_choice.get(), *self.parent.available_rewards)
        self.reward_options.config(width = 23)
        self.reward_options.grid(row = 3, column = 0, sticky = "NW", padx = 10, pady = 3)   
        
        #Network size option Menu and Label initialization
        self.size_label = ttk.Label(self, text  = "Network Size:")
        self.size_label.grid(row = 4, column = 0, sticky = "NW", padx = 10, pady = 3)
        self.size_option = ttk.OptionMenu(self, self.parent.size_choice, self.parent.size_choice.get(), *self.parent.sizes, command = self.choose_size)
        self.size_option.grid(row = 5, column = 0, sticky = "NW", padx = 10, pady = 3)
        self.size_option.config(width = 23)

        #Select Button
        self.select_butt = ttk.Button(self, text = "Select", command = self.select_scalar)
        self.select_butt.place(x = 80, y = 260)
        self.select_butt.grid(row = 6, column = 0, sticky = "NWES", padx = 70, pady = (30, 10))

    #Method called on window destroy
    def on_destroy(self):

        self.parent.toplevel = None
        self.destroy()

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
        self.parent.append_scalar()
        self.on_destroy()