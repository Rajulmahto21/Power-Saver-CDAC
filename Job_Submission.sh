#!/bin/bash

declare -A partitions=(
    ["cn001"]="standard"
    ["cn002"]="standard"
    ["cn003"]="standard"
    ["cn005"]="standard"
    ["cn006"]="standard"
)

mkdir -p /scratch/raghuhv/aryan/slurm_out

for node in "${!partitions[@]}"; do
    partition="${partitions[$node]}"
    sbatch --job-name=power_saver_model_${node} \
           --nodes=1 \
           --ntasks-per-node=1 \
           --cpus-per-task=1 \
           --partition="$partition" \
           --time=12:00:00 \
           --nodelist=${node} \
           --output=/scratch/raghuhv/aryan/slurm_out/job_output_${node}.log \
           --error=/scratch/raghuhv/aryan/slurm_out/job_error_${node}.log \
           --wrap="source /scratch/raghuhv/aryan/py/bin/activate && python3 /scratch/raghuhv/Final_Model_March/RAPL_Power_Fetching.py"
    sleep 2
done
