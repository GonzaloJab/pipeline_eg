import os
import paramiko
from datetime import datetime

from functions.create_db import create_dataset_csv

# Create dataset CSVs locally first
def create_dataset_csvs(task,timestamp,sftp,task_dir):

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
            val_path=local_val_csv,
            split_ratio= 0.8,
            sample_percentage=2
        )


        # Create remote paths
        remote_train_csv = os.path.join(task_dir, f'train_{task.name}.csv')
        remote_val_csv = os.path.join(task_dir, f'val_{task.name}.csv')

        # Replace \ with / in remote paths
        remote_train_csv = remote_train_csv.replace('\\', '/')
        remote_val_csv = remote_val_csv.replace('\\', '/')

        # Create remote directory if it doesn't exist
        try:
            sftp.mkdir(task_dir)
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

        # Clean up local files
        os.remove(local_train_csv)
        os.remove(local_val_csv)

        return remote_train_csv, remote_val_csv

def execute_training_cmd(WORKING_DIR,CONDA_HOOK,CONDA_ENV,MLRUNS_DIR,task,remote_train_csv,remote_val_csv,log_path,pid_path,running_tasks):
    # Build the training command
    python_cmd = (
        f"python /media/isend/ssd_storage/1_EYES_TRAIN/train.py "
        f"--GPU {task.gpu} "
        f"--training_name {task.name} "
        f"--model {task.model} --weights {task.weights} "
        f"--train_dataset \"{remote_train_csv}\" "
        f"--val_dataset \"{remote_val_csv}\" "
        f"--remote_mode True "
        f"--remote_dir {MLRUNS_DIR} "
        f"--batch_size {task.batch_size} --epochs {task.epochs} --lr {task.lr} "
        f"--exp_LR_decrease_factor {task.exp_lr_decrease_factor} --step_size {task.step_size} "
        f"--gamma {task.gamma} --solver {task.solver} --momentum {task.momentum} "
        f"--weight_decay {task.weight_decay} --num_workers {task.num_workers} "
        f"--unfreeze_index {9} "
        f"--prefetch_factor {task.prefetch_factor}"
    )

    # Wrap the command with proper shell setup and redirection
    full_cmd = (
        f"cd {WORKING_DIR} && "
        f"source ~/anaconda3/etc/profile.d/conda.sh && "
        f"conda activate {CONDA_ENV} && "
        f"nohup {python_cmd} > \"{log_path}\" 2>&1 & "
        f"echo $! > \"{pid_path}\""
    )
    
    return full_cmd

def execute_testing_cmd(WORKING_DIR,TEST_RESULT_DIR, CONDA_HOOK, CONDA_ENV, task, log_path, pid_path, running_tasks):
    # Build the testing command
    if len(task.weights) > 1 and task.model == 'GAMMA_ARCHI':
        weights_str = f"--gamma_weights {task.weights[0]} {task.weights[1]} {task.weights[2]} {task.weights[3]} {task.weights[4]}"
    else:
        weights_str = f"--weights {task.weights[0]}"
    
    python_cmd = (
        f"python /media/isend/ssd_storage/2_EYES_INFER/inference.py "
        f"--model {task.model} "
        f"--GPU {task.gpu} "
        f"--training_name {task.name} "
        f"--remote_mode True "
        f"{weights_str} "
        f"--data_in {task.test_dataset} "
        f"--output_dir {TEST_RESULT_DIR} "
        f"--batch_size {task.batch_size} "
        f"--num_workers {task.num_workers} "
        f"--prefetch_factor {task.prefetch_factor}"
    )

    # Wrap the command with proper shell setup and redirection
    full_cmd = (
        f"cd {WORKING_DIR} && "
        f"source ~/anaconda3/etc/profile.d/conda.sh && "
        f"conda activate {CONDA_ENV} && "
        f"nohup {python_cmd} > \"{log_path}\" 2>&1 & "
        f"echo $! > \"{pid_path}\""
    )
    
    return full_cmd
        
        
        