import json
import yaml
import os
from azure.mgmt.network import NetworkManagementClient
from msrest.authentication import BasicTokenAuthentication
from azure.core.pipeline.policies import BearerTokenCredentialPolicy
from azure.core.pipeline import PipelineRequest, PipelineContext
from azure.core.pipeline.transport import HttpRequest
from azure.identity import DefaultAzureCredential

class CredentialWrapper(BasicTokenAuthentication):
    def __init__(self, credential=None, resource_id="https://management.azure.com/.default", **kwargs):
        """Wrap any azure-identity credential to work with SDK that needs azure.common.credentials/msrestazure.
        Default resource is ARM (syntax of endpoint v2)
        :param credential: Any azure-identity credential (DefaultAzureCredential by default)
        :param str resource_id: The scope to use to get the token (default ARM)
        """
        super(CredentialWrapper, self).__init__(None)
        if credential is None:
            credential = DefaultAzureCredential()
        self._policy = BearerTokenCredentialPolicy(credential, resource_id, **kwargs)

    def _make_request(self):
        return PipelineRequest(
            HttpRequest(
                "CredentialWrapper",
                "https://fakeurl"
            ),
            PipelineContext(None)
        )

    def set_token(self):
        """Ask the azure-core BearerTokenCredentialPolicy policy to get a token.
        Using the policy gives us for free the caching system of azure-core.
        We could make this code simpler by using private method, but by definition
        I can't assure they will be there forever, so mocking a fake call to the policy
        to extract the token, using 100% public API."""
        request = self._make_request()
        self._policy.on_request(request)
        # Read Authorization, and get the second part after Bearer
        token = request.http_request.headers["Authorization"].split(" ", 1)[1]
        self.token = {"access_token": token}

    def signed_session(self, session=None):
        self.set_token()
        return super(CredentialWrapper, self).signed_session(session)

if __name__ == "__main__":
    import os
    credentials = CredentialWrapper()
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "<subscription_id>")

    from azure.mgmt.resource import ResourceManagementClient
    client = ResourceManagementClient(credentials, subscription_id)
    for rg in client.resource_groups.list():
        print(rg.name)

subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
resource_group_name = 'ansible-challenge'
public_ips = ['ansible-vm1-pip', 'ansible-vm2-pip']

# Create the credential object
credential = CredentialWrapper()

# Create the NetworkManagementClient
network_client = NetworkManagementClient(credential, subscription_id)

host_information = {
    'all': {
        'children': {
            'ansible-vm1-pip': {
                'hosts': {}
            },
            'ansible-vm2-pip': {
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