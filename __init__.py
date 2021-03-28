from hoshino import Service

help_ = ""
sv = Service("destiny2", help_=help_)

root_path = 'https://www.bungie.net/Platform'
headers = {"X-API-Key":'aff47ade61f643a19915148cfcfc6d7d'}
proxies = {'http': '127.0.0.1:7890','https': '127.0.0.1:7890'}