#!/bin/bash
echo "--------------------------------------------"
echo "Installing Stream Processing Platform"
echo "--------------------------------------------"
echo "--------------------------------------------"
echo "Requirements"
echo "--------------------------------------------"
apt update
apt install snapd
sudo apt install pkg-config
sudo apt install libsystemd-dev
mkdir -p /opt/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /opt/miniconda3/miniconda.sh
bash /opt/miniconda3/miniconda.sh -b -u -p /opt/miniconda3
source /opt/miniconda3/etc/profile.d/conda.sh

# Add Conda-Forge channel for package installation
conda config --add channels conda-forge
conda config --set channel_priority strict

# Create a conda environment with Python 3.6
echo "Creating Conda environment with Python 3.6..."
conda create --name myenv python=3.6 -y

# Activate the environment
echo "Activating the conda environment 'myenv'..."
conda activate myenv

echo "Installing Python dependencies"
pip install -r requirements.txt
snap install helm --classic
echo "--------------------------------------------"
echo "RabbitMQ"
echo "--------------------------------------------"
helm repo add stable https://charts.helm.sh/stable
sudo mkdir -p /root/.kube
sudo cp /etc/rancher/k3s/k3s.yaml /root/.kube/config
kubectl create namespace rabbit
helm install mu-rabbit stable/rabbitmq --namespace rabbit --set rabbitmqVhost=streams
kubectl wait --namespace rabbit --for condition=ready pod/mu-rabbit-rabbitmq-0 --timeout=120s
kubectl expose -n rabbit pod mu-rabbit-rabbitmq-0 --port=15672 --target-port=15672 --name=loadbalancer --type=LoadBalancer
echo "--------------------------------------------"
echo "NodeRED"
echo "--------------------------------------------"
mkdir /opt/NodeRED
kubectl apply -f nodered-namespace.yaml
kubectl apply -f nodered-pv.yaml
kubectl apply -f nodered-pvc.yaml
kubectl apply -f nodered-deployment.yaml
name=$(kubectl get pods -n gui -o jsonpath='{.items[0].metadata.name}')
kubectl wait --namespace gui --for condition=ready pod/$name --timeout=120s
kubectl expose -n gui pod  $name --port=1880 --target-port=1880 --name=loadbalancer --type=LoadBalancer
nodered_ip=$(kubectl get pod $name -n gui -o jsonpath='{.status.podIP}')
sleep 60
curl -XPUT -H "Content-type: application/json" --data-binary "@main-subflow.json" "http://${nodered_ip}:1880/flow/global"
echo "--------------------------------------------"
echo "KEDA"
echo "--------------------------------------------"
# Without admission webhooks
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0-core.yaml
echo "--------------------------------------------"
echo "Instance Manager"
echo "--------------------------------------------"
RABBITMQ_USERNAME="user"
RABBITMQ_PASSWORD=$(kubectl get secret mu-rabbit-rabbitmq --namespace rabbit -o jsonpath='{.data.rabbitmq-password}' | base64 --decode)
# Create .env file and store the credentials
pod_ip=$(kubectl get pod mu-rabbit-rabbitmq-0 -n rabbit -o jsonpath='{.status.podIP}')
cd ..
cd instancemanager
echo "RABBITMQ_USERNAME=$RABBITMQ_USERNAME" > .env
echo "RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD" >> .env
if [ -n "$pod_ip" ]; then
    # Create .env file and store the pod IP address
    echo "POD_IP=$pod_ip" >> .env
    echo "Pod IP Address found: $pod_ip"
else
    # If pod IP address is not found, display a message
    echo "Pod IP Address not found for RabbitMQ."
fi
cd ..
cp instancemanager/.env converter_streams
cd instancemanager
cd ..
mkdir /opt/Stream-Processing/
cp -r instancemanager /opt/Stream-Processing
cd installation
cp instancemanager.service /etc/systemd/system/
systemctl enable instancemanager.service
systemctl start instancemanager.service
echo "--------------------------------------------"
echo "Converter"
echo "--------------------------------------------"
cd ..
cp -r converter_streams /opt/Stream-Processing
cd installation
cp converter.service /etc/systemd/system/
systemctl enable converter.service
systemctl start converter.service
