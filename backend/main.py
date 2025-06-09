"""Modified FastAPI app to allow remote training launch, PID tracking, stopping tasks, and log streaming via SSH."""
## CMD:  uvicorn main:app --reload


import os
import asyncio
from datetime import datetime
from typing import List, Dict
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import paramiko
from contextlib import asynccontextmanager, suppress

from functions.create_db import (
    update_db, 
    get_db_versions, 
    create_db, 
    create_dataset_csv,
    get_unique_labels
)

# Load .env file from the parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'),override=True)

# Constants
LOG_PATH = os.getenv("LOG_PATH", "/media/isend/ssd_storage/1_EYES_TRAIN/remote_runs/logs")

# Make CORS more permissive
ALLOWED_ORIGINS = ["*"]

'''
Previous CORS config was too permissive
'''
SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_KEY = os.getenv("SSH_PRIVATE_KEY_PATH")
CONDA_HOOK = "/home/isend/anaconda3/bin/conda shell.bash hook"
CONDA_ENV = os.getenv("CONDA_ENV", "YOLO")
WORKING_DIR = os.getenv("WORKING_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN")
CSV_DATASETS_FOLDER = os.getenv("CSV_DATASETS_FOLDER", "/media/isend/ssd_storage/1_EYES_TRAIN/datasets")
DB_PATH = os.getenv("DB_PATH", "ISEND_images.db")
DB_DIR = os.getenv("DB_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN/databases")  # New constant for database directory

# Make sure the database directory exists
os.makedirs(DB_DIR, exist_ok=True)

print(f"Allowed origins: {ALLOWED_ORIGINS}")
#print(f"Database path: {DB_FULL_PATH}")
print(f"CSV datasets folder: {CSV_DATASETS_FOLDER}")

# FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up the application...")
    '''
    try:
        # Initialize database
        create_db(DB_FULL_PATH)
        print(f"Database initialized at {DB_FULL_PATH}")
    except Exception as e:
        print(f"Error initializing database: {e}")
    '''
    # Start MLflow server in a separate try block
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

        print("Connected to remote server, checking conda environment...")

        # Kill any existing MLflow processes
        ssh.exec_command("pkill -f 'mlflow server'")
        print("Cleaned up any existing MLflow processes")

        # Define MLflow paths
        mlflow_tracking_uri = os.path.join(WORKING_DIR, "mlruns")
        mlflow_artifacts = os.path.join(WORKING_DIR, "mlartifacts")

        # Ensure directories exist
        mkdir_cmd = f"mkdir -p {mlflow_tracking_uri} {mlflow_artifacts}"
        ssh.exec_command(mkdir_cmd)

        # Start MLflow server with conda environment - using screen to properly detach
        # First, ensure screen is installed
        ssh.exec_command("command -v screen || sudo apt-get install screen -y")
        
        # Create a script to run MLflow
        mlflow_script = (
            f"source ~/anaconda3/etc/profile.d/conda.sh\n"
            f"conda activate {CONDA_ENV}\n"
            f"cd {WORKING_DIR}\n"
            f"mlflow server "
            f"--host 0.0.0.0 "
            f"--port 8080 "
            f"--backend-store-uri {mlflow_tracking_uri} "
            f"--default-artifact-root {mlflow_artifacts}"
        )
        
        # Write the script to a file
        script_path = "/tmp/start_mlflow.sh"
        ssh.exec_command(f"echo '{mlflow_script}' > {script_path} && chmod +x {script_path}")

        # Start MLflow in a detached screen session
        screen_cmd = (
            f"screen -dmS mlflow bash -c '{script_path}'"
        )

        print("Starting MLflow server in detached screen session...")
        ssh.exec_command(screen_cmd)

        # Give it a moment to start
        time.sleep(2)

        # Verify it's running
        _, stdout, _ = ssh.exec_command("screen -ls | grep mlflow")
        if stdout.read().decode():
            print("MLflow server started successfully in screen session")
        else:
            print("Warning: MLflow screen session not found")

    except Exception as e:
        print(f"Failed to start MLflow server: {e}")
    finally:
        if 'ssh' in locals():
            ssh.close()

    # Start the background task worker
    task = asyncio.create_task(worker())
    
    yield  # This is where the application runs
    
    # Shutdown
    print("Shutting down the application...")
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task

