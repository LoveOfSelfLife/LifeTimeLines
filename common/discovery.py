import os
import logging

service_lookup = {
      'entities':  { "host": "http://localhost", "port": 8080 }
    , 'photos':    { "host": "http://localhost", "port": 8081 }
    , 'amain':     { "host": "http://localhost", "port": 8082 }
    , 'otmgr':     { "host": "http://localhost", "port": 8084 }
    , 'feapp':     { "host": "http://localhost", "port": 8085 }
    , 'fe':        { "host": "http://localhost", "port": 8086 }    
}

def get_service_host_port(service):
    if service_lookup.get(service) is None:
        raise ValueError(f'Unknown service: {service}')
    
    if os.getenv('ORCH_TESTING_MODE'):
        return service_lookup[service]['host'], service_lookup[service]['port']
    else:
        return f'https://{service}.ltl.richkempinski.com', None

def get_service_port(service):
    _,port = get_service_host_port(service)
    return port

def get_service_url(service):
    host, port = get_service_host_port(service)
    port = f':{port}' if port else ''
    return f'{host}{port}'
