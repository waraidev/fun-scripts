import json
import googlemaps
from datetime import datetime

gmaps = googlemaps.Client(key='') # paste key here for testing.

with open('data/addys.json') as j:
    homes = json.load(j)

breakfast = "Waffle House"

def get_matrix():
    places = []
    homes_coded = []
    for k, v in homes.items():
        latlong = gmaps.geocode(v)
        homes_coded.append(latlong[0]['geometry']['location'])
        search = gmaps.places(query=breakfast, location=latlong[0]['geometry']['location'])
        for i, result in enumerate(search['results'], start=1):
            places.append(result['geometry']['location'])
            if i == 6:
                print(f'Found Waffle Houses for {k.capitalize()}!')
                break

    places = [p for p in places if places.count(p) > 1]
    places = [dict(t) for t in {tuple(p.items()) for p in places}]

    return gmaps.distance_matrix(origins=homes_coded, 
        destinations=places, 
        mode='driving', 
        units='imperial',
        arrival_time=datetime(2022, 5, 2, 7, 5))

def find_breakfast(matrix):
    cumulative_dists = {}
    for r in matrix['rows']:
        for i, el in enumerate(r['elements'], start=0):
            if matrix['destination_addresses'][i] in cumulative_dists:
                cumulative_dists[matrix['destination_addresses'][i]] = cumulative_dists[matrix['destination_addresses'][i]] + el['duration']['value']
            else:
                cumulative_dists[matrix['destination_addresses'][i]] = el['duration']['value']

    return cumulative_dists

if __name__ == '__main__':
    dists = find_breakfast(get_matrix())
    while True:
        min_dist = min(dists, key=dists.get)
        print(f'Closest address to everyone: [{min_dist}]')
        choice = input("Do you like this address? (Y/n): ")
        if choice.lower() == 'n':
            print(f'Removing [{min_dist}] from list')
            dists.pop(min_dist)
        else:
            print('Have a great breakfast!')
            break
