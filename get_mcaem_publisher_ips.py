"""Dynamically fetch Publisher IP addresses and print them to stdout.

To run:

1. Set the RS_USERNAME environment variable to your Rackspace username.
2. Set the RS_API_KEY environment variables to your Rackspace API key. You can
   find your API key under the "Account Settings" page while logged into the
   Rackspace Cloud Control Panel. (See
   https://support.rackspace.com/how-to/view-and-reset-your-api-key/ for
   more information.)
3. Set the MCAEM_APP_ID and MCAEM_ENV_ID environment variables. To get these,
   log in to the Digital Managed Cloud control panel
   (https://digital.rackspace.com) and navigate to the desired MCAEM
   environment. In the URL for this page the first GUID is the MCAEM_APP_ID,
   the second GUID is the MCAEM_ENV_ID.

   For example, if the URL to your MCAEM environment is
   https://digital.rackspace.com/mcaem/instances/123/environments/456, the
   MCAEM_APP_ID is 123 and the MCAEM_ENV_ID is 456.
4. Invoke this script:

    python get_mcaem_publisher_ips.py

The script will print each Publisher IP, one IP per line. For example:

    12.34.56.78
    111.222.0.3

This script can run on either Python 2.7 or 3.x.
"""
import json
import os
import sys
try:
    import httplib
except ImportError:
    # Python3 fallback:
    import http.client as httplib


def main():
    # Ensure that Rackspace credential and MCAEM envvars are set:
    for var in ('RS_USERNAME', 'RS_API_KEY', 'MCAEM_APP_ID', 'MCAEM_ENV_ID'):
        if os.getenv(var) is None:
            print("Environment variable '{}' must be set!".format(var))
            sys.exit(1)

    # POST credentials to the `tokens` endpoint, get an auth token:
    auth_params = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": os.getenv('RS_USERNAME'),
                "apiKey": os.getenv('RS_API_KEY')
            }
        }
    }
    try:
        conn = httplib.HTTPSConnection(
            'identity.api.rackspacecloud.com')
        conn.request('POST', '/v2.0/tokens', json.dumps(auth_params),
                     {'Content-Type': 'application/json'})
        response = conn.getresponse()
        resp_data = json.loads(response.read().decode('utf-8'))

        # Rackspace account number
        x_tenant_id = resp_data['access']['token']['tenant']['id']
        # Rackspace auth token
        x_auth_token = resp_data['access']['token']['id']
    finally:
        conn.close()

    # Fetch Publisher details from the MCAEM environment:
    try:
        conn = httplib.HTTPSConnection(
            'aem.digital.rackspace.com')
        loc = '/v0/aem/instances/{app}/environments/{env}'.format(
            app=os.getenv('MCAEM_APP_ID'),
            env=os.getenv('MCAEM_ENV_ID')
        )
        conn.request('GET', loc, None, {'X-Tenant-Id': x_tenant_id,
                                        'X-Auth-Token': x_auth_token})
        response = conn.getresponse()

        # Extract Publisher IPs from the MCAEM environment details:
        resp_data = json.loads(response.read().decode('utf-8'))
        apps = resp_data['data']['components'][0]['applications']
        publisher_tier = [x for x in apps if x['role'] == 'publisher'][0]
        for publisher in publisher_tier['resources']['instances']:
            print(publisher['public_ip_address'])
    finally:
        conn.close()


if __name__ == '__main__':
    main()
