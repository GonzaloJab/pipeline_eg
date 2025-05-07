"""Modified FastAPI app to allow remote training launch, PID tracking, stopping tasks, and log streaming via SSH."""
## CMD:  uvicorn main:app --reload


import os
import asyncio
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import paramiko
from contextlib import asynccontextmanager, suppress

# Load .env file from the parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Constants
LOG_PATH = os.getenv("LOG_PATH", "/media/isend/ssd_storage/1_EYES_TRAIN/remote_runs/logs")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "None").split(",")
SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_KEY = os.getenv("SSH_PRIVATE_KEY_PATH")
CONDA_HOOK = "/home/isend/anaconda3/bin/conda shell.bash hook"
CONDA_ENV = os.getenv("CONDA_ENV", "YOLO")
WORKING_DIR= os.getenv("WORKING_DIR", "/media/isend/ssd_storage/1_EYES_TRAIN/remote_runs")

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TrainingTask(BaseModel):
    name: str
    model: str
    weights: str
    data_in: str = Field(..., alias="dataIn")
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

    class Config:
        allow_population_by_field_name = True
        extra = "allow"

# In-memory task store and queue
tasks: List[TrainingTask] = []
task_queue = asyncio.Queue()
running_tasks: List[str] = []

# Run command via SSH
async def run_remote_training(task: TrainingTask):
    log_path = os.path.join(LOG_PATH, f"train_{task.name}.log")
    pid_path = os.path.join(LOG_PATH, f"train_{task.name}.pid")

    python_cmd = (
    # CHANGE WORKING DIRECTORY
        f"cd {WORKING_DIR} && "    
    # RUN SCRIPT    
        f"nohup python /media/isend/ssd_storage/1_EYES_TRAIN/train.py "
        f"--model {task.model} --weights {task.weights} "
        f"--data_in \"{task.data_in}\" --output_dir \"{task.output_directory}\" "
        f"--batch_size {task.batch_size} --epochs {task.epochs} --lr {task.lr} "
        f"--exp_LR_decrease_factor {task.exp_lr_decrease_factor} --step_size {task.step_size} "
        f"--gamma {task.gamma} --solver {task.solver} --momentum {task.momentum} "
        f"--weight_decay {task.weight_decay} --num_workers {task.num_workers} "
        f"--unfreeze_index {9} "
        f"--prefetch_factor {task.prefetch_factor} > \"{log_path}\" 2>&1 & "
        f"echo $! > \"{pid_path}\""
        #f"sleep 2 && ps -eo pid,cmd | grep '[p]ython.*train.py' | awk '{{print $1}}' > \"{pid_path}\""
    )

    full_cmd = f"bash -l -c 'eval \"$({CONDA_HOOK})\" && conda activate {CONDA_ENV} && {python_cmd} '"
    print(f"Executing command: {full_cmd}")
    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, pkey=key)
        ssh.exec_command(full_cmd)
        ssh.close()
        if task.name not in running_tasks:
            running_tasks.append(task.name)
    except Exception as e:
        print(f"SSH command failed: {e}")
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(worker())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

app.router.lifespan_context = lifespan

@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}

@app.get("/trains", response_model=List[dict])
async def get_tasks():
    result = []
    for task in tasks:
        status = determine_task_status(task.name)
        task_dict = task.dict(by_alias=True)
        task_dict["status"] = status
        result.append(task_dict)
    return result

@app.get("/trains/queue")
async def get_queued_tasks():
    return [task.name for task in tasks if task.name not in running_tasks]

@app.get("/trains/running")
async def get_running_tasks():
    return running_tasks

@app.post("/trains", response_model=TrainingTask)
async def create_task(task: TrainingTask):
    if task.submitted_at is None:
        task.submitted_at = datetime.utcnow()
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
    return tasks.pop(task_id)
