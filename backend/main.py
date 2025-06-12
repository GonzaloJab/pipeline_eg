"""Modified FastAPI app to allow remote training and testing launch, PID tracking, stopping tasks, and log streaming via SSH."""
## CMD:  uvicorn main:app --reload


import os
import asyncio
from datetime import datetime
from typing import List, Dict, Union
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
import paramiko
from contextlib import asynccontextmanager, suppress
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import cachetools

from functions.create_db import (
    get_db_versions, 
    create_dataset_csv,
    get_unique_labels,
    check_directories_modified
)
from functions.generate_db import generate_db
from functions.execute_cmds import (
    execute_training_cmd, 
    create_dataset_csvs,
    execute_testing_cmd
)

# Load .env file from the parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'),override=True)



# Update CORS configuration to be more specific
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

'''
Previous CORS config was too permissive
'''
# Constants

SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_KEY = os.getenv("SSH_PRIVATE_KEY_PATH")
CONDA_HOOK = "/home/isend/anaconda3/bin/conda shell.bash hook"
CONDA_ENV = os.getenv("CONDA_ENV", "YOLO")

# Maximum number of tasks that can run simultaneously on each GPU
MAX_TASKS_PER_GPU = 1

# Paths
WORKING_DIR = os.getenv("WORKING_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN")
DB_PATH = os.getenv("DB_PATH", "ISEND_images.db")
DB_DIR = os.getenv("DB_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN/databases")
TRAIN_TASK_BASE_DIR = os.getenv("TRAIN_TASK_BASE_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN/0_remote_runs/train_tasks")
TEST_TASK_BASE_DIR = os.getenv("TEST_TASK_BASE_DIR", "/media/isend/ssd_storage/2_EYES_INFER/0_remote_runs/test_tasks")
MLRUNS_DIR = os.getenv("MLRUNS_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN/0_remote_runs/mlruns")
TEST_RESULT_DIR = os.getenv("TEST_RESULT_DIR", "/media/isend/ssd_storage/2_EYES_INFER/0_remote_runs/test_results")
MAX_TASKS_PER_GPU
# Make sure required directories exist locally
for directory in [TRAIN_TASK_BASE_DIR, TEST_TASK_BASE_DIR, DB_DIR]:
    try:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")
    except Exception as e:
        print(f"Warning: Could not create directory {directory}: {e}")

print(f"Allowed origins: {ALLOWED_ORIGINS}")



# FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up the application...")
    
    # Ensure remote directories exist
    await ensure_remote_directories()

    # Start MLflow server in a separate try block
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

        print("Connected to remote server, checking conda environment...")

        # Kill any existing MLflow processes
        ssh.exec_command("pkill -f mlflow.server:app")
        print("Cleaned up any existing MLflow processes")

        # Ensure directories exist
        mkdir_cmd = f"mkdir -p {MLRUNS_DIR} "
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
            f"--backend-store-uri {MLRUNS_DIR} "
            f"--default-artifact-root {MLRUNS_DIR}/artifacts "
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

# Configure CORS with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add error handling middleware
@app.middleware("http")
async def add_error_handling(request: Request, call_next):
    try:
        # Log the incoming request
        print(f"Incoming request: {request.method} {request.url.path}")
        response = await call_next(request)
        # Log the response
        print(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        print(f"Error handling request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# Models
class BaseTask(BaseModel):
    name: str
    taskType: str
    gpu: str = Field(default="12GB")
    submitted_at: datetime = None

    class Config:
        allow_population_by_field_name = True
        extra = "allow"

class TrainingTask(BaseTask):
    model: str
    weights: str
    datasetType: str
    selectedDatabase: str
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
    train_csv: str = None
    val_csv: str = None

class TestingTask(BaseTask):
    model: str
    weights: list[str] = Field(..., alias="weights")
    test_dataset: str = Field(..., alias="testDataset")
    batch_size: int = Field(..., alias="batchSize")
    num_workers: int = Field(..., alias="numWorkers")
    prefetch_factor: int = Field(..., alias="prefetchFactor")
    gpu: str = Field(default="12GB")

# In-memory task store and queues (now GPU-specific)
tasks: List[Union[TrainingTask, TestingTask]] = []
task_queues = {
    '8GB': asyncio.Queue(),
    '12GB': asyncio.Queue()
}
running_tasks_by_gpu = {
    '8GB': [],
    '12GB': []
}
task_names: set = set()

# Start the worker task when the application starts
@app.on_event("startup")
async def startup_event():
    """Start the worker task when the app starts"""
    print("\n=== Starting FastAPI Application ===")
    print("Starting worker task...")
    asyncio.create_task(worker())
    print("Worker task created")

@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}

# Add cache for task statuses with 5 second TTL
task_status_cache = cachetools.TTLCache(maxsize=1000, ttl=5)

# Add cache for SSH connections
ssh_connection_cache = {
    'client': None,
    'last_used': 0
}

def get_cached_ssh():
    """Get a cached SSH connection or create a new one if expired"""
    current_time = time.time()
    
    # If connection exists and was used in last 30 seconds, reuse it
    if (ssh_connection_cache['client'] and 
        current_time - ssh_connection_cache['last_used'] < 30):
        ssh_connection_cache['last_used'] = current_time
        return ssh_connection_cache['client']
    
    # Close old connection if it exists
    if ssh_connection_cache['client']:
        try:
            ssh_connection_cache['client'].close()
        except:
            pass
    
    # Create new connection
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key, timeout=5)
        
        ssh_connection_cache['client'] = ssh
        ssh_connection_cache['last_used'] = current_time
        return ssh
    except Exception as e:
        print(f"Error creating SSH connection: {e}")
        return None

