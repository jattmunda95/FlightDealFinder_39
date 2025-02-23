import os
import requests
import datetime as dt
from flight_search import FlightSearch

# AMA_API_KEY = os.environ.get("AMADEUS_API_KEY")
# AMA_API_SECRET = os.environ.get("AMADEUS_API_SECRET")
# AMA_TOKEN_ENDPOINT = 'https://test.api.amadeus.com/v1/security/oauth2/token'

FLIGHT_SHEET_END = 'https://api.sheety.co/6468d5dc7184d3ac9f2b8861e127bc0a/flightLog/itin1'

ORIGIN_IATA = 'MEL'

def main():

    flight_search = FlightSearch()

    itinerary = requests.get(FLIGHT_SHEET_END).json()['itin1']
    print(itinerary)

    code_price_dict = {}

    for location in itinerary:
        if location['iataCode'] == '':
            city_initial = location['location']
            iata_code = flight_search.get_iata_codes(city_initial)
            if iata_code is not None:
                location['iataCode'] = iata_code
                code_price_dict[iata_code] = (location['price'], location['location'])
            else:
                location['iataCode'] = 'NONE'
        elif location['iataCode'] != 'NONE':
            code_price_dict[location['iataCode']] = (location['price'], location['location'])
    print(code_price_dict)
    row_no = 2
    for item in itinerary:
        params = {
            'itin1' : item,
        }
        requests.put(f"{FLIGHT_SHEET_END}/{row_no}", json=params).raise_for_status()
        row_no += 1

    for code, (price, name) in code_price_dict.items():
        date = dt.datetime.today()
        return_date = date + dt.timedelta(days=23)
        date_str = date.strftime('%Y-%m-%d')
        return_date_str = return_date.strftime('%Y-%m-%d')
        flight_found = flight_search.check_deals(name, ORIGIN_IATA, code, date_str, return_date_str, price)
        if flight_found:
            print("Flight found!")
            break

    # print(itinerary)
    # TODO Run a for loop in main with the date checking, for tickets 30 days in advance



if __name__ == '__main__':
    main()
