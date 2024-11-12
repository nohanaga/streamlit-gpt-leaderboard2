from io import BytesIO, StringIO
from typing import Union, Optional, Callable

import streamlit as st

from src.config import ADMIN_USERNAME
from src.submissions.submissions_manager import SubmissionManager, SingleParticipantSubmissions

import pandas as pd
import numpy as np
import asyncio
import random
#from app import get_leaderboard, get_username
from src.display.leaderboard import Leaderboard
from src.config import (SUBMISSIONS_DIR, EVALUATOR_CLASS, EVALUATOR_KWARGS, PASSWORDS_DB_FILE,
                        ARGON2_KWARGS, ALLOWED_SUBMISSION_FILE_EXTENSION, MAX_NUM_USERS, ADMIN_USERNAME)
from src.evaluation.evaluator import Evaluator
import base64
from src.evaluation.gpteval import execute_eval

import random
import os

class SubmissionSidebar:
    def __init__(self, username: str, submission_manager: SubmissionManager,
                 submission_file_extension: Optional[str] = None,
                 submission_validator: Optional[Callable[[Union[StringIO, BytesIO]], bool]] = None):
        self.username = username
        self.submission_manager = submission_manager
        self.submission_file_extension = submission_file_extension
        self.submission_validator = submission_validator
        self.participant: SingleParticipantSubmissions = None
        self.file_uploader_key = f"file upload {username}"

    def init_participant(self):
        self.submission_manager.add_participant(self.username, exists_ok=True)
        self.participant = self.submission_manager.get_participant(self.username)

    def run_submission(self):
        st.sidebar.title(f"Hello {self.username}!")
        if self.username != ADMIN_USERNAME:
            st.sidebar.markdown("## Submit Your Results :fire:")
            self.submit()

    def submit(self):
        file_extension_suffix = f" (.{self.submission_file_extension})" if self.submission_file_extension else None
        submission_io_stream = st.sidebar.file_uploader("Upload your submission file" + file_extension_suffix,
                                                        type=self.submission_file_extension,
                                                        key=self.file_uploader_key)
        submission_name = st.sidebar.text_input('Submission name (optional):', value='', max_chars=30)
        if st.sidebar.button('Submit'):
            if submission_io_stream is None:
                st.sidebar.error('Please upload a submission file.')
            else:
                submission_failed = True
                with st.spinner('Uploading your submission...'):
                    # CSVファイルの読み込み
                    data = pd.read_csv(submission_io_stream)
                    st.session_state['data'] = data.replace(np.nan, '', regex=True)
                    st.write(st.session_state['data'])
                    submission_failed = False

                    # if self.submission_validator is None or self.submission_validator(submission_io_stream):
                    #     print("😎upload_submission", submission_io_stream, submission_name)
                    #     self._upload_submission(submission_io_stream, submission_name)
                    #     submission_failed = False
                if submission_failed:
                    st.sidebar.error("Upload failed. The submission file is not valid.")
                else:
                    st.sidebar.success("Upload successful!")
        
        # OKボタンを設置
        if st.button('Start evaluation', type="primary"):
            if submission_io_stream is None:
                st.error('Please upload a submission file.')
            else:
                # # CSVデータの処理
                json_result = asyncio.run(self._main("start"))
                self._upload_submission(submission_io_stream, submission_name, json_result)
                
                # 'scores'のデータをDataFrameに変換
                scores_df = pd.DataFrame(json_result['scores'])
                # CSVにエンコード
                csvfile = scores_df.to_csv(index=False)
                b64 = base64.b64encode(csvfile.encode()).decode()  # Base64エンコード

                # ダウンロードリンクを作成
                href = f'<a href="data:file/csv;base64,{b64}" download="results.csv">Download Results</a>'
                st.markdown(href, unsafe_allow_html=True)

    def _upload_submission(self, io_stream: Union[BytesIO, StringIO], submission_name: Optional[str] = None, json_result=None):
        self.init_participant()
        # CSV のコピー
        # JSONを保存するのはここ TODO
        self.participant.add_submission(io_stream, submission_name, self.submission_file_extension, json_result)
    
    # main coroutine
    async def _main(self, some_argument):
        # 非同期処理の実行
        average_score, each_rows = await self.process_csv(st.session_state['data'])
        
        # 解析結果の表示
        #if st.session_state['result'] is not None:
        if average_score is not None:
            # Show result
            st.write('Evaluation result:')
            st.write("average_score:")
            st.write(average_score)
            # record の値の合計を算出
            total_score = sum(average_score.values())
            st.write(f"total_score: {total_score:.3f}")

            # JSON用データ
            data = {
                "scores": each_rows,
                "average_score": average_score,
                "total_score": total_score
            }

            return data


    # データ処理関数
    async def process_csv(self, data):
        # 進捗バーの初期化
        progress_bar = st.progress(0)
        status_text = st.empty()
        status1 = st.status("Evaluating...", expanded=True)
        average_score = 0
        # データ行数
        total_rows = len(data)
        record = {"gpt_relevance": 0, "gpt_groundedness": 0, "gpt_similarity": 0, "gpt_fluency": 0, "ada_cosine_similarity": 0}
        #st.session_state['count'] = total_rows

        each_rows = []
        # 各行ごとに処理
        for i, row in data.iterrows():
            # ステータスの更新
            status_text.text(f'Evaluating: {i + 1}/{total_rows} rows')

            # 行のデータを処理
            #processed_row = await self._execute_eval_test(row)
            processed_row = await execute_eval(row)
            each_rows.append(processed_row)
            status1.write(str(i) + " : " + str(processed_row))
            # 進捗バーの更新
            progress_bar.progress((i + 1) / total_rows)

            # return_score の各キーに対して、record の対応するキーの値に加算
            for key, value in processed_row.items():
                if key in record:
                    record[key] += value

        # record の各キーをレコード数で除算して平均を計算
        if total_rows > 0:
            average_score = {key: round(value / total_rows, 3) for key, value in record.items()}

        # ステータスのクリア
        status_text.text('Evaluation complete')
        status1.update(label="Evaluation complete!", state="complete", expanded=False)
        return average_score, each_rows
