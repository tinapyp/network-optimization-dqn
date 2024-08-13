import os
import shutil
import logging
from datetime import datetime

class ModelVersioning:
    def __init__(self, model_dir='./models', backup_dir='./models_backup', log_file='./logs/model_versioning.log'):
        self.model_dir = model_dir
        self.backup_dir = backup_dir
        self.log_file = log_file
        self._setup_logging()

        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def _setup_logging(self):
        logging.basicConfig(filename=self.log_file, level=logging.INFO, 
                            format='%(asctime)s %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)

    def save_model(self, model, model_name='dqn_model'):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_path = os.path.join(self.model_dir, f'{model_name}.h5')
            backup_path = os.path.join(self.backup_dir, f'{model_name}_{timestamp}.h5')

            if os.path.exists(model_path):
                shutil.copy(model_path, backup_path)
                self.logger.info(f"Model {model_name} backed up as {backup_path}")

            model.save(model_path)
            self.logger.info(f"Model {model_name} saved at {model_path}")
        except Exception as e:
            self.logger.error(f"Error saving model {model_name}: {str(e)}")

    def load_model(self, model_name='dqn_model'):
        from tensorflow.keras.models import load_model
        
        model_path = os.path.join(self.model_dir, f'{model_name}.h5')
        try:
            if os.path.exists(model_path):
                model = load_model(model_path)
                self.logger.info(f"Model {model_name} loaded from {model_path}")
                return model
            else:
                self.logger.warning(f"Model {model_name} not found at {model_path}")
                return None
        except Exception as e:
            self.logger.error(f"Error loading model {model_name}: {str(e)}")
            return None

    def get_all_versions(self, model_name='dqn_model'):
        try:
            versions = [f for f in os.listdir(self.backup_dir) if f.startswith(model_name)]
            self.logger.info(f"Found {len(versions)} versions of {model_name}")
            return versions
        except Exception as e:
            self.logger.error(f"Error retrieving model versions for {model_name}: {str(e)}")
            return []

    def restore_version(self, version_name):
        try:
            backup_path = os.path.join(self.backup_dir, version_name)
            model_path = os.path.join(self.model_dir, version_name.split('_')[0] + '.h5')

            if os.path.exists(backup_path):
                shutil.copy(backup_path, model_path)
                self.logger.info(f"Model restored from {backup_path} to {model_path}")
            else:
                self.logger.warning(f"Backup {backup_path} not found")
        except Exception as e:
            self.logger.error(f"Error restoring model version {version_name}: {str(e)}")

if __name__ == '__main__':
    model_versioning = ModelVersioning()