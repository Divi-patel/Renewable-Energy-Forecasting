import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import warnings
from scipy import stats
from scipy.stats import gaussian_kde
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Renewable Energy Portfolio Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1rem;
    }
    .plot-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

class StreamlitEnergyDashboard:
    """
    Streamlit dashboard for renewable energy portfolio visualization
    """
    
    def __init__(self):
        # Initialize paths
        self.base_path = Path('.')
        self.portfolio_path = self.base_path / 'Renewable Portfolio LLC'
        
        # Modern color palette
        self.colors = {
            'generation': '#70AD47',  # Green
            'price': '#4472C4',       # Blue for real-time
            'price_da': '#ED7D31',    # Orange for day-ahead
            'revenue': '#ED7D31',     # Orange
        }
        
        # Month names
        self.month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December']
    
    def get_project_folders(self):
        """Get all project folders"""
        project_folders = []
        if not self.portfolio_path.exists():
            return project_folders
            
        for item in self.portfolio_path.iterdir():
            if item.is_dir():
                if ((item / 'Generation').exists() or (item / 'Price').exists() or 
                    (item / 'Price_da').exists() or (item / 'Revenue').exists()):
                    project_folders.append(item)
        return project_folders
    
    def clean_site_name(self, site_name):
        """Clean up site name for display"""
        clean_name = site_name.replace('_LLC', '').replace('_Power', '')
        clean_name = clean_name.replace('_', ' ').title()
        return clean_name
    
    def get_all_sites(self):
        """Get all unique site names from the project folders"""
        return [folder.name for folder in self.get_project_folders()]
    
    def format_y_axis(self, ax, metric_type, temporal):
        """Format y-axis based on metric type and temporal resolution"""
        if metric_type == 'generation':
            if temporal in ['daily', 'monthly']:
                ax.set_ylabel('Generation (MWh)', fontsize=11)
            else:
                ax.set_ylabel('Generation (MW)', fontsize=11)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        elif metric_type == 'price' or metric_type == 'price_da':
            ax.set_ylabel('Price ($/MWh)', fontsize=11)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        elif metric_type == 'revenue':
            if temporal == 'monthly':
                ax.set_ylabel('Revenue ($1000s)', fontsize=11)
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:,.0f}'))
            else:
                ax.set_ylabel('Revenue ($)', fontsize=11)
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    def find_stats_file(self, project_folder, metric_type, temporal):
        """Find the appropriate stats file in the project folder"""
        metric_folder = project_folder / metric_type.capitalize()
        
        if not metric_folder.exists():
            return None
        
        patterns = [
            f'*_{metric_type}_{temporal}_stats.csv',
            f'*_{temporal}_stats.csv',
            f'*{temporal}stats.csv'
        ]
        
        for pattern in patterns:
            files = list(metric_folder.glob(pattern))
            if files:
                return files[0]
        
        return None
    
    def find_timeseries_file(self, project_folder, metric_type, temporal):
        """Find the appropriate timeseries file in the project folder"""
        metric_folder = project_folder / metric_type.capitalize()
        
        if not metric_folder.exists():
            return None
        
        patterns = [
            f'*_{metric_type}_{temporal}_timeseries.csv',
            f'*_{temporal}_timeseries.csv',
            f'*{temporal}timeseries.csv',
            f'*_{metric_type}_{temporal}_timeseries_compressed.csv'
        ]
        
        for pattern in patterns:
            files = list(metric_folder.glob(pattern))
            if files:
                return files[0]
        
        return None
    
    def plot_monthly_forecast(self, site_name, metric_type):
        """Create monthly forecast plot"""
        project_folder = self.portfolio_path / site_name
        if not project_folder.exists():
            return None
            
        timeseries_file = self.find_timeseries_file(project_folder, metric_type, 'monthly')
        
        if not timeseries_file:
            stats_file = self.find_stats_file(project_folder, metric_type, 'monthly')
            if stats_file:
                return self.plot_monthly_forecast_from_stats(site_name, metric_type, stats_file)
            return None
        
        try:
            df = pd.read_csv(timeseries_file)
            year_cols = [col for col in df.columns if str(col).isdigit()]
            
            if not year_cols:
                return None
            
            df['mean'] = df[year_cols].mean(axis=1)
            df['p5'] = df[year_cols].quantile(0.05, axis=1)
            df['p95'] = df[year_cols].quantile(0.95, axis=1)
            
            fig, ax = plt.subplots(figsize=(12, 7))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            x = range(len(df))
            
            if metric_type == 'price':
                ax.plot(x, df['mean'], 
                       color=self.colors['price'],
                       linewidth=3,
                       label='Real-Time Price',
                       zorder=5,
                       marker='o',
                       markersize=6)
                
                # Try to load day-ahead price data
                price_da_folder = project_folder / 'Price_da'
                if price_da_folder.exists():
                    dt_patterns = [
                        '*_monthly_timeseries.csv',
                        '*monthly_timeseries.csv',
                        '*_price_da_monthly_timeseries.csv'
                    ]
                    
                    dt_file = None
                    for pattern in dt_patterns:
                        files = list(price_da_folder.glob(pattern))
                        if files:
                            dt_file = files[0]
                            break
                    
                    if dt_file:
                        try:
                            df_dt = pd.read_csv(dt_file)
                            year_cols_dt = [col for col in df_dt.columns if str(col).isdigit()]
                            
                            if year_cols_dt:
                                df_dt['mean'] = df_dt[year_cols_dt].mean(axis=1)
                                ax.plot(x, df_dt['mean'], 
                                       color=self.colors['price_da'],
                                       linewidth=3,
                                       label='Day-Ahead Price',
                                       zorder=5,
                                       marker='s',
                                       markersize=6,
                                       linestyle='--')
                        except:
                            pass
            else:
                ax.fill_between(x, df['p5'], df['p95'],
                              alpha=0.3,
                              color=self.colors[metric_type],
                              label='P5-P95 Confidence Band',
                              edgecolor='none')
                
                ax.plot(x, df['mean'], 
                       color=self.colors[metric_type],
                       linewidth=3,
                       label='Mean',
                       zorder=5,
                       marker='o',
                       markersize=6)
            
            clean_name = self.clean_site_name(site_name)
            title = f'Monthly {metric_type.capitalize()} Forecast - {clean_name}'
            ax.set_title(title, fontsize=14, fontweight='normal', pad=15)
            
            ax.set_xticks(x)
            if 'month_name' in df.columns:
                ax.set_xticklabels(df['month_name'], rotation=45, ha='right')
            else:
                ax.set_xticklabels([self.month_names[i] for i in range(12)], rotation=45, ha='right')
            ax.set_xlabel('')
            
            self.format_y_axis(ax, metric_type, 'monthly')
            
            ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.grid(False, axis='x')
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('lightgray')
            ax.spines['bottom'].set_color('lightgray')
            
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                     ncol=2, frameon=False, fontsize=10)
            
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.15)
            
            return fig
            
        except Exception as e:
            st.error(f"Error in monthly {metric_type} for {site_name}: {str(e)}")
            return None
    
    def plot_monthly_forecast_from_stats(self, site_name, metric_type, stats_file):
        """Create monthly forecast plot using stats file"""
        try:
            df = pd.read_csv(stats_file)
            
            fig, ax = plt.subplots(figsize=(12, 7))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            x = range(len(df))
            
            if metric_type == 'price':
                ax.plot(x, df['mean'], 
                       color=self.colors['price'],
                       linewidth=3,
                       label='Real-Time Price',
                       zorder=5,
                       marker='o',
                       markersize=6)
                
                # Try to load day-ahead price data
                project_folder = self.portfolio_path / site_name
                price_da_folder = project_folder / 'Price_da'
                if price_da_folder.exists():
                    dt_patterns = [
                        '*_monthly_stats.csv',
                        '*monthly_stats.csv',
                        '*_price_da_monthly_stats.csv'
                    ]
                    
                    dt_file = None
                    for pattern in dt_patterns:
                        files = list(price_da_folder.glob(pattern))
                        if files:
                            dt_file = files[0]
                            break
                    
                    if dt_file:
                        try:
                            df_dt = pd.read_csv(dt_file)
                            if 'mean' in df_dt.columns:
                                ax.plot(x, df_dt['mean'], 
                                       color=self.colors['price_da'],
                                       linewidth=3,
                                       label='Day-Ahead Price',
                                       zorder=5,
                                       marker='s',
                                       markersize=6,
                                       linestyle='--')
                        except:
                            pass
            else:
                if 'p5' in df.columns and 'p95' in df.columns:
                    ax.fill_between(x, df['p5'], df['p95'],
                                  alpha=0.3,
                                  color=self.colors[metric_type],
                                  label='P5-P95 Confidence Band',
                                  edgecolor='none')
                
                ax.plot(x, df['mean'], 
                       color=self.colors[metric_type],
                       linewidth=3,
                       label='Mean',
                       zorder=5,
                       marker='o',
                       markersize=6)
            
            clean_name = self.clean_site_name(site_name)
            title = f'Monthly {metric_type.capitalize()} Forecast - {clean_name}'
            ax.set_title(title, fontsize=14, fontweight='normal', pad=15)
            
            ax.set_xticks(x)
            if 'month_name' in df.columns:
                ax.set_xticklabels(df['month_name'], rotation=45, ha='right')
            else:
                ax.set_xticklabels([self.month_names[i] for i in range(12)], rotation=45, ha='right')
            ax.set_xlabel('')
            
            self.format_y_axis(ax, metric_type, 'monthly')
            
            ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.grid(False, axis='x')
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('lightgray')
            ax.spines['bottom'].set_color('lightgray')
            
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                     ncol=2, frameon=False, fontsize=10)
            
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.15)
            
            return fig
            
        except Exception as e:
            st.error(f"Error in monthly {metric_type} from stats: {str(e)}")
            return None
    
    def plot_daily_forecast(self, site_name, metric_type):
        """Create daily forecast plot with 7-day rolling average"""
        project_folder = self.portfolio_path / site_name
        if not project_folder.exists():
            return None
            
        timeseries_file = self.find_timeseries_file(project_folder, metric_type, 'daily')
        stats_file = self.find_stats_file(project_folder, metric_type, 'daily')
        
        if not timeseries_file and not stats_file:
            return None
        
        try:
            if timeseries_file:
                df = pd.read_csv(timeseries_file)
                year_cols = [col for col in df.columns if str(col).isdigit()]
                
                if year_cols:
                    df['mean'] = df[year_cols].mean(axis=1)
                    df['p25'] = df[year_cols].quantile(0.25, axis=1)
                    df['p75'] = df[year_cols].quantile(0.75, axis=1)
            else:
                df = pd.read_csv(stats_file)
            
            df['mean_smooth'] = df['mean'].rolling(window=7, center=True, min_periods=4).mean()
            if 'p25' in df.columns and 'p75' in df.columns:
                df['p25_smooth'] = df['p25'].rolling(window=7, center=True, min_periods=4).mean()
                df['p75_smooth'] = df['p75'].rolling(window=7, center=True, min_periods=4).mean()
            
            df_smooth = df.dropna(subset=['mean_smooth'])
            
            fig, ax = plt.subplots(figsize=(16, 8))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            x = range(len(df_smooth))
            
            if metric_type == 'price':
                ax.plot(x, df_smooth['mean_smooth'], 
                       color=self.colors['price'],
                       linewidth=2.5,
                       label='Real-Time Price (7-day avg)',
                       zorder=5)
                
                # Try to load day-ahead price data
                price_da_folder = project_folder / 'Price_da'
                if price_da_folder.exists():
                    dt_patterns = [
                        '*_daily_timeseries.csv',
                        '*daily_timeseries.csv',
                        '*_price_da_daily_timeseries.csv'
                    ]
                    
                    dt_file = None
                    for pattern in dt_patterns:
                        files = list(price_da_folder.glob(pattern))
                        if files:
                            dt_file = files[0]
                            break
                    
                    if dt_file:
                        try:
                            df_dt = pd.read_csv(dt_file)
                            year_cols_dt = [col for col in df_dt.columns if str(col).isdigit()]
                            
                            if year_cols_dt:
                                df_dt['mean'] = df_dt[year_cols_dt].mean(axis=1)
                                df_dt['mean_smooth'] = df_dt['mean'].rolling(window=7, center=True, min_periods=4).mean()
                                df_dt_smooth = df_dt.dropna(subset=['mean_smooth'])
                                
                                if len(df_dt_smooth) == len(df_smooth):
                                    ax.plot(x, df_dt_smooth['mean_smooth'], 
                                           color=self.colors['price_da'],
                                           linewidth=2.5,
                                           label='Day-Ahead Price (7-day avg)',
                                           zorder=5,
                                           linestyle='--')
                        except:
                            pass
            else:
                if 'p25_smooth' in df_smooth.columns and 'p75_smooth' in df_smooth.columns:
                    ax.fill_between(x, 
                                  df_smooth['p25_smooth'], 
                                  df_smooth['p75_smooth'],
                                  alpha=0.3,
                                  color=self.colors[metric_type],
                                  label='P25-P75 Confidence Band (7-day avg)',
                                  edgecolor='none')
                
                ax.plot(x, df_smooth['mean_smooth'], 
                       color=self.colors[metric_type],
                       linewidth=2.5,
                       label='Mean (7-day avg)',
                       zorder=5)
            
            clean_name = self.clean_site_name(site_name)
            title = f'Daily {metric_type.capitalize()} Forecast (7-day Rolling Average) - {clean_name}'
            ax.set_title(title, fontsize=14, fontweight='normal', pad=15)
            
            tick_positions = list(range(0, len(df_smooth), 30))
            if 'date_label' in df_smooth.columns:
                tick_labels = [df_smooth.iloc[i]['date_label'] for i in tick_positions]
            else:
                tick_labels = []
                for i in tick_positions:
                    month = int(df_smooth.iloc[i]['month'])
                    day = int(df_smooth.iloc[i]['day'])
                    tick_labels.append(f"{self.month_names[month-1][:3]} {day}")
            
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right')
            ax.set_xlabel('')
            
            self.format_y_axis(ax, metric_type, 'daily')
            
            ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.grid(True, axis='x', alpha=0.2, linestyle=':', linewidth=0.5)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('lightgray')
            ax.spines['bottom'].set_color('lightgray')
            
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12),
                     ncol=2, frameon=False, fontsize=10)
            
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.12)
            
            return fig
            
        except Exception as e:
            st.error(f"Error in daily {metric_type}: {str(e)}")
            return None
    
    def plot_hourly_forecast(self, site_name, metric_type):
        """Create hourly average profile"""
        if metric_type == 'revenue':
            return None
        
        project_folder = self.portfolio_path / site_name
        if not project_folder.exists():
            return None
            
        timeseries_file = self.find_timeseries_file(project_folder, metric_type, 'hourly')
        stats_file = self.find_stats_file(project_folder, metric_type, 'hourly')
        
        if not timeseries_file and not stats_file:
            return None
        
        try:
            if timeseries_file:
                df = pd.read_csv(timeseries_file)
                year_cols = [col for col in df.columns if str(col).isdigit()]
                
                if year_cols:
                    df['mean'] = df[year_cols].mean(axis=1)
                    df['p5'] = df[year_cols].quantile(0.05, axis=1)
                    df['p95'] = df[year_cols].quantile(0.95, axis=1)
                
                if 'hour' not in df.columns:
                    if 'datetime' in df.columns or 'timestamp' in df.columns:
                        time_col = 'datetime' if 'datetime' in df.columns else 'timestamp'
                        df[time_col] = pd.to_datetime(df[time_col])
                        df['hour'] = df[time_col].dt.hour
                    else:
                        df['hour'] = df.index % 24
                
                hourly_profile = df.groupby('hour').agg({
                    'mean': 'mean',
                    'p5': 'mean',
                    'p95': 'mean'
                }).reset_index()
            else:
                df = pd.read_csv(stats_file)
                if 'hour' in df.columns:
                    hourly_profile = df.groupby('hour').agg({
                        'mean': 'mean',
                        'p5': 'mean',
                        'p95': 'mean'
                    }).reset_index()
                else:
                    return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            if metric_type == 'price':
                if 'p5' in hourly_profile.columns and 'p95' in hourly_profile.columns:
                    ax.fill_between(hourly_profile['hour'], 
                                  hourly_profile['p5'], 
                                  hourly_profile['p95'],
                                  alpha=0.3,
                                  color=self.colors['price'],
                                  label='P5-P95 RT Price',
                                  edgecolor='none')
                
                ax.plot(hourly_profile['hour'], hourly_profile['mean'], 
                       color=self.colors['price'],
                       linewidth=3,
                       marker='o',
                       markersize=6,
                       label='Real-Time Price Mean',
                       zorder=5)
                
                # Try to load day-ahead price data
                price_da_folder = project_folder / 'Price_da'
                if price_da_folder.exists():
                    dt_patterns = [
                        '*_hourly_timeseries.csv',
                        '*hourly_timeseries.csv',
                        '*_hourly_stats.csv',
                        '*hourly_stats.csv'
                    ]
                    
                    dt_file = None
                    for pattern in dt_patterns:
                        files = list(price_da_folder.glob(pattern))
                        if files:
                            dt_file = files[0]
                            break
                    
                    if dt_file:
                        try:
                            df_dt = pd.read_csv(dt_file)
                            
                            if 'timeseries' in dt_file.name:
                                year_cols_dt = [col for col in df_dt.columns if str(col).isdigit()]
                                if year_cols_dt:
                                    df_dt['mean'] = df_dt[year_cols_dt].mean(axis=1)
                                    
                                    if 'hour' not in df_dt.columns:
                                        df_dt['hour'] = df_dt.index % 24
                                    
                                    hourly_profile_dt = df_dt.groupby('hour')['mean'].mean().reset_index()
                            else:
                                if 'hour' in df_dt.columns:
                                    hourly_profile_dt = df_dt.groupby('hour')['mean'].mean().reset_index()
                                else:
                                    hourly_profile_dt = None
                            
                            if hourly_profile_dt is not None:
                                ax.plot(hourly_profile_dt['hour'], hourly_profile_dt['mean'], 
                                       color=self.colors['price_da'],
                                       linewidth=3,
                                       marker='s',
                                       markersize=6,
                                       label='Day-Ahead Price Mean',
                                       zorder=5,
                                       linestyle='--')
                        except:
                            pass
            else:
                if 'p5' in hourly_profile.columns and 'p95' in hourly_profile.columns:
                    ax.fill_between(hourly_profile['hour'], 
                                  hourly_profile['p5'], 
                                  hourly_profile['p95'],
                                  alpha=0.3,
                                  color=self.colors[metric_type],
                                  label='P5-P95 Confidence Band',
                                  edgecolor='none')
                
                ax.plot(hourly_profile['hour'], hourly_profile['mean'], 
                       color=self.colors[metric_type],
                       linewidth=3,
                       marker='o',
                       markersize=6,
                       label='Mean',
                       zorder=5)
            
            clean_name = self.clean_site_name(site_name)
            title = f'Average Hourly {metric_type.capitalize()} Profile - {clean_name}'
            ax.set_title(title, fontsize=14, fontweight='normal', pad=15)
            
            ax.set_xlabel('Hour of Day', fontsize=11)
            ax.set_xticks(range(0, 24, 2))
            ax.set_xlim(-0.5, 23.5)
            
            self.format_y_axis(ax, metric_type, 'hourly')
            
            ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.grid(True, axis='x', alpha=0.2, linestyle=':', linewidth=0.5)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('lightgray')
            ax.spines['bottom'].set_color('lightgray')
            
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                     ncol=2, frameon=False, fontsize=10)
            
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.15)
            
            return fig
            
        except Exception as e:
            st.error(f"Error in hourly {metric_type}: {str(e)}")
            return None
    
    def plot_monthly_duration_curve(self, site_name, month_idx):
        """Create monthly duration curve for price"""
        project_folder = self.portfolio_path / site_name
        if not project_folder.exists():
            return None
            
        price_folder = project_folder / 'Price'
        if not price_folder.exists():
            return None
            
        timeseries_file = price_folder / f"{site_name}_price_hourly_timeseries_compressed.csv"
        
        if not timeseries_file.exists():
            return None
        
        try:
            df = pd.read_csv(timeseries_file)
            
            year_cols = [col for col in df.columns if str(col).isdigit()]
            
            if not year_cols:
                return None
            
            month_data = df[df['month'] == month_idx].copy()
            
            if len(month_data) == 0:
                return None
            
            month_values = []
            for year in year_cols:
                year_values = pd.to_numeric(month_data[year], errors='coerce').dropna()
                month_values.extend(year_values.tolist())
            
            if not month_values:
                return None
            
            sorted_values = np.sort(month_values)[::-1]
            n_values = len(sorted_values)
            duration_pct = np.linspace(0, 100, n_values)
            
            percentiles_to_mark = [1, 5, 25, 50, 75, 95, 99]
            percentile_values = {}
            percentile_indices = {}
            
            for p in percentiles_to_mark:
                idx = int((100 - p) / 100 * n_values)
                idx = min(idx, n_values - 1)
                percentile_values[p] = sorted_values[idx]
                percentile_indices[p] = idx
            
            mean_value = np.mean(month_values)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            ax.plot(duration_pct, sorted_values, 
                   color='red', linewidth=2, zorder=5)
            
            ax.axhline(y=mean_value, color='black', linestyle='--', 
                      linewidth=1.2, alpha=0.8)
            
            y_range = max(sorted_values) - min(sorted_values)
            mean_label_y = mean_value + y_range * 0.02
            
            if mean_label_y > max(sorted_values) * 0.95:
                mean_label_y = mean_value - y_range * 0.02
            
            mean_label = f'Mean: ${mean_value:.2f}'
            
            ax.text(50, mean_label_y, mean_label, 
                   ha='center', va='bottom' if mean_label_y > mean_value else 'top', 
                   fontsize=10, fontweight='bold')
            
            percentile_colors = {
                99: 'green', 95: 'green', 75: 'green',
                50: 'blue', 25: 'orange', 5: 'red', 1: 'red'
            }
            
            for p in percentiles_to_mark:
                idx = percentile_indices[p]
                value = percentile_values[p]
                duration = duration_pct[idx]
                
                ax.plot(duration, value, 'o', 
                       color=percentile_colors.get(p, 'gray'),
                       markersize=6, zorder=10)
                
                label = f'P{p}'
                value_text = f'${value:.1f}'
                
                y_range = max(sorted_values) - min(sorted_values)
                if p >= 50:
                    va = 'bottom'
                    y_offset = value + y_range * 0.015
                else:
                    va = 'top'
                    y_offset = value - y_range * 0.015
                
                ax.text(duration, y_offset, label, 
                       ha='center', va=va, fontsize=8, 
                       color=percentile_colors.get(p, 'gray'),
                       fontweight='bold')
                
                bbox_props = dict(boxstyle="round,pad=0.2", 
                                facecolor='white', 
                                edgecolor='black',
                                linewidth=0.8)
                ax.text(duration, value, value_text,
                       ha='center', va='center', fontsize=8,
                       bbox=bbox_props, zorder=11)
            
            clean_name = self.clean_site_name(site_name)
            month_name = self.month_names[month_idx - 1]
            
            title = f'Price Duration Curve - {month_name} - {clean_name}'
            if min(sorted_values) < 0:
                title += '\n(includes negative prices)'
            
            ax.set_title(title, fontsize=12, fontweight='normal', pad=10)
            ax.set_xlabel('Duration (% of time)', fontsize=11)
            ax.set_ylabel('Price ($ per MWh)', fontsize=11)
            
            ax.set_xlim(0, 100)
            ax.set_xticks(range(0, 101, 20))
            
            y_min = min(sorted_values) * 1.1 if min(sorted_values) < 0 else 0
            y_max = max(sorted_values) * 1.1
            ax.set_ylim(y_min, y_max)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            if min(sorted_values) < 0:
                ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5, zorder=3)
            
            ax.grid(True, axis='both', alpha=0.3, linestyle='-', linewidth=0.5)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('lightgray')
            ax.spines['bottom'].set_color('lightgray')
            
            plt.tight_layout()
            
            return fig
            
        except Exception as e:
            st.error(f"Error in duration curve: {str(e)}")
            return None
    
    def plot_monthly_distribution_curve(self, site_name, metric_type, month_idx):
        """Create monthly distribution curve for generation and revenue"""
        if metric_type not in ['generation', 'revenue']:
            return None
        
        project_folder = self.portfolio_path / site_name
        if not project_folder.exists():
            return None
            
        timeseries_file = self.find_timeseries_file(project_folder, metric_type, 'monthly')
        
        if not timeseries_file:
            return None
        
        try:
            df = pd.read_csv(timeseries_file)
            
            year_cols = [col for col in df.columns if str(col).isdigit()]
            
            if not year_cols:
                return None
            
            month_data = df[df['month'] == month_idx].copy()
            
            if len(month_data) == 0:
                return None
            
            month_values = []
            for year in year_cols:
                year_value = pd.to_numeric(month_data[year].iloc[0], errors='coerce')
                if not pd.isna(year_value):
                    month_values.append(year_value)
            
            if len(month_values) < 3:
                return None
            
            month_values = np.array(month_values)
            
            mean_val = np.mean(month_values)
            median_val = np.median(month_values)
            std_val = np.std(month_values)
            p5_val = np.percentile(month_values, 5)
            p95_val = np.percentile(month_values, 95)
            
            fig, ax = plt.subplots(figsize=(10, 7))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            x_min = min(month_values) - 0.2 * (max(month_values) - min(month_values))
            x_max = max(month_values) + 0.2 * (max(month_values) - min(month_values))
            x_smooth = np.linspace(x_min, x_max, 300)
            
            kde = gaussian_kde(month_values, bw_method='scott')
            kde_values = kde(x_smooth)
            
            ax.plot(x_smooth, kde_values, 
                   color=self.colors[metric_type],
                   linewidth=3,
                   label='KDE Distribution',
                   zorder=5)
            
            ax.fill_between(x_smooth, 0, kde_values,
                          alpha=0.3,
                          color=self.colors[metric_type],
                          edgecolor='none')
            
            normal_dist = stats.norm.pdf(x_smooth, mean_val, std_val)
            ax.plot(x_smooth, normal_dist, 'k--', linewidth=2, 
                   label=f'Normal fit (μ={mean_val:,.0f}, σ={std_val:,.0f})')
            
            y_jitter = np.random.uniform(0, max(kde_values) * 0.05, size=len(month_values))
            ax.scatter(month_values, y_jitter, 
                      color=self.colors[metric_type],
                      alpha=0.6,
                      s=50,
                      edgecolors='black',
                      linewidth=1,
                      label=f'Actual values (n={len(month_values)})',
                      zorder=10)
            
            ax.axvline(x=mean_val, color='red', linestyle='--', linewidth=2, 
                      label=f'Mean: {mean_val:,.0f}')
            ax.axvline(x=median_val, color='blue', linestyle='--', linewidth=2, 
                      label=f'Median: {median_val:,.0f}')
            ax.axvline(x=p5_val, color='green', linestyle=':', linewidth=1.5, 
                      label=f'P5: {p5_val:,.0f}')
            ax.axvline(x=p95_val, color='green', linestyle=':', linewidth=1.5, 
                      label=f'P95: {p95_val:,.0f}')
            
            clean_name = self.clean_site_name(site_name)
            month_name = self.month_names[month_idx - 1]
            
            if metric_type == 'generation':
                title = f'Monthly Generation Distribution - {month_name} - {clean_name}'
                ax.set_xlabel('Monthly Generation (MWh)', fontsize=11)
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            else:
                title = f'Monthly Revenue Distribution - {month_name} - {clean_name}'
                ax.set_xlabel('Monthly Revenue ($)', fontsize=11)
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            title += f'\n(Distribution across {len(month_values)} simulation years)'
            ax.set_title(title, fontsize=12, fontweight='normal', pad=10)
            ax.set_ylabel('Probability Density', fontsize=11)
            
            ax.set_ylim(bottom=0)
            
            ax.grid(True, axis='both', alpha=0.3, linestyle='-', linewidth=0.5)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('lightgray')
            ax.spines['bottom'].set_color('lightgray')
            
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                     ncol=3, frameon=False, fontsize=9)
            
            cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
            textstr = f'Years: {len(month_values)}\nStd Dev: {std_val:,.0f}\nCV: {cv:.1f}%\nMin: {min(month_values):,.0f}\nMax: {max(month_values):,.0f}'
            
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.02, 0.95, textstr, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props)
            
            plt.tight_layout()
            plt.subplots_adjust(bottom=0.15)
            
            return fig
            
        except Exception as e:
            st.error(f"Error in distribution curve: {str(e)}")
            return None
    
    def create_combined_forecast(self, site_name):
        """Create a combined plot showing all three metrics"""
        project_folder = self.portfolio_path / site_name
        if not project_folder.exists():
            return None
        
        metrics_available = []
        for metric in ['generation', 'price', 'revenue']:
            metric_folder = project_folder / metric.capitalize()
            if metric_folder.exists():
                monthly_files = list(metric_folder.glob('*monthly*.csv'))
                if monthly_files:
                    metrics_available.append(metric)
        
        if len(metrics_available) < 2:
            return None
        
        try:
            fig, axes = plt.subplots(len(metrics_available), 1, 
                                   figsize=(12, 4*len(metrics_available)), 
                                   sharex=True)
            fig.patch.set_facecolor('white')
            
            if len(metrics_available) == 1:
                axes = [axes]
            
            for idx, metric in enumerate(metrics_available):
                ax = axes[idx]
                ax.set_facecolor('white')
                
                timeseries_file = self.find_timeseries_file(project_folder, metric, 'monthly')
                
                if not timeseries_file:
                    continue
                
                df = pd.read_csv(timeseries_file)
                
                year_cols = [col for col in df.columns if str(col).isdigit()]
                
                if year_cols:
                    df['mean'] = df[year_cols].mean(axis=1)
                    df['p5'] = df[year_cols].quantile(0.05, axis=1)
                    df['p95'] = df[year_cols].quantile(0.95, axis=1)
                
                x = range(len(df))
                
                if metric == 'price':
                    ax.plot(x, df['mean'], 
                           color=self.colors['price'],
                           linewidth=3,
                           label='Real-Time Price',
                           marker='o',
                           markersize=5)
                    
                    price_da_folder = project_folder / 'Price_da'
                    if price_da_folder.exists():
                        dt_patterns = [
                            '*_monthly_timeseries.csv',
                            '*monthly_timeseries.csv',
                            '*_price_da_monthly_timeseries.csv'
                        ]
                        
                        dt_file = None
                        for pattern in dt_patterns:
                            files = list(price_da_folder.glob(pattern))
                            if files:
                                dt_file = files[0]
                                break
                        
                        if dt_file:
                            try:
                                df_dt = pd.read_csv(dt_file)
                                year_cols_dt = [col for col in df_dt.columns if str(col).isdigit()]
                                
                                if year_cols_dt:
                                    df_dt['mean'] = df_dt[year_cols_dt].mean(axis=1)
                                    ax.plot(x, df_dt['mean'], 
                                           color=self.colors['price_da'],
                                           linewidth=3,
                                           label='Day-Ahead Price',
                                           marker='s',
                                           markersize=5,
                                           linestyle='--')
                            except:
                                pass
                else:
                    if 'p5' in df.columns and 'p95' in df.columns:
                        ax.fill_between(x, df['p5'], df['p95'],
                                      alpha=0.3,
                                      color=self.colors[metric],
                                      label='P5-P95')
                    
                    ax.plot(x, df['mean'], 
                           color=self.colors[metric],
                           linewidth=3,
                           label='Mean',
                           marker='o',
                           markersize=5)
                
                subplot_titles = {
                    'generation': 'Monthly Generation (MWh)',
                    'price': 'Monthly Price ($/MWh)',
                    'revenue': 'Monthly Revenue ($)'
                }
                ax.set_title(subplot_titles[metric], fontsize=12, pad=10)
                
                self.format_y_axis(ax, metric, 'monthly')
                
                ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
                ax.grid(False, axis='x')
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('lightgray')
                ax.spines['bottom'].set_color('lightgray')
                
                ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25),
                         ncol=2, frameon=False, fontsize=9)
                
                if idx == len(metrics_available) - 1:
                    ax.set_xticks(x)
                    if 'month_name' in df.columns:
                        ax.set_xticklabels(df['month_name'], rotation=45, ha='right')
                    else:
                        ax.set_xticklabels([self.month_names[i] for i in range(12)], rotation=45, ha='right')
            
            clean_name = self.clean_site_name(site_name)
            fig.suptitle(f'Combined Monthly Forecasts - {clean_name}', 
                        fontsize=16, fontweight='normal', y=0.995)
            
            plt.tight_layout()
            plt.subplots_adjust(hspace=0.5, top=0.96)
            
            return fig
            
        except Exception as e:
            st.error(f"Error in combined forecast: {str(e)}")
            return None

