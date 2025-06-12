import sqlite3
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import pandas as pd
import re
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json

# Constants
HASH_STATE_FILE = "directory_hashes.json"

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

def get_database_hash(db_path: str) -> str:
    """
    Get a hash of the database contents to check for changes.
    Returns a string representing the current state of the database.
    """
    if not os.path.exists(db_path):
        return ""
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all current records
        cursor.execute("""
            SELECT filepath, filename, label_DnD, label_PvsM, label_Punct, label_Multi,
                   client, diameter, image_width, image_height
            FROM images
            ORDER BY filepath
        """)
        rows = cursor.fetchall()
        
        # Create a string representation of the data
        data_str = '|'.join([str(row) for row in rows])
        
        # Use a hash function to create a compact representation
        return hashlib.md5(data_str.encode()).hexdigest()
    except Exception as e:
        print(f"Error getting database hash: {e}")
        return ""
    finally:
        conn.close()


def get_current_db_path(db_dir: str) -> str:
    """
    Get the path of the most recent database file.
    """
    try:
        # List all database files
        db_files = [f for f in os.listdir(db_dir) if f.endswith('.db')]
        if not db_files:
            return None
            
        # Sort by timestamp (newest first)
        db_files.sort(reverse=True)
        return os.path.join(db_dir, db_files[0])
    except Exception as e:
        print(f"Error getting current database: {e}")
        return None

def get_db_versions(base_path: str) -> list:
    """Get all available database versions with their creation timestamps."""
    directory = os.path.dirname(base_path)
    base_name = os.path.splitext(os.path.basename(base_path))[0]
    versions = []
    
    try:
        # List all database files matching the pattern
        for file in os.listdir(directory):
            if file.startswith(base_name) and file.endswith('.db'):
                try:
                    # Extract timestamp from filename
                    timestamp_str = file.replace(f"{base_name}_", "").replace(".db", "")
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    file_path = os.path.join(directory, file)
                    
                    # Check if this is the current version (symlink points to it)
                    is_current = False
                    if os.path.exists(base_path):
                        if os.path.islink(base_path):
                            real_path = os.path.realpath(base_path)
                            is_current = (real_path == file_path)
                    
                    versions.append({
                        'version': file,
                        'created_at': timestamp.isoformat(),
                        'is_current': is_current
                    })
                except ValueError:
                    continue
        
        # Sort by timestamp, newest first
        versions.sort(key=lambda x: x['created_at'], reverse=True)
        return versions
    except Exception as e:
        print(f"Error listing database versions: {e}")
        return []

