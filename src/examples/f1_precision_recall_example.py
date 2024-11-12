import json
from io import BytesIO, StringIO

from pathlib import Path
from typing import Tuple, Type, Dict, Union
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

from src.examples.generate_predictions import GROUND_TRUTH_DATA
from src.evaluation.evaluator import Evaluator
from src.evaluation.metric import Metric

import pandas as pd
import streamlit as st

class F1(Metric):
    @classmethod
    def name(cls) -> str:
        return 'score'

    @classmethod
    def higher_is_better(cls) -> bool:
        return True

    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return f"score(value={self.value})"

# class Precision(Metric):
#     @classmethod
#     def name(cls) -> str:
#         return 'Precision'

#     @classmethod
#     def higher_is_better(cls) -> bool:
#         return True

#     def __init__(self, value):
#         super().__init__(value)

#     def __repr__(self):
#         return f"Precision(value={self.value})"
    
# class Recall(Metric):
#     @classmethod
#     def name(cls) -> str:
#         return 'Recall'

#     @classmethod
#     def higher_is_better(cls) -> bool:
#         return True
    
#     def __init__(self, value):
#         super().__init__(value)

#     def __repr__(self):
#         return f"Recall(value={self.value})"

class ExampleEvaluator(Evaluator):
    def __init__(self):
        super().__init__()
        #self.true_label_dict = GROUND_TRUTH_DATA
        #self.labels_array = np.array(list(self.true_label_dict.values()))

    @classmethod
    def metrics(cls) -> Tuple[Type[Metric], ...]:
        #return (F1, Precision, Recall)
        return (F1)

    def evaluate(self, filepath: Path) -> Tuple[Metric, ...]:
        if filepath.suffix == '.json':
            with filepath.open('r') as f:
                predictions = json.load(f)

            return self._evaluate_prediction_dict(predictions)
        else:
            return None
        

    def _evaluate_prediction_dict(self, predictions: Dict[str, int]) -> Tuple[Metric, ...]:
        # preds_array = np.array([predictions.get(k, 1-self.true_label_dict[k])
        #                         for k in self.true_label_dict.keys()])
        precision = 0.22
        recall = 0.11
        f1 = predictions.get('total_score', 0)
        # precision, recall, f1, _ = precision_recall_fscore_support(y_true=self.labels_array,
        #                                                            y_pred=preds_array,
        #                                                            average='binary')
        #return (F1(f1), Precision(precision), Recall(recall))
        return (F1(f1))

    def validate_submission(self, io_stream: Union[StringIO, BytesIO]) -> bool:
        io_stream.seek(0)
        try:
            print("🥶🥶validate_submission", io_stream)
            self._evaluate_prediction_dict(json.load(io_stream))
            return True
        except:
            return False
        


    