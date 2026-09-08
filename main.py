import os
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
from paddleocr import PaddleOCR

import streamlit as st
import numpy as np
import cv2
import geopandas as gpd
from PIL import Image
import PIL
import os
import pandas as pd
import tempfile
from pathlib import Path
import re
from shapely.geometry import Polygon
import ezdxf



def Save_Uploaded_File (File, save_folder):
    save_path = Path(save_folder,File.name)
    with open(save_path, mode='wb') as w:
            w.write(File.getbuffer())
    return

## set up Layout
st.set_page_config(
     page_title="IMAGE-TABLE TO OTHERS",
     layout="wide",
     initial_sidebar_state="expanded",)

Main = st.container()

Main.header("CONVERT ẢNH TỌA ĐỘ GÓC RANH SANG CÁC ĐỊNH DẠNG KHÁC")

if "converted" not in st.session_state:
    st.session_state.converted = False

uploaded_files = st.file_uploader(
    "Upload ảnh",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)
# Sắp xếp theo số ở cuối tên file
if len(uploaded_files)>1:
    uploaded_files = sorted(
        uploaded_files,
        key=lambda x: int(re.search(r'(\d+)(?=\.[^.]+$)', x.name).group(1))
    )

if uploaded_files:
    # Chỉ hiển thị nút, chưa OCR

    if st.button("CONVERT"):
        st.session_state.converted = True

    if st.session_state.converted:
        reader = PaddleOCR(
            lang='en',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )
        out = []
        with tempfile.TemporaryDirectory() as tmp:

            for uploaded_file in uploaded_files:
                Save_Uploaded_File(uploaded_file, tmp)
                image = cv2.imread(f"{tmp}/{uploaded_file.name}")
                sharpen_kernel = np.array([ [0, -1, 0],
                                            [-1, 5, -1],
                                            [0, -1, 0]])
                sharpen = cv2.filter2D(image, -1, sharpen_kernel)

                # Đọc các đoạn text, lọc ra giá trị là tọa độ.cls
                result = reader.predict(sharpen)

                for res in result:
                    texts = res['rec_texts']
                    scores = res['rec_scores']

                    for text, score in zip(texts, scores):
                        # Chỉ giữ số và dấu .
                        if all(c in '0123456789.' for c in text):
                            out.append((text, score))
        
        T = []
        for text, score in out:
            text = text.replace(" ", ".")
            text = text.replace(",", ".")
            try:
                value = float(text)
                if len(text)> 7 and len(text) < 11:
                    T.append(text)
            except ValueError:
                pass

        # Save file TXT
        if T[0] == T[len(T)-2] and T[1] == T[len(T)-1]:
            T = T
        else:   
            T.append(T[0])
            T.append(T[1])

        # Kiểm tra tọa độ có đạt chuẩn hay không (trong phạm vi HCM). Thông báo chất lượng ảnh không tốt
        def is_number(x):
            try:
                float(x)
                return True
            except:
                return False
        if len(T) % 2 == 0:
            T = [x.strip() for x in T]

            coords = []

            n = 0

            while n < len(T) - 1:

                if is_number(T[n]) and is_number(T[n+1]):

                    y = float(T[n])
                    x = float(T[n+1])

                    # Điều kiện khoảng cách giữa các điểm liên tiếp
                    if len(coords) == 0:
                        coords.append((x, y))
                        n += 2
                        continue

                    last_x, last_y = coords[-1]

                    if abs(x - last_x) <= 1000 and abs(y - last_y) <= 1000:
                        coords.append((x, y))
                        n += 2
                        continue
                n += 1

            st.write(coords)
            st.write("Số cặp tọa độ:",len(coords))
        
            # Tạo polygon
            polygon = Polygon(coords)
            gdf = gpd.GeoDataFrame(
                {"id": [1]},
                geometry=[polygon]
            )

            # Xuất dữ liệu từ GIS sang cad
            doc = ezdxf.new("R2007")
            msp = doc.modelspace()

            # Thêm polygon vào DXF
            msp.add_lwpolyline(
                coords,
                close=True
            )

            # File tạm
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".dxf"
            )

            temp_file.close()

            doc.saveas(temp_file.name)

            # Tải

            with open(temp_file.name, "rb") as f:
                dxf_data = f.read()

            os.remove(temp_file.name)

            st.success("Đã hoàn thành!")

            st.download_button(
                label="TẢI RANH CAD",
                data=dxf_data,
                file_name="Ranh.dxf",
                mime="application/dxf",
                on_click="ignore"
            )

        else: st.warning('Chất lượng ảnh quá kém, đề nghị chụp lại')
