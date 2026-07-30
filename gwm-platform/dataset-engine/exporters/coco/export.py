"""
exporters/coco/export.py — converts internal dataset labels to COCO format.
"""

import os
import json
from exporters.internal import read_labels

def export_coco(output_dir: str, frame_count: int) -> str:
    """
    Generate COCO-format export from internal dataset format.
    """
    coco_dir = os.path.join(output_dir, "coco")
    os.makedirs(coco_dir, exist_ok=True)

    categories = [
        {"id": 1, "name": "car", "supercategory": "vehicle"},
        {"id": 2, "name": "pedestrian", "supercategory": "person"},
        {"id": 3, "name": "cyclist", "supercategory": "vehicle"},
        {"id": 4, "name": "truck", "supercategory": "vehicle"},
        {"id": 5, "name": "bus", "supercategory": "vehicle"}
    ]

    cat_map = {"car": 1, "vehicle": 1, "pedestrian": 2, "person": 2, "cyclist": 3, "truck": 4, "bus": 5}

    images = []
    annotations = []
    ann_id = 1

    for frame_id in range(frame_count):
        stem = f"{frame_id:06d}"
        image_info = {
            "id": frame_id,
            "width": 1280,
            "height": 720,
            "file_name": f"{stem}.png"
        }
        images.append(image_info)

        actors = read_labels(frame_id, output_dir)
        for actor in actors:
            cls_name = actor.get("class", "car").lower()
            cat_id = cat_map.get(cls_name, 1)

            # bbox in [x, y, w, h]
            bbox_2d = actor.get("bbox_2d", [0, 0, 50, 50])
            x, y, w, h = bbox_2d[0], bbox_2d[1], bbox_2d[2] - bbox_2d[0], bbox_2d[3] - bbox_2d[1]

            ann = {
                "id": ann_id,
                "image_id": frame_id,
                "category_id": cat_id,
                "bbox": [round(x, 2), round(y, 2), round(w, 2), round(h, 2)],
                "area": round(w * h, 2),
                "iscrowd": 0
            }
            annotations.append(ann)
            ann_id += 1

    coco_data = {
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    out_json = os.path.join(coco_dir, "instances_default.json")
    with open(out_json, "w") as f:
        json.dump(coco_data, f, indent=2)

    print(f"[COCO Exporter] Export complete -> {out_json} ({frame_count} frames, {len(annotations)} annotations)")
    return coco_dir
