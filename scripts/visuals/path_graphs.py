import os

import pandas as pd
import geopandas as gpd
import numpy as np

from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import unary_union, linemerge
from shapely import simplify

import folium
from branca.colormap import LinearColormap

from .utils import save_folium_map

def segments(curve):
    return list(map(LineString, zip(curve.coords[:-1], curve.coords[1:])))


class DataProcessor():
    def __init__(self, colors):
        self.colors = colors

    def create_station_points_dict(self, stations_path):
        stations_df = pd.read_csv(stations_path)
        stations_df["geometry"] = [Point(xy) for xy in zip(stations_df.x, stations_df.y)]

        self.station_coords_dict = stations_df.set_index("ID")["geometry"].to_dict()
        self.stations_df = stations_df.set_index("ID")

    def create_path_geometries_dict(self, journey_routes_path):
        path_geometries = gpd.read_file(journey_routes_path)[["ids", "geometry"]].rename(columns={"ids":"path_id"})
        path_geometries = path_geometries.drop_duplicates("path_id")

        mask = path_geometries["geometry"].apply(lambda x: type(x) == LineString)
        path_geometries = path_geometries[mask]
        path_geometries = path_geometries.reset_index(drop=True)
        path_geometries["geometry"] = path_geometries["geometry"].apply(lambda line: LineString([(round(point[0], 4), round(point[1], 4)) for point in line.coords]))

        self.path_geometries_dict = path_geometries.set_index("path_id")["geometry"].to_dict()

    def load_grouped_counts(self, grouped_counts_path):
        data = pd.read_csv(grouped_counts_path)
        data["geometry"] = data["ids"].map(self.path_geometries_dict)
        data = data.dropna()
        self.data = data.reset_index(drop=True)


    def create_and_save_map(self, station_group, time_group, lat_center, lon_center, zoom, save_path):
        data2 = self.data[(self.data["Departure station id"].isin(station_group)) & (self.data["time"].isin(time_group))]

        data2["segments"] = data2["geometry"].apply(lambda x: segments(x))

        data2 = data2.explode("segments")
        data2["segments_wkt"] = data2["segments"].apply(lambda x: x.wkt)
        data2 = data2.groupby("segments_wkt").agg({"count":"sum", "segments":"first"}).reset_index()
        data2 = data2.groupby("count")["segments"].apply(list).reset_index()
        data2["segments"] = data2["segments"].apply(lambda x: unary_union(x))
        data2["segments"] = data2["segments"].apply(lambda x: linemerge(x) if type(x) == MultiLineString else x)
        data2["segments"] = data2["segments"].apply(lambda line: simplify(line, tolerance=0.00007))

        gdf = gpd.GeoDataFrame(data2, geometry="segments", crs="EPSG:4326")
        gdf["count"] = np.log2(gdf["count"] + 1)

        custom_cmap = LinearColormap(self.colors, vmin=gdf["count"].min(), vmax=gdf["count"].max())

        m = folium.Map(location=[lat_center, lon_center], zoom_start=zoom, tiles="CartoDB dark_matter",)
        gdf.explore(m=m, column="count", cmap=custom_cmap, vmin=1, vmax=8)

        if len(station_group) == 1:
            gpd.GeoDataFrame(geometry=[self.stations_df["geometry"][station_group[0]]], crs=gdf.crs).explore(m=m, color="#DCBF01", marker_kwds={"radius":4}, style_kwds={"fillOpacity":1})

        save_folium_map(m=m, save_path=save_path)


def path_graphs_main():
    cwd = os.getcwd()
    journey_routes_path = f"{cwd}/data/processed/journey_routes.gpkg"
    stations_path = f"{cwd}/data/raw/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin_7704606743268189464.csv"
    grouped_counts_path = f"{cwd}/data/processed/grouped_counts.csv"

    colors = [(0,0,0,0), (16*2, 1*2, 102*2, 128), (255,255,255,255)]

    herttoniemenranta_group = [
        257,
        256,
        255,
        254
        ]

    railway_station_group = [
        19,
        22,
        21
        ]

    vuosaari = 317
    pajamäki = 216
    tapanila = 351

    morning_times = ["06:00:00", "07:00:00", "08:00:00", "09:00:00", "10:00:00"]
    evening_times = ["14:00:00", "15:00:00", "16:00:00", "17:00:00", "18:00:00"]

    processor = DataProcessor(colors=colors)
    processor.create_station_points_dict(stations_path)
    processor.create_path_geometries_dict(journey_routes_path)
    processor.load_grouped_counts(grouped_counts_path)

    map_lon_center = processor.stations_df["x"].mean()
    map_lat_center = processor.stations_df["y"].mean()

    processor.create_and_save_map(station_group=herttoniemenranta_group, time_group=morning_times, lat_center=map_lat_center, lon_center=map_lon_center, zoom=12, save_path=f"{cwd}/presentation/herttoniemi_morning.png")
    processor.create_and_save_map(station_group=herttoniemenranta_group, time_group=evening_times, lat_center=map_lat_center, lon_center=map_lon_center, zoom=12, save_path=f"{cwd}/presentation/herttoniemi_afternoon.png")

    processor.create_and_save_map(station_group=railway_station_group, time_group=morning_times, lat_center=map_lat_center, lon_center=map_lon_center-0.1, zoom=12, save_path=f"{cwd}/presentation/steissi_morning.png")
    processor.create_and_save_map(station_group=railway_station_group, time_group=evening_times, lat_center=map_lat_center, lon_center=map_lon_center-0.1, zoom=12, save_path=f"{cwd}/presentation/steissi_afternoon.png")

    for station_id, station_name in zip([vuosaari, pajamäki, tapanila], ["vuosaari", "pajamäki", "tapanila"]):
        lon = processor.stations_df.loc[station_id].x
        lat = processor.stations_df.loc[station_id].y
        processor.create_and_save_map(station_group=[station_id], time_group=morning_times, lat_center=lat-0.03, lon_center=lon-0.07, zoom=13, save_path=f"{cwd}/presentation/{station_name}.png")
    

if __name__ == "__main__":
    main()