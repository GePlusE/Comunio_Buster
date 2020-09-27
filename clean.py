import pandas as pd
from datetime import date, datetime
import time


def clean_csv(filename):

    with open(filename) as f:
        count0 = sum(1 for line in f)
    df = pd.read_csv(filename)
    df.drop_duplicates(inplace=True)
    df.to_csv(filename, index=False)

    with open(filename) as f:
        count1 = sum(1 for line in f)

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if (count0 - count1) > 0:
        print(
            timestamp + f": Cleaned {count0 - count1} duplicates",
            file=open("LogFile.txt", "a"),
        )


clean_csv("fact_Player.csv")
