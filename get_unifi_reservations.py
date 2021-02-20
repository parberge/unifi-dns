#!/usr/bin/env python3
import os
import re
import sys
import logging
import requests

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())

baseurl = os.environ.get('UNIFI_BASEURL', 'https://unifi:8443')
username = os.environ.get('UNIFI_USERNAME')
password = os.environ.get('UNIFI_PASSWORD')
site = os.environ.get('UNIFI_SITE', 'default')
fixed_only = os.environ.get('FIXED_ONLY', False)
log_level = os.environ.get("LOG_LEVEL", "INFO")

log.setLevel(logging.getLevelName(log_level))


def get_configured_clients(session):
    # Get configured clients
    r = session.get(f'{baseurl}/api/s/{site}/list/user', verify=False)
    r.raise_for_status()
    return r.json()['data']


def get_active_clients(session):
    # Get active clients
    r = session.get(f'{baseurl}/api/s/{site}/stat/sta', verify=False)
    r.raise_for_status()
    return r.json()['data']


def get_clients():
    s = requests.Session()
    # Log in to controller
    r = s.post(f'{baseurl}/api/login', json={'username': username, 'password': password}, verify=False)
    r.raise_for_status()
    
    clients = {}
    # Add clients with alias and reserved IP
    for c in get_configured_clients(s):
        if 'name' in c and 'fixed_ip' in c:
            clients[c['mac']] = {'name': c['name'], 'ip': c['fixed_ip']}

    if fixed_only is False:
        # Add active clients with alias
        # Active client IP overrides the reserved one (the actual IP is what matters most)
        for c in get_active_clients(s):
            if 'name' in c and 'ip' in c:
                clients[c['mac']] = {'name': c['name'], 'ip': c['ip']}
    
    friendly_clients = list()
    for client in clients.values():
        if re.search('^[a-zA-Z0-9-]+$', client['name']):
            friendly_clients.append(client)
        else:
            log.debug(f"{client['name']} skipped due to invalid characters.")

    return sorted(friendly_clients, key=lambda i: i['name'])


if __name__ == '__main__':
    try:
        for c in get_clients():
            log.info(f"{c['ip']}, {c['name']}")
    except requests.exceptions.ConnectionError:
        log.critical(f'Could not connect to unifi controller at {baseurl}')
        log.debug(f"Exception information below", exc_info=True)
        exit(1)
    except requests.exceptions.HTTPError:
        if baseurl.startswith("http://"):
            log.error(f"Got HTTP error connecting to {baseurl}. You should probably connect using HTTPS instead of HTTP")
        log.debug(f"Exception information below", exc_info=True)
        exit(1)
