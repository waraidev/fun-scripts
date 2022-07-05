import json
import googlemaps
from datetime import datetime

gmaps = googlemaps.Client(key='') # paste key here for testing.

with open('data/new_addys.json') as j:
    homes = json.load(j)

place = "305 Brookhaven Ave #1250, Brookhaven, GA 30319"
house_church = "2590 Tanglewood Rd, Decatur, GA 30033"

def get_matrix():
    homes_coded = []
    for k, v in homes.items():
        latlong = gmaps.geocode(v)
        homes_coded.append(latlong[0]['geometry']['location'])
        print(f'Translated address for {k.capitalize()}!')

    return gmaps.distance_matrix(origins=homes_coded, 
        destinations=[
            gmaps.geocode(place)[0]['geometry']['location'], 
            gmaps.geocode(house_church)[0]['geometry']['location']], 
        mode='driving', 
        units='imperial',
        arrival_time=datetime(2022, 6, 8, 19, 0))

if __name__ == '__main__':
    matrix = get_matrix()
    names = list(homes.keys())

    for i, r in enumerate(matrix['rows'], start=0):
        diff = int(r['elements'][0]['duration']['text'][:2]) - int(r['elements'][1]['duration']['text'][:2])
        if diff < 0:
            print(f"{names[i]} would take {diff} less minutes to get to Lucky's.")
        else:
            print(f"{names[i]} would take {diff} more minutes to get to Lucky's.")
