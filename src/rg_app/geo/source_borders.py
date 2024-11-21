import os.path
import zipfile
from contextlib import AsyncExitStack

import aiofiles
import httpx
from geopandas import GeoDataFrame
from opentelemetry import trace

from rg_app.geo.src_load import bundle_to_combo, load_gml_files

DEFAULT_GML_URL = "https://opendata.geoportal.gov.pl/prg/granice/00_jednostki_administracyjne_gml.zip"
CACHE_LOCATION = "data/gml_pak.zip"

TARGET_CRS = "EPSG:4326"
SOURCE_CRS = "EPSG:2180"


async def _async_copy_file(src_path: str, dst_path: str) -> None:
    """
    Asynchronously copy a file from source to destination.

    Args:
        src_path: Source file path
        dst_path: Destination file path
    """
    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    # Open and copy file asynchronously
    async with aiofiles.open(src_path, "rb") as fsrc:
        async with aiofiles.open(dst_path, "wb") as fdst:
            # Read and write in chunks to handle large files
            chunk_size = 64 * 1024  # 64KB chunks
            while True:
                chunk = await fsrc.read(chunk_size)
                if not chunk:
                    break
                await fdst.write(chunk)


def fix_crs(gdf: GeoDataFrame) -> GeoDataFrame:
    gdf.geometry.set_crs(crs=SOURCE_CRS, inplace=True, allow_override=True)
    gdf.geometry = gdf.geometry.to_crs(crs=TARGET_CRS)
    return gdf


async def get_gdf(url: str | None = None, cache_file_path: str | None = None) -> GeoDataFrame:
    url = url or DEFAULT_GML_URL
    cache_file_path = cache_file_path or CACHE_LOCATION

    tracer = trace.get_tracer("download_gml")

    async with AsyncExitStack() as aes:
        aes.enter_context(tracer.start_as_current_span("get_gdf"))
        temp_file = await aes.enter_async_context(aiofiles.tempfile.NamedTemporaryFile("wb+"))
        temp_file_path = str(temp_file.name)
        tmp_dir = await aes.enter_async_context(aiofiles.tempfile.TemporaryDirectory())
        if os.path.exists(cache_file_path):
            with tracer.start_as_current_span("copy_cache_file") as span:
                span.set_attribute("cache_file_path", cache_file_path)
                span.set_attribute("temp_file_path", temp_file_path)
                await _async_copy_file(cache_file_path, temp_file_path)
        else:
            with tracer.start_as_current_span("download_file") as span:
                span.set_attribute("url", url)
                client = await aes.enter_async_context(httpx.AsyncClient())
                resp = await aes.enter_async_context(client.stream("GET", url))
                async for chunk in resp.aiter_bytes():
                    await temp_file.write(chunk)
        zip_ref = aes.enter_context(zipfile.ZipFile(str(temp_file.name), "r"))
        dir_name = str(tmp_dir)
        with tracer.start_as_current_span("extract_zip") as span:
            span.set_attribute("dir_name", dir_name)
            zip_ref.extractall(dir_name)
        with tracer.start_as_current_span("load_gml_files") as span:
            bundle = load_gml_files(dir_name)
        with tracer.start_as_current_span("bundle_to_combo") as span:
            combo = bundle_to_combo(bundle)
        with tracer.start_as_current_span("fix_crs") as span:
            combo = fix_crs(combo)
        return combo
    raise RuntimeError("Should not reach this point")


if __name__ == "__main__":
    import asyncio

    asyncio.run(get_gdf())
