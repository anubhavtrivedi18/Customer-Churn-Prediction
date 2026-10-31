import sys

from src.exception import MyException
from src.logger import logging
from src.components.data_ingestion import DataIngestion
from src.components.data_validation import DataValidation
from src.entity.config_entity import (
    DataIngestionConfig,
    DataValidationConfig
)


def main():
    try:
        data_ingestion_config = DataIngestionConfig()

        data_ingestion = DataIngestion(
            data_ingestion_config=data_ingestion_config
        )

        data_ingestion_artifact = data_ingestion.initiate_data_ingestion()

        print("Data Ingestion Completed Successfully!")
        print(data_ingestion_artifact)

        data_validation_config = DataValidationConfig()

        data_validation = DataValidation(
            data_ingestion_artifact=data_ingestion_artifact,
            data_validation_config=data_validation_config
        )

        data_validation_artifact = data_validation.initiate_data_validation()

        print("Data Validation Completed Successfully!")
        print(data_validation_artifact)

    except Exception as e:
        raise MyException(e, sys) from e


if __name__ == "__main__":
    main()