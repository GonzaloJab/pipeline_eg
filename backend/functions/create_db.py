import sqlite3
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import pandas as pd
import re
from datetime import datetime
import os
from dotenv import load_dotenv


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

def create_db(db_name: str):
    """Create a new database with the given name."""
    # Create the database in the specified path
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create the images table with version support and all label columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL,
            filename TEXT NOT NULL,
            label_DnD TEXT NOT NULL,
            label_PvsM TEXT NOT NULL,
            label_Punct TEXT NOT NULL,
            label_Multi TEXT NOT NULL,
            client TEXT NOT NULL,
            diameter REAL,
            image_width INTEGER,
            image_height INTEGER,
            version TEXT NOT NULL,
            is_current BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create an index on version and is_current for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_version_current 
        ON images(version, is_current)
    ''')

    conn.commit()
    conn.close()

def get_new_db_path(base_path: str) -> str:
    """Generate a new database path with timestamp only if needed."""
    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    
    # If the filename already has a timestamp, use it as is
    if filename.startswith('20'):  # Check if filename starts with a year
        return base_path
    
    # Otherwise, add timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.splitext(filename)[0]
    return os.path.join(directory, f"{timestamp}_{base_name}.db")

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
            WHERE is_current = 1
            ORDER BY filepath
        """)
        rows = cursor.fetchall()
        
        # Create a string representation of the data
        data_str = '|'.join([str(row) for row in rows])
        
        # Use a hash function to create a compact representation
        import hashlib
        return hashlib.md5(data_str.encode()).hexdigest()
    except Exception as e:
        print(f"Error getting database hash: {e}")
        return ""
    finally:
        conn.close()

def has_database_changes(current_db: str) -> bool:
    """
    Check if there would be changes in the database by comparing current data
    with what's in the database.
    Returns True if changes are detected, False otherwise.
    """
    # Get hash of current database
    current_hash = get_database_hash(current_db)
    
    # Create a temporary database with new data
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_path = temp_db.name
    
    try:
        # Create and populate temporary database
        create_db(temp_path)
        
        # Get hash of new data
        new_hash = get_database_hash(temp_path)
        
        # Compare hashes
        return current_hash != new_hash
    finally:
        # Clean up temporary database
        if os.path.exists(temp_path):
            os.unlink(temp_path)

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

def update_db(db_path: str):
    """Update database with new data and create a new version if changes are detected."""
    # Get the current database path
    db_dir = os.path.dirname(db_path)
    current_db = get_current_db_path(db_dir)
    
    # If we have a current database, check for changes
    if current_db and not has_database_changes(current_db):
        print("No changes detected in the database")
        return current_db, False
    
    # If the file already exists with a timestamp, use it directly
    if os.path.basename(db_path).startswith('20'):
        create_db(db_path)
        return db_path, True

    # Otherwise, generate new database path with timestamp
    new_db_path = get_new_db_path(db_path)
    
    # Create new database
    create_db(new_db_path)
    
    # After successfully creating the new database, update the symlink
    try:
        if os.path.exists(db_path):
            if os.path.islink(db_path):
                os.unlink(db_path)
            else:
                # If it's a regular file, move it to a timestamped version
                old_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                old_db_path = os.path.join(
                    os.path.dirname(db_path),
                    f"{old_timestamp}_{os.path.splitext(os.path.basename(db_path))[0]}.db"
                )
                os.rename(db_path, old_db_path)
        
        # Create the symlink to the new database
        os.symlink(new_db_path, db_path)
        print(f"Created new database version: {new_db_path}")
        print(f"Updated symlink: {db_path} -> {new_db_path}")
    except Exception as e:
        print(f"Failed to update symlink: {e}")
    
    return new_db_path, True

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

def create_dataset_csv(db_path: str, output_dir: str, dataset_type: str, train_path: str = None, val_path: str = None, split_ratio: float = 0.8) -> tuple:
    """
    Create train and validation CSV datasets from the database based on dataset type.
    
    Args:
        db_path (str): Path to the SQLite database
        output_dir (str): Directory to save the CSV files
        dataset_type (str): One of 'DnD', 'PvsM', 'Punct', 'Multiple'
        train_path (str, optional): Specific path for training CSV
        val_path (str, optional): Specific path for validation CSV
        split_ratio (float): Ratio for train/validation split (default: 0.8)
    
    Returns:
        tuple: (train_csv_path, val_csv_path)
    """
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
        WHERE is_current = 1
        AND {target_column} != ''
        AND {target_column} IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        raise ValueError(f"No data found for dataset type {dataset_type}")
    
    # Print dataset statistics
    print(f"\nDataset statistics for {dataset_type}:")
    print(f"Total samples: {len(df)}")
    print("\nLabel distribution:")
    print(df['label'].value_counts())
    
    # Shuffle the dataframe
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Split into train and validation sets
    split_idx = int(len(df) * split_ratio)
    train_df = df[:split_idx]
    val_df = df[split_idx:]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Use provided paths or generate with timestamp
    if not train_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        train_path = os.path.join(output_dir, f'train_{dataset_type}_{timestamp}.csv')
    if not val_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        val_path = os.path.join(output_dir, f'val_{dataset_type}_{timestamp}.csv')
    
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

if __name__ == "__main__":
    # Load environment variables
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    
    # Get database directory from environment
    DB_DIR = os.getenv("DB_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN/databases")
    DB_PATH = os.path.join(DB_DIR, "ISEND_images.db")
    
    # Ensure database directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Update database
    update_db(DB_PATH)
    
    # List versions
    versions = get_db_versions(DB_PATH)
    print("\nAvailable database versions:")
    for version in versions:
        current_marker = " (current)" if version['is_current'] else ""
        print(f"{version['version']} - Created: {version['created_at']}{current_marker}")
