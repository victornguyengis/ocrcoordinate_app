import streamlit as st
import numpy as np
import cv2
import easyocr
from PIL import Image
import PIL
import os
import pandas as pd
import tempfile
from pathlib import Path


def Save_Uploaded_File (File, save_folder):
    save_path = Path(save_folder,File.name)
    with open(save_path, mode='wb') as w:
            w.write(File.getbuffer())
    return
## set up Layout
st.set_page_config(
     page_title="IMAGE-TABLE TO TXT",
     layout="wide",
     initial_sidebar_state="expanded",)
prmsContainer = st.experimental_get_query_params()
Main = st.container()

col1, col2 = st.columns((5,5))

Main.header("CONVERT ẢNH TỌA ĐỘ GÓC RANH SANG TXT")
uploaded_file = Main.file_uploader("Chọn ảnh: ")
if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as tmp:
        Save_Uploaded_File(uploaded_file, tmp)
        image = cv2.imread(f"{tmp}/{uploaded_file.name}")
        
        reader = easyocr.Reader(['en'], gpu = False)
        sharpen_kernel = np.array([ [0, -1, 0],
                                    [-1, 5, -1],
                                    [0, -1, 0]])
        sharpen = cv2.filter2D(image, -1, sharpen_kernel)

        # Đọc các đoạn text, lọc ra giá trị là tọa độ.cls
        out = reader.readtext(sharpen,allowlist ='0123456789.',min_size = 1,contrast_ths=0.15,adjust_contrast=0.5)
        T = []
        for t in out:
            bbox, text, score = t
            text = text.replace(" ", ".")
            text = text.replace(",", ".")
            try:
                t = float(text)
                if len(text)> 7 and len(text) < 11:
                    T.append(text)
            except: ''
        # Kiểm tra tọa độ có đạt chuẩn hay không (trong phạm vi HCM). Thông báo chất lượng ảnh không tốt.
        Test = ['1']
        n = 0
        while n < len(T) :
            if len(T[n]) == 10 and len(T[n+1]) == 9:
                if n >= 2 and abs(float(T[n])-float(T[n-2]))<=200 and abs(float(T[n+1])-float(T[n-1]))<=200:
                    Test.append('1')
                n = n +2
            else: break
        # Save file TXT
        if T[0] == T[len(T)-2] and T[1] == T[len(T)-1]:
            if len(T)/len(Test)==2:
                Text = ""
                n = 0
                while n < len(T):
                    Text = Text + str(T[n] + " " + T[n+1]) + '\n'
                    n = n = n + 2
                st.write(Text)
                st.download_button('TẢI FILE TXT', Text, file_name = "Toado.txt")
            else: st.warning('Chất lượng ảnh quá kém, đề nghị chụp lại hoặc điền tay')
        else: st.warning('Ảnh chứa bảng tọa độ của 2 mảnh thửa đất khác nhau, đề nghị nhập tay')

        col1.header("Ảnh đầu vào")
        col1.image(image)  
        col2.header("Ảnh xử lý sơ bộ")
        col2.image(sharpen)