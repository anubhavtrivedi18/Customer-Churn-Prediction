from src.entity.config_entity import ModelEvaluationConfig
from src.entity.artifact_entity import ModelTrainerArtifact, DataIngestionArtifact, ModelEvaluationArtifact
from sklearn.metrics import f1_score
from src.exception import MyException
from src.constants import TARGET_COLUMN
from src.logger import logging
import sys
import pandas as pd
from typing import Optional
from src.entity.s3_estimator import Proj1Estimator
from dataclasses import dataclass
from src.constants import SCHEMA_FILE_PATH
from src.utils.main_utils import load_object, read_yaml_file
@dataclass
class EvaluationModelResponse:
    trained_model_f1_score: float
    best_model_f1_score: Optional[float]
    is_model_accepted: bool
    difference: float

class ModelEvaluation:

    def __init__(self,model_eval_config: ModelEvaluationConfig,data_ingestion_artifact: DataIngestionArtifact,
                 model_trainer_artifact: ModelTrainerArtifact):
        try:
            self.model_eval_config = model_eval_config
            self.data_ingestion_artifact = data_ingestion_artifact
            self.model_trainer_artifact = model_trainer_artifact
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)

        except Exception as e:
            raise MyException(e,sys) from e


    def get_best_model(self) -> Optional[Proj1Estimator]:
        try:
            bucket_name = self.model_eval_config.bucket_name
            model_path=self.model_eval_config.s3_model_key_path
            proj1_estimator = Proj1Estimator(bucket_name=bucket_name,
                                               model_path=model_path)

            if proj1_estimator.is_model_present(model_path=model_path):
                return proj1_estimator
            return None
        except Exception as e:
            raise MyException(e,sys) from e

    def drop_column(self, df):
        

        """Drop the id column if it exists."""
        logging.info("Dropping  column")

        drop_col = self._schema_config['drop_columns']

        df = df.drop(columns=drop_col, errors='ignore')

        return df

    def evaluate_model(self):
        try:
            test_df = pd.read_csv(self.data_ingestion_artifact.testing_file_path)
            x,y = test_df.drop(TARGET_COLUMN, axis = 1), test_df[TARGET_COLUMN]
            logging.info("Test data loaded and now transforming it for prediction...")

            x = self.drop_column(x)
            trained_model = load_object(
                file_path=self.model_trainer_artifact.trained_model_file_path
            )
            trained_model_f1_score = f1_score(
                y,
                trained_model.predict(x),
                pos_label="Yes",
            )
            logging.info("F1 score for newly trained model: %s", trained_model_f1_score)

            best_model_f1_score = None
            best_model = self.get_best_model()

            if best_model is not None:
                logging.info(f"Computing F1_score for production model..")
                y_hat_best_model = best_model.predict(x)
                best_model_f1_score = f1_score(y,y_hat_best_model,pos_label = "Yes")
                logging.info(f"F1_score-Production Model: {best_model_f1_score}, F1_score-New Trained Model: {trained_model_f1_score}")


            baseline_score = 0.0 if best_model_f1_score is None else best_model_f1_score
            difference = trained_model_f1_score - baseline_score
            result = EvaluationModelResponse(trained_model_f1_score=trained_model_f1_score,
                                                 best_model_f1_score=best_model_f1_score,
                                                 is_model_accepted=(
                                                     best_model_f1_score is None
                                                     or difference > self.model_eval_config.change_threshold_score
                                                 ),
                                                 difference=difference)


            logging.info(f"Result: {result}")
            return result

        except Exception as e:
            raise MyException(e,sys)



    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        """
        Method Name :   initiate_model_evaluation
        Description :   This function is used to initiate all steps of the model evaluation
        
        Output      :   Returns model evaluation artifact
        On Failure  :   Write an exception log and then raise an exception
        """  
        try:
            print("------------------------------------------------------------------------------------------------")
            logging.info("Initialized Model Evaluation Component.")
            evaluate_model_response = self.evaluate_model()
            s3_model_path = self.model_eval_config.s3_model_key_path

            model_evaluation_artifact = ModelEvaluationArtifact(
                is_model_accepted=evaluate_model_response.is_model_accepted,
                s3_model_path=s3_model_path,
                trained_model_path=self.model_trainer_artifact.trained_model_file_path,
                changed_f1_score=evaluate_model_response.difference)

            logging.info(f"Model evaluation artifact: {model_evaluation_artifact}")
            return model_evaluation_artifact
        except Exception as e:
            raise MyException(e, sys) from e         