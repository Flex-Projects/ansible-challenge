import json
import yaml
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient

subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
resource_group_name = 'ansible-challenge'
public_ips = ['vm1', 'vm2']

# Create the credential object
credential = DefaultAzureCredential()

# Create the NetworkManagementClient
network_client = NetworkManagementClient(credential, subscription_id)

host_information = {
    'all': {
        'children': {
            'vm1': {
                'hosts': {}
            },
            'vm2': {
                'hosts': {}
            }
        }
    }
}

for public_ip in public_ips:
    # Get the public IP details
    ip_details = network_client.public_ip_addresses.get(resource_group_name, public_ip)
    host_info = {
        'ansible_host': ip_details.ip_address,
        'ansible_user': "azureuser"
    }

    host_information['all']['children'][public_ip]['hosts'] = host_info

# Write the inventory to the file
with open('inventory/inventory.yml', 'w') as inventory_file:
    inventory_file.write(yaml.dump(host_information))

# Output the inventory dictionary as JSON
print(json.dumps(host_information))