def get_latest_version(db_name: str) -> str:
    """Get the latest version number from the database"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT version FROM images 
        WHERE is_current = 1 
        LIMIT 1
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        current_version = result[0]
        # Extract the version number and increment it
        version_num = int(current_version.split('v')[1])
        return f"v{version_num + 1}"
    return "v1"  # First version

def create_dataset_csv(db_path: str, output_dir: str, dataset_type: str, train_path: str = None, val_path: str = None, 
                   split_ratio: float = 0.8, sample_percentage: float = 100.0) -> tuple:
    """
    Create train and validation CSV datasets from the database based on dataset type.
    Uses stratified sampling to ensure even distribution of both labels and clients.
    
    Args:
        db_path (str): Path to the SQLite database
        output_dir (str): Directory to save the CSV files
        dataset_type (str): One of 'DnD', 'PvsM', 'Punct', 'Multiple'
        train_path (str, optional): Specific path for training CSV
        val_path (str, optional): Specific path for validation CSV
        split_ratio (float): Ratio for train/validation split (default: 0.8)
        sample_percentage (float): Percentage of total data to use (default: 100.0)
    
    Returns:
        tuple: (train_csv_path, val_csv_path)
    """
    # Input validation
    if not 0 < sample_percentage <= 100:
        raise ValueError("sample_percentage must be between 0 and 100")
    if not 0 < split_ratio < 1:
        raise ValueError("split_ratio must be between 0 and 1")
    
    # Set random seed for reproducibility
    RANDOM_SEED = 42
    
    # Map dataset type to corresponding column
    type_to_column = {
        'DnD': 'label_DnD',
        'PvsM': 'label_PvsM',
        'Punct': 'label_Punct',
        'Multiple': 'label_Multi'
    }
    
    if dataset_type not in type_to_column:
        raise ValueError(f"Dataset type must be one of {list(type_to_column.keys())}")
    
    target_column = type_to_column[dataset_type]
    
    conn = sqlite3.connect(db_path)
    
    # Query to get only images with non-empty labels in the target column
    query = f"""
        SELECT filepath, filename, {target_column} as label, client,
               image_width, image_height
        FROM images
        WHERE {target_column} != ''
        AND {target_column} IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        raise ValueError(f"No data found for dataset type {dataset_type}")
    
    # Print initial dataset statistics
    print(f"\nInitial dataset statistics for {dataset_type}:")
    print(f"Total samples: {len(df)}")
    print("\nInitial label distribution:")
    print(df['label'].value_counts())
    print("\nInitial client distribution:")
    print(df['client'].value_counts())
    
    # Create a combined stratification column (label_client)
    df['strat'] = df['label'] + '_' + df['client']
    
    # If sample_percentage < 100, reduce the dataset size while maintaining distributions
    if sample_percentage < 100:
        # Calculate the number of samples to keep
        n_samples = int(len(df) * (sample_percentage / 100))
        print(f"\nReducing dataset to {sample_percentage}% ({n_samples} samples)")
        
        # Sample from each stratum proportionally
        sampled_df = pd.DataFrame()
        for strat in df['strat'].unique():
            strat_df = df[df['strat'] == strat]
            strat_samples = int(len(strat_df) * (sample_percentage / 100))
            if strat_samples == 0:  # Ensure at least one sample per stratum
                strat_samples = 1
            sampled_strat = strat_df.sample(n=min(strat_samples, len(strat_df)), 
                                          random_state=RANDOM_SEED)
            sampled_df = pd.concat([sampled_df, sampled_strat])
        df = sampled_df
        
        print("\nReduced dataset statistics:")
        print(f"Total samples after reduction: {len(df)}")
        print("\nLabel distribution after reduction:")
        print(df['label'].value_counts())
        print("\nClient distribution after reduction:")
        print(df['client'].value_counts())
    
    # Initialize empty DataFrames for train and validation
    train_df = pd.DataFrame()
    val_df = pd.DataFrame()
    
    # Process each label-client combination separately
    for strat in df['strat'].unique():
        strat_df = df[df['strat'] == strat]
        
        # Shuffle the stratified dataframe
        strat_df = strat_df.sample(frac=1, random_state=RANDOM_SEED)
        
        # Calculate split index for this stratum
        split_idx = int(len(strat_df) * split_ratio)
        
        # Add to train and validation sets
        train_df = pd.concat([train_df, strat_df[:split_idx]])
        val_df = pd.concat([val_df, strat_df[split_idx:]])
    
    # Drop the stratification column
    train_df = train_df.drop('strat', axis=1)
    val_df = val_df.drop('strat', axis=1)
    
    # Shuffle the final datasets
    train_df = train_df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    val_df = val_df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    
    # Print final distribution statistics
    print("\nFinal Training set distribution:")
    print("Labels:")
    print(train_df['label'].value_counts())
    print("\nClients:")
    print(train_df['client'].value_counts())
    
    print("\nFinal Validation set distribution:")
    print("Labels:")
    print(val_df['label'].value_counts())
    print("\nClients:")
    print(val_df['client'].value_counts())
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Use provided paths or generate with timestamp
    if not train_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        size_suffix = f"_{int(sample_percentage)}pct" if sample_percentage < 100 else ""
        train_path = os.path.join(output_dir, f'train_{dataset_type}{size_suffix}_{timestamp}.csv')
    if not val_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        size_suffix = f"_{int(sample_percentage)}pct" if sample_percentage < 100 else ""
        val_path = os.path.join(output_dir, f'val_{dataset_type}{size_suffix}_{timestamp}.csv')
    
    # Save CSV files
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    
    print(f"\nCreated datasets:")
    print(f"Training set: {len(train_df)} samples -> {train_path}")
    print(f"Validation set: {len(val_df)} samples -> {val_path}")
    
    return train_path, val_path

def get_available_dataset_types(db_name: str) -> dict:
    """
    Get counts of available samples for each dataset type in the current version.
    
    Args:
        db_name (str): Path to the SQLite database
    
    Returns:
        dict: Dictionary with counts for each dataset type
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    dataset_types = {
        'DnD': 'label_DnD',
        'PvsM': 'label_PvsM',
        'Punct': 'label_Punct',
        'Multiple': 'label_Multi'
    }
    
    counts = {}
    for dtype, column in dataset_types.items():
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM images 
            WHERE is_current = 1 
            AND {column} != ''
            AND {column} IS NOT NULL
        """)
        counts[dtype] = cursor.fetchone()[0]
    
    conn.close()
    return counts

