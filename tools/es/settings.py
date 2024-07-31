import os

from elasticsearch import Elasticsearch

_ELASTICSEARCH_URL = os.environ["ELASTICSERACH_URL"]
ALIAS_NAME = "jma-gis-polygons"

es = Elasticsearch(_ELASTICSEARCH_URL, request_timeout=30)
