#!/usr/bin/env python3

"""シェイプデータをElasticsearchにインデクスします"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from settings import ALIAS_NAME, es
from shapely.geometry import MultiLineString, MultiPolygon, mapping, shape
from shapely.geometry.polygon import orient

_logger = logging.getLogger(__name__)


def iter_features(filename: str):
    with open(filename) as f:
        for line in f:
            feature = json.loads(line)
            yield feature


def iter_actions(feature_iter, index_name: str, kind: str):
    for feature in feature_iter:
        name = feature["properties"]["name"]
        code = feature["properties"]["code"]
        geom = shape(feature["geometry"])

        if code is None:
            continue

        # simplification
        tolerance = 0.0025
        if tolerance > 0:
            geom = simplify(geom, tolerance=0.0025)

        yield {
            "_index": index_name,
            "_id": kind + "-" + code,
            "kind": kind,
            "name": name,
            "code": code,
            "geometry": mapping(geom),
        }


def simplify(g, tolerance=0.0025):
    if g.type == "Polygon":
        return orient(g.simplify(tolerance, preserve_topology=True).buffer(0))
    elif g.type == "MultiPolygon":
        polys = []
        for gg in g.geoms:
            p = orient(gg.simplify(tolerance, preserve_topology=True).buffer(0))
            if p.area > 1e-15:
                polys.append(p)

        return MultiPolygon(polys)
    elif g.type == "LineString":
        return g.simplify(tolerance, preserve_topology=True)
    elif g.type == "MultiLineString":
        polys = []
        for gg in g.geoms:
            polys.append(gg.simplify(tolerance, preserve_topology=True))
        return MultiLineString(polys)
    else:
        raise RuntimeError("unsupported geometry type")


def index_shapes(index_name):
    sources = sorted(Path("output/geojson/").glob("*.json"))

    for filename in sources:
        kind = filename.stem

        if kind in ["maritime"]:
            continue

        try:
            for ok, result in streaming_bulk(
                es,
                iter_actions(iter_features(str(filename)), index_name, kind),
                chunk_size=10,
            ):
                _, result = result.popitem()
                print(result)
                if not ok:
                    exit(1)
        except Exception as e:
            print(e)
            exit()


def process(es: Elasticsearch, alias_name=ALIAS_NAME):
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    index_name = f"{ALIAS_NAME}-{suffix}"
    _logger.info(f"{index_name=}")

    # インデクスを作る
    res = es.indices.create(
        index=index_name,
        settings={
            "number_of_shards": 6,
            "number_of_replicas": 1,
        },
        mappings={
            "dynamic": "strict",
            "_source": {"excludes": ["geometry"]},
            "properties": {
                "name": {"type": "keyword"},
                "code": {"type": "keyword"},
                "kind": {"type": "keyword"},
                "geometry": {"type": "geo_shape"},
            },
        },
    )
    _logger.info(f"{res=}")

    # シェイプデータをインデクスする
    index_shapes(index_name)

    # エイリアスを入れかえる
    if es.indices.exists_alias(name=alias_name):
        old_indices = list(es.indices.get_alias(name=alias_name).keys())
    else:
        old_indices = []

    if len(old_indices) == 0:
        es.indices.put_alias(index=index_name, name=alias_name)
    elif len(old_indices) == 1:
        old_index = old_indices[0]
        es.indices.update_aliases(
            actions=[
                {"remove": {"index": old_index, "alias": alias_name}},
                {"add": {"index": index_name, "alias": alias_name}},
            ]
        )
    else:
        raise RuntimeError("two or more old indices found")


if __name__ == "__main__":
    _logger.addHandler(logging.StreamHandler(sys.stderr))
    _logger.setLevel(logging.INFO)

    process(es)
