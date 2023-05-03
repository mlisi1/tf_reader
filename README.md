# TF Reader
## What is TF Reader?
TF Reader is a wannabe TensorBoard offline alternative. As I was working on a Reinforcement Learning project, I found Tensorboard to be limited for the use I wanted to make.
The main problem I was facing was not having a more thorough division for Scalars, the missing feature of displaying custom plots.

The scope of this app is surely extremely narrow, and the usage is fairly constraint by my use cases, but with my free time I will try and mantain active this project as best as I can, and I wated to share it, as it could be helpful to someone.

Powered by ```tkinter``` GUI, TF Reader embeds ```matplotlib``` to plot training results loaded from TensorBoard binary files, thans to ```tbparse``` SummaryReader. Given the fact that loading all the detected files at the start of the program would take too long, thanks to a particular (but narrow in scope) folder structure, every training session and relevant file paths are saved in an internal datacalss and then loaded only when the data is requested for the plot.

Only Scalars plotting is possible right now, but more features will eventually be added.

## Features
The features implemented at the moment are the following:
+ Automatic training folder scan
+ Identifies training sessions by model tags, reward tags and size
     + Further selection based on the Scalar Tag
+ Curves on the plot can be smoothed via slider
+ Training specific dataclass is read and showed in a scalar-specific Info window

![alt text](http://url/to/img.png)


![alt text]([http://url/to/img.png](https://www.mediafire.com/view/xln9gbfbw94iynf))



By being born from a Reainforcement Learning need, ```tf_reader``` is based on a particular folder structure. 
```
.
└── trainings_dir/
     ├── Env [MT1] [MT2] [...] | [RT1] [RT2] [...]/
     |      ├── YYYYMMDD-HHMMSS/
     |      |      └── dir/
     |      |          ├──-ModelName-TPID/
     |      |          |        ├──tf_events_file
     |      |          |        └──best-model.pt
     |      |          └──ModelName-TPID.params
     |      ├── YYYYMMDD-HHMMSS/
     |      |      └── ...
     |      └── YYYYMMDD-HHMMSS/
     |             └── ...
     ├──  Env [MT1] [MT2] [...] | [RT1] [RT2] [...]/
     |      ├── YYYYMMDD-HHMMSS/
     |      |      └── ...
     |      ├── YYYYMMDD-HHMMSS/
     |      |      └── ...
     |      └── YYYYMMDD-HHMMSS/
     |             └── ...
     └── ...
```
As hard as it sounds, it's just a fancy way of dividing different trainings in a dir tree. The first folder encountered contains the Envionment name (Gymnasium envs), the model tags (MT1,..) and reward tags ([RT1],..). The first are tags representing changes on the model, such as modifying the number of layers, while the latter ones are changes to the reward given to the agent.
Then, for every model and reward variations, there are the different sessions 