def determine_task_status(task_dict: dict, ssh_client: paramiko.SSHClient = None) -> dict:
    """Determine task status with caching"""
    task_name = task_dict.get('name', '')
    print(f"\n=== Checking status for task {task_name} ===")
    
    try:
        gpu = task_dict.get('gpu', '12GB')
        print(f"[STATUS] Checking task {task_name} on GPU {gpu}")
        
        # First check if task is in queue for its GPU
        queue_list = list(task_queues[gpu]._queue)
        if any(t.name == task_name for t in queue_list):
            try:
                position = next(i for i, t in enumerate(queue_list) if t.name == task_name) + 1
                print(f"[STATUS] Task {task_name} is in queue at position {position}")
                status = {
                    "status": "queued",
                    "queue_position": position
                }
                return status
            except StopIteration:
                print(f"[STATUS] Could not determine queue position for task {task_name}")
                return {"status": "queued"}
        
        print(f"[STATUS] Task {task_name} not in queue, checking if running")
        
        # Use provided SSH client or get cached one
        should_close_ssh = False
        if not ssh_client:
            print(f"[STATUS] Getting new SSH connection for task {task_name}")
            ssh_client = get_cached_ssh()
            if not ssh_client:
                print(f"[STATUS] Failed to get SSH connection for task {task_name}")
                return {"status": "unknown", "error": "SSH connection failed"}
        
        try:
            task_type = task_dict.get('taskType', '').lower()
            base_dir = TEST_TASK_BASE_DIR if task_type == 'testing' else TRAIN_TASK_BASE_DIR
            task_dir = os.path.join(base_dir, task_name).replace('\\', '/')
            basename = 'test' if task_type=='testing' else 'train'
            log_path = f"{task_dir}/{basename}.log"
            pid_path = f"{task_dir}/{basename}.pid"
            
            print(f"[STATUS] Checking PID file at {pid_path}")
            
            # First check if PID exists and process is running
            _, stdout, _ = ssh_client.exec_command(
                f"if [ -f '{pid_path}' ]; then "
                f"  pid=$(cat '{pid_path}' 2>/dev/null); "
                f"  if [ -n \"$pid\" ] && ps -p $pid > /dev/null; then "
                f"    echo 'RUNNING'; "
                f"  else "
                f"    echo 'NOT_RUNNING'; "
                f"  fi; "
                f"else "
                f"  echo 'NO_PID_FILE'; "
                f"fi"
            )
            process_status = stdout.read().decode().strip()
            print(f"[STATUS] Process status: {process_status}")
            
            # Now check log file content
            _, stdout, _ = ssh_client.exec_command(f"if [ -f '{log_path}' ]; then tail -n 100 '{log_path}' 2>/dev/null; fi")
            log_content = stdout.read().decode().lower()
            print(f"[STATUS] Log file exists: {bool(log_content)}")
            
            # Define patterns for different types of errors
            cuda_error_patterns = [
                "cuda out of memory",
                "cuda runtime error",
                "cuda error",
                "out of memory",
                "gpu 0 has a total capacity"
            ]
            
            general_error_patterns = [
                "error:", 
                "exception:", 
                "traceback", 
                "failed", 
                "assertion error", 
                "runtime error"
            ]
            
            success_patterns = [
                "training completed successfully",
                "testing completed successfully",
                "finished processing all images",
                "completed processing dataset"
            ]
            
            # Check for CUDA/GPU errors first
            if any(pattern in log_content for pattern in cuda_error_patterns):
                print(f"[STATUS] Found CUDA error in task {task_name}")
                error_message = "CUDA/GPU error detected (possibly out of memory)"
                if task_name in running_tasks_by_gpu[gpu]:
                    print(f"[STATUS] Removing crashed task {task_name} from running tasks (CUDA error)")
                    running_tasks_by_gpu[gpu].remove(task_name)
                return {"status": "error", "error": error_message}
            
            # Then check for other errors
            elif any(pattern in log_content for pattern in general_error_patterns):
                print(f"[STATUS] Found general error in task {task_name}")
                error_message = "General error detected in task execution"
                if task_name in running_tasks_by_gpu[gpu]:
                    print(f"[STATUS] Removing crashed task {task_name} from running tasks (general error)")
                    running_tasks_by_gpu[gpu].remove(task_name)
                return {"status": "error", "error": error_message}
            
            # Check for successful completion
            elif any(pattern in log_content for pattern in success_patterns) or (process_status == 'NOT_RUNNING' and log_content and not any(pattern in log_content for pattern in general_error_patterns)):
                print(f"[STATUS] Task {task_name} completed successfully")
                if task_name in running_tasks_by_gpu[gpu]:
                    print(f"[STATUS] Removing completed task {task_name} from running tasks")
                    running_tasks_by_gpu[gpu].remove(task_name)
                return {"status": "completed"}
            
            # Check if task is actually running
            elif process_status == 'RUNNING':
                print(f"[STATUS] Task {task_name} is running")
                return {"status": "running"}
            
            else:
                # If PID file exists but process not running, it's crashed
                if process_status == 'NOT_RUNNING':
                    print(f"[STATUS] Task {task_name} has PID file but not running - crashed")
                    error_message = "Task crashed (PID exists but process not running)"
                    if task_name in running_tasks_by_gpu[gpu]:
                        print(f"[STATUS] Removing crashed task {task_name} from running tasks")
                        running_tasks_by_gpu[gpu].remove(task_name)
                    return {"status": "error", "error": error_message}
                else:
                    print(f"[STATUS] Task {task_name} is idle")
                    return {"status": "idle"}
            
        except Exception as e:
            print(f"[STATUS] Error checking task {task_name} status: {e}")
            return {"status": "unknown", "error": str(e)}
        finally:
            if should_close_ssh:
                ssh_client.close()
                    
    except Exception as e:
        print(f"[STATUS] Error determining status for task {task_name}: {e}")
        return {"status": "unknown", "error": str(e)}

