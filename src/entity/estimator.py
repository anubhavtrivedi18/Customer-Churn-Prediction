import sys

import numpy as np
import pandas as pd
from scipy.sparse import issparse
from sklearn.pipeline import Pipeline
from typing import Tuple

from src.exception import MyException
from src.logger import logging

class TargetValueMapping:
    def __init__(self):
        self.yes:int = 0
        self.no:int = 1
    def _asdict(self):
        return self.__dict__
    def reverse_mapping(self):
        mapping_response = self._asdict()
        return dict(zip(mapping_response.values(),mapping_response.keys()))

class MyModel:
    def __init__(self, preprocessing_object: Pipeline, trained_model_object: object):
        """
        :param preprocessing_object: Input Object of preprocesser
        :param trained_model_object: Input Object of trained model 
        """
        self.preprocessing_object = preprocessing_object
        self.trained_model_object = trained_model_object

    def predict(self, dataframe: pd.DataFrame) -> np.ndarray:
        """
        Function accepts preprocessed inputs (with all custom transformations already applied),
        applies scaling using preprocessing_object, and performs prediction on transformed features.
        """
        try:
            logging.info("Starting prediction process.")

            # Step 1: Apply scaling transformations using the pre-trained preprocessing object
            transformed_feature = self._transform_features(dataframe)

            # Step 2: Perform prediction using the trained model
            logging.info("Using the trained model to get predictions")
            predictions = self.trained_model_object.predict(transformed_feature)

            return predictions

        except Exception as e:
            logging.error("Error occurred in predict method", exc_info=True)
            raise MyException(e, sys) from e

    def predict_proba(
        self, dataframe: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        try:
            if not hasattr(self.trained_model_object, "predict_proba"):
                raise TypeError("The trained classifier does not support probability estimates.")

            transformed_feature = self._transform_features(dataframe)
            probabilities = self.trained_model_object.predict_proba(transformed_feature)
            classes = self.trained_model_object.classes_
            return classes, probabilities
        except Exception as e:
            logging.error("Error occurred in predict_proba method", exc_info=True)
            raise MyException(e, sys) from e

    def _transform_features(self, dataframe: pd.DataFrame) -> object:
        transformed_features = self.preprocessing_object.transform(dataframe)
        if issparse(transformed_features):
            return transformed_features.toarray()
        return transformed_features


    def __repr__(self):
        return f"{type(self.trained_model_object).__name__}()"

    def __str__(self):
        return f"{type(self.trained_model_object).__name__}()"