import pandas as pd
import geopandas as gpd
import numpy as np
import os
from shapely.geometry import Point

'''
Use the grouped counts dataframe to calculate the net flow for each station
(i.e. returns - departures)
For the output dataframe we take log2(net flow + 1)
'''

def create_station_points_dict(stations_path):
    stations_df = pd.read_csv(stations_path)
    stations_df["geometry"] = [Point(xy) for xy in zip(stations_df.x, stations_df.y)]
    station_points_dict = stations_df.set_index("ID")["geometry"].to_dict()
    return station_points_dict

def load_data(path):
    return pd.read_csv(path)[["Departure station id", "Return station id", "time", "count"]]

def create_departures_df(grouped_counts_df, station_points_dict):
    data = grouped_counts_df.groupby(["Departure station id", "time"])["count"].sum().reset_index()
    data["coords"] = data["Departure station id"].map(station_points_dict)
    data = data.dropna()

    data["lon"] = data["coords"].apply(lambda point: point.coords[0][0])
    data["lat"] = data["coords"].apply(lambda point: point.coords[0][1])

    data = data.rename(columns={"count": "departures"})

    return data

def create_returns_df(grouped_counts_df):
    data = grouped_counts_df.groupby(["Return station id", "time"])["count"].sum().reset_index()
    data = data.dropna()

    data = data.rename(columns={"count": "returns"})

    return data

def create_net_flow_df(departures_df, returns_df):
    net_flow_df = departures_df.merge(returns_df[["Return station id", "time", "returns"]], left_on=["Departure station id", "time"], right_on=["Return station id", "time"]).drop(columns=["Return station id"])

    net_flow_df["net_flow"] = net_flow_df["returns"] - net_flow_df["departures"]
    net_flow_df["sign"] = net_flow_df["net_flow"]
    net_flow_df["net_flow"] = np.log2(np.abs(net_flow_df["net_flow"]) + 1)
    net_flow_df["net_flow"] = np.copysign(net_flow_df["net_flow"], net_flow_df["sign"])
    net_flow_df["volume"] = net_flow_df["departures"] + net_flow_df["returns"]
    net_flow_df = net_flow_df.drop(columns=["sign"])
    
    return net_flow_df



def net_flows_main():
    cwd = os.getcwd()
    grouped_counts_path = f"{cwd}/data/processed/grouped_counts.csv"
    save_path = f"{cwd}/data/processed/net_flow_df.csv"
    gdf_save_path = f"{cwd}/data/processed/net_flow_gdf.gpkg"
    stations_path = f"{cwd}/data/raw/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin_7704606743268189464.csv"

    station_points_dict = create_station_points_dict(stations_path)
    grouped_counts_df = load_data(grouped_counts_path)

    departures_df = create_departures_df(grouped_counts_df[["Departure station id", "time", "count"]], station_points_dict)
    returns_df = create_returns_df(grouped_counts_df[["Return station id", "time", "count"]])

    net_flow_df = create_net_flow_df(departures_df, returns_df)

    gpd.GeoDataFrame(net_flow_df, geometry="coords", crs="EPSG:4326").to_file(gdf_save_path)

    net_flow_df.to_csv(save_path, index=False)

if __name__ == "__main__":
    net_flows_main()