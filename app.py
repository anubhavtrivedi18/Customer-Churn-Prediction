import os
import logging
import numbers
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError
from fastapi.staticfiles import StaticFiles

from src.entity.config_entity import ChurnPredictorConfig
from src.entity.s3_estimator import Proj1Estimator


app = FastAPI(title="Customer Churn Prediction API")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_ROWS = 5000

predictor_config = ChurnPredictorConfig()
model: Optional[Proj1Estimator] = None


def _get_model() -> Proj1Estimator:
    global model
    if model is None:
        model = Proj1Estimator(
            bucket_name=predictor_config.model_bucket_name,
            model_path=predictor_config.model_file_path,
        )
    return model


class CustomerInput(BaseModel):
    MonthlyRevenue: float = Field(
        ..., description="Monthly customer revenue. Observed range: -6.17 to 1223.38."
    )
    MonthlyMinutes: float = Field(
        ..., description="Monthly call minutes. Observed range: 0 to 7359."
    )
    TotalRecurringCharge: float = Field(
        ..., description="Monthly recurring charge. Observed range: -11 to 400."
    )
    RoamingCalls: float = Field(
        ..., description="Roaming call usage. Observed range: 0 to 1112.4."
    )
    PercChangeMinutes: float = Field(
        ..., description="Change in minutes usage. Observed range: -3875 to 5192."
    )
    PercChangeRevenues: float = Field(
        ..., description="Change in revenue. Observed range: -1107.7 to 2483.5."
    )
    DroppedCalls: float = Field(
        ..., description="Number of dropped calls. Observed range: 0 to 221.7."
    )
    BlockedCalls: float = Field(
        ..., description="Number of blocked calls. Observed range: 0 to 384.3."
    )
    UnansweredCalls: float = Field(
        ..., description="Number of unanswered calls. Observed range: 0 to 848.7."
    )
    CustomerCareCalls: float = Field(
        ..., description="Calls to customer care. Observed range: 0 to 327.3."
    )
    ThreewayCalls: float = Field(
        ..., description="Three-way calls. Observed range: 0 to 66."
    )
    ReceivedCalls: float = Field(
        ..., description="Received calls. Observed range: 0 to 2692.4."
    )
    OutboundCalls: float = Field(
        ..., description="Outbound calls. Observed range: 0 to 644.3."
    )
    InboundCalls: float = Field(
        ..., description="Inbound calls. Observed range: 0 to 519.3."
    )
    PeakCallsInOut: float = Field(
        ..., description="Peak-time calls. Observed range: 0 to 2090.7."
    )
    OffPeakCallsInOut: float = Field(
        ..., description="Off-peak calls. Observed range: 0 to 1474.7."
    )
    DroppedBlockedCalls: float = Field(
        ..., description="Dropped or blocked calls. Observed range: 0 to 411.7."
    )
    CallWaitingCalls: float = Field(
        ..., description="Calls using call waiting. Observed range: 0 to 212.7."
    )
    MonthsInService: int = Field(
        ..., description="Number of months as a customer. Observed range: 6 to 61."
    )
    UniqueSubs: int = Field(
        ..., description="Number of unique subscribers. Observed range: 1 to 196."
    )
    ActiveSubs: int = Field(
        ..., description="Number of active subscribers. Observed range: 0 to 53."
    )
    ServiceArea: str = Field(
        ...,
        description=(
            "Customer's service-area code. Select an exact value returned by GET /options."
        ),
    )
    Handsets: float = Field(
        ..., description="Number of handsets. Observed range: 0 to 24."
    )
    HandsetModels: float = Field(
        ..., description="Number of handset models. Observed range: 0 to 15."
    )
    CurrentEquipmentDays: float = Field(
        ..., description="Days using current equipment. Observed range: -5 to 1812."
    )
    AgeHH1: float = Field(
        ..., description="Age of household member 1. Observed range: 0 to 99."
    )
    AgeHH2: float = Field(
        ..., description="Age of household member 2. Observed range: 0 to 99."
    )
    HandsetRefurbished: Literal["Yes", "No"] = Field(
        ..., description="Whether the handset is refurbished: Yes or No."
    )
    HandsetWebCapable: Literal["Yes", "No"] = Field(
        ..., description="Whether the handset supports web: Yes or No."
    )
    BuysViaMailOrder: Literal["Yes", "No"] = Field(
        ..., description="Whether the customer buys via mail order: Yes or No."
    )
    RespondsToMailOffers: Literal["Yes", "No"] = Field(
        ..., description="Whether the customer responds to mail offers: Yes or No."
    )
    HandsetPrice: Literal[
        "10", "100", "130", "150", "180", "200", "240", "250",
        "30", "300", "40", "400", "500", "60", "80", "Unknown",
    ] = Field(..., description="Handset price category. Select one listed option.")
    MadeCallToRetentionTeam: Literal["Yes", "No"] = Field(
        ..., description="Whether the customer called the retention team: Yes or No."
    )
    CreditRating: Literal[
        "1-Highest",
        "2-High",
        "3-Good",
        "4-Medium",
        "5-Low",
        "6-VeryLow",
        "7-Lowest",
    ] = Field(..., description="Credit-rating category. Select one listed option.")
    PrizmCode: Literal["Other", "Rural", "Suburban", "Town"] = Field(
        ..., description="Customer's PRIZM area category."
    )
    MaritalStatus: Literal["No", "Unknown", "Yes"] = Field(
        ..., description="Marital-status category: Yes, No, or Unknown."
    )
    RetentionCalls: int = Field(
        ..., description="Retention-team calls. Observed range: 0 to 4."
    )
    RetentionOffersAccepted: int = Field(
        ..., description="Retention offers accepted. Observed range: 0 to 3."
    )
    ReferralsMadeBySubscriber: int = Field(
        ..., description="Subscriber referrals. Observed range: 0 to 35."
    )
    IncomeGroup: int = Field(
        ..., description="Income group code. Observed range: 0 to 9."
    )
    AdjustmentsToCreditRating: int = Field(
        ..., description="Credit-rating adjustments. Observed range: 0 to 25."
    )


