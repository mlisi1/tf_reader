import inspect


from dataclasses import dataclass


@dataclass
class TrainingParameters:
    # dataclass attributes created in __init__ and address by self.
    # TODO - perhaps add validation to check when unnecessary parameters are specified e.g. batch_size for tabular
    env_name: str = "Ant-v4"# the str representing the environment, found in src.constants.env_names
    agent_name: str  = "CountinuousDQN"# the str representing the agent, found in src.constants.agent_names
    # network: str = "DNN"  # The type of network to use within an agent ("DNN" or "CNN")

    num_episodes: int = 1000
    

    test_group_label: str = None  # A label used to identify a batch of experiments
    save_every_n: int = 20  # How frequently should copies of the model be saved during training?

    buffer_size: int = int(1e4)  # PyTorch buffer size to use during training
    batch_size: int = 4  # PyTorch batch size to use during training
    update_every: int = 4  # After how many interacts should we update the model?
    update_every_eps = 1  # Deprecated
    update_steps: int = 10  # Used by LDQN
    hidden_size: int = 256
    sample_size: int = 10

    epsilon: float = 0.9  # Hyperparameter used in epsilon-greedy algorithms (and others)
    epsilon_decay: float = 0.99
    epsilon_min: float = 0.0
    epsilon_decay_start: int = 10
    slack: float = 0.001  # Hyperparameter used by lexicographic algorithms

    learning_rate: float = 1e-3

    # AproPo
    lambda_lr_2: float = 0.05
    alpha: float = 1
    beta: float = 0.95

    no_cuda: bool = True

    num_test: int = 200

    reward_size: int = 2
    constraint: int = 0.1

    constraints: str = "[(0.3, 0.5), (0.0, 0.1)]"

    lextab_on_policy: bool = False

    # After dataclass attributes are initialised, validate the training parameters
    def render_and_print(self):
        print(self.render_to_string())

    def render_to_string(self):
        x = ""
        for atr_name, atr in inspect.getmembers(self):
            if not atr_name.startswith("_") and not inspect.ismethod(atr):
                x += f" < {atr_name}: {str(atr)} >, "
        return x

    def render_to_file(self, dir):
        x = self.render_to_string()
        with open(dir, "w") as f: f.write(x)
