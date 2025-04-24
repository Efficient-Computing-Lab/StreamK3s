echo "--------------------------------------------"
echo "Uninstalling Stream Processing Platform"
echo "--------------------------------------------"
echo "--------------------------------------------"
echo "Stopping Instancemanager"
echo "--------------------------------------------"
systemctl stop instancemanager.service
systemctl disable instancemanager.service
rm -r /etc/systemd/system/instancemanager.service
echo "--------------------------------------------"
echo "Stopping Converter"
echo "--------------------------------------------"
systemctl stop converter.service
systemctl disable converter.service
rm -r /etc/systemd/system/converter.service
rm -r /opt/Stream-Processing/
echo "--------------------------------------------"
echo "Stopping NodeRED"
echo "--------------------------------------------"
kubectl delete -f nodered-deployment.yaml
kubectl delete -f nodered-pvc.yaml
kubectl delete -f nodered-pv.yaml
kubectl delete -f nodered-namespace.yaml
rm -r /opt/NodeRED/
echo "--------------------------------------------"
echo "Stopping KEDA"
echo "--------------------------------------------"
kubectl delete -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0-core.yaml
echo "--------------------------------------------"
echo "Stopping RabbitMQ"
echo "--------------------------------------------"
kubectl delete namespace rabbit
echo "Stopping Miniconda"
echo "--------------------------------------------"
/opt/miniconda3/uninstall.sh
rm -r /root/.kube/