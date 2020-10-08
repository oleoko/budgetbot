from bs4 import BeautifulSoup
import requests
import time

def get_rate():
    page = 'https://bank.gov.ua/'
    request = requests.get(page)
    time.sleep(0.01)
    soup = BeautifulSoup(request.text, "html.parser")
    rates = []

    mydivs = soup.findAll("div", {"class": "value-full"})
    for i in mydivs:
        stri = str(i.contents[1])
        rate = round(float(stri.split("<")[1].split('>')[1].split(' ')[0].replace(',', '.')), 4)
        rates.append(rate)