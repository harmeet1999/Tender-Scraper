import cv2
import os
import typing
import numpy as np

from mltu.inferenceModel import OnnxInferenceModel
from mltu.utils.text_utils import ctc_decoder, get_cer

class ImageToWordModel(OnnxInferenceModel):
    def __init__(self, char_list: typing.Union[str, list], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char_list = char_list

    def predict(self, image: np.ndarray):
        image = cv2.resize(image, self.input_shape[:2][::-1])
        cv2.imwrite("sample/_result.png", image)

        image_pred = np.expand_dims(image, axis=0).astype(np.float32)
        
        cv2.imwrite("sample/result.png", image_pred)

        preds = self.model.run(None, {self.input_name: image_pred})[0]

        text = ctc_decoder(preds, self.char_list)[0]

        return text

if __name__ == "__main__":
    import pandas as pd
    from tqdm import tqdm
    from mltu.configs import BaseModelConfigs

    configs = BaseModelConfigs.load("docs/configs.yaml")

    model = ImageToWordModel(model_path=configs.model_path, char_list=configs.vocab)
    
    image_file_name = os.path.join("docs", "Kaptcha.jpg")
    image = cv2.imread(image_file_name)

    prediction_text = model.predict(image)
    
    print(prediction_text)

    # df = pd.read_csv("Models/02_captcha_to_text/202212211205/val.csv").values.tolist()

    # accum_cer = []
    # for image_path, label in tqdm(df):
    #     image = cv2.imread(image_path)

    #     prediction_text = model.predict(image)

    #     cer = get_cer(prediction_text, label)
    #     print(f"Image: {image_path}, Label: {label}, Prediction: {prediction_text}, CER: {cer}")

    #     accum_cer.append(cer)

    # print(f"Average CER: {np.average(accum_cer)}")