import os

import pandas as pd
import geopandas as gpd
import numpy as np
import folium

from owslib.wfs import WebFeatureService

from branca.colormap import LinearColormap

from .utils import save_folium_map


class DataProcessor():
    def __init__(self,):
        pass

    def download_espoo_areas(self, espoo_gml_path):
        # URL of the WFS service
        wfs_url = "https://kartat.espoo.fi/teklaogcweb/wfs.ashx"

        # Connect to the WFS service
        wfs = WebFeatureService(url=wfs_url, version="1.1.0")

        typename = "kanta:TilastollinenAlue"

        response = wfs.getfeature(typename=typename, outputFormat="GML3", srsname="EPSG:4326")

        with open(espoo_gml_path, "wb") as f:
            f.write(response.read())

    def load_areas(self, espoo_gml_path, helsinki_areas_path, sea_path_1, sea_path_2):
        # espoo
        espoo_pienalueet = gpd.read_file(espoo_gml_path, engine="fiona")
        espoo_pienalueet = espoo_pienalueet[espoo_pienalueet["tyyppi"]=="pienalue"][["tunnus","geometry"]].rename(columns={"tunnus":"id_espoo"})

        # helsinki
        helsinki_pienalueet = gpd.read_file(helsinki_areas_path)[["geometry"]]

        # both
        pienalueet_gdf = pd.concat([espoo_pienalueet, helsinki_pienalueet.to_crs("EPSG:4326")]).reset_index(drop=True)
        pienalueet_gdf["area_id"] = pienalueet_gdf.index
        self.pienalueet_gdf = pienalueet_gdf.copy()

        # sea
        meri1 = gpd.read_file(sea_path_1).to_crs("EPSG:4326")
        meri1 = meri1[meri1["Kohdeluokk"]==36211]
        meri2 = gpd.read_file(sea_path_2).to_crs("EPSG:4326")

        self.meri = pd.concat([meri1, meri2])

    def load_data(self, net_flow_df_path, points_gdf_path, stations_path):
        self.net_flow_df = pd.read_csv(net_flow_df_path)
        self.points_gdf = gpd.read_file(points_gdf_path)
        self.stations_df = pd.read_csv(stations_path)


    def process_data(self):
        areas_to_drop = [176,
                        340,
                        388,
                        339,
                        211,
                        387,
                        177,
                        166,
                        362,
                        286,
                        148,
                        230
                        ]
        # overlay points and areas
        pienalueet_gdf = self.pienalueet_gdf[~self.pienalueet_gdf["area_id"].isin(areas_to_drop)]
        df = gpd.sjoin(self.points_gdf.to_crs("EPSG:3387"), pienalueet_gdf.to_crs("EPSG:3387"), how="left")
        net_flow_df_grouped = self.net_flow_df.groupby("Departure station id")["volume"].sum().reset_index()

        def weighted_avg(group):
            return (group["group"] * group["volume"]).sum() / group["volume"].sum()

        # determine the group of the area
        df2 = pd.merge(df, net_flow_df_grouped, how="left")
        area_group_dict = df2.groupby("area_id")[["group","volume"]].apply(weighted_avg).round().to_dict()
        pienalueet_gdf["group"] = pienalueet_gdf["area_id"].map(area_group_dict)
        
        # drop emtpy areas in espoo
        pienalueet_gdf["drop"] = np.where((~pienalueet_gdf["group"].notna()) & (pienalueet_gdf["id_espoo"].notna()) & ~(pienalueet_gdf["id_espoo"]==311), 1, 0)
        pienalueet_gdf = pienalueet_gdf[pienalueet_gdf["drop"] == 0]

        # fill areas with no stations with gpd.sjoin_nearest()
        nans = pienalueet_gdf[~pienalueet_gdf["group"].notna()]
        df = gpd.sjoin_nearest(self.points_gdf.to_crs("EPSG:3387"), nans.to_crs("EPSG:3387")[["geometry", "area_id"]], how="right")[["area_id", "group"]]
        area_group_nans_dict = df.groupby("area_id")["group"].agg(lambda x: pd.Series.mode(x).iloc[0] if not x.empty else None).to_dict()
        nans["group"] = nans["area_id"].map(area_group_nans_dict)
        pienalueet_gdf = pd.concat([pienalueet_gdf.dropna(subset="group"), nans])

        pienalueet_gdf = gpd.overlay(pienalueet_gdf, self.meri, how="difference")
        pienalueet_gdf = pienalueet_gdf.dissolve("group", aggfunc="first").reset_index()
    
        pienalueet_gdf = pienalueet_gdf.replace({1.0:0.0, 0.0:1.0})

        self.pienalueet_gdf = pienalueet_gdf.copy()


    def create_and_save_map(self, save_path):
        colors = [(16, 1, 102), (220,191,1)] # blue to yellow

        custom_cmap = LinearColormap(colors, vmin=0.0, vmax=1.0)
        pienalueet_gdf = self.pienalueet_gdf.to_crs("EPSG:3387")
        pienalueet_gdf["geometry"] = pienalueet_gdf["geometry"].buffer(1)

        lon_center = self.stations_df["x"].mean()
        lat_center = self.stations_df["y"].mean()

        pienalueet_gdf = pienalueet_gdf.replace({1.0:0.0, 0.0:1.0})
        
        m = folium.Map(location=[lat_center+0.015, lon_center-0.05], zoom_start=12, tiles="CartoDB positron")
        pienalueet_gdf.explore(m=m, column="group", style_kwds={"fillOpacity":0.17, "opacity":0.2}, cmap=custom_cmap)

        save_folium_map(m=m, save_path=save_path)

def segmented_map_main():
    cwd = os.getcwd()
    espoo_gml_path = f"{cwd}/data/raw/tilastollinenalue_espoo.gml"
    helsinki_areas_path = f"{cwd}/data/raw/pienalueet_WFS.gpkg"
    sea_path_1 = f"{cwd}/data/raw/meri/L41_VesiAlue.shp"
    sea_path_2 = f"{cwd}/data/raw/meri/K42_VesiAlue.shp"
    save_path = f"{cwd}/presentation/segmentation.png"
    net_flow_df_path = f"{cwd}/data/processed/net_flow_df.csv"
    points_gdf_path = f"{cwd}/data/processed/points_gdf.gpkg"
    stations_path = f"{cwd}/data/raw/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin_7704606743268189464.csv"

    processor = DataProcessor()
    processor.download_espoo_areas(espoo_gml_path)
    processor.load_areas(espoo_gml_path, helsinki_areas_path, sea_path_1, sea_path_2)
    processor.load_data(net_flow_df_path, points_gdf_path, stations_path)
    processor.process_data()
    processor.create_and_save_map(save_path)


if __name__ == "__main__":
    main()