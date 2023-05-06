import tkinter as tk
from tkinter import ttk

import numpy as np

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




#=============== PLOT CONTAINER ====================
#Frame used to contain Matplotlibs tk wrapper; handles low level plot functions
class PlotContainer(ttk.Frame):

    def __init__(self, container, scalars, scalar_choice):

        #Initialize frame and figure
        tk.Frame.__init__(self, container)
        self.fig, self.ax = plt.subplots()  
        self.ax.grid()       

        #Initialize Matplotlib wrappers and place them
        self.canvas = FigureCanvasTkAgg(self.fig, master = self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM)
 
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, expand =True)

        #Initialize scalar defining arrays
        self.scalars = scalars
        self.scalar_name = [scalar_choice]
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
        self.scalar_name = []
        self.colors = []

    #Gets data from scalars
    def data_from_scalar(self):

        #Delete previous data
        del self.data
        self.data = []  
        

        #Gather correct values
        for i in range(len(self.scalars)):
            
            data = self.scalars[i][self.scalars[i]['tag'] == self.scalar_name[i]]            
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


        #Set plot limits and draw
        self.ax.set_xlim(min_x-10, max_x+10)
        self.ax.set_ylim(min_y-10, max_y+50)        
        self.canvas.draw()

    #Fast update method; it only redraws the plot;
    #>used when the scalars haven't changed but plot needs to be redrawn
    def fast_update(self):

        self.canvas.draw()

    #NOT YET IMPLEMENTED
    @property
    def max_scalar(self):

        for i in range(len(self.scalars)):
            x = self.data[i]['step']
            y = self.smooth(self.data[i]['value'].values, smooth_value)

    



#===================== SCROLLABLE FRAME ===============
#Frame with scrollbar
class ScrollableFrame(ttk.Frame):

    def __init__(self, container, row, column, height, width,  *args, **kwargs):

        #Initialize frame
        super().__init__(container, *args, **kwargs)

        #Initialize canvas and scrollbar, both attached to the frame
        canvas = tk.Canvas(self, height = height, width = width)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)

        #Scrollable frame where widgets will be attached
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.columnconfigure(row)
        self.scrollable_frame.rowconfigure(column)

        #Configure scrollbar and scrollbar frame
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        #Place items
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


#======================== SCALAR LABELS ======================
#Conveniently defined labels with hover methods
class ScalarLabel(ttk.Label):

    def __init__(self, container, text, line, update_fn):

        #Initialize label
        super().__init__(container, text = text)

        #Get line and line color
        self.line = line
        self.color = line.get_color()

        #Assign the color to the label
        self.configure(foreground = self.color)
        
        #Reference to the update function (fast update)
        self.update_fn = update_fn

        # Bind the hover functions to the <Enter> and <Leave> events
        self.bind("<Enter>", self.on_enter)       
        self.bind("<Leave>", self.on_leave)

    #Method called externally; updates the assigned line if plot has changed
    def update_line(self, line):

        self.line = line

    #Hover functions
    def on_enter(self, event):

        #Highlight label and assigned line
        self.configure(foreground="black")
        self.line.set_linewidth(3)
        self.update_fn()

    def on_leave(self, event):

        #Deselect label and line
        self.configure(foreground=self.color)
        self.line.set_linewidth(1)
        self.update_fn()




if __name__ == "__main__":

    root = tk.Tk()
    root.geometry('700x700')

    frame = ScrollableFrame(root, 20, 2, 300, 50)

    for i in range(50):
        ttk.Label(frame.scrollable_frame, text="Sample scrolling label").grid(column = 0,row =i)

    frame.pack()
    root.mainloop()