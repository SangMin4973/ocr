import numpy as np
import cv2
from google.cloud import vision
import io
import os
import matplotlib.pyplot as plt
from PIL import ImageFont, ImageDraw, Image
import platform

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'tidal-guild-411918-9971810ce15c.json'
 
client_options = {'api_endpoint': 'eu-vision.googleapis.com'}

# [Google Cloud Vision text_detection]
def gcv_detect_text(path):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient(client_options=client_options)

    # [START vision_python_migration_text_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    return response

# [get Text information from GCV response]
def get_text_info(response):
    symbols_info = []
    words_info = []
    paragraphs_info = []
    blocks_info = []

    full_text = response.full_text_annotation.text
    for page in response.full_text_annotation.pages:
        page_text = ""
        for block in page.blocks:
            
            block_text= ""
            for paragraph in block.paragraphs:
                
                paragraph_text= ""
                for word in paragraph.words:
                    
                    words_symbol= ""
                    for symbol in word.symbols:

                        words_symbol = words_symbol+symbol.text
                        if "detected_break" in dir(symbol.property) :
                            if symbol.property.detected_break.type == 1:
                                words_symbol=words_symbol+" "
                            elif symbol.property.detected_break.type == 3:
                                words_symbol=words_symbol+"\n"
                                
                        symbol_vertices = []
                        for sv in symbol.bounding_box.vertices:
                            symbol_vertices.append([sv.x, sv.y])
                        symbols_info.append([symbol.text, symbol_vertices])

                    paragraph_text=paragraph_text+words_symbol
                    word_vertices = []    
                    for wv in word.bounding_box.vertices:
                        word_vertices.append([wv.x, wv.y])
                    words_info.append([words_symbol, word_vertices])

                block_text=block_text+paragraph_text
                paragraph_vertices = []  
                for pv in paragraph.bounding_box.vertices:
                        paragraph_vertices.append([pv.x, pv.y])
                paragraphs_info.append([paragraph_text, paragraph_vertices])

            page_text=page_text+block_text
            block_vertices = [] 
            for bv in block.bounding_box.vertices:
                        block_vertices.append([bv.x, bv.y])
            blocks_info.append([block_text, block_vertices])

    text_info = {
        'text_content' : full_text,
        'blocks_info' : blocks_info,
        'paragraphs_info' : paragraphs_info, 
        'words_info' : words_info,
        'symbols_info' : symbols_info,
    }

    return text_info

# [Draw Bounding Box]
def draw_bbox(img, infos, line_color= (0,0,0), line_thickness=2) :
    for info in infos :
        img = cv2.polylines(img, [np.array(info[1], np.int32)], True, line_color, thickness=line_thickness)
    return img

# [Save Bounding Box Image]
def save_bbox_img(img_path, text_info, output_path, draw_blocks = True, draw_paragraphs = True, draw_words = True, draw_symbols = False):

    #color 설정
    blocks_line = (255,0,0)
    paragraphs_line = (0,255,0)
    words_line = (0,0,255)
    symbols_line = (0xff,0xff,00)

    blocks_info = text_info["blocks_info"]
    paragraphs_info = text_info["paragraphs_info"]
    words_info = text_info["words_info"]
    symbols_info = text_info["symbols_info"]

    #이미지 open *Option : cv2.IMREAD_COLOR, cv2.IMREAD_GRAYSCALE, cv2.IMREAD_UNCHANGED

    draw_info = ""
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if draw_blocks :
        img = draw_bbox(img, blocks_info, line_color=blocks_line)
        draw_info += "_blocks"
    if draw_paragraphs :
        img = draw_bbox(img, paragraphs_info, line_color=paragraphs_line)
        draw_info += "_paragraphs"
    if draw_words :
        img = draw_bbox(img, words_info, line_color=words_line)
        draw_info += "_words"
    if draw_symbols :    
        img = draw_bbox(img, symbols_info, line_color=symbols_line, line_thickness=1)
        draw_info += "_symbols"

    #저장
    if (output_path[-1] != "/"):
        output_path += "/"

    str_start = img_path.rfind("/")
    str_finish = img_path.rfind(".")
    output_file = output_path + img_path[str_start+1:str_finish] + "_result" + draw_info + ".jpg"
    cv2.imwrite(output_file, img)
    print("Successful Save img: ", output_file)

def save_text_info(img_path, text_info, output_path):
    # 저장 경로 조정
    output_path = output_path if output_path.endswith('/') else output_path + '/'

    # 파일명에서 확장자 제거
    file_name = os.path.basename(img_path)
    str_finish = file_name.rfind(".")
    output_file = os.path.join(output_path, file_name[:str_finish] + "_result.txt")

    # 텍스트 파일 저장
    with open(output_file, 'w') as f:
        data = text_info["text_content"]
        f.write(data)

    print("Successful Save txt: ", output_file)

#한글폰트
def putText(image, text, x, y, color=(0, 255, 0), font_size=22):
    if type(image) == np.ndarray:
        color_coverted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(color_coverted)

    if platform.system() == 'Darwin':
        font = 'AppleGothic.ttf'
    elif platform.system() == 'Windows':
        font = 'malgun.ttf'
    else:
        font = 'NanumGothic.ttf'

    image_font = ImageFont.truetype(font, font_size)
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(image)

    draw.text((x, y), text, font=image_font, fill=color)

    numpy_image = np.array(image)
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

    return opencv_image
