import logging
import base64
import json

import requests
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import get_image_local_path, get_single_tag_keys

logger = logging.getLogger(__name__)


class Yolov8(LabelStudioMLBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        (
            self.from_name,
            self.to_name,
            self.value,
            self.labels_in_config,
        ) = get_single_tag_keys(self.parsed_label_config, "RectangleLabels", "Image")

    def predict(self, tasks, **kwargs):
        image_path = tasks[0]["data"][self.value]

        url = "http://bentoml:3000/annotation"
        payload = {}
        files = [
            ("", (image_path.split("/")[-1], open(image_path, "rb"), "image/jpeg"))
        ]
        headers = {"accept": "application/json"}
        response = requests.request(
            "POST", url, headers=headers, data=payload, files=files
        )
        json_response = json.loads(response.text)
        img_height = json_response["height"]
        img_width = json_response["width"]

        results = []
        all_scores = []
        for r in json_response["results"]:
            bbox = list(r["box"].values())
            if not bbox:
                continue
            score = float(r["confidence"])
            if score < 0.5:
                continue
            xmin, ymin, xmax, ymax = bbox
            results.append(
                {
                    "from_name": self.from_name,
                    "to_name": self.to_name,
                    "type": "rectanglelabels",
                    "value": {
                        "rectanglelabels": [r["name"]],
                        "x": xmin / img_width * 100,
                        "y": ymin / img_height * 100,
                        "width": (xmax - xmin) / img_width * 100,
                        "height": (ymax - ymin) / img_height * 100,
                    },
                    "score": score,
                }
            )
            all_scores.append(score)
        avg_score = sum(all_scores) / max(len(all_scores), 1)
        return [{"result": results, "score": avg_score}]
