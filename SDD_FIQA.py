import os
import pandas as pd
import torch
import torchvision.transforms as T
from PIL import Image
from misc.extract_bbox import *
from model import model
import numpy as np
import cv2

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model_path = 'model/SDD_FIQA_checkpoints_r50.pth'


def process_fiqa_image(img):  # read image & data pre-process

    data = torch.randn(1, 3, 112, 112)

    transform = T.Compose([
        T.Resize((112, 112)),
        T.ToTensor(),
        T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)
    data[0, :, :, :] = transform(im_pil)

    return data


def network(model_path, device):
    net = model.R50([112, 112], use_type="Qua").to(device)
    net_dict = net.state_dict()
    data_dict = {
        key.replace('module.', ''): value for key, value in torch.load(model_path, map_location=device).items()}
    net_dict.update(data_dict)
    net.load_state_dict(net_dict)
    net.eval()

    return net


def FIQA(df, img_list): # input_img
    net = network(model_path, device)
    fiqa_score = []
    bbox_list = []
    qualified_img = []
    filename = []
    for idx in range(len(df)):
        bboxes = get_target_bbox(img_list[idx], df["bboxes"][idx], p=0.15)
        score = []
        for bbox in bboxes:
            if bbox.shape[0] > 0 and bbox.shape[1] > 0:
                img = process_fiqa_image(bbox).to(device)
                pred_score = net(img).data.cpu().numpy().squeeze()
                score.append(pred_score)

            if max(score) > 40:
                qualified_img.append(img_list[idx])
                filename.append(df['filename'][idx])
                bbox_list.append(df["bboxes"][idx])
                fiqa_score.append(score)


    new_df = pd.DataFrame({'filename': filename, 'bboxes': bbox_list, "fiqa_score": fiqa_score})
    return new_df, np.array(qualified_img)
