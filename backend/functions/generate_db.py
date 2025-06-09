import sqlite3
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import pandas as pd
import re
from datetime import datetime

# Define the mapping of class names to integers
Classes_dict_DnD = {
        "0_NO-DEFECT": '0_NO-DEFECT',
        "DEFECT": 'DEFECT',
        '00_CUT': '0_NO-DEFECT',
        '00_DIRT': '0_NO-DEFECT',
        '00_NONE': '0_NO-DEFECT',
        '00_RUG': '0_NO-DEFECT',
        '00_STAINS': '0_NO-DEFECT',
        '00_TAILTIP': 'DEFECT',
        '00_VOID': '0_NO-DEFECT',
        '00_WAVES': '0_NO-DEFECT',
        "01_BROKEN": 'DEFECT',
        "03_HAIRS": 'DEFECT',
        "03_CRACKS": 'DEFECT',
        "04_DENT": 'DEFECT',
        "06_INCRUST": 'DEFECT',
        "08_LACKS": 'DEFECT',
        "11_SLIVERS": 'DEFECT',
        "12_STAMP": 'DEFECT',
        "14_FLAKE": 'DEFECT',
        "02_COMET": 'DEFECT',
        "07_IRREG": 'DEFECT',
        "09_M-SLIVERS": 'DEFECT',
        "10_SEAMS": 'DEFECT',
        "13_VSHAPE": 'DEFECT',
        "04_PUNCT": 'DEFECT',
        "05_MULT": 'DEFECT',
        }

Classes_dict_PvsM = {
        "0_NO-DEFECT": '',
        "DEFECT": '',
        '00_CUT': '',
        '00_DIRT': '',
        '00_NONE': '',
        '00_RUG': '',
        '00_STAINS': '',
        '00_TAILTIP': '00_TAILTIP',
        '00_VOID': '',
        '00_WAVES': '',
        "01_BROKEN": '01_BROKEN',
        "03_HAIRS": '03_HAIRS',
        "03_CRACKS": '04_PUNCT',
        "04_DENT": '04_PUNCT',
        "06_INCRUST": '04_PUNCT',
        "08_LACKS": '04_PUNCT',
        "11_SLIVERS": '04_PUNCT',
        "12_STAMP": '04_PUNCT',
        "14_FLAKE": '04_PUNCT',
        "02_COMET": '05_MULT',
        "07_IRREG": '05_MULT',
        "09_M-SLIVERS": '09_M-05_MULT',
        "10_SEAMS": '05_MULT',
        "13_VSHAPE": '05_MULT',
        "04_PUNCT": '04_PUNCT',
        "05_MULT": '05_MULT',
        }

Classes_dict_Punct = {
        "0_NO-DEFECT": '',
        "DEFECT": '',
        '00_CUT': '',
        '00_DIRT': '',
        '00_NONE': '',
        '00_RUG': '',
        '00_STAINS': '',
        '00_TAILTIP': '',
        '00_VOID': '',
        '00_WAVES': '',
        "01_BROKEN": '',
        "03_HAIRS": '',
        "03_CRACKS": '03_CRACKS',
        "04_DENT": '04_DENT',
        "06_INCRUST": '06_INCRUST',
        "08_LACKS": '08_LACKS',
        "11_SLIVERS": '11_SLIVERS',
        "12_STAMP": '12_STAMP',
        "14_FLAKE": '14_FLAKE',
        "02_COMET": '',
        "07_IRREG": '',
        "09_M-SLIVERS": '',
        "10_SEAMS": '',
        "13_VSHAPE": '',
        "04_PUNCT": '',
        "05_MULT": '',
        }

Classes_dict_Multi = {
        "0_NO-DEFECT": '',
        "DEFECT": '',
        '00_CUT': '',
        '00_DIRT': '',
        '00_NONE': '',
        '00_RUG': '',
        '00_STAINS': '',
        '00_TAILTIP': '',
        '00_VOID': '',
        '00_WAVES': '',
        "01_BROKEN": '',
        "03_HAIRS": '',
        "03_CRACKS": '',
        "04_DENT": '',
        "06_INCRUST": '',
        "08_LACKS": '',
        "11_SLIVERS": '',
        "12_STAMP": '',
        "14_FLAKE": '',
        "02_COMET": '02_COMET',
        "07_IRREG": '07_IRREG',
        "09_M-SLIVERS": '09_M-SLIVERS',
        "10_SEAMS": '10_SEAMS',
        "13_VSHAPE": '13_VSHAPE',
        "04_PUNCT": '',
        "05_MULT": '',
        }

list_directories = [
            r'Z:/2_TRAIN_DATA/1_DnD/DEFECT',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_CUT',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_DIRT',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_NONE',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_RUG',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_STAINS',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_TAILTIP',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_VOID',
            r'Z:/2_TRAIN_DATA/2_NoDef/00_WAVES',
            r'Z:/2_TRAIN_DATA/3_PvsM',
            r'Z:/2_TRAIN_DATA/4_PUNCT',
            r'Z:/2_TRAIN_DATA/5_MULT',
            r'Z:/2_TRAIN_DATA/7_DUISBURG_ONLY'
]

def determine_company_with_ImageFilename(filename):
        if len(filename.split('_')) == 6:
            return 'DUISBURG'
        elif len(filename.split('_')) == 4 and re.search('[a-zA-Z]', (filename.split('_'))[0]):
            return 'VERINA'
        elif len(filename.split('_')) == 5 and len(filename.split('_')[1]) == 1:
            return 'DUISBURG'
        elif  len(filename.split('_')) == 5 and len(filename.split('_')[1]) == 7:
            return 'GSW'
        else:
            return 'UNK_FILETYPE'

images = []
image_widths = []
image_heights = []

for directory in tqdm(list_directories):
    images.append([f for f in Path(directory).rglob("*") if (f.suffix.lower() == ".jpg" and f.is_file() and 'Augmented' not in str(f))])

# Flatten the list of lists into a single list
images = [item for sublist in images for item in sublist]
filenames = [f.name for f in images]
labels = [f.parent.name for f in images]

labels_DnD = [Classes_dict_DnD[label] for label in labels]
labels_PvsM = [Classes_dict_PvsM[label] for label in labels]
labels_Punct = [Classes_dict_Punct[label] for label in labels]
labels_Multi = [Classes_dict_Multi[label] for label in labels]

clients = [determine_company_with_ImageFilename(f.name) for f in images]
diameters = [None] * len(images)  # Placeholder for diameter

for image in tqdm(images):
    try:
        with Image.open(image) as img:
            image_width, image_height = img.size
            image_widths.append(image_width)
            image_heights.append(image_height)
    except Exception as e:
        print(f"Error processing image {image}: {e}")
        image_widths.append(None)
        image_heights.append(None)

df = pd.DataFrame({
    'filepath': [str(f) for f in images],
    'filename': filenames,
    'label_DnD': labels_DnD,
    'label_PvsM': labels_PvsM,
    'label_Punct': labels_Punct,
    'label_Multi': labels_Multi,
    'label_detail': labels,
    'client': clients,
    'diameter': diameters,
    'image_width': image_widths,
    'image_height': image_heights,
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
})

# Connexion à la base de données
with sqlite3.connect('ISEND_images.db') as conn:
    df.to_sql('images', conn, if_exists='replace', index=False)