# Create the FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Configure CORS - simplified and permissive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Changed to False since we're using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handling middleware
@app.middleware("http")
async def add_error_handling(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Error handling request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# Models
class TrainingTask(BaseModel):
    name: str
    model: str
    weights: str
    datasetType: str
    selectedDatabase: str  # New field for selected database
    output_directory: str = Field(..., alias="outputDirectory")
    batch_size: int = Field(..., alias="batchSize")
    epochs: int
    lr: float
    exp_lr_decrease_factor: float = Field(..., alias="expLRDecreaseFactor")
    step_size: int = Field(..., alias="stepSize")
    gamma: float
    solver: str
    momentum: float
    weight_decay: float = Field(..., alias="weightDecay")
    num_workers: int = Field(..., alias="numWorkers")
    prefetch_factor: int = Field(..., alias="prefetchFactor")
    submitted_at: datetime = None
    train_csv: str = None
    val_csv: str = None

    class Config:
        allow_population_by_field_name = True
        extra = "allow"

# In-memory task store and queue
tasks: List[TrainingTask] = []
task_queue = asyncio.Queue()
running_tasks: List[str] = []
task_names: set = set()  # Store all task names

# Run command via SSH
async def run_remote_training(task: TrainingTask):
    log_path = os.path.join(LOG_PATH, f"train_{task.name}.log")
    pid_path = os.path.join(LOG_PATH, f"train_{task.name}.pid")

    # Create dataset CSVs locally first
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        local_train_csv = os.path.join("temp", f'train_{task.name}_{timestamp}.csv')
        local_val_csv = os.path.join("temp", f'val_{task.name}_{timestamp}.csv')
        
        # Ensure local temp directory exists
        os.makedirs("temp", exist_ok=True)
        
        # Create the datasets locally
        train_csv, val_csv = create_dataset_csv(
            task.selectedDatabase,  # Use selected database
            "temp",  # Local temp directory
            dataset_type=task.datasetType,
            train_path=local_train_csv,
            val_path=local_val_csv
        )

        # Setup SSH and SFTP connection
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)
        sftp = ssh.open_sftp()

        # Create remote paths
        remote_train_csv = os.path.join(CSV_DATASETS_FOLDER, f'train_{task.name}_{timestamp}.csv')
        remote_val_csv = os.path.join(CSV_DATASETS_FOLDER, f'val_{task.name}_{timestamp}.csv')

        # Create remote directory if it doesn't exist
        try:
            sftp.mkdir(CSV_DATASETS_FOLDER)
        except IOError:
            pass  # Directory already exists

        # Transfer the files
        print(f"Transferring CSV files to remote machine...")
        sftp.put(local_train_csv, remote_train_csv)
        sftp.put(local_val_csv, remote_val_csv)
        print(f"Files transferred successfully")

        # Store the remote CSV paths in the task
        task.train_csv = remote_train_csv
        task.val_csv = remote_val_csv

        # Run the training command
        python_cmd = (
            f"cd {WORKING_DIR} && "    
            f"nohup python /media/isend/ssd_storage/1_EYES_TRAIN/train.py "
            f"--training_name {task.name} "
            f"--model {task.model} --weights {task.weights} "
            f"--train_dataset \"{remote_train_csv}\" "
            f"--val_dataset \"{remote_val_csv}\" "
            f"--output_dir \"{task.output_directory}\" "
            f"--batch_size {task.batch_size} --epochs {task.epochs} --lr {task.lr} "
            f"--exp_LR_decrease_factor {task.exp_lr_decrease_factor} --step_size {task.step_size} "
            f"--gamma {task.gamma} --solver {task.solver} --momentum {task.momentum} "
            f"--weight_decay {task.weight_decay} --num_workers {task.num_workers} "
            f"--unfreeze_index {9} "
            f"--prefetch_factor {task.prefetch_factor} > \"{log_path}\" 2>&1 & "
            f"echo $! > \"{pid_path}\""
        )

        full_cmd = f"bash -l -c 'eval \"$({CONDA_HOOK})\" && conda activate {CONDA_ENV} && {python_cmd} '"
        print(f"Executing command: {full_cmd}")
        
        ssh.exec_command(full_cmd)
        if task.name not in running_tasks:
            running_tasks.append(task.name)

        # Clean up local files
        os.remove(local_train_csv)
        os.remove(local_val_csv)

    except Exception as e:
        print(f"Error during task execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'sftp' in locals():
            sftp.close()
        if 'ssh' in locals():
            ssh.close()

# Get task statuses
async def get_task_statuses():
    statuses = {}
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

        for task in tasks:
            log_file = os.path.join(LOG_PATH, f"train_{task.name}.log")
            pid_file = os.path.join(LOG_PATH, f"train_{task.name}.pid")

            # Check if PID is alive
            _, stdout, _ = ssh.exec_command(f"test -f '{pid_file}' && pid=$(cat '{pid_file}') && ps -p $pid > /dev/null && echo RUNNING")
            is_running = "RUNNING" in stdout.read().decode()

            if is_running:
                statuses[task.name] = "running"
            else:
                # Check if log exists and ends with typical success or error string
                _, stdout, _ = ssh.exec_command(f"tail -n 10 '{log_file}'")
                log_tail = stdout.read().decode()

                if "Traceback" in log_tail or "Error" in log_tail:
                    statuses[task.name] = "error"
                elif "Finished" in log_tail or "Epoch" in log_tail:
                    statuses[task.name] = "completed"
                else:
                    statuses[task.name] = "idle"

        ssh.close()

    except Exception as e:
        print(f"[STATUS ERROR] {e}")

    return statuses

def determine_task_status(task_name: str) -> str:
    pid_file = os.path.join(LOG_PATH, f"train_{task_name}.pid")
    log_file = os.path.join(LOG_PATH, f"train_{task_name}.log")

    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

        # Check if PID file exists
        stdin, stdout, _ = ssh.exec_command(f"cat '{pid_file}'")
        pid = stdout.read().decode().strip()

        if pid:
            # Check if process is still running
            stdin, stdout, _ = ssh.exec_command(f"ps -p {pid}")
            ps_output = stdout.read().decode().strip()
            if pid in ps_output:
                return "running"

        # If not running, check for crash or success in log
        stdin, stdout, _ = ssh.exec_command(f"tail -n 20 '{log_file}'")
        tail_output = stdout.read().decode().lower()

        if "error" in tail_output or "traceback" in tail_output:
            return "error"
        elif tail_output:
            return "completed"

        return "idle"

    except Exception as e:
        print(f"Status check failed: {e}")
        return "unknown"

@app.post("/trains/stop/{task_name}")
async def stop_task(task_name: str):
    pid_file = os.path.join(LOG_PATH, f"train_{task_name}.pid")
    log_path = os.path.join(LOG_PATH, f"train_{task_name}.log")
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

        # Check if PID file exists
        stdin, stdout, stderr = ssh.exec_command(f"test -f '{pid_file}' && echo EXISTS")
        if "EXISTS" not in stdout.read().decode():
            raise HTTPException(status_code=404, detail="PID file not found")

        # GET PID from file
        stdin, stdout, stderr = ssh.exec_command(f"cat '{pid_file}'")
        pid = stdout.read().decode().strip()
        
        # Kill the ENTIRE process tree
        kill_cmd = f"""
            # Kill the entire process group
            PGID=$(ps -o pgid= {pid} | grep -o '[0-9]*')
            if [ -n "$PGID" ]; then
                kill -9 -"$PGID" 2>/dev/null
            else
                kill -9 {pid} 2>/dev/null
            fi
            # Verify process is gone
            if ! ps -p {pid} >/dev/null; then
                rm -f '{pid_file}' '{log_path}'
                echo "SUCCESS"
            else
                echo "FAILED_TO_KILL"
            fi
        """

        stdin, stdout, stderr = ssh.exec_command(kill_cmd)
        err = stderr.read().decode().strip()
        
        if err:
            raise HTTPException(status_code=500, detail=f"Failed to kill process: {err}")

        ssh.close()

        if task_name in running_tasks:
            running_tasks.remove(task_name)

        return {"message": f"Task '{task_name}' stopped."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trains/logs/{task_name}")
async def stream_logs(task_name: str):
    log_path = os.path.join(LOG_PATH, f"train_{task_name}.log")

    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

        transport = ssh.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.exec_command(f"tail -f {log_path}")

        async def log_stream():
            try:
                while True:
                    if channel.recv_ready():
                        yield channel.recv(1024).decode("utf-8")
                    await asyncio.sleep(0.5)
            except Exception as e:
                yield f"\n[ERROR] Streaming stopped: {e}"

        return StreamingResponse(log_stream(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH log streaming failed: {e}")

async def worker():
    while True:
        task = await task_queue.get()
        print(f"Running task: {task.name}")
        await run_remote_training(task)
        task_queue.task_done()

@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}

@app.get("/trains", response_model=List[dict])
async def get_tasks():
    try:
        result = []
        for task in tasks:
            status = determine_task_status(task.name)
            task_dict = task.dict(by_alias=True)
            task_dict["status"] = status
            result.append(task_dict)
        return result
    except Exception as e:
        print(f"Error in get_tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trains/queue")
async def get_queued_tasks():
    return [task.name for task in tasks if task.name not in running_tasks]

@app.get("/trains/running")
async def get_running_tasks():
    return running_tasks

@app.post("/trains", response_model=TrainingTask)
async def create_task(task: TrainingTask):
    # Check if task name already exists
    if task.name in task_names:
        raise HTTPException(
            status_code=400,
            detail=f"Task name '{task.name}' already exists. Please choose a different name."
        )
    
    if task.submitted_at is None:
        task.submitted_at = datetime.utcnow()
    
    # Add task name to set and task to list
    task_names.add(task.name)
    tasks.append(task)
    return task

@app.post("/trains/{task_id}/run")
async def run_task(task_id: int):
    if task_id < 0 or task_id >= len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    await task_queue.put(tasks[task_id])
    return {"message": f"Task '{tasks[task_id].name}' queued."}

@app.delete("/trains/{task_id}", response_model=TrainingTask)
async def delete_task(task_id: int):
    if task_id < 0 or task_id >= len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    try:
        # Connect to remote machine
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)
        
        # Files to clean up
        files_to_remove = [
            os.path.join(LOG_PATH, f"train_{task.name}.log"),
            os.path.join(LOG_PATH, f"train_{task.name}.pid")
        ]
        
        # Add CSV files if they exist in the task
        if hasattr(task, 'train_csv') and task.train_csv:
            files_to_remove.append(task.train_csv)
        if hasattr(task, 'val_csv') and task.val_csv:
            files_to_remove.append(task.val_csv)
            
        # Remove files
        for file_path in files_to_remove:
            cmd = f"rm -f '{file_path}'"
            ssh.exec_command(cmd)
            print(f"Removing file: {file_path}")
        
        # If task is in running_tasks list, remove it
        if task.name in running_tasks:
            running_tasks.remove(task.name)
            
    except Exception as e:
        print(f"Error cleaning up files: {e}")
    finally:
        if 'ssh' in locals():
            ssh.close()
    
    # Remove task name from set and task from list
    task_names.remove(task.name)
    return tasks.pop(task_id)

@app.get("/csv-files", response_model=List[str])
async def get_csv_files():
    """
    Connect via SSH to list CSV files in the remote CSV_FOLDER.
    """
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)
        
        command = f"ls -1 {CSV_DATASETS_FOLDER}*.csv"
        # print(f"Executing command: {command}")
        stdin, stdout, stderr = ssh.exec_command(command)
        files_output = stdout.read().decode('utf-8').strip()
        ssh.close()
        # print(f"Command output: {files_output}")
        
        if files_output:
            files = [os.path.basename(f) for f in files_output.splitlines()]
        else:
            files = []
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list CSV files: {e}")
    

@app.post("/refresh-database")
async def refresh_database():
    """
    Refresh the database by scanning the image directories and creating a new version.
    Previous versions are preserved. Only creates a new version if changes are detected.
    """
    try:
        # Create timestamp with correct format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        new_db_path = os.path.join(DB_DIR, f"{timestamp}_train.db")
        
        # Create and update the database
        final_path, was_updated = update_db(new_db_path)
        
        if was_updated:
            return {
                "message": "Database refreshed successfully with new changes",
                "path": final_path,
                "status": "updated"
            }
        else:
            return {
                "message": "Database is already up to date - no changes detected",
                "path": final_path,
                "status": "unchanged"
            }
            
    except Exception as e:
        print(f"Failed to refresh database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh database: {str(e)}")

@app.get("/database/versions")
async def get_database_versions():
    """
    Get all available database files from the DB_DIR directory.
    """
    try:
        db_files = []
        for file in os.listdir(DB_DIR):
            if file.endswith('.db'):
                file_path = os.path.join(DB_DIR, file)
                stats = os.stat(file_path)
                is_current = (os.path.realpath(os.path.join(DB_DIR, DB_PATH)) == 
                            os.path.realpath(file_path)) if os.path.exists(os.path.join(DB_DIR, DB_PATH)) else False
                
                db_files.append({
                    "filename": file,
                    "path": file_path,
                    "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                    "is_current": is_current
                })
        
        # Sort by creation time, newest first
        db_files.sort(key=lambda x: x["created_at"], reverse=True)
        return db_files
    except Exception as e:
        print(f"Error in get_database_versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/labels")
async def get_available_labels():
    """
    Get all available unique labels for each label column in the current version.
    """
    try:
        labels = get_unique_labels(DB_FULL_PATH)
        return labels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get labels: {str(e)}")

@app.get("/trains/names")
async def get_task_names():
    return {"names": list(task_names)}

