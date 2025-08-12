# mm2superbai


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

[COCOからインポートする](https://apps.superb-ai.com/browse/d9415dad-1977-457d-a10b-409af2cc4c0e)