import requests
import csv

def read_sync(url):
    response = requests.get(url, stream=True)
    cnt = 0

    for line in response.iter_lines():
        
        cnt += 1
        print(f"line: {line}")
    return cnt

if __name__ == '__main__':
    url = 'http://localhost:8000/solr1.csv'
    res = read_sync(url)
    print(res)
