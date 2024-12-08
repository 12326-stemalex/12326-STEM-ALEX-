import os
import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy.stats import linregress

# Define thresholds and weights
THRESHOLDS = {
    'Temperature': {'max': 25.6, 'unit': '°C', 'weight': 0.4},
    'Humidity': {'max': 40, 'unit': '%', 'weight': 0.3},
    'Sound': {'warning': 85, 'unit': 'dB', 'weight': 0.3}
}

# Path to the CSV file
csv_path = os.path.join(os.path.dirname(__file__), 'sensor_data.csv')

# Check if file exists
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"The file {csv_path} does not exist. Please ensure the CSV file is in the correct location.")

# Read and clean data
df = pd.read_csv(csv_path)
df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
df_cleaned = df.dropna(subset=['Timestamp'])

# Ensure that we are using loc to avoid SettingWithCopyWarning
df_cleaned['Date'] = df_cleaned['Timestamp'].dt.date  # This avoids warning for modifying a slice

# Check if the data has the required columns
required_columns = ['Timestamp', 'Temperature', 'Humidity', 'Sound']
for col in required_columns:
    if col not in df_cleaned.columns:
        raise ValueError(f"Missing required column: {col} in the dataset.")

if df_cleaned.empty:
    raise ValueError("No valid data in the CSV file. Please check the file contents.")

# Function to calculate environmental health score
def calculate_environmental_health_score(df):
    scores = {}
    overall_score = 0

    for sensor, config in THRESHOLDS.items():
        if sensor not in df.columns or df[sensor].isna().all():
            scores[sensor] = 0
            continue

        sensor_data = df[sensor].dropna()
        if sensor in ['Temperature', 'Humidity']:
            score = 100 * (np.clip(sensor_data / config['max'], 0, 1))
        elif sensor == 'Sound':
            score = 100 * (np.clip((config['warning'] - sensor_data) / config['warning'], 0, 1))
        else:
            score = pd.Series(100)

        scores[sensor] = score.mean() if not sensor_data.empty else 0
        overall_score += scores[sensor] * config['weight']

    return {
        'overall_score': overall_score,
        'sensor_scores': scores,
        'health_status': get_health_status(overall_score)
    }

# Get health status
def get_health_status(score):
    if score >= 80:
        return "Excellent", "The environment is very healthy and comfortable."
    elif score >= 60:
        return "Good", "The environment is generally comfortable with some areas for improvement."
    elif score >= 40:
        return "Fair", "Several environmental factors need attention."
    else:
        return "Poor", "Immediate attention required for multiple environmental factors."