async def worker():
    """Background worker to process tasks from the queue"""
    print("\n=== Worker Started ===")
    while True:
        try:
            print("\n[WORKER] Checking queues...")
            ssh = None
            try:
                # Get a single SSH connection to use for all status checks
                ssh = get_cached_ssh()
                if ssh:
                    # First, check and cleanup completed/errored tasks
                    for gpu in ['12GB', '8GB']:
                        print(f"[WORKER] Checking running tasks on GPU {gpu}")
                        # Create a copy of the list to avoid modification during iteration
                        running_tasks = running_tasks_by_gpu[gpu].copy()
                        for task_name in running_tasks:
                            # Find the task object
                            task_obj = next((t for t in tasks if t.name == task_name), None)
                            if task_obj:
                                try:
                                    status = determine_task_status(task_obj.dict(by_alias=True), ssh)
                                    print(f"[WORKER] Task {task_name} status: {status}")
                                    if status["status"] in ["completed", "error"]:
                                        print(f"[WORKER] Removing completed/errored task {task_name}")
                                        if task_name in running_tasks_by_gpu[gpu]:
                                            running_tasks_by_gpu[gpu].remove(task_name)
                                except Exception as e:
                                    print(f"[WORKER] Error checking task {task_name} status: {e}")
                                    continue
                
                # Now process queues if GPUs are available
                for gpu in ['12GB', '8GB']:
                    try:
                        print(f"[WORKER] Processing queue for GPU {gpu}")
                        print(f"[WORKER] Current running tasks on {gpu}: {running_tasks_by_gpu[gpu]}")
                        print(f"[WORKER] Queue size for {gpu}: {task_queues[gpu].qsize()}")
                        
                        # Skip if queue is empty
                        if task_queues[gpu].empty():
                            print(f"[WORKER] Queue empty for GPU {gpu}")
                            continue
                            
                        # Check if we can run more tasks on this GPU
                        if len(running_tasks_by_gpu[gpu]) >= MAX_TASKS_PER_GPU:
                            print(f"[WORKER] Maximum tasks ({MAX_TASKS_PER_GPU}) already running on GPU {gpu}")
                            continue
                        
                        # Get next task
                        print(f"[WORKER] Getting next task from GPU {gpu} queue")
                        task = await task_queues[gpu].get()
                        if not task:
                            print(f"[WORKER] Got None task from queue for GPU {gpu}")
                            continue
                            
                        print(f"[WORKER] Processing task {task.name} for GPU {gpu}")
                        
                        try:
                            # Run the task
                            print(f"[WORKER] Attempting to run task {task.name}")
                            success = await run_remote_task(task)
                            if success:
                                print(f"[WORKER] Successfully started task {task.name}")
                            else:
                                print(f"[WORKER] Failed to start task {task.name}")
                                # Put task back in queue if it failed to start
                                await task_queues[gpu].put(task)
                                print(f"[WORKER] Put task {task.name} back in queue")
                        except Exception as e:
                            print(f"[WORKER] Error running task {task.name}: {e}")
                            # Remove from running tasks if there was an error
                            if task.name in running_tasks_by_gpu[gpu]:
                                running_tasks_by_gpu[gpu].remove(task.name)
                                print(f"[WORKER] Removed failed task {task.name} from running tasks")
                            # Put task back in queue
                            await task_queues[gpu].put(task)
                            print(f"[WORKER] Put task {task.name} back in queue after error")
                    except Exception as e:
                        print(f"[WORKER] Error processing queue for GPU {gpu}: {e}")
                        continue
                        
            except Exception as e:
                print(f"[WORKER] Error in worker loop: {e}")
            finally:
                # Don't close cached SSH connection
                pass
                
        except Exception as e:
            print(f"[WORKER] Worker loop error: {e}")
        
        print("[WORKER] Sleeping for 5 seconds...")
        await asyncio.sleep(5)  # Check every 5 seconds

