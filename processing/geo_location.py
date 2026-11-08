import requests

URL_IPINFO = 'http://ipinfo.io'
def get_location(ip):
    response= requests.get(URL_IPINFO + "/" + ip+'/json')
    if response.status_code == 200:
        return response.json()

if __name__ == "__main__":
    print(get_location('176.32.193.16'))