# Create threshold figure
def create_threshold_figure(df, sensor_type):
    fig = go.Figure()

    # Actual data trace
    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df[sensor_type],
        name=sensor_type,
        line=dict(color='#2ecc71'),
        hoverinfo='text',
        hovertemplate=f'%{{x}}<br>%{{y:.2f}} {THRESHOLDS[sensor_type]["unit"]}<extra></extra>'
    ))

    # Add threshold lines
    if sensor_type in ['Temperature', 'Humidity']:
        fig.add_shape(
            type="line",
            x0=df['Timestamp'].min(),
            x1=df['Timestamp'].max(),
            y0=THRESHOLDS[sensor_type]['max'],
            y1=THRESHOLDS[sensor_type]['max'],
            line=dict(color="red", dash="dash"),
        )
        fig.add_annotation(
            x=df['Timestamp'].iloc[len(df) // 2],
            y=THRESHOLDS[sensor_type]['max'],
            text=f"Max Comfort ({THRESHOLDS[sensor_type]['max']}{THRESHOLDS[sensor_type]['unit']})",
            showarrow=False,
            font=dict(color="red"),
        )

    fig.update_layout(
        title=f'{sensor_type} Over Time',
        xaxis_title='Time',
        yaxis_title=f'{sensor_type} ({THRESHOLDS[sensor_type]["unit"]})',
        hovermode='x unified',
        showlegend=True
    )

    return fig

# Create scatter plot between humidity and temperature with correlation lines per day
def create_humidity_vs_temperature_figure(df):
    fig = go.Figure()

    # Group by day
    grouped = df.groupby('Date')

    # Plot data points and add regression line per day
    for date, group in grouped:
        fig.add_trace(go.Scatter(
            x=group['Humidity'],
            y=group['Temperature'],
            mode='markers',
            marker=dict(size=8, opacity=0.7),
            name=f'{date}'
        ))

        # Check if there are enough unique values for regression
        if len(group['Humidity'].unique()) > 1:  # Only do regression if values are not identical
            slope, intercept, r_value, p_value, std_err = linregress(group['Humidity'], group['Temperature'])
            line_x = np.array([group['Humidity'].min(), group['Humidity'].max()])
            line_y = slope * line_x + intercept
            fig.add_trace(go.Scatter(
                x=line_x,
                y=line_y,
                mode='lines',
                line=dict(color='black', dash='dash'),
                showlegend=False,
                name=f"Correlation Line - {date}"
            ))

            # Add equation of the line as annotation
            equation_text = f"y = {slope:.2f}x + {intercept:.2f}"
            fig.add_annotation(
                x=line_x[1],  # Place the annotation at the end of the line
                y=line_y[1],
                text=equation_text,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1,
                ax=-50,  # Adjust the arrow position
                ay=0,
                font=dict(size=10, color='black')
            )

    fig.update_layout(
        title='Humidity vs Temperature with Correlation Lines',
        xaxis_title=f'Humidity ({THRESHOLDS["Humidity"]["unit"]})',
        yaxis_title=f'Temperature ({THRESHOLDS["Temperature"]["unit"]})',
        hovermode='closest',
        showlegend=True
    )

    return fig

# Recommendations
def generate_recommendations(health_score):
    recommendations = []
    if health_score['overall_score'] < 60:
        recommendations.append("Consider improving ventilation to enhance air quality.")
    if health_score['sensor_scores'].get('Temperature', 0) < 60:
        recommendations.append("Adjust the heating/cooling system to maintain a comfortable temperature.")
    if health_score['sensor_scores'].get('Humidity', 0) < 60:
        recommendations.append("Use a dehumidifier or humidifier to maintain optimal levels.")
    if health_score['sensor_scores'].get('Sound', 0) < 60:
        recommendations.append("Implement noise reduction measures.")
    return recommendations

# Dash app layout
app = dash.Dash(__name__)
health_score = calculate_environmental_health_score(df_cleaned)

app.layout = html.Div([
    html.H1("Environment Monitoring Dashboard", style={"text-align": "center"}),

    # Overall Health Score
    html.Div([
        html.H2(f"Overall Environmental Health Score: {health_score['overall_score']:.2f}/100",
                style={"text-align": "center", "color": "green"}),
        html.P(f"Status: {health_score['health_status'][0]}", style={"text-align": "center", "font-weight": "bold"}),
        html.P(health_score['health_status'][1], style={"text-align": "center", "margin-bottom": "20px"}),
    ], style={"margin-bottom": "30px"}),

    # Recommendations
    html.Div([
        html.H4("Recommendations", style={"font-weight": "bold"}),
        html.Ul([html.Li(rec) for rec in generate_recommendations(health_score)])
    ], style={"background-color": "#f9f9f9", "padding": "10px", "border-radius": "5px", "border": "1px solid #ccc"}),

    # Graphs for each sensor
    html.Div([
        dcc.Graph(figure=create_threshold_figure(df_cleaned, 'Temperature')),
        dcc.Graph(figure=create_threshold_figure(df_cleaned, 'Humidity')),
        dcc.Graph(figure=create_threshold_figure(df_cleaned, 'Sound')),
        dcc.Graph(figure=create_humidity_vs_temperature_figure(df_cleaned)),
    ]),
])

if __name__ == '__main__':
    app.run_server(debug=True)