async def run_remote_task(task: Union[TrainingTask, TestingTask]):
    ssh = None
    try:
        print(f"\n=== Starting execution of task {task.name} ===")
        # get timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Determine task directory based on task type
        base_dir = TEST_TASK_BASE_DIR if isinstance(task, TestingTask) else TRAIN_TASK_BASE_DIR
        task_dir = os.path.join(base_dir, task.name).replace('\\', '/')
        os.makedirs(task_dir, exist_ok=True)
        print(f"[EXEC] Created local task directory: {task_dir}")

        # Define task-specific paths
        file_prefix = 'test' if isinstance(task, TestingTask) else 'train'
        log_path = f"{task_dir}/{file_prefix}.log"
        pid_path = f"{task_dir}/{file_prefix}.pid"

        print(f"[EXEC] Setting up SSH connection for task {task.name}")
        # Setup SSH connection
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)
        sftp = ssh.open_sftp()

        # Create remote task directory
        remote_task_dir = os.path.join(base_dir, task.name).replace('\\', '/')
        print(f"[EXEC] Creating remote task directory: {remote_task_dir}")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p '{remote_task_dir}' {TEST_RESULT_DIR}")
        
        err = stderr.read().decode()
        if err:
            raise Exception(f"Failed to create remote directory: {err}")

        # Add task to running tasks list if not already there
        gpu = task.gpu
        if task.name not in running_tasks_by_gpu[gpu]:
            running_tasks_by_gpu[gpu].append(task.name)
            print(f"[EXEC] Added task {task.name} to running tasks for GPU {gpu}")
        print(f"[EXEC] Current running tasks on GPU {gpu}: {running_tasks_by_gpu[gpu]}")

        # Execute the task based on its type
        if isinstance(task, TestingTask):
            print(f"[EXEC] Preparing testing command for task {task.name}")
            command = execute_testing_cmd(
                WORKING_DIR=WORKING_DIR,
                TEST_RESULT_DIR=TEST_RESULT_DIR,
                CONDA_HOOK=CONDA_HOOK,
                CONDA_ENV=CONDA_ENV,
                task=task,
                log_path=log_path,
                pid_path=pid_path,
                running_tasks=running_tasks_by_gpu[gpu]
            )
        else:
            print(f"[EXEC] Preparing training command for task {task.name}")
            remote_train_csv, remote_val_csv = create_dataset_csvs(task,timestamp,sftp,remote_task_dir)
            command = execute_training_cmd(
                WORKING_DIR,
                CONDA_HOOK,
                CONDA_ENV,
                MLRUNS_DIR,
                task,
                remote_train_csv,remote_val_csv,log_path,pid_path,running_tasks_by_gpu[gpu])

        print(f"[EXEC] Executing command for task {task.name}:\n{command}")
        stdin, stdout, stderr = ssh.exec_command(f"setsid bash -c '{command}' </dev/null >/dev/null 2>&1 & disown")
        error = stderr.read().decode()
        
        if error:
            print(f"[EXEC] Error starting task {task.name}: {error}")
            raise Exception(f"Failed to start task: {error}")

        print(f"[EXEC] Waiting for task {task.name} to start...")
        await asyncio.sleep(1)

        # Verify the process started by checking PID file
        _, stdout, _ = ssh.exec_command(f"if [ -f '{pid_path}' ]; then cat '{pid_path}'; fi")
        pid = stdout.read().decode().strip()
        if not pid:
            print(f"[EXEC] No PID file found for task {task.name}")
            raise Exception("PID file not created - task may have failed to start")
            
        # Verify process is running
        _, stdout, _ = ssh.exec_command(f"ps -p {pid} > /dev/null && echo 'RUNNING'")
        if "RUNNING" not in stdout.read().decode():
            print(f"[EXEC] Process {pid} not running for task {task.name}")
            raise Exception(f"Process {pid} not running after start")

        print(f"[EXEC] Successfully started task {task.name} with PID {pid}")
        return True

    except Exception as e:
        print(f"[EXEC] Error during task execution for {task.name}: {e}")
        gpu = task.gpu
        if task.name in running_tasks_by_gpu[gpu]:
            running_tasks_by_gpu[gpu].remove(task.name)
            print(f"[EXEC] Removed failed task {task.name} from running tasks for GPU {gpu}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if ssh:
            ssh.close()

# Get task statuses
async def get_training_task_statuses():
    statuses = {}
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)
        task_dir = os.path.join(TRAIN_TASK_BASE_DIR, task.name).replace('\\', '/')

        for task in tasks:
            log_file = os.path.join(task_dir, "train.log")
            pid_file = os.path.join(task_dir, "train.pid")

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

