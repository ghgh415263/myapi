from fastapi import APIRouter, File, UploadFile

from database import SessionLocal
from datetime import datetime

from models import Result

import json
import os
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from io import BytesIO
from pydantic import BaseModel

router = APIRouter(
    prefix="",
)

class JsonRequest(BaseModel):
    storeFilename: str

@router.post("/analyze")
def analyze(jsonRequest: JsonRequest):

    db = SessionLocal()
    findedResult = db.query(Result).filter(Result.store_filename==jsonRequest.storeFilename).all()
    if findedResult != None:
        print("db에서 조회")
        return json.loads(findedResult[0].result)

    class_list = ["Adialer.C", "Agent.FYI", "Allaple.A", "Allaple.L", "Alueron.gen!J",
                  "Autorun.K", "C2LOP.P", "C2LOP.gen!g", "Dialplatform.B", "Dontovo.A",
                  "Fakerean", "Instantaccess", "Lolyda.AA1", "Lolyda.AA2", "Lolyda.AA3",
                  "Lolyda.AT", "Malex.gen!J", "Obfuscator.AD", "Rbot!gen", "Skintrim.N",
                  "Swizzor.gen!E", "Swizzor.gen!l", "VB.AT", "Wintrim.BX", "Yuner.A"]

    model_path = 'models/malwareClassification_cnn.ckpt'
    model = load_model(model_path)

    with open("C:/workspace/malware/malwarefile/" + jsonRequest.storeFilename, 'rb') as file:
        file_size = os.path.getsize("C:/workspace/malware/malwarefile/" + jsonRequest.storeFilename)

        numpy_array = preprocessing(file)

        predictions = model.predict(numpy_array)
        predictions = predictions[0].tolist()

        result = {}
        outputList = []
        for i in range(len(predictions)):
            predictions[i] = format(predictions[i], '.5f')
            output = {"className": class_list[i], "probability": predictions[i]}
            outputList.append(output)
        result["apiModelName"] = "vgg16_model_v1"
        result["outputList"] = outputList

        resultForSave = Result(store_filename=jsonRequest.storeFilename, result=json.dumps(result), create_date=datetime.now())
        db.add(resultForSave)
        db.commit()
        print("새로운 파일에 대한 처리")

    return result


def preprocessing(file):
    K_BYTE = 1024

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    width = 0
    if file_size < (K_BYTE * 10):
        width = 32
    elif file_size < (K_BYTE * 30):
        width = 64
    elif file_size < (K_BYTE * 60):
        width = 128
    elif file_size < (K_BYTE * 100):
        width = 256
    elif file_size < (K_BYTE * 200):
        width = 384
    elif file_size < (K_BYTE * 500):
        width = 512
    elif file_size < (K_BYTE * 1000):
        width = 768
    else:
        width = 1024

    remain_pixel = file_size % width;
    raw_array = np.fromfile(file, dtype="uint8", count=(file_size - remain_pixel))
    image_array = raw_array.reshape(-1, width)

    im = Image.fromarray(image_array).resize((224, 224), Image.BILINEAR).convert("RGB")
    numpy_array = np.reshape(im, [1, 224, 224, 3])
    return numpy_array