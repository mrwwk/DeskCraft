import time
import subprocess
import torch
import threading

def get_gpu_utilization(gpu_id):
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits', '-i', str(gpu_id)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error querying GPU {gpu_id} utilization: {result.stderr}")
            return None
        utilization = int(result.stdout.strip())
        return utilization
    except Exception as e:
        print(f"Exception occurred while querying GPU {gpu_id} utilization: {e}")
        return None

def tensor_multiplication(gpu_id):
    while not stop_tensor_multiplication[gpu_id]:
        a = torch.randn(1000, 2000, device=f'cuda:{gpu_id}')
        b = torch.randn(2000, 1000, device=f'cuda:{gpu_id}')
        c = torch.matmul(a, b)
        # print(a.device, b.device, c.device)
        # print(c.shape)
        # time.sleep(0.1)  # Small sleep to prevent 100% utilization

def monitor_gpu(gpu_id):
    global stop_tensor_multiplication
    tensor_thread = None
    low_utilization_counter = 0

    while True:
        utilization = get_gpu_utilization(gpu_id)
        if utilization is not None:
            # print(f"GPU {gpu_id} Utilization: {utilization}%")
            if utilization < 10:
                low_utilization_counter += 1
            else:
                low_utilization_counter = 0

            if low_utilization_counter >= 1 and (tensor_thread is None or not tensor_thread.is_alive()):
                stop_tensor_multiplication[gpu_id] = False
                tensor_thread = threading.Thread(target=tensor_multiplication, args=(gpu_id,))
                tensor_thread.start()
                # print('started', gpu_id)
            elif utilization > 20 and tensor_thread is not None and tensor_thread.is_alive():
                stop_tensor_multiplication[gpu_id] = True
                tensor_thread.join()
                tensor_thread = None
                # print('end', gpu_id)

        time.sleep(1)

if __name__ == "__main__":
    stop_tensor_multiplication = [False] * 8
    monitor_threads = []

    for gpu_id in range(8):
        monitor_thread = threading.Thread(target=monitor_gpu, args=(gpu_id,))
        monitor_threads.append(monitor_thread)
        monitor_thread.start()

    for monitor_thread in monitor_threads:
        monitor_thread.join()
