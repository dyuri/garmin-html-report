# Garmin Activity Report Generator

A specialized Python tool designed to transform raw Garmin CSV exports into a rich, interactive HTML dashboard. This project visualizes running performance metrics, helping athletes analyze their training progress over time.

## 🚀 Features

- **Interactive Dashboard**: A single-file HTML report containing all data and visualizations.
- **Adaptive Theming**: Automatically switches between a clean **Light Mode** and a retro **Gruvbox Dark Mode** based on system preferences.
- **Advanced Visualizations**:
  - 📊 **Monthly Distance**: Bar chart tracking volume per month.
  - 📈 **Cumulative Distance (YTD)**: Line chart showing total distance progression.
  - 🏃 **Pace vs. Heart Rate**: Scatter plot to analyze aerobic efficiency.
  - 👣 **Cadence Distribution**: Histogram of steps per minute (SPM).
  - ❤️ **HR Zone Distribution**: Doughnut chart classification based on Heart Rate Reserve (Max: 182, Rest: 50).
- **Deep Dive Data**:
  - **Leaderboards**: Automatic calculation of longest runs and highest elevation gains.
  - **Detailed List**: Sortable, searchable (via browser), and collapsible table of all activities.

## 🛠️ Prerequisites

- **Python 3.x**
- **Jinja2** (Templating engine)

Install the required dependency:
```bash
pip install jinja2
```

## 📖 Usage

1.  **Export your data**: Get your activity history CSV from Garmin Connect.
2.  **Run the generator**:
    ```bash
    python3 generate_report.py <path_to_your_csv_file>
    ```
    *Example:*
    ```bash
    python3 generate_report.py Garmin-activities-2025.csv
    ```
3.  **View the Report**: Open the generated `report.html` in your web browser.

## 📂 Project Structure

- `generate_report.py`: The core logic script. Parses CSV data, calculates statistics (including HR zones and buckets), and renders the HTML.
- `template.html`: The HTML5/Jinja2 template containing the dashboard structure, CSS styling, and Chart.js logic.
- `report.html`: The generated output file (self-contained, ready to share).

## 🎨 Technology Stack

- **Python**: Data processing & logic.
- **Jinja2**: HTML templating.
- **Chart.js**: Client-side interactive charting (via CDN).
- **CSS Variables**: For seamless theme adaptation.
- **Google Fonts**: Inter font family for modern typography.
