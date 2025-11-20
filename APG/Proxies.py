import requests
import random
from fp.fp import FreeProxy


class Proxies:
    proxy_list = None

    def get_free_proxies(self):
        proxies = []
        # Proxies gathered are a subset of the proxies available at https://github.com/proxifly/free-proxy-list
        # Proxifly allows for the free use of these proxies, assuming standard use practices are adhered to
        url = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/US/data.json"
        content = requests.get(url).json()
        for item in content:
            if item['protocol'] == "http":
                proxies.append(item['proxy'])
        return proxies

    def get_python_proxy(self):
        selected_proxy = FreeProxy(https=True).get()
        return {"http": selected_proxy, "https": selected_proxy}

    def get_rand_proxy(self):
        if self.proxy_list is None:
            self.proxy_list = self.get_free_proxies()
        selected_proxy = random.choice(self.proxy_list)
        return {"http": selected_proxy, "https": selected_proxy}
