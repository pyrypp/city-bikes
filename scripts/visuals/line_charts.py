import os

import pandas as pd
import geopandas as gpd

import plotly.graph_objects as go
from plotly.subplots import make_subplots

'''
Creates and saves the line charts for the presentation as html files.
'''

def trips_per_hour():
    cwd = os.getcwd()
    grouped_counts_path = f"{cwd}/data/processed/grouped_counts.csv"
    save_path = f"{cwd}/presentation/trips_per_hour.html"


    grouped_counts_df = pd.read_csv(grouped_counts_path)

    df = grouped_counts_df.groupby("time")["count"].sum().reset_index()
    df["count"] = df["count"] / 214
    df["time"] = pd.to_datetime(df["time"])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["count"],
            mode="lines",
            line=dict(shape="spline", color="#100166", width=4)
        ))

    fig.update_layout(
        plot_bgcolor="#FFFAF7", 
        paper_bgcolor="#FFFAF7", 
        showlegend=False, 
        width=850,
        height=650, 
        margin=dict(t=70),
        template="simple_white",
        title="Trips per hour",
        xaxis=dict(
            tickmode="auto",
            nticks=9,
            tickformat="%H:%M",
            ticklen=10
        ),
        yaxis=dict(showgrid=True, gridwidth=2, range=[0,1250], ticklen=10),
        font=dict(size=20)
        )

    fig.write_html(save_path)


def net_flow_groups():
    cwd = os.getcwd()
    points_gdf_path = f"{cwd}/data/processed/points_gdf.gpkg"
    net_flow_df = f"{cwd}/data/processed/net_flow_df.csv"
    save_path = f"{cwd}/presentation/net_flow_groups.html"

    points_gdf = gpd.read_file(points_gdf_path)
    net_flow_df = pd.read_csv(net_flow_df)


    net_flow_segmented = pd.merge(net_flow_df, points_gdf[["Departure station id", "group"]])
    df = net_flow_segmented.groupby(["group", "time"])["net_flow"].mean().reset_index()
    df["time"] = pd.to_datetime(df["time"])

    fig = make_subplots(1,2)

    fig.add_trace(
        go.Scatter(
            x=df[df["group"]==0]["time"],
            y=df[df["group"]==0]["net_flow"],
            mode="lines",
            line=dict(shape="spline", color="#100166", width=4)
            ),
            row=1,
            col=1
            )

    fig.add_trace(
        go.Scatter(
            x=df[df["group"]==1]["time"],
            y=df[df["group"]==1]["net_flow"],
            mode="lines",
            line=dict(shape="spline", color="#100166", width=4)
            ),
            row=1,
            col=2
            )

    fig.add_trace(
        go.Scatter(
            x=[df["time"].min(), df["time"].max()],
            y=[0,0],
            mode="lines",
            line=dict(color="black", width=1.7),
        ),
        row=1, 
        col="all"
    )

    fig.update_layout(
        plot_bgcolor="#FFFAF7", 
        paper_bgcolor="#FFFAF7", 
        showlegend=False, 
        width=1600,
        height=650, 
        margin=dict(t=70),
        template="simple_white",
        yaxis_title="log2(net flow + 1)",
        xaxis=dict(
            tickmode="auto",
            nticks=6,
            tickformat="%H:%M",
            ticklen=10
        ),
        xaxis2=dict(
        tickmode="auto",
        nticks=6,
        tickformat="%H:%M",
        ticklen=10
        ),

        yaxis=dict(showgrid=True, gridwidth=2, range=[-5.8,5.8], ticklen=10),
        yaxis2=dict(showgrid=True, gridwidth=2, range=[-5.8,5.8], ticklen=10, showticklabels=False),
        font=dict(size=20)
        )

    fig.add_hline(y=0, row=1, col="all")

    fig.write_html(save_path)

if __name__ == "__main__":
    trips_per_hour()
    net_flow_groups()