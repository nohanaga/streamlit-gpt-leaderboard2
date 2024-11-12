import pandas as pd
from bokeh.models import HoverTool, DatetimeTickFormatter
from bokeh.palettes import all_palettes
from bokeh.plotting import figure
import streamlit as st

from src.evaluation.evaluator import Evaluator
from src.submissions.submissions_manager import SingleParticipantSubmissions

class PersonalProgress:
    def __init__(self, participant_submissions: SingleParticipantSubmissions, evaluator: Evaluator):
        self.participant_submissions = participant_submissions
        self.evaluator = evaluator
        self.metric_names = ["score"]#[metric.name() for metric in self.evaluator.metrics()]
        self.submission_name_column = 'Submission name'
        self.submission_time_column = 'Submission time'

    def show_progress(self, progress_plot_placeholder=None):
        bokeh_plot = self._get_bokeh_progress_plot()
        if progress_plot_placeholder is not None:
            progress_plot_placeholder.bokeh_chart(bokeh_plot, use_container_width=True)
        else:
            st.bokeh_chart(bokeh_plot, use_container_width=True)

   #@st.cache_data(show_spinner=False)
    # @st.cache(hash_funcs={SingleParticipantSubmissions: lambda x: x.submissions_hash()},
    #           allow_output_mutation=True, show_spinner=False, suppress_st_warning=True)
    def _get_bokeh_progress_plot(_self):
        _self.participant_submissions.update_results(evaluator=_self.evaluator)

        # progress_df = pd.DataFrame([[self.participant_submissions.get_submission_name_from_path(submission_filepath),
        #                              self.participant_submissions.get_datetime_from_path(submission_filepath),
        #                              *[res.value for res in submission_results]]
        #                             for submission_filepath, submission_results in
        #                             self.participant_submissions.results.items()],
        #                            columns=[self.submission_name_column, self.submission_time_column,
        #                                     *self.metric_names])

        # ステップ 1: 各提出ファイルパスと提出結果を取得する
        submissions = list(_self.participant_submissions.results.items())

        # ステップ 2: 各提出ファイルパスと提出結果から必要な情報を抽出する
        submission_data = [
            [
                _self.participant_submissions.get_submission_name_from_path(submission_filepath),
                _self.participant_submissions.get_datetime_from_path(submission_filepath),
                submission_results.value  # ここでF1の値を取得
            ]
            for submission_filepath, submission_results in submissions
        ]

        # ステップ 3: データフレームを作成する
        progress_df = pd.DataFrame(
            submission_data,
            columns=[_self.submission_name_column, _self.submission_time_column, 'score']
        )

        progress_df.sort_values(by=_self.submission_time_column, inplace=True)
        ret = _self._create_bokeh_plot_from_df(progress_df, _self.submission_time_column, _self.submission_name_column)
  
        return ret

    def _create_bokeh_plot_from_df(self, progress_df: pd.DataFrame, submission_time_col: str, submission_name_col: str):
        p = figure(x_axis_type='datetime')
        for column, color in zip(self.metric_names, get_colormap(len(self.metric_names))):
            glyph_line = p.line(
                x=submission_time_col,
                y=column,
                legend_label=" " + column,
                source=progress_df,
                color=color,
            )
            glyph_scatter = p.scatter(
                x=submission_time_col,
                y=column,
                legend_label=" " + column,
                source=progress_df,
                color=color,
                marker='circle',
                fill_alpha=0.3,
            )
            p.add_tools(HoverTool(
                tooltips=[(submission_time_col, f'@{{{submission_time_col}}}{{%Y-%m-%d %H:%M:%S}}'),
                          (submission_name_col, f'@{{{submission_name_col}}}'),
                          (column, f'@{{{column}}}')],
                formatters={f'@{{{submission_time_col}}}': 'datetime'},
                mode='vline',
                renderers=[glyph_line if len(progress_df) > 1 else glyph_scatter],
            ))
        
        p.xaxis.formatter=DatetimeTickFormatter(days="%m/%d %H:%M",
            months="%m/%d %H:%M",
            hours="%m/%d %H:%M",
            minutes="%m/%d %H:%M")
        
        p.legend.click_policy = "hide"
        return p


def get_colormap(n_cols):
    if n_cols <= 10:
        colormap = all_palettes["Category10"][10][:n_cols]
    elif n_cols <= 20:
        colormap = all_palettes["Category20"][n_cols]
    else:
        colormap = all_palettes["Category20"][20] * int(n_cols / 20 + 1)
        colormap = colormap[:n_cols]
    return colormap
