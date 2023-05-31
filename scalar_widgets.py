import tkinter as tk
from tkinter import ttk

import numpy as np
import os

#Matplotlib plot utilities and tk wrapper
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
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

        #Get line and line color
        self.lines = lines
        if self.lines is not None:
            self.color = lines[0].get_color()
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
            self.configure(foreground = self.lines[0].get_color())
        else:
            self.configure(foreground = "#000000")

    #Hover functions
    def on_enter(self, event):

        #Highlight label and assigned line
        if self.lines != None:
            self.configure(foreground="black")
            for i, line in enumerate(self.lines):
                self.lines[i].set_linewidth(3)
                self.update_fns[i]()

    def on_leave(self, event):

        #Deselect label and line
        if self.lines != None:
            self.configure(foreground=self.color)
            for i, line in enumerate(self.lines):
                self.lines[i].set_linewidth(1)
                self.update_fns[i]()

    #Removes this scalar label's lines
    def remove_lines(self):

        #Undraw lines
        for i, line in enumerate(self.lines):

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
        self.offset = (300, 220)
        

 
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

        for plot in self.plots:
            self.remove_plot(plot)



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

    #Save all the plots into a single image
    def save_multiple_plots(self, mode = False):      

        #piece of code to handle the positioning of multiple plots
        #>could be better written
        small = True
        image = None
        bottom_image = []

        if len(self.plots) == 3:
            small = False

        if len(self.plots) > 3:
            small = mode

        for i, plot in enumerate(self.plots):            
            
            #Initialize the image 
            if i == 0:
                image = np.array(plot.fig.canvas.renderer.buffer_rgba())
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                continue

            #vconcat if 2, hconcat if 3
            if i < 3:   
                new_image = np.array(plot.fig.canvas.renderer.buffer_rgba())
                new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
                image = cv2.vconcat([image, new_image]) if small else cv2.hconcat([image, new_image])
                continue

            if i >= 3:                

                #create a new bottom/side image
                if i == 3:                    
                    bottom_image = np.array(plot.fig.canvas.renderer.buffer_rgba())
                    bottom_image = cv2.cvtColor(bottom_image, cv2.COLOR_RGB2BGR)
                    continue

                #hconcat/vconcat to bottom/side image depending on mode var
                #>customizable by the user in the future
                if len(bottom_image) != 0:                        
                    new_image = np.array(plot.fig.canvas.renderer.buffer_rgba())
                    new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
                    bottom_image = cv2.vconcat([bottom_image, new_image]) if small else cv2.hconcat([bottom_image, new_image])
                    continue

        #concat top/bottom or left/right images
        if len(bottom_image) != 0:
            extended_canvas = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
            extended_canvas[0:bottom_image.shape[0], 0:bottom_image.shape[1]] = bottom_image

            bottom_image = cv2.cvtColor(extended_canvas, cv2.COLOR_RGB2BGR)
            image = cv2.hconcat([image, bottom_image]) if small else cv2.vconcat([image, bottom_image])


        filepath = os.path.join(self.root_dir, 'saved_scalars/plots')

        #If the dirs doesn't exist, create it
        if not os.path.isdir(filepath):
            os.mkdir(filepath)

        #Save dialog window
        file_path = tk.filedialog.asksaveasfilename(parent = self, initialdir = filepath, initialfile = "plot.png", 
                    filetypes=(("PNG Image File", "*.png"), ("Bitmap", "*.bmp"), ("JPEG File", "*.jpg"), ("All files", "*.*")), 
                    defaultextension = '.png')

        #Save image
        cv2.imwrite(file_path, image)  
  





if __name__ == "__main__":

    root = tk.Tk()
    root.geometry('700x700')

    frame = ScrollableFrame(root, 20, 2, 300, 50)

    for i in range(50):
        ttk.Label(frame.scrollable_frame, text="Sample scrolling label").grid(column = 0,row =i)

    frame.pack()
    root.mainloop()