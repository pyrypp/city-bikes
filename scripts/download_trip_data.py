import pandas as pd
import requests
import zipfile
import os

'''
Downloads the trips dataset zip, unzips it and saves as csv.
'''

def download_trip_data(data_url, zip_path, processed_csv_path) -> None:
    r = requests.get(data_url)
    with open(zip_path, "wb") as f:
        f.write(r.content)

    dfs = []

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_name in zip_ref.namelist()[1:]:
            with zip_ref.open(file_name) as file:
                df = pd.read_csv(file)
                dfs.append(df)

    trip_df = pd.concat(dfs)
    trip_df.to_csv(processed_csv_path, index=False)



def download_trip_data_main():
    cwd = os.getcwd()
    trip_data_url = "https://dev.hsl.fi/citybikes/od-trips-2024/od-trips-2024.zip"
    trip_zip_path = f"{cwd}/data/raw/od-trips-2024.zip"
    trip_save_path = f"{cwd}/data/processed/trips.csv"

    download_trip_data(trip_data_url, trip_zip_path, trip_save_path)

if __name__ == "__main__":
    download_trip_data_main()