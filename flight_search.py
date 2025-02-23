import os
import requests
from twilio.rest import Client





class FlightSearch:



    def __init__(self):
        self._ama_api_key = os.environ.get('AMADEUS_API_KEY')
        self._ama_api_secret = os.environ.get('AMADEUS_API_SECRET')
        self._twilio_sid = 'AC59b4ff14eb55c816546ed67b30666c55'
        self._twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self._twilio_phone_number = '+14172442201'
        self._city_search_lnk = 'https://test.api.amadeus.com/v1/reference-data/locations'
        self._deal_search_lnk = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
        self.token = ''
        self.itinerary = []


        # print(access_token)

    def get_token(self):
        token_header = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        token_params = {
            'grant_type': 'client_credentials',
            'client_id': self._ama_api_key,
            'client_secret': self._ama_api_secret
        }

        access_token_resp = requests.post('https://test.api.amadeus.com/v1/security/oauth2/token', data=token_params,
                                          headers=token_header).json()
        self.token = access_token_resp['access_token']
        # print(self.token)


    def get_iata_codes(self, city_name: str) -> str:

        self.get_token()

        city_auth_header = {
            "Authorization" : 'Bearer ' + self.token,
            # 'Content-Type': 'application/json',
        }

        city_search_params = {
            'subType' : 'AIRPORT',
            'keyword' : f'{city_name}',
            'view' : 'LIGHT',
        }

        city_search_response = requests.get(self._city_search_lnk, params=city_search_params, headers=city_auth_header).json()
        # print(city_search_response)
        if city_search_response['meta']['count'] == 0:
            return 'NONE'
        else:
            for item in city_search_response['data']:
                if item['subType'] == 'AIRPORT' and item['address']['cityName'] == city_name.upper():
                    return item['iataCode']

    def check_deals(self, location_name: str, origin_code: str, destination_code: str, date: str, return_date: str, max_price: str, no_adults: int = 1):
        self.get_token()

        flight_search_header = {
            'Authorization': 'Bearer ' + self.token,
        }

        flight_search_body = {
            'originLocationCode': origin_code,
            'destinationLocationCode': destination_code,
            'departureDate': date,
            'adults' : no_adults,
            'maxPrice' : max_price,
            'currencyCode' : 'AUD',
            'returnDate' : return_date,
        }

        flight_search_call = requests.get(self._deal_search_lnk, headers=flight_search_header, params=flight_search_body).json()
        airlines = flight_search_call['dictionaries']['carriers']
        airline_list = []
        for airline in airlines.values():
            airline_list.append(airline)
        print(airlines)
        print(flight_search_call)
        best_flight = flight_search_call['data'][0]
        if flight_search_call['meta']['count'] != 0:

            flight_itinerary = best_flight['itineraries']
            departure_duration = flight_itinerary[0]['duration'].replace('PT','')
            arrival_duration = flight_itinerary[1]['duration'].replace('PT','')
            flight_price = best_flight['price']['total']

                # duration = flight_itinerary[]

            client = Client(self._twilio_sid, self._twilio_auth_token)
            text_msg = (f"FROM: {date} TO: {return_date}\n "
                  f"\n"
                  f"GOING TO: {location_name}\n"
                  f"Airlines: {airline_list}\n"
                  f"Duration:\n"
                  f"  Going: {departure_duration}\n"
                  f"  Coming: {arrival_duration}\n"
                  f"Price: {flight_price}\n")

            send_msg = client.messages.create(to="+61466008554", from_=self._twilio_phone_number, body=text_msg)
            return True
