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
		self.sessions = []
		self.model_dict = {}

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
		  
		        self.model_dict[model_tags].append(folder_name)
		    else:
		        self.model_dict[model_tags] = [folder_name]

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

		string = f'{session.model_tags}\n{session.reward_tags} [{session.params[0].hidden_size},{session.params[0].batch_size}]\n'
		return string

	#Scalar retrieval function; checks all the selected tags
	def get_scalar_from_tags(self, model, reward, batch = 0, hid = 0):      


		tmp = []

		#Find only relevant session folders
		selected_folder_iterator = self.retrieve_folder(model, reward)

		#Initialize pool
		pool = Pool(processes = 10)

		for folder in selected_folder_iterator:

			
			for session in self.sessions:
				
				if folder+'/' in session.tf_events_path:

					#Check for size matches                                         
					if session.params[0].batch_size == batch and session.params[0].hidden_size == hid and batch != 0 and hid != 0:

						#Append [session, session_name]
						tmp.append([pool.apply(self.process_session, args=(session,)), self.get_name(session), session.params[0]])          

					#All sizes selected             
					if batch == 0 and hid == 0:

						#Append [session, session_name]
						tmp.append([pool.apply(self.process_session, args=(session,)), self.get_name(session), session.params[0]])                     
           
		return tmp


	#Scans training dir and seeks for sessions
	#>exclude_faults = True discards training with a valid tag name but that ends with .something
	def parse_sessions(self, exclude_faults=True):

        #Reset tags
		self.model_tags = []
		self.reward_tags = []

        #Go to trainings dir
		os.chdir(self.trainings_dir)

		for directory in glob.glob('*'):

            #Exclude every dir ending in .something
			if exclude_faults and '.' in directory:
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

				#Assign values to training session
				temp = TrainingSession()
				temp.model_tags = model_tags
				temp.reward_tags = reward_tags
				temp.tags_dir = directory

				#Retrieve .params file
				#>a dataclass printed to the file during training
				params_path = glob.glob(glob.escape(f"{model}")+"/*/*.params")[0]                   
				temp.params_path = params_path

				#Parse .params file
				temp.params = self.read_dataclass_file(params_path, TrainingParameters)

				#Retrieve tf_events file path
				tf_events_path = glob.glob(glob.escape(f"{model}")+"/*/*/events*")[0]           
				temp.tf_events_path = tf_events_path


				self.sessions.append(temp)


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





