import traceback
import logging
import coloredlogs
import os
import json
from datetime import datetime
import shutil # ファイルコピーのために追加
import argparse
from typing import List, Dict, Tuple, Any
import cv2


# ログの設定
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger, fmt='%(asctime)s - %(levelname)s - %(message)s')


def read_mm_roi_config(roi_config_path: str) -> Dict[str, Any]:
    """Mech-Mind DLK形式のROI設定を読み込む

    Mech-Mind DLK形式のROI設定ファイルからROIの比率を読み込みます。
    比率は辞書形式で返されます。

    Parameters
    ----------
    roi_config_path: str
        Mech-Mind DLK形式のROI設定ファイルのパス

    Returns
    -------
    Dict[str, Any]
        ROI設定の辞書。キーは "startXRatio", "startYRatio", "widthRatio", "heightRatio" です。

    Raises
    ------
    ValueError
        ROI設定ファイルに "startXRatio", "startYRatio", "widthRatio", "heightRatio" が見つからなかった場合は、
        その旨のエラーメッセージを出力します。
    """
    with open(roi_config_path, 'r', encoding='utf-8') as f:
        roi_config = json.load(f)
    
    # 必要なキーが存在するか確認
    required_keys = ["startXRatio", "startYRatio", "widthRatio", "heightRatio"]
    for key in required_keys:
        if key not in roi_config[0]:
            raise ValueError(f"ROI設定ファイルに {key} が見つかりません。")

    return roi_config[0]