CUSTOMER_FEATURE_COLUMNS = list(CustomerInput.__annotations__)


def _service_area_options() -> List[str]:
    configured_path = os.environ.get("CHURN_DATA_PATH")
    if configured_path:
        data_path = Path(configured_path)
    else:
        artifact_dir = Path(__file__).resolve().parent / "artifact"
        candidates = list(
            artifact_dir.glob("*/data_ingestion/feature_store/data.csv")
        )
        if not candidates:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Service-area choices are unavailable. Set CHURN_DATA_PATH "
                    "to the project's feature-store CSV."
                ),
            )
        data_path = max(candidates, key=lambda path: path.stat().st_mtime)

    if not data_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Configured data file does not exist: {data_path}",
        )

    try:
        areas = pd.read_csv(data_path, usecols=["ServiceArea"])["ServiceArea"]
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not read ServiceArea values from the configured data file.",
        ) from exc

    return sorted(areas.dropna().astype(str).unique().tolist())


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/options")
def input_options() -> Dict[str, List[str]]:
    return {
        "ServiceArea": _service_area_options(),
        "HandsetRefurbished": ["Yes", "No"],
        "HandsetWebCapable": ["Yes", "No"],
        "BuysViaMailOrder": ["Yes", "No"],
        "RespondsToMailOffers": ["Yes", "No"],
        "HandsetPrice": [
            "10", "100", "130", "150", "180", "200", "240", "250",
            "30", "300", "40", "400", "500", "60", "80", "Unknown",
        ],
        "MadeCallToRetentionTeam": ["Yes", "No"],
        "CreditRating": [
            "1-Highest",
            "2-High",
            "3-Good",
            "4-Medium",
            "5-Low",
            "6-VeryLow",
            "7-Lowest",
        ],
        "PrizmCode": ["Other", "Rural", "Suburban", "Town"],
        "MaritalStatus": ["No", "Unknown", "Yes"],
    }


def _probability_results(dataframe: pd.DataFrame) -> List[Dict[str, object]]:
    estimator = _get_model()
    predictions = estimator.predict(dataframe)
    classes, probabilities = estimator.predict_proba(dataframe)
    class_indexes = {str(label): index for index, label in enumerate(classes)}
    if "Yes" not in class_indexes or "No" not in class_indexes:
        raise ValueError("The classifier must have 'Yes' and 'No' classes.")

    churn_index = class_indexes["Yes"]
    non_churn_index = class_indexes["No"]
    results = []
    for prediction, row_probabilities in zip(predictions, probabilities):
        results.append(
            {
                "prediction": str(prediction),
                "churn_probability_percent": round(
                    float(row_probabilities[churn_index]) * 100, 2
                ),
                "non_churn_probability_percent": round(
                    float(row_probabilities[non_churn_index]) * 100, 2
                ),
            }
        )
    return results


def _normalize_column_name(column: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(column).lower())


def _resolve_id_column(columns: List[str]) -> str:
    candidates = [
        column
        for column in columns
        if _normalize_column_name(column) in {"id", "customerid"}
        and column not in CUSTOMER_FEATURE_COLUMNS
    ]
    if len(candidates) > 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "More than one possible ID column was found. Keep only one "
                "column named 'ID' or 'CustomerID'."
            ),
        )
    if not candidates:
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file must include an ID column, such as 'ID' or "
                "'CustomerID'."
            ),
        )
    return candidates[0]


