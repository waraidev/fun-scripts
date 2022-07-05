import json
from numpy.random import default_rng as rng
from numpy.random import randint as ri
from numpy import array, array2string
from smtplib import SMTP

def get_matrix():
    matrix = []

    # B = blue team
    # R = red team
    # G = green team
    # A = assassin
    # N = neutral

    ones = 0
    twos = 0
    threes = 0
    i = 0
    wilds = rng().choice(30, size=5, replace=False)

    for _ in range(6):
        row = []
        for _ in range(5):
            while(True):
                num = ri(1, 4)
                if i == wilds[0]:
                    row.append('A')
                    break
                elif i in wilds:
                    row.append('N')
                    break
                elif num == 1 and ones <= 8:
                    row.append('B')
                    ones += 1
                    break
                elif num == 2 and twos < 8:
                    row.append('R')
                    twos += 1
                    break
                elif num == 3 and threes < 8:
                    row.append('G')
                    threes += 1
                    break
            i += 1
        matrix.append(row)

    return array(matrix)

def send_email(message):
    with open('data/gmail.json') as j:
        gmail_info = json.load(j)

    for dest in gmail_info['receiver_emails']:
        session = SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(gmail_info['sender_email'], gmail_info['pass'])

        session.sendmail(
            gmail_info['sender_email'], 
            dest,
            message
        )

        session.quit()

if __name__ == '__main__':
    m = get_matrix()
    send_email(array2string(m))
    print("Codenames matrix sent!")
