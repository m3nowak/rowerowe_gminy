import os.path
import time
import urllib.request

import pandas as pd


def download_coa_list(df_path: str, output_dir: str, resulting_df_path: str | None = None, skip_downloaded: bool = True):
    df = pd.read_json(df_path, dtype={"TERYT": str})

    ldf = df.dropna(subset=["coa_link"])

    ldf["coa_fname"] = ldf["TERYT"].astype(str) + "." + ldf["coa_link"].str.split(".").str[-1].astype(str)
    # download images

    headers = {"User-Agent": "RoweroweGminy/0.0 (https://rowerowegminy.pl/; rowerowe-gminy@mp.miknowak.pl)"}
    for row in ldf.itertuples():
        url = str(row.coa_link)
        if url.startswith("//"):
            url = "https:" + url
        tgt_fname = os.path.join(output_dir, str(row.coa_fname))
        if skip_downloaded and os.path.exists(tgt_fname):
            print(f"Skipping {url}, COA of {row.name}")
        else:
            with open(tgt_fname, "wb") as f:
                req = urllib.request.Request(url, headers=headers)
                f.write(urllib.request.urlopen(req).read())
            print(f"Downloaded {url}, COA of {row.name}")
            time.sleep(0.05)
    ldf["coa_link"] = ldf["coa_fname"]
    ldf.drop(columns=["coa_fname"], inplace=True)

    #update df coa_link
    df.update(ldf)

    if resulting_df_path:
        df.to_json(resulting_df_path, orient="records")
