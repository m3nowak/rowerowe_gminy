import os.path
import time
import typing as ty
import urllib.error
import urllib.request

import pandas as pd

POLAND_SVG_LINK = "https://upload.wikimedia.org/wikipedia/commons/c/c9/Herb_Polski.svg"


def download_coa_list(
    df_path: str, output_dir: str, resulting_df_path: str | None = None, skip_downloaded: bool = True, limit: int = 0
):
    df = pd.read_json(df_path, dtype={"TERYT": str})

    ldf = df.copy()  # df.dropna(subset=["coa_link"])

    ldf["coa_low_quality"] = False

    ldf["coa_fname"] = ldf["TERYT"].astype(str) + "." + ldf["coa_link"].str.split(".").str[-1].astype(str)
    # download images

    headers = {"User-Agent": "RoweroweGminy/0.0 (https://rowerowegminy.pl/; rowerowe-gminy@mp.miknowak.pl)"}
    download_image(headers, POLAND_SVG_LINK, os.path.join(output_dir, "0.svg"))
    for idx, row in ldf.iterrows():
        if row.coa_link is None:
            continue
        idx = ty.cast(int, idx)
        row = ty.cast(ty.Any, row)
        # f it if something goes wrong check this line
        url = str(row.coa_link)
        if url.startswith("//"):
            url = "https:" + url
        tgt_fname = os.path.join(output_dir, str(row.coa_fname))
        if skip_downloaded and os.path.exists(tgt_fname):
            name = ty.cast(str, row.name)
            print(f"Skipping {url}, COA of {name}")
        else:
            # session = new_session(model_name="isnet-anime")
            download_image(headers, url, tgt_fname)
            # if tgt_fname.endswith(".jpg") or tgt_fname.endswith(".jpeg"):
            #     ldf.at[row.name, "coa_low_quality"] = True
            # img = Image.open(tgt_fname)
            # img = ty.cast(Image.Image, remove(img, session=session))
            # tgt_fname = tgt_fname.split(".")[0] + ".png"
            # img.save(tgt_fname)
            # print(f"Converted {tgt_fname} to PNG")
        if limit and idx >= limit:
            break

    ldf["coa_link"] = ldf["coa_fname"]
    # set low quality flag if file name ends with .jpg
    ldf["coa_low_quality"] = ldf["coa_fname"].str.endswith(".jpg")
    ldf.drop(columns=["coa_fname"], inplace=True)

    # if limit is not 0, cut the dataframe
    if limit:
        ldf = ldf.head(limit)
        if resulting_df_path:
            ldf.to_json(resulting_df_path, orient="records", indent=2)
    else:
        if resulting_df_path:
            ldf.to_json(resulting_df_path, orient="records")


def download_image(headers, url, tgt_fname):
    with open(tgt_fname, "wb") as f:
        downloaded = False
        resp = None
        while not downloaded:
            try:
                req = urllib.request.Request(url, headers=headers)
                resp = urllib.request.urlopen(req)
                downloaded = True
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(1)
                    continue
                else:
                    raise e
        assert resp is not None
        f.write(resp.read())
    print(f"Downloaded {url} to {tgt_fname}")
    time.sleep(0.05)