def get_unique_labels(db_name: str) -> dict:
    """
    Get all unique values for each label column in the current version of the database.
    
    Args:
        db_name (str): Path to the SQLite database
    
    Returns:
        dict: Dictionary with unique values for each label column
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    label_columns = ['label_DnD', 'label_PvsM', 'label_detail']
    unique_labels = {}
    
    for column in label_columns:
        cursor.execute(f"""
            SELECT DISTINCT {column}
            FROM images
            WHERE is_current = 1
            ORDER BY {column}
        """)
        unique_labels[column] = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return unique_labels

def save_hash_state(hashes: dict, state_file: str = HASH_STATE_FILE):
    """Save directory hashes to a JSON file"""
    state = {
        'hashes': hashes,
        'last_update': datetime.now().isoformat()
    }
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=4)

def load_hash_state(state_file: str = HASH_STATE_FILE) -> dict:
    """Load directory hashes from JSON file"""
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
            return state['hashes']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}

def hash_file(filepath):
    """Hash a single file"""
    sha = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return filepath, sha.hexdigest()

def hash_directory(directory):
    """
    Calculate a SHA-256 hash of all files in a directory using parallel processing.
    Files are processed in sorted order to ensure consistent hashing.
    """
    # Get all files in sorted order
    files = []
    for root, _, filenames in os.walk(directory):
        for name in sorted(filenames):
            files.append(os.path.join(root, name))
    
    if not files:
        return hashlib.sha256().hexdigest()

    # Use thread pool for file hashing
    combined = hashlib.sha256()
    with ThreadPoolExecutor(max_workers=min(32, len(files))) as executor:
        future_to_file = {executor.submit(hash_file, f): f for f in files}
        for future in tqdm(future_to_file, desc=f"Hashing {os.path.basename(directory)}", leave=False):
            try:
                _, file_hash = future.result()
                combined.update(file_hash.encode())
            except Exception as e:
                print(f"Error hashing file: {e}")
                continue
    
    return combined.hexdigest()

def check_directories_modified(directories: list, db_dir: str) -> tuple[bool, dict]:
    """
    Check if any of the provided directories have been modified by comparing with stored hash state.
    
    Args:
        directories (list): List of directory paths to check
        db_dir (str): Directory containing the database files (used for hash state file location)
    
    Returns:
        tuple: (bool indicating if changes detected, dict with details)
    """
    details = {
        "total_directories": len(directories),
        "modified_directories": [],
        "last_check": datetime.now().isoformat()
    }
    
    # Ensure hash state file is in the database directory
    state_file = os.path.join(db_dir, HASH_STATE_FILE)
    stored_hashes = load_hash_state(state_file)
    
    # Get current directory hashes using thread pool
    existing_dirs = [d for d in directories if os.path.exists(d)]
    if not existing_dirs:
        return True, details

    print("Calculating directory hashes...")
    current_hashes = {}
    with ThreadPoolExecutor(max_workers=min(8, len(existing_dirs))) as executor:
        future_to_dir = {executor.submit(hash_directory, d): d for d in existing_dirs}
        for future in tqdm(future_to_dir, desc="Hashing directories"):
            directory = future_to_dir[future]
            try:
                current_hashes[directory] = future.result()
            except Exception as e:
                print(f"Error processing directory {directory}: {e}")
                current_hashes[directory] = None
    
    # Compare hashes
    changes_detected = False
    for directory, current_hash in current_hashes.items():
        if current_hash is None or directory not in stored_hashes or stored_hashes[directory] != current_hash:
            changes_detected = True
            details["modified_directories"].append(directory)
    
    # If no changes detected, we're done
    if not changes_detected:
        return False, details
        
    # If changes detected, update the hash state file
    save_hash_state(current_hashes, state_file)
    
    return True, details

if __name__ == "__main__":
    # Load environment variables
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    # Get database directory from environment
    DB_DIR = os.getenv("DB_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN/databases")
    DB_PATH = os.path.join(DB_DIR, "ISEND_images.db")
    
    # Ensure database directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    # List versions
    versions = get_db_versions(DB_PATH)
    print("\nAvailable database versions:")
    for version in versions:
        current_marker = " (current)" if version['is_current'] else ""
        print(f"{version['version']} - Created: {version['created_at']}{current_marker}")
