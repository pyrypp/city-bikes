import pandas as pd
import geopandas as gpd
import osmnx as ox
import pickle
import os
import logging
from shapely.geometry import Point, LineString
import multiprocessing

'''
Takes in the station_pair_counts.csv dataframe and returns a dataframe with the paths between each station pair.
'''

class DataProcessor():
    def __init__(self, grouper_size):
        self.grouper = grouper_size
    
    def load_data(self, path):
        self.station_pair_counts = pd.read_csv(path)

        # duplicate paths removed
        self.station_pair_counts["ids"] = self.station_pair_counts.apply(lambda row: tuple(sorted((int(row["Departure station id"]), int(row["Return station id"])))), axis=1)
        self.station_pair_counts_dd = self.station_pair_counts.drop_duplicates("ids")

    def save_point_coordinates_to_lists(self):
        self.dep_points_x_list = self.station_pair_counts_dd["x_dep"].tolist()
        self.dep_points_y_list = self.station_pair_counts_dd["y_dep"].tolist()

        self.ret_points_x_list = self.station_pair_counts_dd["x_ret"].tolist()
        self.ret_points_y_list = self.station_pair_counts_dd["y_ret"].tolist()
        print(f"Lenght: {len(self.dep_points_x_list)}")

    def calculate_bbox(self):
        left = min(self.dep_points_x_list)
        bottom = min(self.dep_points_y_list)
        right = max(self.dep_points_x_list)
        top = max(self.dep_points_y_list)
        self.bbox = (left, bottom, right, top)

    def create_graph(self, path):
        G = ox.graph_from_bbox(self.bbox, network_type='bike')
        with open(path, "wb") as f:
            pickle.dump(G, f)
        del G
    
    def load_graph(self, path):
        with open(path, "rb") as f:
            self.G = pickle.load(f)

    def router(self, i, G, orig, dest):
        print(f"Starting process {i}")
        routes = ox.shortest_path(G, orig[i:i+self.grouper], dest[i:i+self.grouper])
        print(f"Finish process {i}")
        return routes

    def calculate_routes(self):
        orig = ox.nearest_nodes(self.G, self.dep_points_x_list, self.dep_points_y_list)
        dest = ox.nearest_nodes(self.G, self.ret_points_x_list, self.ret_points_y_list)
        args = [(i, self.G, orig, dest) for i in range(0, len(orig), self.grouper)]

        with multiprocessing.Pool(multiprocessing.cpu_count()-2) as pool:
            results = pool.starmap(self.router, args)

        # routes = [value for d in results for value in d.values()]
        routes = [x for xs in results for x in xs]
        route_coords = [[(self.G.nodes[node]["x"], self.G.nodes[node]["y"]) for node in route] for route in routes]
        linestrings = [LineString(coords) if len(coords) > 1 else Point(coords) for coords in route_coords]

        # duplicate paths are mapped back to the main df
        self.station_pair_counts_dd["geometry"] = linestrings
        linedict = self.station_pair_counts_dd.set_index("ids")["geometry"].to_dict()

        self.journey_routes_df = gpd.GeoDataFrame(self.station_pair_counts)
        self.journey_routes_df["geometry"] = self.journey_routes_df["ids"].map(linedict)
        self.journey_routes_df = self.journey_routes_df.set_geometry("geometry")
        self.journey_routes_df = self.journey_routes_df.set_crs("EPSG:4326")

    def save_gdf(self, path):
        self.journey_routes_df.to_file(path)

def calculate_paths_main(create_new_graph=True):
    cwd = os.getcwd()
    station_pair_data_path = f"{cwd}/data/processed/station_pair_counts.csv"
    graph_path = f"{cwd}/data/processed/graph.pkl"
    save_path = f"{cwd}/data/processed/journey_routes.gpkg"

    processor = DataProcessor(grouper_size=4000)

    processor.load_data(station_pair_data_path)
    processor.save_point_coordinates_to_lists()
    processor.calculate_bbox()
    if create_new_graph:
        processor.create_graph(graph_path)
    processor.load_graph(graph_path)
    processor.calculate_routes()
    processor.save_gdf(save_path)

if __name__ == "__main__":
    calculate_paths_main()