def main():
    """Main Streamlit app"""
    st.title("⚡ Renewable Energy Portfolio Dashboard")
    st.markdown("---")
    
    # Initialize dashboard
    dashboard = StreamlitEnergyDashboard()
    
    # Check if portfolio path exists
    if not dashboard.portfolio_path.exists():
        st.error(f"❌ Portfolio path '{dashboard.portfolio_path}' not found!")
        st.info("Please ensure the 'Renewable Portfolio LLC' folder exists in the current directory.")
        return
    
    # Get all sites
    sites = dashboard.get_all_sites()
    
    if not sites:
        st.error("❌ No project folders found!")
        st.info("Expected folder structure: Renewable Portfolio LLC/[Site_Name]/[Generation|Price|Price_da|Revenue]/")
        return
    
    # Sidebar for site selection
    with st.sidebar:
        st.header("🏗️ Site Selection")
        
        # Site selector
        clean_site_names = {site: dashboard.clean_site_name(site) for site in sites}
        selected_site = st.selectbox(
            "Select a site:",
            options=sites,
            format_func=lambda x: clean_site_names[x]
        )
        
        st.markdown("---")
        
        # Display site info
        st.subheader("📊 Site Information")
        project_folder = dashboard.portfolio_path / selected_site
        
        metrics_available = []
        for metric in ['generation', 'price', 'price_da', 'revenue']:
            metric_folder_name = metric.capitalize() if metric != 'price_da' else 'Price_da'
            metric_folder = project_folder / metric_folder_name
            if metric_folder.exists():
                metrics_available.append(metric)
        
        st.write(f"**Available metrics:** {len(metrics_available)}")
        for metric in metrics_available:
            display_name = {
                'generation': '⚡ Generation',
                'price': '💰 Real-Time Price',
                'price_da': '📅 Day-Ahead Price',
                'revenue': '💵 Revenue'
            }
            st.write(display_name.get(metric, metric))
    
    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Monthly Forecasts", 
        "📊 Daily Trends", 
        "🕐 Hourly Profiles", 
        "📉 Special Analysis",
        "🎯 Combined View"
    ])
    
    with tab1:
        st.header("Monthly Forecasts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Generation
            if 'generation' in metrics_available:
                with st.spinner('Loading generation data...'):
                    fig = dashboard.plot_monthly_forecast(selected_site, 'generation')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
            
            # Revenue
            if 'revenue' in metrics_available:
                with st.spinner('Loading revenue data...'):
                    fig = dashboard.plot_monthly_forecast(selected_site, 'revenue')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
        
        with col2:
            # Price (includes both RT and DA if available)
            if 'price' in metrics_available:
                with st.spinner('Loading price data...'):
                    fig = dashboard.plot_monthly_forecast(selected_site, 'price')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
                        if 'price_da' in metrics_available:
                            st.info("ℹ️ Chart includes both real-time and day-ahead prices")
    
    with tab2:
        st.header("Daily Trends (7-day Rolling Average)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Generation
            if 'generation' in metrics_available:
                with st.spinner('Loading daily generation data...'):
                    fig = dashboard.plot_daily_forecast(selected_site, 'generation')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
            
            # Revenue
            if 'revenue' in metrics_available:
                with st.spinner('Loading daily revenue data...'):
                    fig = dashboard.plot_daily_forecast(selected_site, 'revenue')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
        
        with col2:
            # Price
            if 'price' in metrics_available:
                with st.spinner('Loading daily price data...'):
                    fig = dashboard.plot_daily_forecast(selected_site, 'price')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
    
    with tab3:
        st.header("Average Hourly Profiles")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Generation
            if 'generation' in metrics_available:
                with st.spinner('Loading hourly generation profile...'):
                    fig = dashboard.plot_hourly_forecast(selected_site, 'generation')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
        
        with col2:
            # Price
            if 'price' in metrics_available:
                with st.spinner('Loading hourly price profile...'):
                    fig = dashboard.plot_hourly_forecast(selected_site, 'price')
                    if fig:
                        st.pyplot(fig)
                        plt.close()
        
        st.info("ℹ️ Revenue hourly profiles are not available as revenue is calculated from generation × price")
    
    with tab4:
        st.header("Special Analysis")
        
        # Create sub-tabs for different analysis types
        analysis_tab1, analysis_tab2 = st.tabs(["💰 Price Duration Curves", "📊 Distribution Analysis"])
        
        with analysis_tab1:
            if 'price' in metrics_available:
                st.subheader("Monthly Price Duration Curves")
                
                # Month selector
                month_names = dashboard.month_names
                selected_month = st.selectbox(
                    "Select month:",
                    options=range(1, 13),
                    format_func=lambda x: month_names[x-1]
                )
                
                with st.spinner(f'Loading duration curve for {month_names[selected_month-1]}...'):
                    fig = dashboard.plot_monthly_duration_curve(selected_site, selected_month)
                    if fig:
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.warning("Duration curve data not available for this month")
            else:
                st.info("Price data not available for this site")
        
        with analysis_tab2:
            st.subheader("Monthly Distribution Analysis")
            
            # Metric selector for distribution
            dist_metrics = []
            if 'generation' in metrics_available:
                dist_metrics.append('generation')
            if 'revenue' in metrics_available:
                dist_metrics.append('revenue')
            
            if dist_metrics:
                selected_dist_metric = st.selectbox(
                    "Select metric:",
                    options=dist_metrics,
                    format_func=lambda x: x.capitalize()
                )
                
                # Month selector
                selected_dist_month = st.selectbox(
                    "Select month for distribution:",
                    options=range(1, 13),
                    format_func=lambda x: dashboard.month_names[x-1],
                    key="dist_month"
                )
                
                with st.spinner(f'Loading {selected_dist_metric} distribution...'):
                    fig = dashboard.plot_monthly_distribution_curve(
                        selected_site, 
                        selected_dist_metric, 
                        selected_dist_month
                    )
                    if fig:
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.warning("Distribution data not available for this selection")
            else:
                st.info("No generation or revenue data available for distribution analysis")
    
    with tab5:
        st.header("Combined Monthly View")
        
        with st.spinner('Creating combined forecast...'):
            fig = dashboard.create_combined_forecast(selected_site)
            if fig:
                st.pyplot(fig)
                plt.close()
            else:
                st.warning("Not enough metrics available for combined view (need at least 2)")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        📊 Renewable Energy Portfolio Dashboard | 
        Data from Git LFS Repository | 
        Built with Streamlit
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
