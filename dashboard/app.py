#!/usr/bin/env python3
"""
Watchkeeper Intelligence Dashboard
Interactive web dashboard for visualizing intelligence data
"""

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import json
import threading
import time
from datetime import datetime, timedelta
import numpy as np

# Import WebSocket client
from dashboard.websocket_client import get_websocket_client

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Watchkeeper Intelligence Dashboard"
server = app.server

# Database connection
DB_PATH = os.getenv('WATCHKEEPER_DB', 'data/intelligence.db')

# WebSocket connection
ws_client = None
real_time_data = {}
real_time_lock = threading.Lock()

def initialize_websocket():
    """Initialize WebSocket connection and subscribe to topics"""
    global ws_client
    ws_client = get_websocket_client()
    
    # Connect to WebSocket server
    if ws_client.connect():
        # Subscribe to intelligence updates
        ws_client.subscribe("intelligence_updates", handle_intelligence_update)
        # Subscribe to system status updates
        ws_client.subscribe("system_status", handle_system_status)
        # Subscribe to alerts
        ws_client.subscribe("alerts", handle_alert)
        return True
    else:
        print("Failed to connect to WebSocket server. Real-time updates disabled.")
        return False

def handle_intelligence_update(payload):
    """Handle intelligence update from WebSocket"""
    with real_time_lock:
        # Store the new intelligence item
        if 'intelligence_items' not in real_time_data:
            real_time_data['intelligence_items'] = []
        real_time_data['intelligence_items'].append(payload)
        
        # Limit the size of the cache
        if len(real_time_data['intelligence_items']) > 100:
            real_time_data['intelligence_items'] = real_time_data['intelligence_items'][-100:]

def handle_system_status(payload):
    """Handle system status update from WebSocket"""
    with real_time_lock:
        real_time_data['system_status'] = payload

