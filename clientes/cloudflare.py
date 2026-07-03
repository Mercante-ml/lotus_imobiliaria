import os
import requests
from django.conf import settings

import json
import base64

class CloudflareTunnelManager:
    """
    Manages Cloudflare Zero Trust Tunnel configurations dynamically.
    Required ENV variables:
    - CLOUDFLARE_API_TOKEN
    - CLOUDFLARE_TUNNEL_TOKEN
    """
    
    def __init__(self):
        self.api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
        self.tunnel_token = os.environ.get('CLOUDFLARE_TUNNEL_TOKEN')
        
        self.account_id = None
        self.tunnel_id = None
        
        if self.tunnel_token:
            try:
                decoded = json.loads(base64.b64decode(self.tunnel_token))
                self.account_id = decoded.get('a')
                self.tunnel_id = decoded.get('t')
            except Exception as e:
                print(f"Erro ao decodificar token do Cloudflare: {e}")
                
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/cfd_tunnel/{self.tunnel_id}/configurations"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _get_current_config(self):
        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get('result', {}).get('config', {})
        return None

    def add_route(self, hostname, service="http://web:8000"):
        if not all([self.api_token, self.account_id, self.tunnel_id]):
            print("Faltam credenciais do Cloudflare no .env")
            return False

        config = self._get_current_config()
        if not config:
            print("Não foi possível buscar a configuração do túnel.")
            return False

        ingress = config.get('ingress', [])
        
        # Check if already exists
        for rule in ingress:
            if rule.get('hostname') == hostname:
                return True # Already mapped

        # Create new rule
        new_rule = {"hostname": hostname, "service": service}
        
        # Ingress rules must end with a catch-all
        if ingress and ingress[-1].get('service') == "http_status:404":
            ingress.insert(-1, new_rule)
        else:
            ingress.append(new_rule)
            # Ensure catch-all exists
            if not ingress or ingress[-1].get('service') != "http_status:404":
                ingress.append({"service": "http_status:404"})

        config['ingress'] = ingress

        # Save config back to Cloudflare
        payload = {"config": config}
        response = requests.put(self.base_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Erro ao salvar rota no Cloudflare: {response.text}")
            return False

    def remove_route(self, hostname):
        """Remove an existing route from the Cloudflare Tunnel ingress rules"""
        if not all([self.api_token, self.account_id, self.tunnel_id]):
            return False

        config = self._get_current_config()
        if not config:
            return False

        ingress = config.get('ingress', [])
        
        # Filter out the hostname
        new_ingress = [rule for rule in ingress if rule.get('hostname') != hostname]
        
        # If lengths are the same, the hostname wasn't there
        if len(new_ingress) == len(ingress):
            return True
            
        config['ingress'] = new_ingress
        
        payload = {"config": config}
        response = requests.put(self.base_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Erro ao remover rota no Cloudflare: {response.text}")
            return False

