"""

Author: Jimmy Yu
Email: jimyu.bme@gmail.com

Goal: implement a random number generator by copying linux's dev/random


Reference:
https://linux.die.net/man/4/random
http://elixir.free-electrons.com/linux/v4.14-rc3/source/drivers/char/random.c

"""


import os
import hashlib
import time

DEFAULT_POOL_NBITS = 4096 # 512 bytes


class NotEnoughEntropyError(Exception): pass


class EntropyPool(object):
    """
    This is a *VERY simplified* version of dev/random


    Interface ---- output
    =====================
    get_random_bytes(nbytes)
        :param nbytes: [int] number of bytes required
        :return : bytes


    Interface ---- input
    ====================
    add_entropy(input_)
        :param input_: take in anything to stir the entropy pool

    add_entropy_from_time_interval()
        This emulates how time intervals between events (e.g. mouse clicks or keyboard presses) can add
        entropy into the pool.



    Normal procedure:
    - entropy pool of n-bits gets initialized
    - un-deterministic inputs get added/stirred into the entropy pool
        - e.g. time between key strokes, mouse clicks, audio noise, temperature noise, etc.
    - number of "bits of randomness" is estimated and tallied
        (in this simplified version, I only keep track of number of times entropy was added)
    - when random number is requested:
        - if the "bits of randomness" tally is too low, WAIT for new entropy to arrive
            (my implementation: credit/debit is simplified to adding/requesting entropy)
        - the content of the pool gets hashed
        - the hash is returned
        - the hash is also fed back into the pool so the next request will be different



    """

    def __init__(self, nbits=DEFAULT_POOL_NBITS, hash_func=None,
                 stir_taps=[128,104,76,51,25,1,0], stir_ror_by=7):
        self.entropy_count = 0
        self.nbits = nbits
        self.content = 0
        self.last_request_t = 0
        self.bit_mask = ((1<<nbits)-1)
        self.stir_taps = stir_taps
        self.stir_ror_by = stir_ror_by
        if hash_func:
            self.hash_func = hash_func
        else:
            self.hash_func = hashlib.md5
        self.add_entropy_from_time_interval()

    def add_entropy(self, input_, credit_entropy=True):
        if isinstance(input_, str):
            input_ = self.convert_str_to_int(input_)
        if not isinstance(input_, int):
            try:
                input_ = int(input_)
            except ValueError:
                raise TypeError('Expecting int, received {}'.format(type(input_)))

        # Stir pool
        self.stir(input_)

        # Credit entropy
        if credit_entropy:
            self.credit_entropy()

    def add_entropy_from_time_interval(self):
        now = time.time()
        t_interval = now - self.last_request_t
        t_interval = int(t_interval * 1000000)
        self.add_entropy(t_interval, credit_entropy=True)
        self.last_request_t = now

    def credit_entropy(self):
        self.entropy_count += 1

    def debit_entropy(self):
        self.entropy_count -= 1
        if self.entropy_count < 0:
            raise NotEnoughEntropyError('Must wait for more entropy to arrive')

    @staticmethod
    def convert_str_to_int(a_string):
        if not isinstance(a_string, str):
            raise TypeError('Expecting str, received {}'.format(type(a_string)))
        return sum([ord(c) for c in a_string])

    def stir(self, input_):
        # Rotate right by __ bits to make sure bit toggles are not limited to lower order bits
        self.content = self.ror(self.content, self.stir_ror_by, self.nbits)

        # bitwise exclusive or
        for tap in self.stir_taps:
            self.content ^= (input_ ** tap) & self.bit_mask

    def get_hash(self, to_hash):
        if isinstance(to_hash, int):
            to_hash = bin(to_hash)
        if isinstance(to_hash, long):
            to_hash = bin(to_hash)
        return self.hash_func(to_hash).digest()

    def get_random_bytes(self, nbytes):
        self.debit_entropy()
        byte_count = 0
        result = bytearray()
        while byte_count < nbytes:
            new_result = self.extract_from_pool()
            new_count = len(new_result)
            if byte_count + new_count <= nbytes:
                result.extend(new_result)
                byte_count += new_count
            else:
                remaining_count = nbytes - byte_count
                result.extend(new_result[0:remaining_count])
                byte_count += remaining_count
                break
        return result

    def extract_from_pool(self):
        # Hash content
        result = self.get_hash(self.content)

        # add back entropy (hash)
        self.add_entropy(result, credit_entropy=False)

        # Return hash
        return result

    @staticmethod
    def rol(val, r_bits, max_bits):
        """ Rotate bits to the left
        https://www.falatic.com/index.php/108/python-and-bitwise-rotation"""
        return (val << r_bits % max_bits) & (2 ** max_bits - 1) | (
        (val & (2 ** max_bits - 1)) >> (max_bits - (r_bits % max_bits)))

    @staticmethod
    def ror(val, r_bits, max_bits):
        """ Rotate bits to the right
        https://www.falatic.com/index.php/108/python-and-bitwise-rotation"""
        return ((val & (2 ** max_bits - 1)) >> r_bits % max_bits) | (
        val << (max_bits - (r_bits % max_bits)) & (2 ** max_bits - 1))