def handle_alert(payload):
    """Handle alert from WebSocket"""
    with real_time_lock:
        if 'alerts' not in real_time_data:
            real_time_data['alerts'] = []
        real_time_data['alerts'].append(payload)
        
        # Limit the size of the cache
        if len(real_time_data['alerts']) > 20:
            real_time_data['alerts'] = real_time_data['alerts'][-20:]

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_intelligence_data(days=30, limit=1000):
    """Load intelligence data from the database"""
    try:
        conn = get_db_connection()
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        query = """
        SELECT * FROM intelligence_items 
        WHERE timestamp >= ? 
        ORDER BY timestamp DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(cutoff_date, limit))
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading intelligence data: {e}")
        return pd.DataFrame()

# Layout components
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/logo.png", height="30px"), width="auto"),
                        dbc.Col(dbc.NavbarBrand("WATCHKEEPER Intelligence Dashboard", className="ms-2")),
                    ],
                    align="center",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Overview", href="#")),
                        dbc.NavItem(dbc.NavLink("Threat Map", href="#")),
                        dbc.NavItem(dbc.NavLink("Analysis", href="#")),
                        dbc.NavItem(dbc.NavLink("Sources", href="#")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
    className="mb-4",
)

# Filters panel
filters = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Filters", className="card-title"),
            html.Div(
                [
                    dbc.Label("Time Range:"),
                    dcc.Dropdown(
                        id="time-range-dropdown",
                        options=[
                            {"label": "Last 24 hours", "value": 1},
                            {"label": "Last 7 days", "value": 7},
                            {"label": "Last 30 days", "value": 30},
                            {"label": "Last 90 days", "value": 90},
                        ],
                        value=30,
                        clearable=False,
                    ),
                ]
            ),
            html.Div(
                [
                    dbc.Label("Region:"),
                    dcc.Dropdown(id="region-dropdown", multi=True),
                ],
                className="mt-3",
            ),
            html.Div(
                [
                    dbc.Label("Threat Level:"),
                    dcc.RangeSlider(
                        id="threat-slider",
                        min=0,
                        max=10,
                        step=0.5,
                        marks={i: str(i) for i in range(0, 11, 2)},
                        value=[0, 10],
                    ),
                ],
                className="mt-3",
            ),
            html.Div(
                [
                    dbc.Label("Source:"),
                    dcc.Dropdown(id="source-dropdown", multi=True),
                ],
                className="mt-3",
            ),
            dbc.Button("Apply Filters", id="apply-filters", color="primary", className="mt-3"),
        ]
    ),
    className="mb-4",
)

# Stats cards
stats_cards = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Total Intelligence Items", className="card-title"),
                        html.H2(id="total-items", className="card-text text-center"),
                    ]
                ),
                className="mb-4 text-center",
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Average Threat Level", className="card-title"),
                        html.H2(id="avg-threat", className="card-text text-center"),
                    ]
                ),
                className="mb-4 text-center",
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("High Threat Items", className="card-title"),
                        html.H2(id="high-threat-count", className="card-text text-center"),
                    ]
                ),
                className="mb-4 text-center",
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Active Sources", className="card-title"),
                        html.H2(id="source-count", className="card-text text-center"),
                    ]
                ),
                className="mb-4 text-center",
            ),
            width=3,
        ),
    ]
)

# Main layout
app.layout = html.Div(
    [
        navbar,
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(filters, width=3),
                        dbc.Col(
                            [
                                stats_cards,
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H5("Intelligence Over Time", className="card-title"),
                                            dcc.Graph(id="time-series-chart"),
                                        ]
                                    ),
                                    className="mb-4",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody(
                                                    [
                                                        html.H5("Threat Distribution by Region", className="card-title"),
                                                        dcc.Graph(id="region-chart"),
                                                    ]
                                                ),
                                            ),
                                            width=6,
                                        ),
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody(
                                                    [
                                                        html.H5("Source Reliability", className="card-title"),
                                                        dcc.Graph(id="source-chart"),
                                                    ]
                                                ),
                                            ),
                                            width=6,
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                            ],
                            width=9,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5("Intelligence Map", className="card-title"),
                                        dcc.Graph(id="intel-map", style={"height": "600px"}),
                                    ]
                                ),
                            ),
                            width=12,
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5("Recent Intelligence Items", className="card-title"),
                                        html.Div(id="intel-table"),
                                    ]
                                ),
                            ),
                            width=12,
                        ),
                    ],
                    className="mb-4",
                ),
                # Hidden div for storing the filtered dataframe
                html.Div(id="filtered-data", style={"display": "none"}),
            ],
            fluid=True,
        ),
    ]
)

# Callbacks
@callback(
    [
        Output("region-dropdown", "options"),
        Output("source-dropdown", "options"),
        Output("filtered-data", "children"),
    ],
    [Input("time-range-dropdown", "value")],
)
def update_filter_options(days):
    """Update filter options based on the selected time range"""
    df = load_intelligence_data(days=days)
    
    # Create region options
    regions = sorted(df["region"].dropna().unique())
    region_options = [{"label": region, "value": region} for region in regions]
    
    # Create source options
    sources = sorted(df["source"].dropna().unique())
    source_options = [{"label": source, "value": source} for source in sources]
    
    # Store the dataframe as JSON in the hidden div
    return region_options, source_options, df.to_json(date_format="iso", orient="split")

@callback(
    [
        Output("total-items", "children"),
        Output("avg-threat", "children"),
        Output("high-threat-count", "children"),
        Output("source-count", "children"),
        Output("time-series-chart", "figure"),
        Output("region-chart", "figure"),
        Output("source-chart", "figure"),
        Output("intel-map", "figure"),
        Output("intel-table", "children"),
    ],
    [Input("apply-filters", "n_clicks")],
    [
        State("filtered-data", "children"),
        State("region-dropdown", "value"),
        State("threat-slider", "value"),
        State("source-dropdown", "value"),
    ],
)
def update_dashboard(n_clicks, json_data, selected_regions, threat_range, selected_sources):
    """Update dashboard based on selected filters"""
    # Load the dataframe from the hidden div
    df = pd.read_json(json_data, orient="split")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_regions:
        filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]
    
    filtered_df = filtered_df[
        (filtered_df["threat_level"] >= threat_range[0]) & 
        (filtered_df["threat_level"] <= threat_range[1])
    ]
    
    if selected_sources:
        filtered_df = filtered_df[filtered_df["source"].isin(selected_sources)]
    
    # Calculate stats
    total_items = len(filtered_df)
    avg_threat = f"{filtered_df['threat_level'].mean():.1f}" if not filtered_df.empty else "0.0"
    high_threat_count = len(filtered_df[filtered_df["threat_level"] >= 7])
    source_count = filtered_df["source"].nunique()
    
    # Time series chart
    filtered_df["date"] = pd.to_datetime(filtered_df["timestamp"])
    time_series_df = filtered_df.groupby(filtered_df["date"].dt.date).size().reset_index(name="count")
    time_series_df["date"] = pd.to_datetime(time_series_df["date"])
    
    time_series_fig = px.line(
        time_series_df, 
        x="date", 
        y="count",
        title="Intelligence Items Over Time",
        labels={"date": "Date", "count": "Number of Items"},
    )
    time_series_fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    
    # Region chart
    region_counts = filtered_df["region"].value_counts().reset_index()
    region_counts.columns = ["region", "count"]
    
    region_fig = px.bar(
        region_counts.head(10),
        x="region",
        y="count",
        title="Top 10 Regions by Intelligence Volume",
        labels={"region": "Region", "count": "Number of Items"},
    )
    region_fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    
    # Source chart
    source_df = filtered_df.groupby("source").agg({
        "threat_level": "mean",
        "id": "count"
    }).reset_index()
    source_df.columns = ["source", "avg_threat", "count"]
    
    source_fig = px.scatter(
        source_df,
        x="count",
        y="avg_threat",
        size="count",
        color="avg_threat",
        hover_name="source",
        title="Source Analysis: Volume vs Average Threat Level",
        labels={"count": "Number of Items", "avg_threat": "Average Threat Level"},
    )
    source_fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    
    # Map
    map_df = filtered_df.dropna(subset=["latitude", "longitude"])
    
    map_fig = px.scatter_mapbox(
        map_df,
        lat="latitude",
        lon="longitude",
        hover_name="title",
        hover_data=["source", "threat_level", "timestamp"],
        color="threat_level",
        size_max=15,
        zoom=1,
        color_continuous_scale=px.colors.sequential.Plasma,
        title="Geographic Distribution of Intelligence",
    )
    map_fig.update_layout(
        mapbox_style="carto-darkmatter",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    
    # Intelligence table
    table_data = filtered_df.sort_values("timestamp", ascending=False).head(10)
    
    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Date"),
                        html.Th("Title"),
                        html.Th("Source"),
                        html.Th("Region"),
                        html.Th("Threat Level"),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(pd.to_datetime(row["timestamp"]).strftime("%Y-%m-%d")),
                            html.Td(row["title"]),
                            html.Td(row["source"]),
                            html.Td(row["region"]),
                            html.Td(
                                html.Span(
                                    f"{row['threat_level']:.1f}",
                                    className=f"badge bg-{'danger' if row['threat_level'] >= 7 else 'warning' if row['threat_level'] >= 4 else 'success'}",
                                )
                            ),
                        ]
                    )
                    for _, row in table_data.iterrows()
                ]
            ),
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
    )
    
    return total_items, avg_threat, high_threat_count, source_count, time_series_fig, region_fig, source_fig, map_fig, table

# Real-time updates panel
real_time_updates_panel = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Real-time Updates", className="card-title"),
            html.Div(id="real-time-status", className="alert alert-secondary"),
            html.Div(id="real-time-alerts", children=[], className="mt-3"),
            dcc.Interval(
                id="real-time-interval",
                interval=2000,  # in milliseconds (2 seconds)
                n_intervals=0
            )
        ]
    ),
    className="mb-4",
)

# Add real-time updates panel to the layout
app.layout.children[1].children[0].children[1].children.insert(0, real_time_updates_panel)

# Callback to update real-time status
@app.callback(
    [Output("real-time-status", "children"),
     Output("real-time-status", "className"),
     Output("real-time-alerts", "children")],
    [Input("real-time-interval", "n_intervals")]
)
def update_real_time_content(n):
    # Check WebSocket connection status
    if ws_client and ws_client.connected:
        status_class = "alert alert-success"
        status_text = "WebSocket Connected: Receiving real-time updates"
    else:
        status_class = "alert alert-warning"
        status_text = "WebSocket Disconnected: Real-time updates unavailable"
    
    # Get latest alerts from real-time data
    alerts_list = []
    with real_time_lock:
        if 'alerts' in real_time_data and real_time_data['alerts']:
            for alert in real_time_data['alerts'][-5:]:  # Show last 5 alerts
                severity = alert.get('severity', 'info')
                if severity == 'critical':
                    alert_class = "alert alert-danger"
                elif severity == 'warning':
                    alert_class = "alert alert-warning"
                else:
                    alert_class = "alert alert-info"
                
                alerts_list.append(
                    html.Div(
                        [
                            html.Strong(f"{alert.get('timestamp', '')}: "),
                            html.Span(alert.get('message', 'No message'))
                        ],
                        className=alert_class
                    )
                )
    
    return status_text, status_class, alerts_list

if __name__ == "__main__":
    # Initialize WebSocket connection
    threading.Thread(target=initialize_websocket).start()
    
    # Run the dashboard app
    app.run_server(debug=True, host="0.0.0.0", port=8050)
