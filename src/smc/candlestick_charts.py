"""
Candlestick Pattern Visualization Module
Generates educational charts for candlestick patterns
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os


class CandlestickPatternVisualizer:
    """Tạo hình ảnh minh họa các mô hình nến Nhật"""
    
    def __init__(self, output_dir: str = "docs/images/candlesticks"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.colors = {
            'bullish': '#26A69A',  # Green
            'bearish': '#EF5350',  # Red
            'neutral': '#78909C',  # Gray
            'background': '#1E1E1E',
            'grid': '#333333',
            'text': '#FFFFFF'
        }
    
    def _create_candle_data(self, pattern_type: str) -> pd.DataFrame:
        """Tạo dữ liệu mẫu cho từng pattern"""
        
        patterns = {
            # Single Candle Patterns
            'doji': {
                'data': [
                    {'open': 100, 'high': 105, 'low': 95, 'close': 100.1}
                ],
                'title': 'Doji'
            },
            'dragonfly_doji': {
                'data': [
                    {'open': 100, 'high': 100.5, 'low': 92, 'close': 100}
                ],
                'title': 'Dragonfly Doji'
            },
            'gravestone_doji': {
                'data': [
                    {'open': 100, 'high': 108, 'low': 99.5, 'close': 100}
                ],
                'title': 'Gravestone Doji'
            },
            'hammer': {
                'data': [
                    {'open': 100, 'high': 101, 'low': 92, 'close': 100.5}
                ],
                'title': 'Hammer'
            },
            'hanging_man': {
                'data': [
                    {'open': 100.5, 'high': 101, 'low': 92, 'close': 100}
                ],
                'title': 'Hanging Man'
            },
            'shooting_star': {
                'data': [
                    {'open': 100, 'high': 108, 'low': 99.5, 'close': 100.5}
                ],
                'title': 'Shooting Star'
            },
            'inverted_hammer': {
                'data': [
                    {'open': 100.5, 'high': 108, 'low': 100, 'close': 100}
                ],
                'title': 'Inverted Hammer'
            },
            'bullish_marubozu': {
                'data': [
                    {'open': 95, 'high': 105, 'low': 95, 'close': 105}
                ],
                'title': 'Bullish Marubozu'
            },
            'bearish_marubozu': {
                'data': [
                    {'open': 105, 'high': 105, 'low': 95, 'close': 95}
                ],
                'title': 'Bearish Marubozu'
            },
            
            # Double Candle Patterns
            'bullish_engulfing': {
                'data': [
                    {'open': 102, 'high': 103, 'low': 98, 'close': 99},
                    {'open': 97, 'high': 106, 'low': 96, 'close': 105}
                ],
                'title': 'Bullish Engulfing'
            },
            'bearish_engulfing': {
                'data': [
                    {'open': 98, 'high': 102, 'low': 97, 'close': 101},
                    {'open': 103, 'high': 104, 'low': 94, 'close': 95}
                ],
                'title': 'Bearish Engulfing'
            },
            'piercing_line': {
                'data': [
                    {'open': 105, 'high': 106, 'low': 98, 'close': 99},
                    {'open': 96, 'high': 104, 'low': 95, 'close': 103}
                ],
                'title': 'Piercing Line'
            },
            'dark_cloud_cover': {
                'data': [
                    {'open': 95, 'high': 102, 'low': 94, 'close': 101},
                    {'open': 104, 'high': 105, 'low': 96, 'close': 97}
                ],
                'title': 'Dark Cloud Cover'
            },
            'tweezer_top': {
                'data': [
                    {'open': 98, 'high': 105, 'low': 97, 'close': 104},
                    {'open': 104, 'high': 105, 'low': 99, 'close': 100}
                ],
                'title': 'Tweezer Top'
            },
            'tweezer_bottom': {
                'data': [
                    {'open': 102, 'high': 103, 'low': 95, 'close': 96},
                    {'open': 96, 'high': 101, 'low': 95, 'close': 100}
                ],
                'title': 'Tweezer Bottom'
            },
            
            # Triple Candle Patterns
            'morning_star': {
                'data': [
                    {'open': 105, 'high': 106, 'low': 98, 'close': 99},
                    {'open': 98, 'high': 99, 'low': 95, 'close': 96},
                    {'open': 97, 'high': 106, 'low': 96, 'close': 105}
                ],
                'title': 'Morning Star'
            },
            'evening_star': {
                'data': [
                    {'open': 95, 'high': 102, 'low': 94, 'close': 101},
                    {'open': 102, 'high': 105, 'low': 101, 'close': 104},
                    {'open': 103, 'high': 104, 'low': 94, 'close': 95}
                ],
                'title': 'Evening Star'
            },
            'three_white_soldiers': {
                'data': [
                    {'open': 95, 'high': 100, 'low': 94, 'close': 99},
                    {'open': 98, 'high': 104, 'low': 97, 'close': 103},
                    {'open': 102, 'high': 108, 'low': 101, 'close': 107}
                ],
                'title': 'Three White Soldiers'
            },
            'three_black_crows': {
                'data': [
                    {'open': 105, 'high': 106, 'low': 100, 'close': 101},
                    {'open': 102, 'high': 103, 'low': 97, 'close': 98},
                    {'open': 99, 'high': 100, 'low': 93, 'close': 94}
                ],
                'title': 'Three Black Crows'
            }
        }
        
        if pattern_type not in patterns:
            raise ValueError(f"Pattern {pattern_type} not found")
        
        pattern = patterns[pattern_type]
        df = pd.DataFrame(pattern['data'])
        df['date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
        
        return df, pattern['title']
    
    def create_single_pattern_chart(self, pattern_type: str, save: bool = True) -> go.Figure:
        """Tạo chart cho một pattern"""
        
        df, title = self._create_candle_data(pattern_type)
        
        fig = go.Figure()
        
        colors = []
        for _, row in df.iterrows():
            if row['close'] >= row['open']:
                colors.append(self.colors['bullish'])
            else:
                colors.append(self.colors['bearish'])
        
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color=self.colors['bullish'],
            decreasing_line_color=self.colors['bearish'],
            increasing_fillcolor=self.colors['bullish'],
            decreasing_fillcolor=self.colors['bearish'],
            name=title
        ))
        
        fig.update_layout(
            title={
                'text': f'<b>{title}</b>',
                'x': 0.5,
                'font': {'size': 24, 'color': self.colors['text']}
            },
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font={'color': self.colors['text']},
            xaxis={
                'gridcolor': self.colors['grid'],
                'showgrid': True,
                'rangeslider': {'visible': False}
            },
            yaxis={
                'gridcolor': self.colors['grid'],
                'showgrid': True,
                'title': 'Price'
            },
            showlegend=False,
            width=600,
            height=400
        )
        
        if save:
            filepath = os.path.join(self.output_dir, f'{pattern_type}.png')
            fig.write_image(filepath, scale=2)
            print(f"Saved: {filepath}")
        
        return fig
    
    def create_all_patterns_grid(self, category: str = 'all') -> go.Figure:
        """Tạo grid hiển thị nhiều patterns"""
        
        single_patterns = ['doji', 'dragonfly_doji', 'gravestone_doji', 'hammer', 
                         'hanging_man', 'shooting_star', 'inverted_hammer',
                         'bullish_marubozu', 'bearish_marubozu']
        
        double_patterns = ['bullish_engulfing', 'bearish_engulfing', 
                          'piercing_line', 'dark_cloud_cover',
                          'tweezer_top', 'tweezer_bottom']
        
        triple_patterns = ['morning_star', 'evening_star',
                          'three_white_soldiers', 'three_black_crows']
        
        if category == 'single':
            patterns = single_patterns
            rows, cols = 3, 3
        elif category == 'double':
            patterns = double_patterns
            rows, cols = 2, 3
        elif category == 'triple':
            patterns = triple_patterns
            rows, cols = 2, 2
        else:
            patterns = single_patterns + double_patterns + triple_patterns
            rows, cols = 5, 4
        
        titles = []
        for p in patterns:
            _, title = self._create_candle_data(p)
            titles.append(title)
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=titles,
            vertical_spacing=0.12,
            horizontal_spacing=0.08
        )
        
        for idx, pattern_type in enumerate(patterns):
            row = (idx // cols) + 1
            col = (idx % cols) + 1
            
            df, _ = self._create_candle_data(pattern_type)
            
            fig.add_trace(
                go.Candlestick(
                    x=list(range(len(df))),
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color=self.colors['bullish'],
                    decreasing_line_color=self.colors['bearish'],
                    increasing_fillcolor=self.colors['bullish'],
                    decreasing_fillcolor=self.colors['bearish'],
                    showlegend=False
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title={
                'text': f'<b>Japanese Candlestick Patterns - {category.title()}</b>',
                'x': 0.5,
                'font': {'size': 28, 'color': self.colors['text']}
            },
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font={'color': self.colors['text']},
            height=300 * rows,
            width=350 * cols,
            showlegend=False
        )
        
        fig.update_xaxes(showticklabels=False, showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor=self.colors['grid'])
        
        for annotation in fig['layout']['annotations']:
            annotation['font'] = {'size': 14, 'color': self.colors['text']}
        
        return fig
    
    def generate_all_images(self):
        """Generate tất cả hình ảnh"""
        
        all_patterns = [
            'doji', 'dragonfly_doji', 'gravestone_doji',
            'hammer', 'hanging_man', 'shooting_star', 'inverted_hammer',
            'bullish_marubozu', 'bearish_marubozu',
            'bullish_engulfing', 'bearish_engulfing',
            'piercing_line', 'dark_cloud_cover',
            'tweezer_top', 'tweezer_bottom',
            'morning_star', 'evening_star',
            'three_white_soldiers', 'three_black_crows'
        ]
        
        print("Generating individual pattern charts...")
        for pattern in all_patterns:
            try:
                self.create_single_pattern_chart(pattern, save=True)
            except Exception as e:
                print(f"Error generating {pattern}: {e}")
        
        print("\nGenerating grid charts...")
        for category in ['single', 'double', 'triple']:
            fig = self.create_all_patterns_grid(category)
            filepath = os.path.join(self.output_dir, f'{category}_patterns_grid.png')
            try:
                fig.write_image(filepath, scale=2)
                print(f"Saved: {filepath}")
            except Exception as e:
                print(f"Error saving {category} grid: {e}")
        
        print("\nAll images generated!")
        return self.output_dir


def create_pattern_comparison(pattern1: str, pattern2: str) -> go.Figure:
    """Tạo chart so sánh 2 patterns"""
    
    viz = CandlestickPatternVisualizer()
    
    fig = make_subplots(rows=1, cols=2, subplot_titles=[pattern1, pattern2])
    
    for idx, pattern in enumerate([pattern1, pattern2]):
        df, title = viz._create_candle_data(pattern)
        col = idx + 1
        
        fig.add_trace(
            go.Candlestick(
                x=list(range(len(df))),
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                increasing_line_color=viz.colors['bullish'],
                decreasing_line_color=viz.colors['bearish'],
                showlegend=False
            ),
            row=1, col=col
        )
    
    fig.update_layout(
        paper_bgcolor=viz.colors['background'],
        plot_bgcolor=viz.colors['background'],
        font={'color': viz.colors['text']},
        height=400,
        width=800
    )
    
    return fig


if __name__ == "__main__":
    viz = CandlestickPatternVisualizer()
    
    print("Creating sample chart...")
    fig = viz.create_single_pattern_chart('bullish_engulfing', save=False)
    fig.show()
    
    print("\nCreating grid chart...")
    grid_fig = viz.create_all_patterns_grid('single')
    grid_fig.show()
