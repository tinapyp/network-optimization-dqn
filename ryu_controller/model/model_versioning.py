import pickle
import os


class ModelVersioning:
    def __init__(self, model_file="best_model.h5", topology_file="best_topology.pkl"):
        self.model_file = model_file
        self.topology_file = topology_file

    def save_model(self, model):
        model.save(self.model_file)

    def load_model(self):
        if os.path.exists(self.model_file):
            from tensorflow.keras.models import load_model

            return load_model(self.model_file)
        else:
            raise FileNotFoundError("No model file found.")

    def save_topology(self, topology):
        with open(self.topology_file, "wb") as f:
            pickle.dump(topology, f)

    def load_topology(self):
        if os.path.exists(self.topology_file):
            with open(self.topology_file, "rb") as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError("No topology file found.")
