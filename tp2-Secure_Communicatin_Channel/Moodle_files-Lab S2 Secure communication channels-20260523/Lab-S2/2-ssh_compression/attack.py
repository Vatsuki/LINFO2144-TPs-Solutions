
import math
import tqdm

def get_countries():
    countries = []
    with open("capitals.txt", "r") as f:
        for line in f:
            countries.append(line.strip())
    return countries


class AttackTamper:
    def __init__(self, compress):
        self.compress = compress
        self.bytes = 0

    def handle_data(self, data):
        return data

def attack_decrypt(client_fn):
    # Your attack here.
    return ""