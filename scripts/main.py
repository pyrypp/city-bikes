from calculate_paths import calculate_paths_main
from clustering import clustering_main
from create_grouped_counts import grouped_counts_main
from create_net_flows import net_flows_main
from create_station_pairs import station_pairs_main
from download_trip_data import download_trip_data_main

from visuals.line_charts import trips_per_hour, net_flow_groups
from visuals.night_life_map import night_life_map_main
from visuals.path_graphs import path_graphs_main
from visuals.segmented_map import segmented_map_main

import pandas as pd
pd.options.mode.chained_assignment = None

def load_and_process_data():
    download_trip_data_main()
    station_pairs_main()
    grouped_counts_main()
    net_flows_main()
    calculate_paths_main(create_new_graph=True)
    clustering_main()

def create_visuals():
    trips_per_hour()
    net_flow_groups()
    night_life_map_main()
    path_graphs_main()
    segmented_map_main()

if __name__ == "__main__":
    load_and_process_data()
    create_visuals()
