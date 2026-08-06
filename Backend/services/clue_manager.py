import random
import string

from utils import load_json

CLUES = load_json("data/clues.json")["clues"]


def get_clue(number):

    return CLUES[number - 1]["question"]


def verify_clue(number, answer):

    return answer == CLUES[number - 1]["answer"]


def generate_secret_code():

    return "".join(

        random.choice(string.digits)

        for _ in range(4)

    )