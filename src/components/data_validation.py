import json
import sys
import os

import pandas as pd

from pandas import DataFrame

from src.exception import MyException
from src.logger import logging
from src.utils.main_utils import read_yaml_file
from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from src.entity.config_entity import DataValidationConfig
from src.constants import SCHEMA_FILE_PATH


class DataValidation:
    def __init__(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_config: DataValidationConfig):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config =read_yaml_file(file_path=SCHEMA_FILE_PATH)
        except Exception as e:
            raise MyException(e,sys)

    def validate_number_of_columns(self, dataframe: DataFrame) -> bool:
        try:
            expected_columns = set(self._schema_config["columns"])
            actual_columns = set(dataframe.columns)
            duplicate_columns = dataframe.columns[dataframe.columns.duplicated()].tolist()
            missing_columns = sorted(expected_columns - actual_columns)
            unexpected_columns = sorted(actual_columns - expected_columns)
            status = not missing_columns and not unexpected_columns and not duplicate_columns
            logging.info(
                "Dataframe columns match schema: %s; missing=%s, unexpected=%s, duplicates=%s",
                status,
                missing_columns,
                unexpected_columns,
                duplicate_columns,
            )
            return status
        except Exception as e:
            raise MyException(e, sys)

    def is_column_exist(self, df: DataFrame) -> bool:
        try:
            missing_columns = sorted(set(self._schema_config["columns"]) - set(df.columns))
            if missing_columns:
                logging.info("Missing schema columns: %s", missing_columns)
            return not missing_columns
        except Exception as e:
            raise MyException(e, sys) from e

    def validate_data_types(self, dataframe: DataFrame) -> bool:
        try:
            invalid_columns = []
            for column in self._schema_config["numerical_columns"]:
                if column in dataframe and not pd.api.types.is_numeric_dtype(dataframe[column]):
                    invalid_columns.append(column)

            categorical_columns = (
                self._schema_config["categorical_columns"]
                + self._schema_config["target_column"]
            )
            for column in categorical_columns:
                if column in dataframe and pd.api.types.is_numeric_dtype(dataframe[column]):
                    invalid_columns.append(column)

            if invalid_columns:
                logging.info("Columns with invalid data types: %s", invalid_columns)
            return not invalid_columns
        except Exception as e:
            raise MyException(e, sys) from e

    @staticmethod
    def read_data(file_path) -> DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise MyException(e, sys)
        

    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            validation_error_msg = ""
            logging.info("Starting data validation")
            train_df, test_df = (DataValidation.read_data(file_path=self.data_ingestion_artifact.training_file_path),
                                 DataValidation.read_data(file_path=self.data_ingestion_artifact.testing_file_path))

            # Validate schema columns for train/test dataframes.
            status = self.validate_number_of_columns(dataframe=train_df)
            if not status:
                validation_error_msg += "Training dataframe columns do not match the schema. "
            else:
                logging.info("Training dataframe columns match the schema.")

            status = self.validate_number_of_columns(dataframe=test_df)
            if not status:
                validation_error_msg += "Test dataframe columns do not match the schema. "
            else:
                logging.info("Test dataframe columns match the schema.")

            # Check required schema columns independently for useful diagnostics.
            status = self.is_column_exist(df=train_df)
            if not status:
                validation_error_msg += "Training dataframe is missing required schema columns. "
            else:
                logging.info("Training dataframe contains all required schema columns.")

            if not self.validate_data_types(train_df):
                validation_error_msg += "Training dataframe contains columns with invalid data types. "

            status = self.is_column_exist(df=test_df)
            if not status:
                validation_error_msg += "Test dataframe is missing required schema columns. "
            else:
                logging.info("Test dataframe contains all required schema columns.")

            if not self.validate_data_types(test_df):
                validation_error_msg += "Test dataframe contains columns with invalid data types. "

            validation_status = len(validation_error_msg) == 0

            data_validation_artifact = DataValidationArtifact(
                validation_status=validation_status,
                message=validation_error_msg,
                validation_report_file_path=self.data_validation_config.validation_report_file_path
            )

            # Ensure the directory for validation_report_file_path exists
            report_dir = os.path.dirname(self.data_validation_config.validation_report_file_path)
            os.makedirs(report_dir, exist_ok=True)

            # The report path uses YAML extension; JSON is valid YAML.
            validation_report = {
                "validation_status": validation_status,
                "message": validation_error_msg.strip()
            }

            with open(self.data_validation_config.validation_report_file_path, "w", encoding="utf-8") as report_file:
                json.dump(validation_report, report_file, indent=4)

            logging.info("Data validation artifact created and saved to JSON file.")
            logging.info(f"Data validation artifact: {data_validation_artifact}")
            return data_validation_artifact
        except Exception as e:
            raise MyException(e, sys) from e