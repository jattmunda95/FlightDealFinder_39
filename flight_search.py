import os
import requests
from twilio.rest import Client





class FlightSearch:



    def __init__(self):

        # Initialization of All Environment Variables
        self._ama_api_key = os.environ.get('AMADEUS_API_KEY')
        self._ama_api_secret = os.environ.get('AMADEUS_API_SECRET')
        self._twilio_sid = os.environ.get('TWILIO_SID')
        self._twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self._twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')

        # API Endpoints
        self._city_search_lnk = 'https://test.api.amadeus.com/v1/reference-data/locations'
        self._deal_search_lnk = 'https://test.api.amadeus.com/v2/shopping/flight-offers'

        # Empty variables for later population
        self.token = ''
        self.itinerary = []


        # print(access_token)

    def get_token(self):
        """
        Gets Amadeus API token on run and then stores it in a class variable `token` for class level used and API requests
        :return: None
        """
        # AUTHORIZATION HEADER FOR AMADEUS API TOKEN REQUEST
        token_header = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        # AUTHORIZATION PARAMETERS FOR AMADEUS API TOKEN REQUEST
        token_params = {
            'grant_type': 'client_credentials',
            'client_id': self._ama_api_key,
            'client_secret': self._ama_api_secret
        }

        # RESPONSE FROM AMADEUS API WITH TOKEN/SECRET
        access_token_resp = requests.post('https://test.api.amadeus.com/v1/security/oauth2/token', data=token_params,
                                          headers=token_header).json()
        self.token = access_token_resp['access_token']
        # print(self.token) Debugging line


    def get_iata_codes(self, city_name: str) -> str:
        """
        Make request to Amadeus API, passing ti city_name and other parameters highlighted in API documentation.
        link: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search
        :param city_name: Get IATA code for `city_name`
        :return: String of city IATA code
        """
        self.get_token()

        # REQUEST AUTHENTICATION HEADER
        city_auth_header = {
            "Authorization" : 'Bearer ' + self.token,
            # 'Content-Type': 'application/json',
        }

        # SEARCH REQUEST BODY
        city_search_params = {
            'subType' : 'AIRPORT',
            'keyword' : f'{city_name}',
            'view' : 'LIGHT',
        }

        city_search_response = requests.get(self._city_search_lnk, params=city_search_params, headers=city_auth_header).json()
        # print(city_search_response)
        # Case handling of responses from IATA Code Amadeus API
        if city_search_response['meta']['count'] == 0:
            return 'NONE'
        else:
            for item in city_search_response['data']:
                if item['subType'] == 'AIRPORT' and item['address']['cityName'] == city_name.upper():
                    return item['iataCode']

    def check_deals(self, location_name: str, origin_code: str, destination_code: str, date: str, return_date: str, max_price: str, no_adults: int = 1) -> bool:
        """
        Function responsible for retrieving flight offers matching criteria based on `location_name`,`origin_code`,`destination_code`, `date`, `return_date`, `max_price` and `no_adults`.
        If data retrieval and API execution is successful, the function sends a message to a personal phone number from a Twilio phone number through the Twilio API SMS Service. If
        execution is done fully then the function returns `True`.

        :param location_name: `String` of Destination City's Name
        :param origin_code: `String` of Departure City's Name
        :param destination_code: 'String' of Destination Location's IATA Code
        :param date: `String` of Departure Date
        :param return_date: `String` of Return Date
        :param max_price: `String` of Max Price
        :param no_adults: `String` of No. of Adults
        :return: Boolean to check function execution status
        """
        self.get_token()

        # API REQUEST AUTHORIZATION HEADER
        flight_search_header = {
            'Authorization': 'Bearer ' + self.token,
        }

        # API REQUEST PARAMETER BODY
        flight_search_body = {
            'originLocationCode': origin_code,
            'destinationLocationCode': destination_code,
            'departureDate': date,
            'adults' : no_adults,
            'maxPrice' : max_price,
            'currencyCode' : 'AUD',
            'returnDate' : return_date,
        }

        # API REQUEST MADE
        flight_search_call = requests.get(self._deal_search_lnk, headers=flight_search_header, params=flight_search_body).json()

        # Returned data parsing using dictionary syntax
        airlines = flight_search_call['dictionaries']['carriers']
        airline_list = []

        #   Appending airlines to list for use in message
        for airline in airlines.values():
            airline_list.append(airline)

        # Debugging statements
        # print(airlines)
        # print(flight_search_call)

        # Returned flights are sorted by relevance as default, hence 1st option, best option
        best_flight = flight_search_call['data'][0]
        if flight_search_call['meta']['count'] != 0:

            flight_itinerary = best_flight['itineraries']
            departure_duration = flight_itinerary[0]['duration'].replace('PT','')
            arrival_duration = flight_itinerary[1]['duration'].replace('PT','')
            flight_price = best_flight['price']['total']

                # duration = flight_itinerary[]

            # Twilio Client Initialization
            client = Client(self._twilio_sid, self._twilio_auth_token)
            # SMS Text Message Strucuture
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
        # When execution is failed or no deals are returned
        return False
