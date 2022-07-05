import random
from numpy import mean
from tqdm import tqdm

num_rolls2 = []
num_rolls3 = []
num_rolls4 = []

for _ in tqdm(range(1000), desc='Rolling dice', ncols=150):
    count = 0
    while True:
        r = [
            random.randrange(1, 21),
            random.randrange(1, 21),
            random.randrange(1, 21),
            random.randrange(1, 21)
        ]
        count += 1
        if all(x == r[0] for x in r) and r[0] == 20:
            break
    num_rolls4.append(count)

    count = 0
    while True:
        r = [
            random.randrange(1, 21),
            random.randrange(1, 21),
            random.randrange(1, 21)
        ]
        count += 1
        if all(x == r[0] for x in r) and r[0] == 20:
            break
    num_rolls3.append(count)

    count = 0
    while True:
        r = [
            random.randrange(1, 21),
            random.randrange(1, 21)
        ]
        count += 1
        if r[0] == r[1] and r[0] == 20:
            break
    num_rolls2.append(count)

print('Getting averages...')
print(f'Average number of rolls to get four 20s in a row: {round(mean(num_rolls4), 2)}')
print(f'Average number of rolls to get three 20s in a row: {round(mean(num_rolls3), 2)}')
print(f'Average number of rolls to get two 20s in a row: {round(mean(num_rolls2), 2)}')
        
# Warning, this will take approximately 8 minutes to run