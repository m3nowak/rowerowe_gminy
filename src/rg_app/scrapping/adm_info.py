import logging
import os.path
import urllib.parse
import urllib.request

import bs4
import pandas as pd

import rg_app.core

pd.options.mode.copy_on_write = True

WIKI_BASE_URL = "https://pl.wikipedia.org"

logging.basicConfig(level=logging.INFO)


def get_communes_data() -> pd.DataFrame:
    df_list = pd.read_html("https://pl.wikipedia.org/wiki/Lista_gmin_w_Polsce", match="Powiat", extract_links="body")
    assert len(df_list) == 1, "There should be only one table with communes"
    df = df_list[0]
    # drop 2 last columns
    df = df.iloc[:, :-2]
    # rename columns
    df.columns = ["TERYT", "commune", "county", "voivodeship", "area", "population"]

    df["link"] = df["commune"].apply(lambda x: x[1])
    df["name"] = df["commune"].apply(lambda x: x[0])

    del df["commune"]

    df["county_link"] = df["county"].apply(lambda x: x[1])
    df["county"] = df["county"].apply(lambda x: x[0])

    df["is_mnpp"] = df["county_link"].isna()
    df["county_link"] = df["county_link"].fillna(df["link"])

    df["voivodeship_link"] = df["voivodeship"].apply(lambda x: x[1])
    df["voivodeship"] = df["voivodeship"].apply(lambda x: x[0])

    df["area"] = df["area"].apply(lambda x: float(x[0].replace(",", ".")))

    df["population"] = df["population"].apply(lambda x: int(x[0].replace(" ", "")))

    df["TERYT"] = df["TERYT"].apply(lambda x: x[0])

    return df


def mk_counties_data(communes_data: pd.DataFrame) -> pd.DataFrame:
    communes_data = communes_data.copy()
    counties_data = (
        communes_data.groupby("county")
        .agg(
            name=pd.NamedAgg(column="county", aggfunc="first"),  # rename column to "name"
            TERYT=pd.NamedAgg(column="TERYT", aggfunc="first"),
            link=pd.NamedAgg(column="county_link", aggfunc="first"),
            area=pd.NamedAgg(column="area", aggfunc="sum"),
            population=pd.NamedAgg(column="population", aggfunc="sum"),
            communes=pd.NamedAgg(column="name", aggfunc="count"),
            voivodeship=pd.NamedAgg(column="voivodeship", aggfunc="first"),
            voivodeship_link=pd.NamedAgg(column="voivodeship_link", aggfunc="first"),
        )
        .reset_index()
    )
    counties_data["TERYT"] = counties_data["TERYT"].apply(lambda x: x[:-3])
    return counties_data


def mk_voivodeships_data(communes_data: pd.DataFrame) -> pd.DataFrame:
    communes_data = communes_data.copy()
    voivodeships_data = (
        communes_data.groupby("voivodeship")
        .agg(
            name=pd.NamedAgg(column="voivodeship", aggfunc="first"),  # rename column to "name"
            TERYT=pd.NamedAgg(column="TERYT", aggfunc="first"),
            link=pd.NamedAgg(column="voivodeship_link", aggfunc="first"),
            area=pd.NamedAgg(column="area", aggfunc="sum"),
            population=pd.NamedAgg(column="population", aggfunc="sum"),
            communes=pd.NamedAgg(column="name", aggfunc="count"),
            counties=pd.NamedAgg(column="county", aggfunc="nunique"),
        )
        .reset_index()
    )
    voivodeships_data["TERYT"] = voivodeships_data["TERYT"].apply(lambda x: x[:-5])
    return voivodeships_data


def _fix_coa_link(link: str) -> str:
    return link
    # skip fixing
    # link = link.replace("//", "")
    # splitted = link.split("/")[:-1]
    # if "thumb" in splitted:
    #     splitted.remove("thumb")
    # else:
    #     logging.warning(f"COA link does not contain 'thumb' {link}")
    # return "https://" + "/".join(splitted)


def get_coa_link(wiki_page_link: str) -> str | None:
    full_link = urllib.parse.urljoin(WIKI_BASE_URL, wiki_page_link)
    html = urllib.request.urlopen(full_link).read().decode("utf-8")
    soup = bs4.BeautifulSoup(html, "html.parser")
    infobox = soup.find("table", class_="infobox")  # type: ignore
    assert infobox is not None, f"No infobox found at {full_link}"
    ibox2 = infobox.find("table", class_="ibox2")  # type: ignore
    if ibox2 is not None:
        img = ibox2.find("img", attrs={"alt": "Herb"})  # type: ignore
        if img is not None:
            img_src = img.attrs["src"]  # type: ignore
            logging.info(f"Got COA link for {full_link}")
            return _fix_coa_link(img_src)
        else:
            logging.info(f"No img found for {full_link}")
    else:
        logging.info(f"No ibox2 found for {full_link}")
    logging.info(f"No COA link found for {full_link}")
    # try direct
    img = soup.find("img", attrs={"alt": "Herb"}, class_="mw-file-element")
    if img is not None:
        img_src = img.attrs["src"]  # type: ignore
        logging.info(f"Got COA link for {full_link}")
        return _fix_coa_link(img_src)
    else:
        logging.info(f"Direct failed for {full_link}")
    return None


def extend_wiki_data(df: pd.DataFrame) -> pd.DataFrame:
    df["coa_link"] = df["link"].apply(get_coa_link)
    logging.info(f"Got {df["coa_link"].count()} COA links out of {df['TERYT'].count()}")
    return df


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    df["TERYT"] = df["TERYT"].astype(str)
    max_teryt_len = df["TERYT"].str.len().max()
    if max_teryt_len == 7:
        df["type"] = "GMI"
    elif max_teryt_len == 4:
        df["type"] = "POW"
        df["is_mnpp"] = False
    elif max_teryt_len == 2:
        df["type"] = "WOJ"
        df["is_mnpp"] = False
    else:
        raise ValueError(f"Unexpected TERYT length {max_teryt_len}")
    result = df[["TERYT", "name", "area", "population", "link", "coa_link"]].copy()
    result.set_index("TERYT")
    return result


def save_data(path: str):
    communes = get_communes_data()
    counties = mk_counties_data(communes)
    voivodeships = mk_voivodeships_data(communes)

    voivodeships = extend_wiki_data(voivodeships)
    counties = extend_wiki_data(counties)
    communes = extend_wiki_data(communes)

    communes.to_json(os.path.join(path, f"{rg_app.core.COMMUNES_FNAME}.json"), orient="records", indent=2)
    counties.to_json(os.path.join(path, f"{rg_app.core.COUNTIES_FNAME}.json"), orient="records", indent=2)
    voivodeships.to_json(os.path.join(path, f"{rg_app.core.VOIVODESHIPS_FNAME}.json"), orient="records", indent=2)

    std = [standardize(communes), standardize(counties), standardize(voivodeships)]
    combo = pd.concat(std)
    combo.to_json(os.path.join(path, f"{rg_app.core.COMBO_FNAME}.json"), orient="records", indent=2)
