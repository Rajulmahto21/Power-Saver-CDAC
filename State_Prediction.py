import warnings
warnings.filterwarnings("ignore", category=Warning)
import os
warnings.filterwarnings("ignore", category=Warning)
import pandas as pd
import joblib
import subprocess

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from prettytable import PrettyTable



logs_folder = r'/scratch/raghuhv/Final_Model_March/logs'
models_folder = 'models'

if not os.path.exists(models_folder):
    os.makedirs(models_folder)

def get_node_info():
    node_info_output = subprocess.check_output(["sinfo", "-N", "-o", "%N %P %20T"]).decode("utf-8")
    lines = node_info_output.splitlines()[1:]  # Skip the header line
    data = []
    for line in lines:
        fields = line.split()
        node_name = fields[0]
        partition_name = fields[1]
        node_state = fields[2]
        if partition_name == "standard*":
            data.append({
                "NODE_NAME": node_name,
                "PARTITION": partition_name,
                "STATE": node_state
            })
    return data

# idle nodes only for standard partition
node_info = get_node_info()
df = pd.DataFrame(node_info)
idle_nodes = list(df[df['STATE'] == 'idle']["NODE_NAME"])

warnings.filterwarnings("ignore", category=Warning)
for i, log_file in enumerate(os.listdir(logs_folder)):
    warnings.filterwarnings("ignore", category=Warning)
    if log_file.endswith('.log'):
        node_name = os.path.splitext(log_file)[0]
        log_path = os.path.join(logs_folder, log_file)

        if (node_name in idle_nodes):
            slurm_state = "IDLE"
            slurm_state_bin = 1
        else:
            slurm_state = "RESERVED"
            slurm_state_bin = 0

        table = PrettyTable(['Node Name', 'Partition', 'Predicted State', 'Slurm State', 'Suggested Node State'])

        dataset = pd.read_csv(log_path, sep='|', header=None, names=['Timestamp', 'CPU_Usage_Percentage', 'CPU_Clock_Speed', 'CPU_Core_Counts', 'CPU_Temperature', 'RAM_Usage_Percentage', 'Disk_Usage', 'Disk_Read', 'Disk_Write_Speed', 'Power_Watts'])

        dataset['CPU_Usage_Percentage'] = dataset['CPU_Usage_Percentage'].str.extract(r'(\d+\.\d+)').astype(float)
        dataset['CPU_Core_Counts'] = dataset['CPU_Core_Counts'].str.extract(r'(\d+)').astype(int)
        dataset['CPU_Temperature'] = dataset['CPU_Temperature'].str.extract(r'(\d+\.\d+)').astype(float)
        dataset['RAM_Usage_Percentage'] = dataset['RAM_Usage_Percentage'].str.extract(r'(\d+\.\d+)').astype(float)
        dataset['Disk_Usage'] = dataset['Disk_Usage'].str.extract(r'(\d+\.\d+)').astype(float)
        dataset['Disk_Read'] = dataset['Disk_Read'].str.extract(r'(\d+\.\d+)').astype(float)
        dataset['Disk_Write_Speed'] = dataset['Disk_Write_Speed'].str.extract(r'(\d+\.\d+)').astype(float)
        dataset['Power_Watts'] = dataset['Power_Watts'].str.extract(r'(\d+\.\d+)').astype(float)
        dataset['CPU_Clock_Speed'] = dataset['CPU_Clock_Speed'].str.extract(r'(\d+\.\d+)').astype(float)

        dataset['Timestamp'] = pd.to_datetime(dataset['Timestamp'].str.strip())

        dataset.to_csv('Major_dataset.csv', index=False)

        path = "Major_dataset.csv"

        df = pd.read_csv(path)

        df2= df.copy()

        df_copy = df.drop(columns=['Timestamp']).copy()

        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_copy)

        warnings.filterwarnings("ignore", category=Warning)
        kmeans = KMeans(n_clusters=2)  
        kmeans_clusters = kmeans.fit_predict(df_scaled)

        df_copy['kmeans_class'] = kmeans_clusters
        df2['kmeans_class'] = kmeans_clusters

        df2.to_csv('WithClass.csv', index=False)

        df = pd.read_csv("WithClass.csv")

        df.index = pd.to_datetime(df['Timestamp'])

        train_size = int(len(df) * 0.71)
        train, test = df[0:train_size], df[train_size:len(df)]

        warnings.filterwarnings("ignore", category=Warning)
        model = ARIMA(train['kmeans_class'], order=(5,1,0))
        warnings.filterwarnings("ignore", category=Warning)
        model_fit = model.fit()
        warnings.filterwarnings("ignore", category=Warning)
        model_filename = os.path.join(models_folder, f"{node_name}.pkl")
        joblib.dump(model_fit, model_filename)
        warnings.filterwarnings("ignore", category=Warning)
        forecast = model_fit.forecast(steps=7200)
        warnings.filterwarnings("ignore", category=Warning)
        values = forecast.value_counts().to_dict()
        if len(values) == 1:
            if int(forecast.iloc[1]) == 0:
                state = "WAKE"
                model_pred_state_bin = 0
            else:
                state = "SLEEP"
                model_pred_state_bin = 1
        else:
            ft = forecast.tolist()
            prev_state = 1.0
            for i in range(len(ft)):
                if ft[i] == 0.0:
                    if prev_state != 0.0:
                        if 0.0 in ft[i+1:i+1801]:
                            state = "WAKE"
                        elif 0.0 in ft[i+1:i+7201]:
                            state = "HIBERNATE"
                        else:
                            state = "SLEEP"
                    prev_state = 0.0
                else:
                    prev_state = 1.0

        if(slurm_state_bin == 1 and model_pred_state_bin == 0):
            suggested_final_node_state = 1
            print_suggested_final_node_state = "SLEEP"
        else:
            suggested_final_node_state = slurm_state_bin and model_pred_state_bin
            if(suggested_final_node_state):
                print_suggested_final_node_state = "SLEEP"
            else:
                print_suggested_final_node_state = "WAKE"

        
        
        table.add_row([node_name, "standard", state, slurm_state, print_suggested_final_node_state])
        print(table)

print("All models trained and saved.")
