# TF Reader
TF Reader is a wannabe TensorBoard offline alternative. As I was working on a Reinforcement Learning project, I found Tensorboard to be limited for the use I wanted to make.
The main problem I was facing was not having a more thorough division for Scalars, the missing feature of displaying custom plots.

The scope of this app is surely extremely narrow, and the usage is fairly constraint by my use cases, but with my free time I will try and mantain active this project as best as I can.

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
