# Renewable Energy Portfolio Dashboard

A comprehensive Streamlit dashboard for visualizing and exploring renewable energy generation, pricing, and revenue data across multiple sites with full data access capabilities.

## 🚀 Quick Start

### Local Development

1. **Clone the repository with Git LFS**:
   ```bash
   git clone https://github.com/Divi-patel/Renewable-Energy-Forecasting.git
   cd Renewable-Energy-Forecasting
   git lfs pull  # Important: Downloads the large CSV files
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

4. **Access the dashboard**:
   Open your browser and go to `http://localhost:8501`

## 📊 Features

### Visualization Capabilities

- **📈 Monthly Forecasts**: View monthly trends for generation, price, and revenue with confidence bands
- **📊 Daily Trends**: Analyze daily patterns with 7-day rolling averages
- **🕐 Hourly Profiles**: Examine average hourly patterns for generation and pricing
- **📉 Special Analysis**:
  - **Price Duration Curves**: Monthly analysis of price distributions with percentile markers
  - **Distribution Analysis**: Statistical analysis of generation and revenue with KDE plots
- **🎯 Combined Views**: Multi-metric visualizations on a single chart
- **💰 Dual Pricing**: Automatic detection and display of both real-time and day-ahead prices

### Data Management Features (NEW!)

- **📁 Data Explorer**: Browse and access all CSV files organized by metric type
- **👁️ Data Preview**: View any CSV file directly in the dashboard with scrollable tables
- **💾 Direct Downloads**: Download any data file with a single click
- **📋 Summary Statistics**: Quick statistical overview of each metric including:
  - Years available in the dataset
  - Annual mean, standard deviation, min, and max values
- **🗂️ Smart Organization**: Files automatically categorized as:
  - Timeseries data (hourly, daily, monthly)
  - Statistics files
  - Other supplementary files

## 📁 Required Folder Structure

```
Renewable-Energy-Forecasting/
├── dashboard.py
├── requirements.txt
├── README.md
└── Renewable Portfolio LLC/
    ├── Site_Name_1/
    │   ├── Generation/
    │   │   ├── *_generation_monthly_timeseries.csv
    │   │   ├── *_generation_daily_timeseries.csv
    │   │   ├── *_generation_hourly_timeseries.csv
    │   │   ├── *_generation_monthly_stats.csv
    │   │   ├── *_generation_daily_stats.csv
    │   │   └── *_generation_hourly_stats.csv
    │   ├── Price/
    │   │   ├── *_price_monthly_timeseries.csv
    │   │   ├── *_price_daily_timeseries.csv
    │   │   ├── *_price_hourly_timeseries_compressed.csv
    │   │   └── *_price_hourly_stats.csv
    │   ├── Price_da/ (optional)
    │   │   └── (similar structure as Price)
    │   └── Revenue/
    │       └── (similar structure)
    └── Site_Name_2/
        └── (similar structure)
```

## 🎯 Dashboard Interface

### Navigation
- **Sidebar**: Site selection and metrics overview
- **Main Tabs**:
  1. **Monthly Forecasts**: Side-by-side comparisons of all metrics
  2. **Daily Trends**: 7-day rolling averages for smooth trend analysis
  3. **Hourly Profiles**: Average hourly patterns throughout the day
  4. **Special Analysis**: Duration curves and distribution analyses
  5. **Combined View**: All metrics in a single synchronized view
  6. **Data Explorer**: Full access to underlying data files

### Data Explorer Tab Features
- **Metric-specific sub-tabs**: Separate tabs for Generation, Price, Price_da, and Revenue
- **File listings**: All available files for each metric with clear categorization
- **Interactive buttons**:
  - **View**: Opens a preview of the data (first 100 rows)
  - **Download**: Saves the complete CSV file to your computer
- **Data summaries**: Optional statistical summaries for quick insights

## 🌐 Deployment Options

### Streamlit Community Cloud (Recommended)

1. **Fork or use your repository**
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Deploy a new app**:
   - Repository: `Divi-patel/Renewable-Energy-Forecasting`
   - Branch: `main`
   - Main file path: `dashboard.py`
4. **Click Deploy**

**Note**: Streamlit Cloud supports Git LFS, so your large files will be available.

### Alternative Deployment Options

#### Heroku
```bash
# Install Heroku CLI, then:
heroku create your-app-name
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-git-lfs.git
heroku buildpacks:add heroku/python
git push heroku main
```

#### Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git-lfs
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN git lfs pull
EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### AWS/Azure/GCP
- Ensure Git LFS support is enabled
- Configure appropriate instance size for data processing
- Set up proper networking for web access

## 🔧 Configuration

### Streamlit Config (optional)
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#70AD47"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 1000
maxMessageSize = 300
```

### Performance Optimization
For large datasets, add to your `dashboard.py`:
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_large_file(filepath):
    return pd.read_csv(filepath)
```

## 📈 Usage Guide

### Viewing Visualizations
1. Select a site from the sidebar dropdown
2. Navigate through tabs to view different visualization types
3. Use interactive selectors for months in Special Analysis tab

### Exploring Data
1. Go to the "Data Explorer" tab
2. Select the metric type (Generation, Price, etc.)
3. Click "View" to preview data in the app
4. Click "Download" to save files locally
5. Enable "Show data summary" for quick statistics

### Understanding the Visualizations
- **Confidence Bands**: P5-P95 ranges show uncertainty in forecasts
- **7-day Rolling Average**: Smooths daily variations for clearer trends
- **Duration Curves**: Show how often prices exceed certain thresholds
- **Distribution Plots**: Display the spread and likelihood of different values

## 🐛 Troubleshooting

### Common Issues

#### "Portfolio path not found"
- Ensure you're running the app from the repository root
- Check that Git LFS files are downloaded: `git lfs pull`
- Verify the folder structure matches the requirements

#### Slow loading
- First load downloads LFS files (one-time)
- Large files may take time to process
- Consider using a production deployment for better performance

#### Missing visualizations
- Check that CSV files follow the expected naming patterns
- Verify all required columns exist in the data files
- Ensure data files are not corrupted

#### Download buttons not working
- Check browser download permissions
- Ensure sufficient disk space
- Try a different browser if issues persist

### Data File Requirements
- CSV files must follow naming conventions with metric and temporal resolution
- Year columns should be numeric (e.g., '2020', '2021')
- Standard columns needed: month, day, hour (depending on resolution)

## 🔒 Security Considerations

- **Data Privacy**: All data processing happens locally or on your deployed server
- **Access Control**: Implement authentication if deploying publicly
- **File Uploads**: Dashboard reads only from the specified directory structure


## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Ensure you've pulled the latest LFS files

## 🎉 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Data storage via Git LFS
- Visualization powered by Matplotlib
- Statistical analysis with SciPy and NumPy

---

**Version**: 0.0 (with Data Explorer)  
**Last Updated**: 07/01/2025  
**Maintainer**: Divy(divy@aamani.ai)
