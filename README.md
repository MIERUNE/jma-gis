# jma-gis

(Work in progress)

気象庁の[予報区等GISデータ](https://www.data.jma.go.jp/developer/gis.html)をもとに、ベクタータイルなどを生成します。

- Demo: https://jma-assets.mierune.dev/tiles/index.html
- 気象関係: https://jma-assets.mierune.dev/tiles/mete/{z}/{x}/{y}.pbf
- 地震・津波関係: https://jma-assets.mierune.dev/tiles/seis/{z}/{x}/{y}.pbf

具体的には以下を行います:

- 「予報区等GISデータ」のダウンロード
- GeoJSON への変換 (カラム名を揃えるなどのわずかな整理も行う)
- ベクタータイル (MVT) の生成
- 各区域の属性値（bbox等）の抽出 (仮)
- (実験的: Elasticsearch へのシェイプデータの挿入)

TODO:

- ベクタタイルセットを予報区区分ごとに分けて用意する (今は全部入りの1つのタイルセット)
- PMTiles の生成？
- Cloudflare R2 へのアップロード
- Amazon S3 へのアップロード
- ベクタタイルの表示デモ
- etc.

## Development

処理の流れは Makefile を参照。

参考に、[`./visualized/`](./visualized/) に各シェイプファイルを可視化した画像を配置しています。

### 必要なもの:

- Python + Rye
- [tippecanoe](https://github.com/felt/tippecanoe)
<!--
- [go-pmtiles](https://github.com/protomaps/go-pmtiles)
    - `go install github.com/protomaps/go-pmtiles@latest`
-->


## ベクタータイルについて

### 仕様

各予報区区分が、それぞれ以下のレイヤ名で格納されています。

気象関係: `https://jma-assets.mierune.dev/tiles/mete/{z}/{x}/{y}.pbf`

| 元のShapefile | レイヤ名 |
| -- | -- |
| 全国・地方予報区等.shp | chihou |
| 府県予報区等.shp | fuken |
| 一次細分区域等.shp | ichiji |
| 市町村等をまとめた地域等.shp | matome |
| 市町村等（＊＊＊）.shp | city |
| 地方海上予報区.shp | maritime |


地震・津波関係: `https://jma-assets.mierune.dev/tiles/seis/{z}/{x}/{y}.pbf`

| 元のShapefile | レイヤ名 |
| -- | -- |
| 緊急地震速報／地方予報区.shp | eew_chihou |
| 緊急地震速報／府県予報区.shp | eew_fuken |
| 地震情報／細分区域.shp | seis_saibun |
| 地震情報／都道府県等.shp | seis_prefecture |
| 津波予報区.shp | tsunami |

各 Feature は `name` (区域名) と `code` (区域コード) の属性を持ちます。

"市町村等（＊＊＊）" については、全種類を1つにまとめています。

各シェイプファイルの領域区分の様子は [`./visualized/`](./visualized/) ディレクトリなどを参考にしてください。

### タイルの生成

```bash
make xyztiles -j 8
```

## ジオメトリの属性値の抽出について

シェイプファイルから、各ジオメトリの重心や面積などの情報を抽出します。

```bash
make shape_properties
```

`output/shape_propertes/*.json` に、JSONファイルとして出力されます

以下の情報を抽出します。

- 名称 (`name`) とコード (`code`)
- 面積 (`area`)
- 重心 (`centroid`)
- バウンディングボックス (`bbox`)
- 長さ (length) - 津波予報区のみ

注意: 重心などの値はあくまでも WGS84 空間上で求めた値です。


<!--
## Elasticsearch インデックスについて

Elasticsearch のインデクスにシェイプデータをインデクスすることができます。インデクスに際して一定のベクトル単純化を行います。

下記のコマンドでインデクスしなおすことができます（エイリアスの張り替えまで自動で行われます）。

```bash
make update_es_index
```

インデクスの内容は以下の通りです:

```python
    "properties": {
        "kind": {"type": "keyword"},  # 種類 (e.g. 一次細分区域等)
        "name": {"type": "keyword"},  # 名前 (e.g. 秩父地方)
        "code": {"type": "keyword"},  # コード
        "geometry": {"type": "geo_shape"},  # ジオメトリ
    }
```
-->

## Authors

- MIERUNE Inc.
- Taku Fukada (original author)

