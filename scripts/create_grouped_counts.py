import pandas as pd
import os


'''
Transforms the trips dataframe into a dataframe with the columns: 
Departure station id, Return station id, time, count, ids
'''


def get_data(path):
    return pd.read_csv(path)

def process_data(df):
    df["Departure"] = pd.to_datetime(df["Departure"], format="mixed")
    df["time"] = df["Departure"].dt.round(freq="60min").dt.time

    df = df.groupby(["Departure station id", "Return station id", "time"])["Return"].count().reset_index().rename(columns={"Return": "count"})
    df["ids"] = df.apply(lambda row: tuple(sorted((int(row["Departure station id"]), int(row["Return station id"])))), axis=1)

    return df

def grouped_counts_main():
    cwd = os.getcwd()
    trips_path = f"{cwd}/data/processed/trips.csv"
    save_path = f"{cwd}/data/processed/grouped_counts.csv"

    grouped_counts_df = get_data(trips_path)
    grouped_counts_df = process_data(grouped_counts_df)

    grouped_counts_df.to_csv(save_path, index=False)


if __name__ == "__main__":
    grouped_counts_main()