import pandas as pd
from shapely.geometry import Point, LineString
import os

'''
Transforms the trips dataframe into a dataframe with the columns: 
Departure station id, Return station id, count, x_dep, y_dep, x_ret, y_ret
'''

class Processor:
    def __init__(self, trips_path, stations_path):
        self.trips_path = trips_path
        self.stations_path = stations_path

    def load_data(self):
        self.trips_df = pd.read_csv(self.trips_path)
        self.stations_df = pd.read_csv(self.stations_path)

    def preprocess_data(self):
        self.stations_df["geometry"] = [Point(xy) for xy in zip(self.stations_df.x, self.stations_df.y)]

        self.trips_df = self.trips_df[self.trips_df["Return station id"] < 997]
        self.trips_df = self.trips_df[self.trips_df["Departure station id"] < 997]

        self.station_pair_counts = self.trips_df.groupby(["Departure station id", "Return station id"])["Departure"].count().reset_index().rename(columns={"Departure":"count"})
        self.station_pair_counts = self.station_pair_counts.merge(self.stations_df[["ID", "x", "y"]], left_on="Departure station id", right_on="ID")
        self.station_pair_counts = self.station_pair_counts.merge(self.stations_df[["ID", "x", "y"]], left_on="Return station id", right_on="ID", suffixes=("_dep", "_ret"))
        self.station_pair_counts = self.station_pair_counts.drop(columns=["ID_dep", "ID_ret"])

    def save_df(self, path):
        self.station_pair_counts.to_csv(path, index=False)

def station_pairs_main():
    cwd = os.getcwd()
    trips_path = f"{cwd}/data/processed/trips.csv"
    stations_path = f"{cwd}/data/raw/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin_7704606743268189464.csv"

    a = Processor(trips_path, stations_path)
    a.load_data()
    a.preprocess_data()
    a.save_df(f"{cwd}/data/processed/station_pair_counts.csv")

if __name__ == "__main__":
    station_pairs_main()