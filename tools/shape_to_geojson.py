"""シェイプファイル (.shp) を GeoJSON に変換する"""

# usage:
# $ python3 shape_to_geojson.py src1.shp > output.json
# $ python3 shape_to_geojson.py src1.shp src2.shp > output.json

import json
import logging
import sys
from pathlib import Path
from typing import Iterable, cast

import geopandas as gpd
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

logger = logging.getLogger(__name__)


filenames = [Path(filename) for filename in sys.argv[1:]]
closed = set()


def iter_features() -> Iterable[dict]:
    for filename in filenames:
        df = gpd.read_file(filename, encoding="utf-8")
        if "code" in df:
            df.sort_values(by="code", inplace=True)
        else:
            df.sort_values(by="regioncode", inplace=True)

        for _, row in df.iterrows():
            # 区域の名称は name ないし regionname カラムから取得する
            if "name" in row:
                name = row["name"]
            elif "regionname" in row:
                name = row["regionname"]
            else:
                continue

            # 区域のコードは code ないし regioncode カラムから取得する
            if "code" in row:
                code = row["code"]
            else:
                code = row["regioncode"]

            # 既に追加済みならスキップ
            if code in closed:
                continue
            closed.add(code)

            geometry = cast(BaseGeometry, row["geometry"])
            if geometry is None:
                continue

            # GeoJSON の Feature を返す
            yield {
                "type": "Feature",
                "properties": {
                    "name": name,
                    "code": code,
                },
                "geometry": mapping(geometry),
            }


f = sys.stdout
first = True
for feat in iter_features():
    json.dump(feat, f, ensure_ascii=False, sort_keys=True)
    f.write("\n")
    first = False