def _read_uploaded_dataframe(
    contents: bytes, suffix: str, id_column: Optional[str]
) -> pd.DataFrame:
    id_dtype = {id_column: "string"} if id_column else None
    try:
        if suffix == ".csv":
            return pd.read_csv(BytesIO(contents), dtype=id_dtype)
        return pd.read_excel(
            BytesIO(contents),
            dtype=id_dtype,
            engine="openpyxl",
        )
    except ImportError as exc:
        logging.exception("Excel support dependency is missing")
        raise HTTPException(
            status_code=503,
            detail="Excel upload support is unavailable. Install the openpyxl dependency.",
        ) from exc
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded file. Check its format and column headers.",
        ) from exc


def _validate_upload_columns(
    dataframe: pd.DataFrame, id_column: Optional[str]
) -> Tuple[pd.DataFrame, List[str]]:
    if dataframe.empty:
        raise HTTPException(status_code=400, detail="The uploaded file contains no data rows.")
    if len(dataframe) > MAX_UPLOAD_ROWS:
        raise HTTPException(
            status_code=413,
            detail=f"Upload no more than {MAX_UPLOAD_ROWS} customer rows at a time.",
        )
    if dataframe.columns.duplicated().any():
        raise HTTPException(
            status_code=400,
            detail="The uploaded file contains duplicate column names.",
        )

    missing_columns = [
        column for column in CUSTOMER_FEATURE_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail={"message": "Required model input columns are missing.", "columns": missing_columns},
        )

    feature_frame = dataframe.loc[:, CUSTOMER_FEATURE_COLUMNS].copy()
    ignored_columns = [
        str(column)
        for column in dataframe.columns
        if column not in CUSTOMER_FEATURE_COLUMNS and column != id_column
    ]
    return feature_frame, ignored_columns


def _normalize_upload_row(row: pd.Series) -> Dict[str, object]:
    values = row.to_dict()
    handset_price = values.get("HandsetPrice")
    if isinstance(handset_price, numbers.Real) and not pd.isna(handset_price):
        if float(handset_price).is_integer():
            values["HandsetPrice"] = str(int(handset_price))
        else:
            values["HandsetPrice"] = str(handset_price)
    return values


@app.post("/predict")
def predict(customer: CustomerInput) -> Dict[str, object]:
    try:
        input_df = pd.DataFrame([customer.dict()])
        prediction = _probability_results(input_df)[0]
        return {
            "churn_prediction": prediction["prediction"],
            "churn_probability_percent": prediction["churn_probability_percent"],
            "non_churn_probability_percent": prediction["non_churn_probability_percent"],
        }
    except Exception as exc:
        logging.exception("Churn prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check the model and AWS configuration.",
        ) from exc


@app.post("/predict-file")
async def predict_file(
    file: UploadFile = File(...),
) -> Dict[str, object]:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=400,
            detail="Upload a .csv or .xlsx file.",
        )

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="The uploaded file must be 10 MB or smaller.",
        )

    # Read headers first so an ID column can be preserved as text in CSV files.
    try:
        if suffix == ".csv":
            headers = list(pd.read_csv(BytesIO(contents), nrows=0).columns)
        else:
            headers = list(
                pd.read_excel(
                    BytesIO(contents),
                    nrows=0,
                    engine="openpyxl",
                ).columns
            )
    except ImportError as exc:
        logging.exception("Excel support dependency is missing")
        raise HTTPException(
            status_code=503,
            detail="Excel upload support is unavailable. Install the openpyxl dependency.",
        ) from exc
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded file headers.",
        ) from exc

    resolved_id_column = _resolve_id_column(headers)
    dataframe = _read_uploaded_dataframe(contents, suffix, resolved_id_column)
    feature_frame, ignored_columns = _validate_upload_columns(
        dataframe,
        resolved_id_column,
    )

    validated_rows = []
    for row_number, (_, row) in enumerate(feature_frame.iterrows(), start=2):
        try:
            validated_rows.append(CustomerInput(**_normalize_upload_row(row)).dict())
        except ValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Invalid customer data on file row {row_number}.",
                    "errors": [
                        {"field": str(error["loc"][0]), "message": error["msg"]}
                        for error in exc.errors()
                    ],
                },
            ) from exc

    try:
        predictions = _probability_results(pd.DataFrame(validated_rows))
    except Exception as exc:
        logging.exception("Batch churn prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Batch prediction failed. Check the model and AWS configuration.",
        ) from exc

    output_rows = []
    for row_index, prediction in enumerate(predictions):
        if resolved_id_column:
            raw_id = dataframe.iloc[row_index][resolved_id_column]
            record_id = None if pd.isna(raw_id) else str(raw_id)
        else:
            raise HTTPException(
                status_code=400,
                detail="An ID column is required in the uploaded file.",
            )
        output_rows.append({"record_id": record_id, **prediction})

    return {
        "filename": filename,
        "row_count": len(output_rows),
        "ignored_columns": ignored_columns,
        "probability_note": "Percentages are model estimates, not guarantees.",
        "predictions": output_rows,
    }