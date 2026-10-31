import sys 
from typing import Tuple
 
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
 
from src.exception import MyException 
from src.logger import logging 
from sklearn.naive_bayes import GaussianNB
from src.utils.main_utils import load_numpy_array_data,load_object,save_object 
from src.entity.config_entity import ModelTrainerConfig 
from src.entity.artifact_entity import (
    ClassificationMetricArtifact,
    DataTransformationArtifact,
    ModelTrainerArtifact,
)
from src.entity.estimator import MyModel 
 
 
class ModelTrainer: 
    def __init__(self,data_transformation_artifact: DataTransformationArtifact, 
                 model_trainer_config: ModelTrainerConfig): 
        self.data_transformation_artifact = data_transformation_artifact 
        self.model_trainer_config = model_trainer_config 
 
    def get_model_object_and_report(
        self, train: np.ndarray, test: np.ndarray
    ) -> Tuple[GaussianNB, ClassificationMetricArtifact]:
        try: 
            logging.info("Training GaussianNB with configured parameters")
 
            # Splitting the train and test data into feature and target varibales 
            x_train,y_train,x_test,y_test = train[:,:-1], train[:,-1], test[:,:-1], test[:,-1] 
            logging.info("train-test split done.") 
 
            # Initialize RandomForestClassifier with specified parameters 
            model = GaussianNB( 
                var_smoothing=self.model_trainer_config.model_var_smoothing 
            ) 
 
            # Fit the Model 
            logging.info("Model training going on...") 
            model.fit(x_train,y_train) 
            logging.info("Model training done.") 
 
            # Prediction and evaluation metrics 
            y_pred = model.predict(x_test) 
            f1 = f1_score(y_test,y_pred,pos_label='Yes') 
            precision = precision_score(y_test,y_pred,pos_label = 'Yes') 
            recall = recall_score(y_test,y_pred,pos_label = 'Yes') 
 
            # Creating metrics artifact 
            metrics_artifact = ClassificationMetricArtifact(f1_score=f1, precision_score=precision,recall_score = recall) 
            return model, metrics_artifact 
 
 
        except Exception as e: 
            raise MyException(e,sys) from e 
 
    def initiate_model_trainer(self) -> ModelTrainerArtifact: 
        logging.info("Entered initiate_model method of ModelTrainer class") 
        try: 
            print('---------------------------------------------------------------------') 
            print("Start Model Training Components") 
            # Load transformed train and test data 
            train_arr = load_numpy_array_data(file_path = self.data_transformation_artifact.transformed_train_file_path) 
            test_arr = load_numpy_array_data(file_path = self.data_transformation_artifact.transformed_test_file_path) 
            logging.info("train-test data loaded") 
 
            # Train model and get metrics 
            trained_model, metrics_score = self.get_model_object_and_report(train = train_arr, test = test_arr) 
            logging.info("Model object and artifact") 
 
 
            # load preprocessing object 
            preprocessing_obj = load_object(file_path =self.data_transformation_artifact.transformed_object_file_path) 
            logging.info("Preprocessing obj loaded.") 
 
 
            # Check if the model object that includes both preprocessing and the trained model 
            if metrics_score.f1_score < self.model_trainer_config.excepted_f1_score:
                logging.info(
                    "Model validation F1 score %.4f is below the required threshold %.4f",
                    metrics_score.f1_score,
                    self.model_trainer_config.excepted_f1_score,
                )
                raise ValueError("Model validation F1 score is below the configured threshold.")
 
 
            # Save the fianl model object that includes both preprocessing and trained model 
            logging.info("Saving new model as performance is better than previos one.") 
            my_model = MyModel(preprocessing_object=preprocessing_obj, trained_model_object=trained_model) 
            save_object(self.model_trainer_config.trained_model_file_path, my_model) 
            logging.info("Save final model object that includes both preprocessing and trained model") 
 
 
            # Create and return ModelTrainerArtifact 
 
            model_trainer_artifact = ModelTrainerArtifact(
            trained_model_file_path=self.model_trainer_config.trained_model_file_path,
            metric_artifact=metrics_score)
 
            logging.info(f"Model trainer artifact: {model_trainer_artifact}") 
 
            return model_trainer_artifact 
 
        except Exception as e: 
            raise MyException(e,sys) from e 
 
 