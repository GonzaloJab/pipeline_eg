import sqlite3
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import pandas as pd
import re
from datetime import datetime
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from functools import partial

def determine_company_with_ImageFilename(filename):
    if len(filename.split('_')) == 6:
        return 'DUISBURG'
    elif len(filename.split('_')) == 4 and re.search('[a-zA-Z]', (filename.split('_'))[0]):
        return 'VERINA'
    elif len(filename.split('_')) == 5 and len(filename.split('_')[1]) == 1:
        return 'DUISBURG'
    elif len(filename.split('_')) == 5 and len(filename.split('_')[1]) == 7:
        return 'GSW'
    else:
        return 'UNK_FILETYPE'

def process_image(image_path):
    """Process a single image and return its properties"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return {
                'filepath': str(image_path),
                'filename': image_path.name,
                'width': width,
                'height': height,
                'label': image_path.parent.name
            }
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return {
            'filepath': str(image_path),
            'filename': image_path.name,
            'width': None,
            'height': None,
            'label': image_path.parent.name
        }

def process_directory(directory):
    """Process all images in a directory"""
    return [f for f in Path(directory).rglob("*") 
            if (f.suffix.lower() == ".jpg" and f.is_file() and 'Augmented' not in str(f))]

def generate_db(save_path):
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
            "09_M-SLIVERS": '05_MULT',
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
        r'Z:/2_TRAIN_DATA/1_DnD/0_NO-DEFECT',
        r'Z:/2_TRAIN_DATA/3_PvsM',
        r'Z:/2_TRAIN_DATA/4_PUNCT',
        r'Z:/2_TRAIN_DATA/5_MULT'
    ]

    # Step 1: Gather all image paths in parallel
    print("Gathering image paths...")
    with ThreadPoolExecutor(max_workers=len(list_directories)) as executor:
        future_to_dir = {executor.submit(process_directory, d): d for d in list_directories}
        images = []
        for future in tqdm(as_completed(future_to_dir), total=len(list_directories)):
            images.extend(future.result())

    # Step 2: Process images in parallel using multiprocessing
    print("Processing images...")
    num_processes = mp.cpu_count()  # Use all available CPU cores
    chunk_size = max(1, len(images) // (num_processes * 4))  # Optimize chunk size
    
    with mp.Pool(processes=num_processes) as pool:
        results = list(tqdm(
            pool.imap(process_image, images, chunksize=chunk_size),
            total=len(images)
        ))

    # Step 3: Create DataFrame from results
    print("Creating DataFrame...")
    df = pd.DataFrame(results)
    
    # Add derived columns
    df['label_DnD'] = df['label'].map(Classes_dict_DnD)
    df['label_PvsM'] = df['label'].map(Classes_dict_PvsM)
    df['label_Punct'] = df['label'].map(Classes_dict_Punct)
    df['label_Multi'] = df['label'].map(Classes_dict_Multi)
    df['client'] = df['filename'].apply(determine_company_with_ImageFilename)
    df['diameter'] = None  # Placeholder for diameter
    df['image_width'] = df['width']
    df['image_height'] = df['height']
    df['label_detail'] = df['label']
    df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Clean up temporary columns
    df = df.drop(['width', 'height', 'label'], axis=1)

    # Step 4: Optimize database writing
    print("Writing to database...")
    with sqlite3.connect(save_path) as conn:
        # Create indices after bulk insert for better performance
        df.to_sql('images', conn, if_exists='replace', index=False, 
                  method='multi', chunksize=10000)  # Use optimal chunk size for SQLite

    print("Database generation complete!")

if __name__ == "__main__":
    import os
    
    save_path = r'E:\FAST_API\backend\databases'
    save_path = os.path.join(save_path, f'images_{datetime.now().strftime("%Y%m%d")}.db')
    generate_db(save_path)