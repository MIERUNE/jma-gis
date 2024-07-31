import json
import logging
import sys

import geopandas as gpd

_logger = logging.getLogger(__name__)


def process(filenames: list[str]):
    closed = set()
    result = []
    for filename in filenames:
        _logger.info(f"processing {filename}")
        df = gpd.read_file(filename, encoding="utf-8")

        for _, row in df.iterrows():
            if row.geometry is None:
                continue

            # 区域の名称は name ないしは regionname カラムから取得する
            if "name" in row:
                name = row["name"]
            elif "regionname" in row:
                name = row["regionname"]
            else:
                name = ""

            # 区域のコードは code ないしは regioncode カラムから取得する
            if "code" in row:
                code = row["code"]
            elif "regioncode" in row:
                code = row["regioncode"]
            else:
                continue

            if code is None:
                continue

            if code in closed:
                continue
            closed.add(code)

            area = row.geometry.area
            centroid = row.geometry.centroid.coords[0]
            bbox = row.geometry.bounds
            props = {
                "name": name,
                "code": code,
                "area": area,
                "centroid": centroid,
                "bbox": bbox,
            }
            if "津波予報区" in filename:
                props["length"] = row.geometry.length
            result.append(props)

    f = sys.stdout
    first = True
    f.write("[\n")
    for obj in sorted(result, key=lambda x: x["code"]):
        if not first:
            f.write(",\n")
        json.dump(obj, f, sort_keys=True, ensure_ascii=False)
        first = False
    f.write("\n]\n")


if __name__ == "__main__":
    _logger.addHandler(logging.StreamHandler())
    _logger.setLevel(logging.INFO)
    process(sys.argv[1:])
