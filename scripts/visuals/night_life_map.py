import os

import pandas as pd
import geopandas as gpd
import folium
import numpy as np

from .utils import save_folium_map

def night_life_map_main():
    cwd = os.getcwd()
    save_path = f"{cwd}/presentation/night_life.png"
    net_flow_gdf_path = f"{cwd}/data/processed/net_flow_gdf.gpkg"
    stations_df_path = f"{cwd}/data/raw/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin_7704606743268189464.csv"

    net_flow_df = gpd.read_file(net_flow_gdf_path)
    stations_df = pd.read_csv(stations_df_path)

    night_life = net_flow_df[net_flow_df["time"].isin(["23:00:00", "00:00:00", "01:00:00", "02:00:00", "03:00:00", "04:00:00"])]
    night_life = night_life.groupby("Departure station id").agg({"departures":"sum", "returns":"sum", "geometry":"first"}).reset_index()

    night_life["net_flow"] = night_life["returns"] - night_life["departures"]
    night_life["sign"] = night_life["net_flow"]
    night_life["net_flow"] = np.log2(np.abs(night_life["net_flow"]) + 1)
    night_life["net_flow"] = np.copysign(night_life["net_flow"], night_life["sign"])

    lon_center = stations_df["x"].mean()
    lat_center = stations_df["y"].mean()

    df = night_life[night_life["net_flow"]<-8]
    df["net_flow"] = np.abs(df["net_flow"])

    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    m = folium.Map(location=[lat_center+0.015, lon_center-0.1], zoom_start=12, tiles="CartoDB dark-matter")
    m = gdf.explore(m=m, column="net_flow", marker_kwds={"radius":10}, cmap="Reds_r", vmin=7, vmax=10.7)

    save_folium_map(m=m, save_path=save_path)


if __name__ == "__main__":
    night_life_map_main()