import os

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

'''
Take the net flow dataframe and segment the stations into two using K-Means clustering.
Saves a dataframe with columns:
Departure station id, group, coords
'''

def create_station_points_dict(stations_path):
    stations_df = pd.read_csv(stations_path)
    stations_df["geometry"] = [Point(xy) for xy in zip(stations_df.x, stations_df.y)]
    station_points_dict = stations_df.set_index("ID")["geometry"].to_dict()
    return station_points_dict

def clustering_main():
    cwd = os.getcwd()
    net_flow_df_path = f"{cwd}/data/processed/net_flow_df.csv"
    save_path = f"{cwd}/data/processed/points_gdf.gpkg"
    stations_path = f"{cwd}/data/raw/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin_7704606743268189464.csv"

    station_points_dict = create_station_points_dict(stations_path)

    net_flow_df = pd.read_csv(net_flow_df_path)
    df = net_flow_df.pivot(columns="time", index="Departure station id", values="net_flow")
    df.fillna(0, inplace=True)

    scaler = StandardScaler()
    df.iloc[:,:] = scaler.fit_transform(df)

    kmeans = KMeans(n_clusters=2)
    kmeans.fit(df)

    df["group"] = kmeans.labels_
    df = pd.DataFrame({"Departure station id":df.index, "group":df.group.tolist()})

    df["coords"] = df["Departure station id"].map(station_points_dict)

    points_gdf = gpd.GeoDataFrame(df, geometry="coords", crs="EPSG:4326")

    points_gdf.to_file(save_path)

if __name__ == "__main__":
    clustering_main()