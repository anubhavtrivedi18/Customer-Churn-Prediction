import sys
import numpy as np
from src.entity.config_entity import ChurnPredictorConfig
from src.entity.s3_estimator import Proj1Estimator
from src.exception import MyException
from src.logger import logging
from pandas import DataFrame

class CustomerData:
    def __init__(self, MonthlyRevenue,
                 MonthlyMinutes,
                 TotalRecurringCharge,
                 RoamingCalls,
                 PercChangeMinutes,
                 PercChangeRevenues,
                 DroppedCalls,
                 BlockedCalls,
                 UnansweredCalls,
                 CustomerCareCalls,
                 ThreewayCalls,
                 ReceivedCalls,
                 OutboundCalls,
                 InboundCalls,
                 PeakCallsInOut,
                 OffPeakCallsInOut,
                 DroppedBlockedCalls,
                 CallWaitingCalls,
                 MonthsInService,
                 UniqueSubs,
                 ActiveSubs,
                 ServiceArea,
                 Handsets,
                 HandsetModels,
                 CurrentEquipmentDays,
                 AgeHH1,
                 AgeHH2,
                 HandsetRefurbished,
                 HandsetWebCapable,
                 BuysViaMailOrder,
                 RespondsToMailOffers,
                 HandsetPrice,
                 MadeCallToRetentionTeam,
                 CreditRating,
                 PrizmCode,
                 MaritalStatus,
                 RetentionCalls,
                 RetentionOffersAccepted,
                 ReferralsMadeBySubscriber,
                 IncomeGroup,
                 AdjustmentsToCreditRating):
        try:
            self.MonthlyRevenue = MonthlyRevenue
            self.MonthlyMinutes = MonthlyMinutes
            self.TotalRecurringCharge = TotalRecurringCharge
            self.RoamingCalls = RoamingCalls
            self.PercChangeMinutes = PercChangeMinutes
            self.PercChangeRevenues = PercChangeRevenues
            self.DroppedCalls = DroppedCalls
            self.BlockedCalls = BlockedCalls
            self.UnansweredCalls = UnansweredCalls
            self.CustomerCareCalls = CustomerCareCalls
            self.ThreewayCalls = ThreewayCalls
            self.ReceivedCalls = ReceivedCalls
            self.OutboundCalls = OutboundCalls
            self.InboundCalls = InboundCalls
            self.PeakCallsInOut = PeakCallsInOut
            self.OffPeakCallsInOut = OffPeakCallsInOut
            self.DroppedBlockedCalls = DroppedBlockedCalls
            self.CallWaitingCalls = CallWaitingCalls
            self.MonthsInService = MonthsInService
            self.UniqueSubs = UniqueSubs
            self.ActiveSubs = ActiveSubs
            self.ServiceArea = ServiceArea
            self.Handsets = Handsets
            self.HandsetModels = HandsetModels
            self.CurrentEquipmentDays = CurrentEquipmentDays
            self.AgeHH1 = AgeHH1
            self.AgeHH2 = AgeHH2
            self.HandsetRefurbished = HandsetRefurbished
            self.HandsetWebCapable = HandsetWebCapable
            self.BuysViaMailOrder = BuysViaMailOrder
            self.RespondsToMailOffers = RespondsToMailOffers
            self.HandsetPrice = HandsetPrice
            self.MadeCallToRetentionTeam = MadeCallToRetentionTeam
            self.CreditRating = CreditRating
            self.PrizmCode = PrizmCode
            self.MaritalStatus = MaritalStatus
            self.RetentionCalls = RetentionCalls
            self.RetentionOffersAccepted = RetentionOffersAccepted
            self.ReferralsMadeBySubscriber = ReferralsMadeBySubscriber
            self.IncomeGroup = IncomeGroup
            self.AdjustmentsToCreditRating = AdjustmentsToCreditRating
        except Exception as e:
            raise MyException(e, sys)


    def get_customer_input_data_frame(self) -> DataFrame:
        try:
            customer_input_data = self.get_customer_data_as_dict()
            return DataFrame(customer_input_data)
        except Exception as e:
            raise MyException(e,sys) from e

    def get_customer_data_as_dict(self):
        try:
            custom_data_input = {
                "MonthlyRevenue": [self.MonthlyRevenue],
                "MonthlyMinutes": [self.MonthlyMinutes],
                "TotalRecurringCharge": [self.TotalRecurringCharge],
                "RoamingCalls": [self.RoamingCalls],
                "PercChangeMinutes": [self.PercChangeMinutes],
                "PercChangeRevenues": [self.PercChangeRevenues],
                "DroppedCalls": [self.DroppedCalls],
                "BlockedCalls": [self.BlockedCalls],
                "UnansweredCalls": [self.UnansweredCalls],
                "CustomerCareCalls": [self.CustomerCareCalls],
                "ThreewayCalls": [self.ThreewayCalls],
                "ReceivedCalls": [self.ReceivedCalls],
                "OutboundCalls": [self.OutboundCalls],
                "InboundCalls": [self.InboundCalls],
                "PeakCallsInOut": [self.PeakCallsInOut],
                "OffPeakCallsInOut": [self.OffPeakCallsInOut],
                "DroppedBlockedCalls": [self.DroppedBlockedCalls],
                "CallWaitingCalls": [self.CallWaitingCalls],
                "MonthsInService": [self.MonthsInService],
                "UniqueSubs": [self.UniqueSubs],
                "ActiveSubs": [self.ActiveSubs],
                "ServiceArea": [self.ServiceArea],
                "Handsets": [self.Handsets],
                "HandsetModels": [self.HandsetModels],
                "CurrentEquipmentDays": [self.CurrentEquipmentDays],
                "AgeHH1": [self.AgeHH1],
                "AgeHH2": [self.AgeHH2],
                "HandsetRefurbished": [self.HandsetRefurbished],
                "HandsetWebCapable": [self.HandsetWebCapable],
                "BuysViaMailOrder": [self.BuysViaMailOrder],
                "RespondsToMailOffers": [self.RespondsToMailOffers],
                "HandsetPrice": [self.HandsetPrice],
                "MadeCallToRetentionTeam": [self.MadeCallToRetentionTeam],
                "CreditRating": [self.CreditRating],
                "PrizmCode": [self.PrizmCode],
                "MaritalStatus": [self.MaritalStatus],
                "RetentionCalls": [self.RetentionCalls],
                "RetentionOffersAccepted": [self.RetentionOffersAccepted],
                "ReferralsMadeBySubscriber": [self.ReferralsMadeBySubscriber],
                "IncomeGroup": [self.IncomeGroup],
                "AdjustmentsToCreditRating": [self.AdjustmentsToCreditRating],
            }
            logging.info("Created vehicle data dict")
            logging.info("Exited get_vehicle_data_as_dict method as VehicleData class")


            return custom_data_input
        except Exception as e:
            raise MyException(e, sys)


class ChurnDataPredictor:
    def __init__(self,prediction_pipeline_config: ChurnPredictorConfig = ChurnPredictorConfig(),) -> None:
        try:
            self.prediction_pipeline_config = prediction_pipeline_config
        except Exception as e:
            raise MyException(e,sys)

    def predict(self, dataframe: DataFrame) -> np.ndarray:
        try:
            logging.info("Entered predict method of VehcileClassifier Class")
            model = Proj1Estimator(
                bucket_name=self.prediction_pipeline_config.model_bucket_name,
                model_path = self.prediction_pipeline_config.model_file_path
            )

            result = model.predict(dataframe)
            return result

        except Exception as e:
            raise MyException(e,sys)

    

        
        