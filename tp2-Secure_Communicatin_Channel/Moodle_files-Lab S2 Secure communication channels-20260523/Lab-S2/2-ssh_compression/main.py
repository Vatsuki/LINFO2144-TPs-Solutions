import attack
import client
import constants
import random

random.seed(73)

def get_countries():
    countries = []
    with open("capitals.txt", "r") as f:
        for line in f:
            countries.append(line.strip())
    return countries


def main():
    countries = get_countries()
    secret = "{\n"
    for i in range(5):
        secret += '"city%d": "%s",\n' % (i, random.choice(countries))
    secret += "}\n"

    c = client.Client()

    def run_client(prefix):
        # This is the function that compresses with our compression algorithm
        # and sends the message. Returns: (bytes_sent, bytes_received)
        return c.run_client(prefix + secret, compress=True)

    guess = attack.attack_decrypt(run_client)

    if secret != guess:
        print("Failed to find the secret\n")
        print("Secret : \n" + secret)
        print("Guess : \n" + guess)
    else:
        print("You found the secret")


if __name__ == "__main__":
    main()