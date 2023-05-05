import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import re
from functools import partial
import datetime
import numpy as np



#GUI
import tkinter as tk
from tkinter import ttk

#local imports
from sessionloader import SessionLoader
from scalar_widgets import ScrollableFrame, ScalarLabel, PlotContainer
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
        self.geometry("920x520")
        self.resizable(tk.FALSE, tk.FALSE)
        self.protocol('WM_DELETE_WINDOW', self.on_destroy)
        self.grid_rowconfigure(10, weight=1)
        self.grid_columnconfigure(20, weight=1)

        self.root_dir = os.getcwd()

        #Plot container initialization
        self.container = ttk.Frame(self)
        self.container.grid(row = 0, rowspan = 10, column = 0, columnspan = 10)
        self.container.grid_rowconfigure(0, weight=10)
        self.container.grid_columnconfigure(0, weight=10)   
        
        #Scalar list frame initialization
        self.scalar_container = ScrollableFrame(self, 20, 2, width = 260, height = 300)
        self.scalar_container.grid(row = 6, column = 20) 


        self.save_butt = ttk.Button(self, text = "Save scalar data", command = self.save_scalar_data)
        self.save_butt.state(["disabled"])
        self.save_butt.place(x = 700, y = 460)

        #Array of scalars and their relative parameters
        self.scalars = []
        self.params = []
        self.max_values = []

        #SessionLoader; handles workdir scanning and file loading/parsing
        self.loader = SessionLoader(workdir)
        self.loader.parse_sessions()

        #Model choice variables
        self.available_models = self.loader.model_tags
        self.available_models.append("All")
        self.model_choice = tk.StringVar()
        self.model_choice.set(self.available_models[0])

        #Size choice variables
        self.sizes = ["256,32", "256,64", "512,64", "512,128", "All"]
        self.size_choice = tk.StringVar()
        self.size_choice.set(self.sizes[0])
        self.chosen_batch = 32
        self.chosen_hid = 256
    
        #Reward choice variables
        self.available_rewards = self.loader.reward_tags
        self.available_rewards.append("All")        
        self.reward_choice = tk.StringVar()
        self.reward_choice.set(self.available_rewards[0])

        #Scalar list GUI arrays
        self.scalar_labels = []
        self.scalar_buttons = []
        self.scalar_names = []

        #Button to add scalars initialization
        self.add_scalar_button = ttk.Button(self, text = "Add Scalar", command = self.add_scalar_fn)
        self.add_scalar_button.place(x = 655, y = 90)

        #Button to clear the plot
        self.clear_button = ttk.Button(self, text = "Clear", command = self.clear)
        self.clear_button.place(x = 775, y = 90)

        #Toplevel variable; used to only allow one additional window at a time
        self.toplevel = None
        
        #calls the SessionLoader to attempt a first load for initialization purposes
        self.frame = None
        self.append_scalar()            

        #Model tag choice variables initialization
        self.tags = []
        self.full_tags = []
        self.get_tags()
        assert len(self.tags) == len(self.full_tags)
        self.tag_choice = tk.StringVar()
        self.tag_choice.set(self.tags[0])

        #Smooth variable and slider initialization
        self.smooth_value = tk.DoubleVar()
        self.smooth_value_label = ttk.Label(self, text = str(self.get_smooth_value))
        self.smooth_value_label.place(x = 750, y = 20)
        self.slider_label = ttk.Label(self, text = "Smooth Value:")
        self.slider_label.place(x = 650, y = 20)
        self.slider = ttk.Scale(self, from_ = 0.0, to = 0.99, variable = self.smooth_value,
                        orient = tk.HORIZONTAL, command = self.update_plot, length = 200)
        self.slider.place(x = 660, y = 50)

        #Initialize plot frame, generate and clear plot       
        self.initialize_plot_frame()
        self.clear()

    #======GETTER AND SETTERS===========
    #Returns the full tag after the chosen tag shown in GUI
    @property
    def get_tag_choice(self):
        key = self.tag_choice.get()
        index = self.tags.index(key)       
        return self.full_tags[index]    

    #Retrieves the set of tags found in the scalar
    ##At the moment it is used only for initialization purposes; the tags cannot be updated at a second moment
    def get_tags(self):


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

    #===========TK WINDOW FUNCTIONS===========
    #Used when quitting main window; self.running is used to stop the main loop
    def on_destroy(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            self.quit()
            self.running = False

    #Just a convenient gruping for tkinter update functions; to be used instead of mainloop()
    def update_gui(self):

        self.update_idletasks()
        self.update()

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
        self.frame.clear()

        #Clear the scalar labels
        self.update_scalar_labels()

    #Initialize plot frame with PlotContainer class
    def initialize_plot_frame(self):

        self.frame = PlotContainer(self.container, self.scalars, self.get_tag_choice)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.tkraise()

    #Standard plot update method: redraws the plot and updates existing scalar label's line variable
    def update_plot(self, smooth_value):

        #Update smooth value label
        self.smooth_value_label.config(text = f'{self.get_smooth_value:.2f}')

        self.frame.update_plot(self.get_smooth_value)

        for i in range(len(self.scalar_labels)):

            self.scalar_labels[i].update_line(self.frame.line[i])

    #================GUI ELEMENT UPDATE FUNCTIONS================================
    #Updates the labes by destroying and recreating according to the scalars
    def update_scalar_labels(self):

        #If there are labels, destroy them
        if len(self.scalar_labels) > 0:            
            for i in range(len(self.scalar_labels)):
                self.scalar_labels[i].destroy()
                self.scalar_buttons[i].destroy()
            self.scalar_labels = []
            self.scalar_buttons = []
        
        #If there are scalars, create labels and buttons
        if len(self.scalar_names) > 0:
            for i in range(len(self.scalar_names)):

                #temporary string for the scalar tag
                tmp_str = re.sub(r'Ant-v4-', "",self.frame.scalar_name[i]).strip(':')
                #instantiate ScalarLabel class; uses fast update method instead of normal update
                tmp = ScalarLabel(self.scalar_container.scrollable_frame, text = f'{self.scalar_names[i]}{tmp_str}', line = self.frame.line[i], update_fn = self.frame.fast_update)
                tmp.grid(column = 0, row = i)
                #create partial for instancing the Info window; for some reason lambda definition was not working
                cmd = partial(self.info_win_bringup, self.params[i], self.scalar_names[i])
                #instantiate Info Button                
                tmp_butt = ttk.Button(self.scalar_container.scrollable_frame, text = "Info", width = 4, command = cmd)              
                tmp_butt.grid(column = 1, row = i)

                #update button and labels list
                self.scalar_labels.append(tmp)
                self.scalar_buttons.append(tmp_butt)

    #===================TOPLEVEL BRINGUP FUNCTIONS=========================
    #Bringup Select Scalar Window if there is no toplevel already
    def add_scalar_fn(self):
        if self.toplevel == None:
            self.toplevel = SelectScalarWin(self)

    #Bringup Info window if there is no toplevel already; instantiated by every Info button
    def info_win_bringup(self, params, scalar_name):

        if self.toplevel is None:

            self.toplevel = InfoWindow(self, params, scalar_name)

    #======================LOAD FUNCTIONS =====================================
    #Load scalar from selected session(s) and update plot
    def append_scalar(self):

        #Retrieve [scalars, scalar_name, params] from SessionLoader
        scalar_iter = self.loader.get_scalar_from_tags(self.model_choice.get(), self.reward_choice.get(), self.chosen_batch, self.chosen_hid)
        
        #Update scalar related variables      
        for tmp in scalar_iter:           
            
            self.scalars.append(tmp[0])
            self.scalar_names.append(tmp[1])
            self.params.append(tmp[2])

            if self.frame is not None:
                self.frame.scalar_name.append(self.get_tag_choice)


           
       

        if len(self.scalars) > 1:
            
            #Append max average reward during test for each scalar
            max_test_value = np.empty(0)
            for i in range(len(self.scalars)):
        
                for tag in self.scalars[i]['tag']:

                    if "Avg" in tag and "Network" in tag and "Test" in tag and not "Best" in tag:

                        x = self.scalars[i][self.scalars[i]['tag'].values == tag]
                        max_test_value = np.append(max_test_value, x['value'].values[-1])
                        break


            #Sort the array and get the indexes
            indexes = np.argsort(max_test_value)[::-1] 
            self.max_values = np.sort(max_test_value)[::-1]
                 
            # self.scalars = self.scalars[indexes]
            self.scalars = [self.scalars[i] for i in indexes]
            self.scalar_names = [self.scalar_names[i] for i in indexes]
            self.params = [self.params[i] for i in indexes]   

            #Activate save button
            self.save_butt.state(["!disabled"])    


               


        #Update plot
        if self.frame is not None:
            self.frame.scalars = self.scalars
            self.update_plot(self.get_smooth_value)
            self.update_scalar_labels()



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

        if len(self.scalars) > 1:

            with open(os.path.join(filepath, filename), 'w') as f:

                #Write relevant infos
                f.write("Scalars Plotted:\n")      
                for i in range(len(self.scalars)):

                    scalar_tag = re.sub(r'Ant-v4-', "",self.frame.scalar_name[i]).strip(':').strip('\n')
                    name = self.scalar_names[i].split('\n')

                    f.write(f'{name[0]}{name[1]}   Max Test Avg: {self.max_values[i]}   Scalar Tag: {scalar_tag}\n')


            

        







    