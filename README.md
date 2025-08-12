# mm2superbai

[Mech-Mind DLK](https://mech-mind.co.jp/product/mech-dlk/)フォーマットのデータセットを[Superb AI](https://superb-ai.com/ja)にアップロードできるCOCOフォーマットへ変換するスクリプトです

## 環境設定

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python mm2superbai.py --input mm_data --output output

------
usage: mm2superbai.py [-h] [--input INPUT] [--output OUTPUT]

Convert dataset to COCO format from Mech-Mind DLK format.

options:
  -h, --help           show this help message and exit
  --input, -i INPUT    Input directory for Mech-Mind DLK format deataset.
  --output, -o OUTPUT  Output directory for COCO format dataset.
```

## ビューアソフトの準備

ビューアソフトのダウンロード

```bash
curl -O https://raw.githubusercontent.com/trsvchn/coco-viewer/main/cocoviewer.py
```

デフォルトではバグがあるので修正する

```diff
--- cocoviewer.py
+++ cocoviewer.py
-                tw, th = draw.textsize(text, font)
+                # tw, th = draw.textsize(text, font)
+                tw = draw.textlength(text, font)
+                th = label_size
```

下記のコマンドで結果を確認できる

```bash
python cocoviewer.py -i output/data -a output/annotations/instances_train2017.json
```

## 参考

- [Mech-Mind DLK](https://mech-mind.co.jp/product/mech-dlk/)
- [Superb AI](https://superb-ai.com/ja)
- [COCOからインポートする](https://apps.superb-ai.com/browse/d9415dad-1977-457d-a10b-409af2cc4c0e)