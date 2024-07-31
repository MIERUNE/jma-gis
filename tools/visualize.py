import logging
from hashlib import sha1
from pathlib import Path

import cartopy.crs
import geopandas as gpd
from matplotlib import pyplot as plt

ccrs = cartopy.crs.Mercator()

logger = logging.getLogger(__name__)


def hash_to_float(n: str):
    hash_object = sha1(str(n).encode("utf-8")).hexdigest()
    hash_int = int(hash_object, 16)
    return hash_int / (2**160 - 1)


for filename in Path("srcdata/shapes").glob("*.shp"):
    print(filename)
    df = gpd.read_file(filename, encoding="utf-8")

    cmap = plt.get_cmap("hsv", len(df))

    fig, ax = plt.subplots(
        figsize=(20, 20), tight_layout=True, subplot_kw={"projection": ccrs}
    )
    colors = df.name.apply(lambda n: cmap(hash_to_float(n)))

    if "津波予報区" in filename.stem:
        ax.add_geometries(
            df["geometry"], crs=ccrs, facecolor="none", linewidth=3, edgecolor=colors
        )
    else:
        ax.add_geometries(
            df["geometry"],
            crs=ccrs,
            linewidth=0.3,
            facecolor=colors,
            edgecolor="black",
        )
        pass

    fig.tight_layout()
    ax.set_xlim(122.5, 150)
    ax.set_ylim(22.5, 50)
    ax.gridlines()
    fig.savefig(Path("./visualized/images").joinpath(filename.stem + ".png"), dpi=300)
