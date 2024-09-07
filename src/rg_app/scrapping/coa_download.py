import os.path
import time
import urllib.request

import pandas as pd


def download_coa_list(df_path: str, output_dir: str, resulting_df_path: str | None = None):
    df = pd.read_json(df_path)

    df["coa_fname"] = df["TERYT"] + "." + df["coa_link"].str.split(".").str[-1]
    # download images

    headers = {"User-Agent": "RoweroweGminy/0.0 (https://rowerowegminy.pl/; rowerowe-gminy@mp.miknowak.pl)"}
    for row in df.itertuples():
        url = str(row.coa_link)
        if row.coa_link is not None:
            if url.startswith("//"):
                url = "https:" + url
            with open(os.path.join(output_dir, str(row.coa_fname)), "wb") as f:
                req = urllib.request.Request(url, headers=headers)
                f.write(urllib.request.urlopen(req).read())
            print(f"Downloaded {url}, COA of {row.name}")
            time.sleep(0.05)
    df["coa_link"] = df["coa_fname"]
    df.drop(columns=["coa_fname"], inplace=True)
    if resulting_df_path:
        df.to_json(resulting_df_path, orient="records")
