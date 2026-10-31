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


SERVICE_AREA_OPTIONS = tuple(
    """
    AIRAIK803 AIRAND864 AIRASH828 AIRAUG706 AIRBEA843 AIRCAM803 AIRCHA843 AIRCOL803 AIRELI252 AIRFLO843 AIRGAF864
    AIRGEO843 AIRGOL919 AIRGRE864 AIRGRN252 AIRGWD864 AIRHHI843 AIRHIC828 AIRJAC910 AIRKIN252 AIRMAR828 AIRMOR828
    AIRMYR843 AIRNEW803 AIRNWB252 AIRORA803 AIRROA252 AIRROC252 AIRSAV912 AIRSPA864 AIRSUM803 AIRWIL910 AIRWIN252
    AIRWYV828 APCANN443 APCBAL410 APCBEL443 APCBET240 APCEAS443 APCFCH703 APCFRD301 APCFRE540 APCLEE703 APCLXT240
    APCSAL443 APCSIL301 APCSVP443 APCWAL240 APCWAR540 APCWAS202 APCWES443 ATHHAM423 ATHJHC423 ATHKIN423 ATHLIM423
    ATLALB912 ATLANE678 ATLATH706 ATLATL678 ATLATN423 ATLBRU912 ATLCHA423 ATLCHN706 ATLCOL706 ATLDAL334 ATLDBL478
    ATLDOT334 ATLDTN706 ATLJCK901 ATLKNO423 ATLLAG706 ATLMAC912 ATLMDV478 ATLMEM901 ATLNOR678 ATLOPE334 ATLOVB601
    ATLPRR478 ATLROS678 ATLSEN662 ATLSWT423 ATLTUN601 ATLVAL229 ATLWMP870 AWIAPP920 AWIFON920 AWIGRE920 AWIMAN920
    AWIOSH920 AWISHE920 BIRBIR205 BIRJAS205 BIRPEL205 BOSBOS508 BOSBOS617 BOSBOS781 BOSBOS978 BOSBRA781 BOSFRA508
    BOSHYA508 BOSMAN603 BOSNSH603 BOSPRO401 BOSPTL207 BOSWOR508 CHIBLO309 CHICHA217 CHICHI312 CHICHI773 CHICPT219
    CHIDAV319 CHIDEC217 CHIDEK815 CHIGRY219 CHIJOL815 CHIKAN815 CHILAG630 CHILAG708 CHILAS815 CHIMTV618 CHINBK847
    CHIPEO309 CHIRCK815 CHIROC309 CHISPR217 CHIWAT319 DALATH903 DALCOM903 DALCRS903 DALDAL214 DALDEN903 DALDTN940
    DALFTW817 DALGRE903 DALGVL940 DALKAU469 DALMNW940 DALMVN903 DALSHR903 DALSLS903 DALSTV254 DENBOU303 DENCOL719
    DENDEN303 DENDIL970 DENFTC970 DENGLD303 DENGRE970 DENVAL970 DETADR517 DETANN734 DETBAT616 DETBNH616 DETBWG419
    DETDET313 DETFER248 DETFLI810 DETFRE419 DETJAC517 DETKAL616 DETLAN517 DETMON734 DETNOR248 DETPON248 DETROS810
    DETSOU248 DETTOL419 DETTRO248 DETWAS419 DETWYN734 FLNARC863 FLNAVO863 FLNBAR863 FLNBEL352 FLNBRD941 FLNBSH352
    FLNCLR813 FLNCOC407 FLNCRY352 FLNDAY904 FLNEUS352 FLNFRN904 FLNGAN352 FLNHNC863 FLNINV352 FLNJAC904 FLNKEH352
    FLNKEN321 FLNKIS407 FLNLAK941 FLNLEE352 FLNLKC904 FLNLKP863 FLNLKW863 FLNNPR813 FLNOCA352 FLNOGC904 FLNORL407
    FLNPAL904 FLNSAG904 FLNSAN407 FLNSAR941 FLNSEB863 FLNSMY904 FLNSTK904 FLNTAL850 FLNTAM813 FLNWAU863 FLNWIL352
    FLNWNH941 FLNWNP407 FLNZEP813 GCWBTR225 GCWGUL228 GCWLAF337 HARBRI203 HARHAR860 HARLON860 HARNEW203 HARNOR203
    HARSPR413 HARWAT203 HOPNAN570 HOUANG409 HOUBMT409 HOUBRN409 HOUCON409 HOUFRE409 HOUGLV409 HOUHOU281 HOUHUN936
    HOULJK409 HOUSPR832 HOUVIC361 HWIHON808 HWIMAU808 INDAND765 INDCIC317 INDCLO765 INDCRA765 INDFRA765 INDIND317
    INDLAF765 INDMUN765 INHBLU419 INHCEL419 INHCRI419 INHDFN419 INHFIN419 INHFTW219 INHHIC419 INHKOK765 INHSBN219
    INHVNW419 INUEVA812 IPMGDR616 IPMHOL616 IPMMID517 IPMSAG517 KCYCLI660 KCYELD316 KCYHES316 KCYHNV816 KCYHUT316
    KCYKCK913 KCYKCM816 KCYLAW913 KCYLEA913 KCYNEW316 KCYOTW785 KCYTOP913 KCYWAR660 KCYWIC316 LAUBRO601 LAUCLM662
    LAUGNW662 LAUHAT601 LAUJAC601 LAUNAT601 LAUTUP662 LAWBUM409 LAXALA562 LAXALB626 LAXANA714 LAXBEV310 LAXBUR818
    LAXCAN661 LAXCAS661 LAXCDG310 LAXCOR909 LAXCOV626 LAXCUL310 LAXDOW562 LAXIND760 LAXING310 LAXIRV949 LAXLAG949
    LAXLAN661 LAXLAX213 LAXLAX323 LAXMON323 LAXOAK805 LAXONT909 LAXOXN805 LAXPAS626 LAXPER909 LAXPSG760 LAXRIV909
    LAXSAN714 LAXSBN909 LAXSFN818 LAXSIM805 LAXSJC949 LAXSMN310 LAXSNP310 LAXVEN805 LAXVIC760 LAXVNY818 LAXWES310
    LOUCOR812 LOUETN502 LOUFRK502 LOULEX606 LOULOU502 LOUNAL812 MIABEL561 MIABON941 MIADEL561 MIADFD954 MIAFTL954
    MIAFTM941 MIAHWD954 MIAJUP561 MIAKEY305 MIAMAR305 MIAMIA305 MIANAP941 MIANDA305 MIAOKE863 MIAPOR941 MIAPSL561
    MIASUG305 MIAVER561 MIAWPB561 MILBEL608 MILBUR262 MILJAN608 MILJNC920 MILKEN414 MILLAK262 MILLKM920 MILMAD608
    MILMIL414 MILRAC414 MILWAT920 MILWAU262 MINBLO952 MINCOR763 MINMIN612 MINSTP612 NCRALB704 NCRASH336 NCRCHA704
    NCRCHE757 NCRCLA919 NCRCON704 NCRCRY919 NCRDNN910 NCRDUR919 NCRFAY910 NCRGRB757 NCRGRE336 NCRGST704 NCRHAR704
    NCRHEN252 NCRHGP336 NCRKAN704 NCRLUM910 NCRMID704 NCRMIL803 NCRMON704 NCRNWN757 NCROXF919 NCRPIT919 NCRPOR757
    NCRPTR804 NCRRAL919 NCRRIC804 NCRROC803 NCRSAL704 NCRSAN919 NCRSHE704 NCRSIC919 NCRSMF757 NCRSMI919 NCRSPN910
    NCRVIR757 NCRWAK919 NCRWIN336 NCRWLM757 NCRYOR803 NEVCHU619 NEVCOR619 NEVELC619 NEVENC760 NEVESC760 NEVLAU702
    NEVLMS619 NEVLVS702 NEVNAT619 NEVOCN760 NEVPOW619 NEVSDG619 NMCGDJ970 NMCPUE719 NMXABI915 NMXALB505 NMXAMA806
    NMXDEL830 NMXEAG830 NMXELP915 NMXFLA520 NMXLAR956 NMXLCR505 NMXLSA505 NMXLUB806 NMXPLA806 NMXPRE520 NMXSAN505
    NMXSAN915 NMXTER915 NMXYUM520 NNYALB518 NNYBUF716 NNYBUR914 NNYPOU914 NNYROC716 NNYSYR315 NNYUTI315 NOLBOG504
    NOLKEN504 NOLPIC601 NOLPOH504 NORALX320 NORDUL218 NORFAR701 NORFER218 NORFRM218 NORMAN507 NOROWT507 NORRDW651
    NORROC507 NORSTC320 NORZIM763 NSHCOL615 NSHNSH615 NSHSPR615 NVUGAR775 NVUREN775 NYCBRO917 NYCCIT914 NYCETT732
    NYCFHD732 NYCJER201 NYCKPT732 NYCMAN917 NYCMTK914 NYCNAS516 NYCNEW201 NYCNEW732 NYCNEW908 NYCNEW973 NYCPAS973
    NYCPLA908 NYCPLS609 NYCQUE917 NYCSUF516 NYCTMR732 NYCWHI914 NYCWOO732 OHHASH606 OHHATH740 OHHCAM740 OHHCHA304
    OHHCHI740 OHHCLA304 OHHFAI304 OHHGAL740 OHHHUN304 OHHJAC740 OHHMOR304 OHHMTA740 OHHPAR304 OHHPOR740 OHHWAV740
    OHHZAN740 OHIAKR330 OHIALL330 OHIASH419 OHIAUR330 OHIBCY419 OHIBER440 OHIBUT419 OHICAN330 OHICIN513 OHICIR740
    OHICLB330 OHICLE216 OHICOL614 OHICOV606 OHIDAY937 OHIDEL740 OHIELY440 OHIHAR330 OHIKEN330 OHILAN740 OHILAW812
    OHILEB513 OHILRN440 OHIMAN419 OHIMAR740 OHIMED330 OHIMID513 OHIMRY937 OHIMTV740 OHINCA937 OHINEW740 OHINOR419
    OHIOBE440 OHIOXF513 OHIPIQ937 OHIPSV440 OHIRAV330 OHISAN419 OHISGF937 OHITRO937 OHITRT937 OHIWAR330 OHIWIL937
    OHIWOO330 OHIXEN937 OHIYNG330 OKCARD580 OKCBAR918 OKCBEN501 OKCBTN501 OKCCAB501 OKCCHC405 OKCCON501 OKCEMP316
    OKCEND580 OKCFAY501 OKCFTS501 OKCJUN785 OKCLAW580 OKCLRK501 OKCMAN785 OKCMCA918 OKCMCP316 OKCMUS918 OKCOKC405
    OKCSAL785 OKCSTW405 OKCTUL918 OKCWIC940 OMAAMS515 OMACDR319 OMADES515 OMAGRN515 OMAIWC319 OMALNC402 OMANEW515
    OMAOMA402 PHIALL484 PHIARD610 PHIAVD610 PHIBRI856 PHICAM302 PHICAP609 PHICHC215 PHICTR610 PHIDOV302 PHIELK443
    PHIGEO302 PHIJEN215 PHILAN717 PHIMER609 PHIMID302 PHIMIL302 PHIMIV856 PHIMUL609 PHIPHI215 PHIPLS609 PHIRDN484
    PHISAL856 PHISCR717 PHITRT609 PHIVIN609 PHIWIL302 PHIWLW609 PHXGLE623 PHXPHX602 PHXSCO480 PHXTUC520 PITBUT412
    PITCAR412 PITCOR412 PITFOR412 PITGIB412 PITGRE412 PITHOM412 PITIND724 PITMNG412 PITMON412 PITNEW412 PITROC412
    PITSOM814 PITUNT412 PITWAS412 PITWEI304 PITWHE304 SANAUS512 SANCOC254 SANCRP512 SANFRE830 SANGEO512 SANGIL830
    SANKER830 SANKIL254 SANLAM512 SANMCA210 SANREF361 SANROM956 SANSAN210 SANSMC512 SANTEM254 SANWOO361 SDABRK605
    SDASFL605 SDAWTR605 SEAABN253 SEAALB541 SEABEA503 SEABLG360 SEABLV425 SEABOI208 SEACDA208 SEACHE360 SEACOR541
    SEADAL503 SEAEUG541 SEAEVE425 SEALEW208 SEALVW360 SEAMON503 SEAMTV360 SEAOKH360 SEAOLY360 SEAPOR503 SEASAL503
    SEASEA206 SEASIL360 SEASPO509 SEATAC253 SEAVAN360 SEWGTP541 SEWHDR541 SEWKEN509 SEWKHF541 SEWMED541 SEWMLF541
    SEWPAS509 SEWPEN541 SEWPRO509 SEWROS541 SEWSUN509 SEWWAL509 SEWYAK509 SFRCBL408 SFRCON925 SFRCRU831 SFRDAN925
    SFRDSR925 SFRFAI707 SFRHAY510 SFROAK510 SFROAK925 SFRPAL650 SFRRCM510 SFRROC916 SFRSAC916 SFRSCL408 SFRSFR415
    SFRSFS650 SFRSGS530 SFRSMO650 SFRSRO707 SFRVAC707 SFRWLC925 SFRWOO530 SFRWTV831 SFURED530 SFUSAC530 SHECAR717
    SHECHA717 SHEEDI540 SHEFTR540 SHEHAG301 SHEHAR540 SHEMAR304 SHEMYE301 SHEWIN540 SHEYOR717 SLCKAY801 SLCOGD801
    SLCPRK435 SLCPRO801 SLCSLC801 SLCTOO801 SLUSTG435 STLCHA636 STLCHE636 STLCMB573 STLCOL618 STLCPG573 STLCRD618
    STLFUL573 STLHNB573 STLJEF573 STLJOP417 STLJOS816 STLOZA573 STLPIT316 STLPRB573 STLQUI217 STLROL573 STLSED660
    STLSPR417 STLSTL314 VAHCHL804 VAHDAN804 VAHLYN804 VAHMTN540 VAHRAD540 VAHROA540 VAHSTA540 VAHWAY540
    """.split()
)


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
    ServiceArea: Literal[*SERVICE_AREA_OPTIONS] = Field(
        ...,
        description="Customer's service-area code. Select one listed option.",
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
    return list(SERVICE_AREA_OPTIONS)


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

    