import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from params import TrainingParameters
import re
from typing import List, Type
from dataclasses import dataclass
from tbparse import SummaryReader
from multiprocessing import Pool
import glob




#======== TRAINING SESSION DATACLASS ================
#Dataclass identifying a training session; absolute path for parameter file and tf_events file are kept
@dataclass
class TrainingSession:

	#Training parameters
	params: TrainingParameters = None 
	params_path: str = None

	#Tf events path
	tf_events_path: str = None

	#Additional session data for easier retrieval
	tags_dir: str = None	
	model_tags: str = None
	reward_tags: str = None

	#Not yet implemented
	datetime: str = None
	seed: int = None








#================ SESSION LOADER ====================
#This class handles trainin folder scanning and, when requested, file loading
#A fancy frame for tbparse SummaryReader
class SessionLoader:

	def __init__(self, trainings_dir):

		#Initialize sessions' arrays
		#>dict has been added, but is not fully integrated in the system; TFReaerWin could use it for labels
		self.trainings_dir = trainings_dir
		self.model_tags = []
		self.reward_tags = []
		self.size_tags = []
		self.sessions = []
		self.model_dict = {}
		self.size_dict = {}
		self.main_dir = os.getcwd()

		self.entries_update = False

	#Retrieves all the combinations of 'hidden_size, batch_size' from the params dataclass
	def get_size_tags(self):

		for session in self.sessions:

			batch = session.params[0].batch_size
			hidden = session.params[0].hidden_size
			size_str = f"{hidden},{batch}"
			if size_str in self.size_tags:
				pass
			else:
				self.size_tags.append(size_str)

	#Updates model tags dict assigning every folder to its model tag combination
	def update_tags_dict(self, folder_name,):       
		
	  #Find matches
		pattern = r'(.*) \| (.*)'
		match = re.match(pattern, folder_name)

		if match:

			#Strip tags of unnecessary characters
			model_tags = match.group(1).strip("Ant ")

			#Create entry if new; else append to existing values
			if model_tags in self.model_dict:
			
				self.model_dict[model_tags].append(glob.glob(glob.escape(folder_name))[0])
			else:
				
				self.model_dict[model_tags] = [glob.glob(glob.escape(folder_name))[0]]
				

	#Updates available sizes for model+reward tags
	def update_size_dict(self):

		#Scan sessions
		for session in self.sessions:

			key = session.model_tags+session.reward_tags
			size = [session.params[0].hidden_size, session.params[0].batch_size, 1]
			match = None

			#If key in dict
			if key in self.size_dict.keys():
				
				#If the size is already in values
				for i, item in enumerate(self.size_dict[key]):

					if size[0] == item[0] and size[1] == item[1]:

						match = i
						break

				#Increase size counter 
				#> OptionsMenu will show as entr "hidden_size, batch_size (n entries)"
				if match is not None:

					self.size_dict[key][match][-1] += 1

				#Else, add it
				else:

					self.size_dict[key].append(size)

			#Else, add it
			else:
				
				self.size_dict[key] = [size]


	#Retrives correct session folder after model and reward tags
	def retrieve_folder(self, model, reward):

  
		mod = model.strip('Ant ')
		rew = reward




		for key in self.model_dict.keys():

			#All models selected
			if model == "All":

				for value in self.model_dict[key]:

					#All reward selected
					if rew == "All":

						yield value

					#Check reward
					if value.endswith(rew):

						yield value

			#Check model
			if mod == key and key.endswith(mod):
				
				for value in self.model_dict[mod]:

					#All reward selected
					if rew == "All":
						
						yield value

					#Check reward
					if value.endswith(rew):

						yield value

	#Main loading function; called in a multiprocessing Pool
	def process_session(self, session):

		reader = SummaryReader(session.tf_events_path)
		return reader.scalars

	#Generates the name string for the session
	def get_name(self, session):

		model_t = session.model_tags.replace("[AWG] ","")
		string = f'{model_t}\n{session.reward_tags} [{session.params[0].hidden_size},{session.params[0].batch_size}]\n'
		return string

	#Scalar retrieval function; checks all the selected tags
	def get_scalar_from_tags(self, model, reward, batch = 0, hid = 0, pool = None):      

		os.chdir(self.trainings_dir)
		tmp = []


		#Find only relevant session folders
		selected_folder_iterator = self.retrieve_folder(model, reward)


		#Initialize pool
		if pool is None:
			pool = Pool(processes = 10)

		for folder in selected_folder_iterator:

			for session in self.sessions:
				
				if folder+'/' in session.tf_events_path:

					#Check for size matches                                         
					if session.params[0].batch_size == batch and session.params[0].hidden_size == hid and batch != 0 and hid != 0:

						#Append [session, session_name, training_parameters]
						tmp.append([pool.apply(self.process_session, args=(session,)), self.get_name(session), session.params[0]])          

					#All sizes selected             
					if batch == 0 and hid == 0:

						#Append [session, session_name, training_parameters]
						tmp.append([pool.apply(self.process_session, args=(session,)), self.get_name(session), session.params[0]])  

		os.chdir(self.main_dir)           
		
		return tmp



	#Allocates correct paths and names to TrainingSession dataclass
	#>supports call via GUI
	def generate_session(self, path = None, model_tags = None, reward_tags = None, directory = None, from_gui = False):

		assert path != None

		#If the fn was called by GUI, preprocess the only argument: path
		if from_gui:

			try:


				model = os.path.basename(os.path.dirname(path))
				global_path = glob.glob(glob.escape(os.path.dirname(path)))

				#Update manually model dict
				model_tags, reward_tags = model.split('|')
				if model_tags in self.model_dict:
				
					self.model_dict[model_tags.strip("Ant ")].append(global_path)

				else:
					
					self.model_dict[model_tags.strip("Ant ")] = global_path


				directory = path

				#Generate model and reward tags "dict"
				if model_tags not in self.model_tags:
					self.model_tags.append(model_tags)

				if reward_tags not in self.reward_tags:
					self.reward_tags.append(reward_tags)
				self.entries_update = True

			#Return value for Error window
			except Exception as e:
				return -1



		#Assign values to training session
		temp = TrainingSession()
		temp.model_tags = model_tags
		temp.reward_tags = reward_tags
		temp.tags_dir = os.path.abspath(directory)

		#Retrieve .params file
		#>a dataclass printed to the file during training
		params_path = glob.glob(glob.escape(f"{path}")+"/*/*.params")[0]                   
		temp.params_path = os.path.abspath(params_path)

		#Parse .params file
		temp.params = self.read_dataclass_file(params_path, TrainingParameters)

		#Retrieve tf_events file path
		tf_events_path = glob.glob(glob.escape(f"{path}")+"/*/*/events*")[0]         
		temp.tf_events_path = os.path.abspath(tf_events_path)


		self.sessions.append(temp)


	#Scans training dir and seeks for sessions
	#>exclude_faults = True discards training with a valid tag name but that ends with .something
	def parse_sessions(self, path = None, exclude_faults = True, from_gui = False):

	  #Go to trainings dir		
		if path == None:

			os.chdir(self.trainings_dir)

		else:

			os.chdir(glob.glob(glob.escape(os.path.dirname(path)))[0])
			self.entries_update = True

		for directory in glob.glob('*'):

			#Exclude every dir ending in .something
			if exclude_faults and '.' in directory:
				continue
		
			if path != None:
				if directory != os.path.basename(path):
					continue




			self.update_tags_dict(directory)

			#Split dir name string
			model_tags, reward_tags = directory.split('|')

			#Generate model and reward tags "dict"
			#>should be changed into a real dict later
			if model_tags not in self.model_tags:
				self.model_tags.append(model_tags)

			if reward_tags not in self.reward_tags:
				self.reward_tags.append(reward_tags)
			
			#Get different training in model|reward dirs
			sub_models = glob.glob(glob.escape(f'{directory}')+'/*')

			for model in sub_models:

				tmp = self.generate_session(model, model_tags, reward_tags, directory)

				if tmp == -1:
					raise Exception

		os.chdir(self.main_dir)
		self.get_size_tags()

	#Dataclass parsing function; used to read training dataclass file
	def read_dataclass_file(self, filename: str, dataclass_type: Type = TrainingParameters) -> List:

		#Open file
		with open(filename, 'r') as f:
			lines = f.readlines()

		objects = []

		#delete unnecessary chars
		for line in lines[0].split(">,  <"):
			line = line.split("<")[0]
			line = line.split(">")[0]

			#Check for matches			
			match = re.search(r'(.+): (.+)', line)

			if match:

				#Get attribute name and attribute values
				attr_name, attr_value = match.groups()
				attr_name = attr_name.strip(" ")
				attr_value = attr_value.strip(" ")

				#If the value is in the dataclass
				if hasattr(dataclass_type, attr_name):
					
					#Get the dataclass attribute value
					attr_type = type(getattr(dataclass_type, attr_name))

					#If the value is valid
					if attr_value != "None":
						
						#Cast the value to its correct type and update new dataclass
						attr_value = attr_type(attr_value)
						if objects:
							obj = objects[-1]
							setattr(obj, attr_name, attr_value)
						else:
							obj = dataclass_type(**{attr_name: attr_value})
							objects.append(obj)

		return objects





