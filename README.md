# TF Reader
## What is TF Reader?
TF Reader is an offline alternative to <a href="https://www.tensorflow.org/tensorboard">TensorBoard</a> that I created while working on a Reinforcement Learning project. I found TensorBoard to be limited for the use I had in mind, specifically with regard to the thorough division of Scalars and the ability to display custom plots. This project also features <a href="https://github.com/rdbende/Azure-ttk-theme">Azure ttk theme</a>.


Although the scope of this app is narrow and its usage is constrained by my personal use cases, I plan to maintain this project in my free time and share it, as it may be helpful to others.

TF Reader is built using the ```tkinter``` GUI and embedded with ```matplotlib``` to plot training results from TensorBoard binary files using ```tbparse``` <a href="https://github.com/j3soon/tbparse">SummaryReader</a>. Since loading all detected files at the start of the program would take too long, the program saves every training session and relevant file path in an internal dataclass and only loads the data when it's requested for plotting.

Currently, the app only supports plotting Scalars, but more features will be added in the future.

## Features
The features implemented at the moment are the following:
+ Automatic training folder scan
+ Identifies training sessions by model tags, reward tags and size
     + Further selection based on the Scalar Tag
+ Curves on the plot can be smoothed via slider
+ Training specific dataclass is read and showed in a scalar-specific Info window
+ Scalar is highlited in the plot when the mouse hovers its label
+ Scalars are ordered based on how well they performed on average during test
+ A list of the scalars plotted can now be saved in a .txt file


<div style="display: flex;">
  <img src="https://i.imgur.com/65mwcBy.png" alt="Main Win" width="60%" height="60%">
  <img src="https://i.imgur.com/hKBDgYK.png" alt="Select Scalar" width="30%" height="30%">
</div>


## Constraints
### Folder Structure

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
Despite sounding complex, the directory tree used in this project is simply a fancy way of organizing different trainings. The first encountered folder contains the name of the environment (in this case, <a href="https://gymnasium.farama.org/">Gymnasium</a> environments), model tags (such as MT1, indicating changes to the model like modifications to the number of layers), and reward tags (such as [RT1], indicating changes to the reward given to the agent).

For each model and reward variation, there are multiple sessions, each containing model checkpoints, tf_events files (which can be uploaded to TensorBoard), and a defining .params file.

### Training's dataclass
The .params file is generated by saving a custom dataclass containing hyperparameters and other values of interest for the scope of the training. 
The `params.py` file includes the dataclass I used for the training. However, given the project's structure, any dataclass can be used without editing the code, as long as it uses the same `render_to_string` function.

### Network Size
Since the network size is obtained from the .params file, the option entries in the program are currently hardcoded. Therefore, editing the code is necessary to use the program with different network sizes. However, I plan to fix this issue soon, as it's easy to implement and will greatly improve the versatility of the program.

## Usage
The first thing needed is ```tkinter``` backend; to install use ```sudo apt install python3-tk```.
Then run ```pip install -r requirements.txt``` to install all the requirements needed.

To run TF Reader, simply run the command ```python3 main.py ./path/to/trainings```