def read_mm_images(image_directory: str) -> List[str]:
    """Mech-Mind DLK形式の画像ディレクトリから画像ファイルを読み込む

    Mech-Mind DLK形式の画像ディレクトリから画像ファイルのリストを取得します。
    画像ファイルはJPEGまたはPNG形式である必要があります。

    Parameters
    ----------
    image_directory: str
        Mech-Mind DLK形式の画像ディレクトリのパス

    Returns
    -------
    List[str]
        画像ファイルのリスト
    
    Raises
    ------
    FileNotFoundError
        指定された画像ディレクトリに画像ファイルが存在しない場合は、
        その旨のエラーメッセージを出力し、
        そのディレクトリが存在しない場合は、FileNotFoundErrorをスローします。
    """
    # 画像ディレクトリの存在を確認
    image_files = [f for f in os.listdir(image_directory) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        raise FileNotFoundError(f"画像ファイルが見つかりません: {image_directory}")
    
    # 画像ファイルのフルパスを取得
    image_files_path = [os.path.join(image_directory, filename) for filename in image_files]
    
    return image_files_path

def read_mm_annotations(annotation_directory: str) -> List[Dict[str, Any]]:
    """Mech-Mind DLK形式のアノテーションディレクトリからアノテーションデータを読み込む

    Mech-Mind DLK形式のアノテーションディレクトリからアノテーションファイルを読み込みます。
    アノテーションファイルはJSON形式である必要があります。

    Parameters
    ----------
    annotation_directory: str
        Mech-Mind DLK形式のアノテーションディレクトリのパス

    Returns
    -------
    List[Dict[str, Any]]
        読み込んだアノテーションデータのリスト

    Raises
    ------
    FileNotFoundError
        指定されたアノテーションディレクトリにアノテーションファイルが存在しない場合、
        またはアノテーションファイルがJSON形式でない場合は、
        その旨のエラーメッセージを出力し、
        そのディレクトリが存在しない場合は、FileNotFoundErrorをスローします。
    """
    annotation_files = [f for f in os.listdir(annotation_directory) if f.lower().endswith('.json')]
    if not annotation_files:
        raise FileNotFoundError(f"アノテーションファイルが見つかりません: {annotation_directory}")
    
    annotations = []
    for filename in annotation_files:
        with open(os.path.join(annotation_directory, filename), 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            json_data['annotation_filename'] = os.path.join(annotation_directory, filename)
            annotations.append(json_data)
    
    return annotations

def read_mm_dataset(input_dir: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Mech-Mind DLK形式のデータセットを読み込む

    Mech-Mind DLK形式のデータセットディレクトリから画像、ROI設定、アノテーションを読み込みます。
    読み込んだデータを配列にして出力する
    
    Parameters
    ----------
    input_dir: str
        Mech-Mind DLK形式のデータセットディレクトリのパス

    Returns
    -------
    Tuple[Dict[str, Any], List[Dict[str, Any]]]
        ROI設定とアノテーションデータのリストを含むタプル
    """
    # Mech-Mindデータセットパスの設定
    roi_config_path = os.path.join(input_dir, 'modules', '0', 'model', 'color_roi.json')
    image_directory = os.path.join(input_dir, 'modules', '0', 'dataset')
    annotation_directory = os.path.join(input_dir, 'modules', '0', 'model', 'data')

    # ROI設定を読み込む
    roi_config = read_mm_roi_config(roi_config_path)

    # 画像ファイルのリストを取得
    image_files = read_mm_images(image_directory)
    
    # アノテーションデータリストを取得する
    annotations = read_mm_annotations(annotation_directory)

    # 画像ファイルとアノテーションデータが一致するか確認
    dataset = []
    for image_file in image_files:
        for annotation in annotations:
            image_filebase = os.path.basename(image_file)
            image_filebase = os.path.splitext(image_filebase)[0]
            annotations_filebase = os.path.basename(annotation['annotation_filename'])
            annotations_filebase = os.path.splitext(annotations_filebase)[0]            
            if image_filebase == annotations_filebase:
                annotation['image_filename'] = image_file  # アノテーションに画像ファイル名を追加                
                dataset.append(annotation)
                break

    return roi_config, dataset

def check_mm_data_dir(input_dir: str):
    """Mech-Mind DLK形式のデータセットディレクトリの存在確認

    Mech-Mind DLK形式のデータセットディレクトリが存在するか確認します。
    存在しない場合はエラーを出力します。

    Parameters
    ----------
    input_dir: str
        Mech-Mind DLK形式のデータセットディレクトリのパス
    """
    # 入力ディレクトリの存在を確認
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"入力ディレクトリが見つかりません: {input_dir}")
    
    # 画像フォルダの存在を確認
    if not os.path.exists(os.path.join(input_dir, 'modules', '0', 'dataset')):
        raise FileNotFoundError(f"画像ディレクトリが見つかりません: {os.path.join(input_dir, 'modules', '0', 'dataset')}")
    # ROI設定ファイルの存在を確認
    if not os.path.exists(os.path.join(input_dir, 'modules', '0', 'model', 'color_roi.json')):
        raise FileNotFoundError(f"ROI設定ファイルが見つかりません: {os.path.join(input_dir, 'modules', '0', 'model', 'color_roi.json')}")
    # アノテーションディレクトリの存在
    if not os.path.exists(os.path.join(input_dir, 'modules', '0', 'model', 'data')):
        raise FileNotFoundError(f"アノテーションディレクトリが見つかりません: {os.path.join(input_dir, 'modules', '0', 'model', 'data')}")
    
    logger.info(f"Mech-Mind DLK形式のデータセットディレクトリ {input_dir} が確認されました。")

def create_output_directory(output_dir: str):
    """出力ディレクトリの作成と初期化

    出力ディレクトリを作成します。既存のディレクトリがあれば削除して新たに作成します。

    Parameters
    ----------
    output_dir: str
        出力ディレクトリのパス
    """
    # 出力ディレクトリが既に存在する場合は削除
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    # 新しい出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    # 必要なサブディレクトリを作成
    os.makedirs(os.path.join(output_dir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'annotations'), exist_ok=True)

    logger.info(f"出力ディレクトリ {output_dir} を作成しました。")

def create_superbai_dataset(roi_config: Dict[str, Any], dataset: List[Dict[str, Any]], output_dir: str):
    """Mech-Mind DLK形式のデータセットをSuperbAI形式に変換

    Mech-Mind DLK形式のROI設定とアノテーションデータをSuperbAI形式に変換し、
    指定された出力ディレクトリに保存します。

    Parameters
    ----------
    roi_config: Dict[str, Any]
        ROI設定の辞書
    dataset: List[Dict[str, Any]]
        アノテーションデータのリスト
    output_dir: str
        出力ディレクトリのパス
    """
    # COCOフォーマットのデータセットを作成
    image_directory = os.path.join(output_dir, 'data')
    annotation_directory = os.path.join(output_dir, 'annotations')

    # ROI設定の取得
    roi_x_ratio = roi_config.get("startXRatio")
    roi_y_ratio = roi_config.get("startYRatio")
    roi_width_ratio = roi_config.get("widthRatio")
    roi_height_ratio = roi_config.get("heightRatio")

    # COOCOアノテーションデータの初期化
    coco_format = {
        "info": {
            "year": datetime.now().year,
            "version": "1.0",
            "description": "Converted dataset to COCO format from Mech-Mind DLK format.",
            "contributor": "SuperbAI",
            "url": "",
            "date_created": datetime.now().isoformat()
        },
        "licenses": [
            {
                "id": 1,
                "name": "Default License",
                "url": ""
            }
        ],
        "images": [],
        "annotations": [],
        "categories": []
    }
    coco_category_map = []

    for idx, data in enumerate(dataset):
        # 画像情報の取得
        image_filename = data["image_filename"]
        image = cv2.imread(image_filename)
        if image is None:
            logger.warning(f"画像ファイル {image_filename} が読み込めません。スキップします。")
            continue
        height, width = image.shape[:2]

        # ROIの計算
        roi_x = int(width * roi_x_ratio)
        roi_y = int(height * roi_y_ratio)
        roi_width = int(width * roi_width_ratio)
        roi_height = int(height * roi_height_ratio)

        # COCO images セクションの追加
        coco_image = {
            "id": idx + 1,
            "file_name": os.path.basename(image_filename),
            "width": width,
            "height": height,
            "license": 1,
            "date_captured": ""
        }
        coco_format["images"].append(coco_image)

        # COCO annotations セクションの追加
        for obj in data.get("objects", []):
            label = obj.get("label")
            bndbox = obj.get("bndbox")
            contours = obj.get("contours")

            if not label or not bndbox or not contours:
                logger.warning(f"オブジェクトにラベルまたはバウンディングボックスがありません: {data}")
                continue

            # カテゴリIDの追加
            if label not in coco_category_map:
                coco_category_map.append(label)
                category_id = coco_category_map.index(label) + 1

                coco_format["categories"].append({
                    "id": category_id,
                    "name": label,
                    "supercategory": "object"  # デフォルトでobjectとする
                })
            
            # バウンディングボックス座標の追加
            bndbox_x, bndbox_y, bndbox_width, bndbox_height = bndbox
            coco_bbox = [
                bndbox_x + roi_x,
                bndbox_y + roi_y,
                bndbox_width,
                bndbox_height
            ]

            # セグメンテーション座標の追加
            coco_segmentation = []
            for contour in contours:
                flat_contour = []
                for point in contour:
                    if len(point[0]) == 2:
                        seg_x = point[0][0] + coco_bbox[0]
                        seg_y = point[0][1] + coco_bbox[1]
                        flat_contour.extend([seg_x, seg_y])
                if flat_contour:
                    coco_segmentation.append(flat_contour)

            # COCO annotations セクションの追加
            coco_annotation = {
                "id": len(coco_format["annotations"]) + 1,
                "image_id": coco_image["id"],
                "category_id": coco_category_map.index(label) + 1,
                "bbox": [round(coord, 2) for coord in coco_bbox],
                "area": round(bndbox_width * bndbox_height, 2),
                "iscrowd": 0,
                "segmentation": coco_segmentation if coco_segmentation else []
            }
            coco_format["annotations"].append(coco_annotation)

        # 画像ファイルを出力ディレクトリにコピー
        destination_image_filename = os.path.join(image_directory, os.path.basename(image_filename))
        shutil.copyfile(image_filename, destination_image_filename)

    # アノテーションデータを書きだし
    with open(os.path.join(annotation_directory, "instances_train2017.json"), 'w', encoding='utf-8') as f:
        json.dump(coco_format, f, indent=4, ensure_ascii=False)

    # ログ出力
    logger.info(f"COCOフォーマットのデータセットを {output_dir} に保存しました。")
    logger.info(f"カテゴリ情報: coco_category_map")
    logger.info(f"画像ファイル数: {len(coco_format['images'])}")
    logger.info(f"アノテーション数: {len(coco_format['annotations'])}")

if __name__ == '__main__':
    try:
        # 引数管理
        parser = argparse.ArgumentParser(description='Convert dataset to COCO format from Mech-Mind DLK format.')
        parser.add_argument('--input', '-i', type=str, default='mm_data', help='Input directory for Mech-Mind DLK format deataset.')
        parser.add_argument('--output', '-o', type=str, default='output', help='Output directory for COCO format dataset.')
        args = parser.parse_args()

        # 入出力ディレクトリのパスを設定
        input_dir = args.input
        output_dir = args.output

        # 入力ディレクトリの存在確認
        check_mm_data_dir(input_dir)

        # 出力ディレクトリの再作成
        create_output_directory(output_dir)

        # Mech-Mind DLK形式のデータセットを読み込む
        roi_config, dataset = read_mm_dataset(input_dir)

        # COCOフォーマットのデータセットを作成
        create_superbai_dataset(roi_config, dataset, output_dir)
        logger.info(f"COCOフォーマットデータセットを {output_dir} に保存しました。")

        # COCOデータセットをZIP圧縮
        zip_filename = os.path.abspath(output_dir)
        logger.info(f"COCOフォーマットのデータセットを {zip_filename} に圧縮開始します。")
        shutil.make_archive(zip_filename, 'zip', base_dir=os.path.basename(zip_filename))
        logger.info(f"COCOフォーマットのデータセットを {zip_filename} に圧縮終了しました。")
        

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        traceback.print_exc()