@app.post("/trains/stop/{task_name}")
async def stop_task(task_name: str):
    """Stop a task by its name"""
    try:
        # Find task by name
        task = next((t for t in tasks if t.name == task_name), None)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with name {task_name} not found")

        # Determine task directory based on task type
        task_type = task.taskType.lower() if hasattr(task, 'taskType') else 'training'
        base_dir = TEST_TASK_BASE_DIR if task_type == 'testing' else TRAIN_TASK_BASE_DIR
        task_dir = os.path.join(base_dir, task_name).replace('\\', '/')
        basename = 'test' if task_type == 'testing' else 'train'
        pid_file = f"{task_dir}/{basename}.pid"
        log_file = f"{task_dir}/{basename}.log"

        print(f"[STOP] Attempting to stop task {task_name} (Type: {task_type})")
        print(f"[STOP] Looking for PID file at: {pid_file}")

        try:
            key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

            # Check if PID file exists and get PID
            _, stdout, _ = ssh.exec_command(f"test -f '{pid_file}' && cat '{pid_file}'")
            pid = stdout.read().decode().strip()
            
            if not pid:
                print(f"[STOP] No PID file found for task {task_name}")
                raise HTTPException(status_code=404, detail="PID file not found")

            print(f"[STOP] Found PID {pid} for task {task_name}")
            
            # Kill the ENTIRE process tree
            kill_cmd = f"""
                # Kill the entire process group
                PGID=$(ps -o pgid= {pid} | grep -o '[0-9]*')
                if [ -n "$PGID" ]; then
                    kill -9 -"$PGID" 2>/dev/null || true
                else
                    kill -9 {pid} 2>/dev/null || true
                fi
                
                # Verify process is gone and clean up files
                if ! ps -p {pid} >/dev/null 2>&1; then
                    rm -f '{pid_file}' '{log_file}' 2>/dev/null || true
                    echo "SUCCESS"
                else
                    echo "FAILED_TO_KILL"
                fi
            """

            _, stdout, stderr = ssh.exec_command(kill_cmd)
            result = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                print(f"[STOP] Error while stopping task: {error}")
            
            if result == "SUCCESS":
                print(f"[STOP] Successfully stopped task {task_name}")
                # Remove from running tasks if it was running
                gpu = task.gpu
                if task_name in running_tasks_by_gpu[gpu]:
                    running_tasks_by_gpu[gpu].remove(task_name)
                    print(f"[STOP] Removed task {task_name} from running tasks on GPU {gpu}")
                return {"message": f"Task '{task_name}' stopped successfully"}
            else:
                print(f"[STOP] Failed to stop task {task_name}")
                raise HTTPException(status_code=500, detail="Failed to stop task process")

        except Exception as e:
            print(f"[STOP] Error stopping task {task_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            if 'ssh' in locals():
                ssh.close()

    except Exception as e:
        print(f"[STOP] Error in stop_task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trains/logs/{task_name}")
async def stream_logs(task_name: str):
    task_dir = os.path.join(TRAIN_TASK_BASE_DIR, task_name).replace('\\', '/')
    log_path = f"{task_dir}/train.log"

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

@app.get("/trains")
async def get_tasks(
    page: int = 1,
    page_size: int = 10,
    status: str = None
):
    """Get tasks with pagination and optional status filter"""
    try:
        print(f"Handling GET /trains request - page {page}, size {page_size}")
        
        # Filter tasks if status is provided
        filtered_tasks = tasks
        if status:
            filtered_tasks = [t for t in tasks if determine_task_status(t.dict(by_alias=True))["status"] == status]
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_tasks = filtered_tasks[start_idx:end_idx]
        
        # Get current queue lists for position information
        queue_lists = {
            gpu: list(queue._queue) 
            for gpu, queue in task_queues.items()
        }
        
        # Use a single SSH connection for all tasks
        result = []
        ssh = get_cached_ssh()
        
        if not ssh:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "SSH connection failed",
                    "tasks": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0
                }
            )
        
        try:
            for task in paginated_tasks:
                task_dict = task.dict(by_alias=True)
                status_info = determine_task_status(task_dict, ssh)
                
                if status_info["status"] == "queued":
                    gpu = task_dict.get('gpu', '12GB')
                    try:
                        position = next(i for i, t in enumerate(queue_lists[gpu]) if t.name == task_dict["name"]) + 1
                        status_info["queue_position"] = position
                    except StopIteration:
                        pass
                    
                task_dict.update(status_info)
                task_dict["id"] = task_dict["name"]  # Use task name as ID
                result.append(task_dict)
        finally:
            # Don't close the cached SSH connection
            pass
        
        return {
            "tasks": result,
            "total": len(filtered_tasks),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(filtered_tasks) + page_size - 1) // page_size
        }
        
    except Exception as e:
        print(f"Error in get_tasks: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "tasks": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        )

@app.get("/trains/queue")
async def get_queued_tasks():
    return [task.name for task in tasks if task.name not in running_tasks_by_gpu['12GB'] and task.name not in running_tasks_by_gpu['8GB']]

@app.get("/trains/running")
async def get_running_tasks():
    return running_tasks_by_gpu['12GB'] + running_tasks_by_gpu['8GB']

@app.post("/tasks", response_model=Union[TrainingTask, TestingTask])
async def create_task(task_dict: dict):
    """Create a new task with a unique ID"""
    try:
        task_name = task_dict.get("name")
        if not task_name:
            raise HTTPException(
                status_code=400,
                detail="Task name is required"
            )
            
        if task_name in task_names:
            raise HTTPException(
                status_code=400,
                detail=f"Task name '{task_name}' already exists. Please choose a different name."
            )
        
        # Generate a unique ID for the task
        task_dict['id'] = len(tasks)  # Use length as ID since we never delete tasks from the list
        
        # Create the appropriate task type based on taskType
        if task_dict["taskType"] == "testing":
            task = TestingTask(**task_dict)
        else:
            task = TrainingTask(**task_dict)
    
        if task.submitted_at is None:
            task.submitted_at = datetime.utcnow()
        
        task_names.add(task_name)
        tasks.append(task)
        
        print(f"Created new task: {task_name} (Type: {task_dict['taskType']}, GPU: {task_dict.get('gpu', '12GB')})")
        return task
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if task_name in task_names:
            task_names.remove(task_name)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/trains/{task_id}/run")
async def run_task(task_id: str):
    """Run a task by its name"""
    try:
        print(f"\n=== Attempting to run task {task_id} ===")
        # Find task by name
        task = next((t for t in tasks if t.name == task_id), None)
                
        if not task:
            print(f"[RUN] Task with name {task_id} not found")
            raise HTTPException(status_code=404, detail=f"Task with name {task_id} not found")
        
        gpu = task.gpu
        task_name = task.name
        print(f"[RUN] Found task {task_name} for GPU {gpu}")
        
        # Check if task is already in queue for its GPU
        queue_list = list(task_queues[gpu]._queue)
        position = None
        if any(t.name == task_name for t in queue_list):
            try:
                position = next(i for i, t in enumerate(queue_list) if t.name == task_name) + 1
            except StopIteration:
                position = -1
                
            print(f"[RUN] Task {task_name} is already in queue at position {position}")
            return {
                "message": f"Task '{task_name}' is already in queue for GPU {gpu}",
                "task_id": task_name,
                "task_name": task_name,
                "status": "queued",
                "queue_position": position
            }
        
        # Check if task is already running on its GPU
        if task_name in running_tasks_by_gpu[gpu]:
            print(f"[RUN] Task {task_name} is already running on GPU {gpu}")
            return {
                "message": f"Task '{task_name}' is already running on GPU {gpu}",
                "task_id": task_name,
                "task_name": task_name,
                "status": "running"
            }
        
        # Add to appropriate GPU queue
        print(f"[RUN] Adding task {task_name} to queue for GPU {gpu}")
        await task_queues[gpu].put(task)
        
        # Get position in queue
        queue_list = list(task_queues[gpu]._queue)
        try:
            position = next(i for i, t in enumerate(queue_list) if t.name == task_name) + 1
        except StopIteration:
            position = -1
        
        print(f"[RUN] Added task {task_name} to queue for GPU {gpu} at position {position}")
        return {
            "message": f"Task '{task_name}' queued successfully for GPU {gpu}",
            "task_id": task_name,
            "task_name": task_name,
            "status": "queued",
            "queue_position": position
        }
    except Exception as e:
        print(f"[RUN] Error queueing task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue task: {str(e)}"
        )

@app.delete("/trains/{task_id}")
async def delete_task(task_id: str):
    """Delete a task by its name"""
    # Find task by name
    task = next((t for t in tasks if t.name == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_type = task.taskType.lower() if hasattr(task, 'taskType') else 'training'
    base_dir = TEST_TASK_BASE_DIR if task_type == 'testing' else TRAIN_TASK_BASE_DIR
    task_dir = os.path.join(base_dir, task.name).replace('\\', '/')
    
    try:
        # Connect to remote machine
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)
        
        print(f"Removing task directory: {task_dir}")
        # Remove the entire task directory
        ssh.exec_command(f"rm -rf '{task_dir}'")
        
        # If task is in running_tasks list, remove it
        gpu = task.gpu
        if task.name in running_tasks_by_gpu[gpu]:
            running_tasks_by_gpu[gpu].remove(task.name)
            
        # Remove from task_names set
        if task.name in task_names:
            task_names.remove(task.name)
            
        # Remove from tasks list
        tasks.remove(task)
            
    except Exception as e:
        print(f"Error cleaning up files: {e}")
    finally:
        if 'ssh' in locals():
            ssh.close()
    
    return {"status": "success", "message": f"Task {task.name} deleted successfully"}

@app.get("/trains/csv-files")
async def get_csv_files():
    """
    Get list of available CSV files for testing.
    """
    try:
        csv_files = []
        # Check both training and testing directories for CSV files
        directories = [TRAIN_TASK_BASE_DIR, TEST_TASK_BASE_DIR]
        
        for directory in directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith('.csv'):
                        # Get relative path from the base directory
                        full_path = os.path.join(root, file)
                        csv_files.append(full_path)
        
        return csv_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list CSV files: {str(e)}")

# Create a scheduler
scheduler = AsyncIOScheduler()

async def scheduled_database_refresh():
    """
    Function that will be called by the scheduler to check and refresh the database.
    """
    try:
        print("Running scheduled database refresh check...")
        await refresh_database()
    except Exception as e:
        print(f"Scheduled refresh failed: {e}")

@app.on_event("startup")
async def start_scheduler():
    """Start the scheduler when the app starts"""
    try:
        # Schedule the database refresh for 3 AM every day
        scheduler.add_job(
            scheduled_database_refresh,
            CronTrigger(hour=3, minute=0),
            id='database_refresh'
        )
        scheduler.start()
        print("Scheduled database refresh job for 3 AM daily")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

@app.on_event("shutdown")
async def stop_scheduler():
    """Stop the scheduler when the app shuts down"""
    scheduler.shutdown()

@app.post("/database/refresh")
async def refresh_database():
    """
    Check if the database needs to be refreshed by comparing directory hashes,
    and only create a new version if changes are detected.
    """
    try:
        # Get base directory from environment variable or use default
        base_dir = os.getenv("TRAIN_DATA_DIR", "Z:/2_TRAIN_DATA")
        
        # Use the list of directories relative to base_dir
        directories = [
            os.path.join(base_dir, "3_PvsM"),
            os.path.join(base_dir, "4_PUNCT"),
            os.path.join(base_dir, "5_MULT")
        ]
        
        # Check if directories exist
        for directory in directories:
            if not os.path.exists(directory):
                raise HTTPException(
                    status_code=500,
                    detail=f"Directory not found: {directory}. Please check if the paths are correct and accessible."
                )
        
        print(f"Checking directories: {directories}")
        was_modified, details = check_directories_modified(directories, DB_DIR)

        if not was_modified:
            return {
                "message": "Database is already up to date - no changes detected",
                "status": "unchanged",
                "details": details
            }

        print(f"Detected changes, creating new database version")
        # If we detected changes, create a new database version
        timestamp = datetime.now().strftime('%d-%m-%Y(%M)')
        new_db_path = os.path.join(DB_DIR, f"train_images_{timestamp}.db")
        
        # Create and update the database
        generate_db(new_db_path)
        
        return {
            "message": "Database refreshed successfully with new changes",
            "status": "updated",
            "path": new_db_path,
            "details": details
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh database: {str(e)}"
        )

@app.get("/trains/database/versions")
async def get_database_versions():
    """
    Get all available database files from the DB_DIR directory.
    """
    print("Handling database versions request")
    try:
        db_files = []
        for file in os.listdir(DB_DIR):
            if file.endswith('.db'):
                file_path = os.path.join(DB_DIR, file)
                stats = os.stat(file_path)
                
                db_files.append({
                    "filename": file,
                    "path": file_path,
                    "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat()
                })
        
        # Sort by creation time, newest first
        db_files.sort(key=lambda x: x["created_at"], reverse=True)
        print(f"Found {len(db_files)} database files")
        return db_files
    except Exception as e:
        print(f"Error in get_database_versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/labels")
async def get_database_labels():
    """
    Get all available unique labels for each label column in the current version.
    """
    try:
        # Get the most recent database file
        db_files = []
        for file in os.listdir(DB_DIR):
            if file.endswith('.db'):
                file_path = os.path.join(DB_DIR, file)
                stats = os.stat(file_path)
                db_files.append((file_path, stats.st_ctime))
        
        if not db_files:
            raise HTTPException(status_code=404, detail="No database files found")
        
        # Sort by creation time and get the most recent
        db_files.sort(key=lambda x: x[1], reverse=True)
        latest_db = db_files[0][0]
        
        # Connect to the database
        conn = sqlite3.connect(latest_db)
        cursor = conn.cursor()
        
        # Get all unique values for each label column
        labels = {}
        
        # Get all columns from the images table
        cursor.execute("PRAGMA table_info(images)")
        columns = cursor.fetchall()
        
        # For each column that ends with '_label'
        for col in columns:
            col_name = col[1]
            if col_name.endswith('_label'):
                cursor.execute(f"SELECT DISTINCT {col_name} FROM images WHERE {col_name} IS NOT NULL")
                unique_values = [row[0] for row in cursor.fetchall()]
                labels[col_name] = unique_values
        
        conn.close()
        return labels
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trains/names")
async def get_task_names():
    return {"names": list(task_names)}

async def ensure_remote_directories():
    """Ensure all required directories exist on the remote machine"""
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)

        # Create all required directories
        directories = [TRAIN_TASK_BASE_DIR]
        for directory in directories:
            ssh.exec_command(f"mkdir -p '{directory}'")
            print(f"Ensured remote directory exists: {directory}")

    except Exception as e:
        print(f"Warning: Could not create remote directories: {e}")
    finally:
        if 'ssh' in locals():
            ssh.close()
