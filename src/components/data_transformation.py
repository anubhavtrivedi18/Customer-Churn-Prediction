import sys
import numpy as np
import pandas as pd
from imblearn.combine import SMOTEENN
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import OrdinalEncoder


from src.constants import *
from src.entity.config_entity import DataTransformationConfig 
from src.entity.artifact_entity import DataTransformationArtifact, DataIngestionArtifact, DataValidationArtifact
from src.exception import MyException
from src.logger import logging
from src.utils.main_utils import save_numpy_array_data,save_object,read_yaml_file


class DataTransformation:
    def __init__(self,data_ingestion_artifact:DataIngestionArtifact,
                 data_transformation_config:DataTransformationConfig,
                 data_validation_artifact: DataValidationArtifact):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_transformed_config = data_transformation_config
            self.data_validation_artifact = data_validation_artifact
            self._schema_config = read_yaml_file(file_path = SCHEMA_FILE_PATH)

        except Exception as e:
            raise MyException(e,sys)

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)

        except Exception as e:
            raise MyException(e,sys)

    def get_data_transformation_object(self) -> Pipeline:
        """
        Create and returns a data transformation object for the data,
        """
        logging.info("Entered get_data_transformation_object method of DataTransformation class")
        try:
            # Load schema configuration
            numerical_columns = self._schema_config['numerical_columns']
            categorical_columns = self._schema_config['categorical_columns']
            target_column = self._schema_config['target_column']
            mean_columns = self._schema_config['mean_columns']
            median_columns = self._schema_config['median_columns']
            nominal_columns = self._schema_config['nominal_columns']
            ordinal_columns = self._schema_config['ordinal_columns']
            ordinal_categories = self._schema_config['ordinal_categories']


            # intialize transformers

            # handling the missing values
            mean_pipeline = Pipeline([
                ('mean_imputer',SimpleImputer(strategy="mean")),
                ('scaler',StandardScaler())
            ])

            median_pipeline = Pipeline([
                ('median_imputer',SimpleImputer(strategy='median')),
                ('scaler',StandardScaler())
            ])

            # hadlling the categorical columns

            onehot_pipeline = Pipeline([
                ('mode_imputer',SimpleImputer(strategy='most_frequent')),
                ('onehot_encoder',OneHotEncoder(handle_unknown='ignore'))

            ])

            ordinal_pipeline = Pipeline([
                ('mode_imputer',SimpleImputer(strategy='most_frequent')),
                ('ordinal_encoder',OrdinalEncoder(categories=ordinal_categories))
            ])


            preprocessor = ColumnTransformer(transformers=[
                ('mean_pipeline',mean_pipeline,mean_columns),
                ('median_pipeline',median_pipeline,median_columns),
                ('onhehot_pipeline',onehot_pipeline,nominal_columns),
                ('rodinal_columns',ordinal_pipeline,ordinal_columns)
            ],remainder='passthrough')

            # Wrapping everything in a single pipeline

            final_pipeline = Pipeline(steps=[('Preprocessor',preprocessor)])
            logging.info("Final Pipeline Ready!!")
            return final_pipeline
        except Exception as e:
            logging.exception("Exception occurred in get_data_transformer_object method of DataTransformation class")
            raise MyException(e,sys) from e


    def drop_column(self, df):
        """Drop the id column if it exists."""
        logging.info("Dropping  column")

        drop_col = self._schema_config['drop_columns']

        df = df.drop(columns=drop_col, errors='ignore')

        return df

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        """ Intiates the data transforamtion component for the pipeline"""
        try:
            logging.info("Data Transformation Started !!")
            if not self.data_validation_artifact.validation_status:
                raise Exception(self.data_validation_artifact.message)

            # Load train and test data

            train_df = self.read_data(file_path = self.data_ingestion_artifact.training_file_path)
            test_df = self.read_data(file_path = self.data_ingestion_artifact.testing_file_path)
            logging.info("Train-Test data loaded")

            input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN])
            target_features_train_df = train_df[TARGET_COLUMN]
            logging.info("Input and Target cols defined for both train and test df.")


            input_features_test_df = test_df.drop(columns=[TARGET_COLUMN])
                
            target_features_test_df = test_df[TARGET_COLUMN]

            # Apply custom transformation in specified sequence

            input_features_train_df = self.drop_column(input_feature_train_df)
            input_features_test_df = self.drop_column(input_features_test_df)

            logging.info("Starting data transforamtion")
            preprocessor = self.get_data_transformation_object()
                                
            logging.info("Got the preprocessor object")


            logging.info("Initializing transformation for Training-Data")
            input_features_train_arr = preprocessor.fit_transform(input_features_train_df)
            logging.info("Initializing transformation for Testing-Data")
            input_features_test_arr = preprocessor.transform(input_features_test_df)

            logging.info("Applying SMOTEENN for handling imbalanced dataset.")
            smt = SMOTEENN(sampling_strategy = "minority")
            input_feature_train_final,target_feature_train_final = smt.fit_resample(
                input_features_train_arr,target_features_train_df)


            logging.info(
    f"X train after SMOTEENN: {input_feature_train_final.shape}"
)

            logging.info(
    f"y train after SMOTEENN: {target_feature_train_final.shape}"
)

            print("X:", input_feature_train_final.shape)
            print("y:", target_feature_train_final.shape)
            input_feature_test_final = input_features_test_arr
            target_feature_test_final = target_features_test_df

            logging.info("SMOTEENN applied to train-test df.")

            print("X train shape:", input_feature_train_final.shape)
            print("X train ndim:", input_feature_train_final.ndim)
            print("X train type:", type(input_feature_train_final))

            print("y train shape:", np.asarray(target_feature_train_final).shape)
            print("y train ndim:", np.asarray(target_feature_train_final).ndim)

            input_feature_train_final = input_feature_train_final.toarray()
            input_feature_test_final = input_feature_test_final.toarray()

            train_arr = np.hstack([input_feature_train_final,np.array(target_feature_train_final).reshape(-1, 1)])
            test_arr = np.hstack([input_feature_test_final,np.array(target_feature_test_final).reshape(-1,1)])

            logging.info("feature-target concatenation done for train-test df.")
            save_object(self.data_transformed_config.transformed_object_file_path,preprocessor)
            save_numpy_array_data(self.data_transformed_config.transformed_train_file_path,array=train_arr)
            save_numpy_array_data(self.data_transformed_config.transformed_test_file_path,array=test_arr)

            logging.info("Saving transformation objet and transformed files.")



            logging.info("Data transforamtion completed successfully")
            return DataTransformationArtifact(
                    transformed_object_file_path=self.data_transformed_config.transformed_object_file_path,
                    transformed_train_file_path = self.data_transformed_config.transformed_train_file_path,
                    transformed_test_file_path = self.data_transformed_config.transformed_test_file_path
                )


        except Exception as e:
            raise MyException(e,sys) from e