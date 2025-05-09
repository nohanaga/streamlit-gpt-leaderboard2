from typing import Dict

import streamlit as st
import pandas as pd

from src.config import SHOW_TOP_K_ONLY, ADMIN_USERNAME
from src.evaluation.evaluator import Evaluator
from src.submissions.submissions_manager import SubmissionManager, SingleParticipantSubmissions


class Leaderboard:
    def __init__(self, submissions_manager: SubmissionManager,
                 evaluator: Evaluator):
        self.submissions_manager = submissions_manager
        self.evaluator = evaluator
        
    # このキャッシュを効かせると、ファイルを変更した際にdataframe の内容が更新されない
    #@st.cache(hash_funcs={SingleParticipantSubmissions: lambda x: x.submissions_hash()}, show_spinner=False, suppress_st_warning=True)
    #@st.cache_data(hash_funcs={SingleParticipantSubmissions: lambda x: x.submissions_hash()}, show_spinner=False)
    def _get_sorted_leaderboard(_self, participants_dict: Dict[str, SingleParticipantSubmissions],
                                username: str) -> pd.DataFrame:
        for participant in participants_dict.values():
            participant.update_results(_self.evaluator)
        #metric_names = [metric.name() for metric in self.evaluator.metrics()]
        #print("self.evaluator.metrics()", metric_names)
        metric_names = ['score']
        # leaderboard = pd.DataFrame([[pname, SingleParticipantSubmissions.get_datetime_from_path(best_result[0]),
        #                              *best_result[1]] for pname, 
        #                              best_result in [(pname, p.get_best_result()) for pname, p in participants_dict.items()]
        #                             if best_result is not None],
        #                            columns=['Competitor', 'Submission Time', *metric_names])

        # ステップ 1: 各参加者の最良結果を取得する
        best_results = [
            (pname, p.get_best_result()) 
            for pname, p in participants_dict.items()
        ]
        # ステップ 2: 最良結果が None でないエントリをフィルタリングする
        filtered_best_results = [
            (pname, best_result) 
            for pname, best_result in best_results 
            if best_result is not None
        ]
        # ステップ 3: 必要な情報を抽出してリストを生成する
        data = [
            [
                pname,
                SingleParticipantSubmissions.get_datetime_from_path(best_result[0]),
                best_result[1]
            ] 
            for pname, best_result in filtered_best_results
        ]
        # ステップ 4: データフレームを作成する
        leaderboard = pd.DataFrame(data, columns=['Competitor', 'Submission Time', 'score'])
        
        # カスタムオブジェクトを適切な型に変換
        leaderboard['score'] = leaderboard['score'].apply(lambda x: x.value)

        leaderboard = leaderboard.sort_values(by=metric_names + ['Submission Time'],
                                              ascending=[False] * len(metric_names) + [True], ignore_index=True)
        
        leaderboard.index += 1
        if username != ADMIN_USERNAME:
            leaderboard = leaderboard.iloc[:SHOW_TOP_K_ONLY]
        return leaderboard

    def display_leaderboard(self, username: str, leaderboard_placeholder = None):
        leaderboard = self._get_sorted_leaderboard(self.submissions_manager.participants, username)
        if leaderboard_placeholder is not None:
            leaderboard_placeholder.table(leaderboard)
        else:
            st.table(leaderboard)
