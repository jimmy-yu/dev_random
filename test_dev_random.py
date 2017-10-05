import unittest
from dev_random import EntropyPool, NotEnoughEntropyError
import hashlib

class TestEntropyPool(unittest.TestCase):
    def setUp(self):
        self.pool_DEFAULT = EntropyPool()
        self.pool_8bits = EntropyPool(nbits=8, stir_taps=[8,6,5,3,1,0])
        self.pool_SHA = EntropyPool(hash_func=hashlib.sha1)

    def test_init(self):
        self.assertEqual(self.pool_DEFAULT.nbits, 4096)
        self.assertLessEqual(len(bin(self.pool_DEFAULT.content)), 4096+2)

        self.assertEqual(self.pool_8bits.nbits, 8)
        self.assertLessEqual(len(bin(self.pool_8bits.content)), 8 + 2)

    def test_rotation(self):
        self.assertEqual(self.pool_DEFAULT.rol(int('1001',2),1,4), int('0011', 2))
        self.assertEqual(self.pool_DEFAULT.ror(int('1001', 2), 1, 4), int('1100', 2))
        self.assertEqual(self.pool_DEFAULT.ror(int('1', 2), 1, 16), int('1000000000000000', 2))

    def test_get_hash(self):
        self.assertEqual(self.pool_DEFAULT.get_hash('shitty shitty bang bang'), b'\tz\xbf\xc0\xf4$+\x19:"\xbc\xab\x95?P\x89')
        self.assertEqual(self.pool_SHA.get_hash('shitty shitty bang bang'), b'J\x11\xc72\x9eD\xd0Q\x8b\xb7\xf4H\xef\x16,\xb7].\xba<')

    def test_stir(self):
        pool = EntropyPool(nbits=16, stir_ror_by=3, stir_taps=[4,2,0])
        start = int('1111', 2)
        pool.content = start

        after_ror = int('1110000000000001', 2)
                    #  0b1110000000000001
        input_ = 2
        tap1 = 16   # 2**4 = 16 = 0b10000
        tap2 = 4    # 2**2 =  4 = 0b  100
        tap3 = 1    # 2**0 =  1 = 0b    1
        expected =  int('1110000000010100', 2)

        pool.stir(input_=2)
        self.assertEqual(pool.content, expected)

    def test_add_entropy_from_time_interval(self):
        orig_content = self.pool_DEFAULT.content
        orig_entropy_count = self.pool_DEFAULT.entropy_count
        orig_t = self.pool_DEFAULT.last_request_t

        self.pool_DEFAULT.add_entropy_from_time_interval()

        self.assertNotEqual(orig_content, self.pool_DEFAULT.content)
        self.assertNotEqual(orig_entropy_count, self.pool_DEFAULT.entropy_count)
        self.assertNotEqual(orig_t, self.pool_DEFAULT.last_request_t)

    def test_add_entropy(self):
        self.assertEqual(self.pool_DEFAULT.entropy_count, 1)
        self.pool_DEFAULT.add_entropy(input_=1111, credit_entropy=False)
        self.assertEqual(self.pool_DEFAULT.entropy_count, 1)
        self.pool_DEFAULT.add_entropy(input_=1111, credit_entropy=True)
        self.assertEqual(self.pool_DEFAULT.entropy_count, 2)

    def test_extract_from_pool(self):
        self.assertNotEqual(self.pool_DEFAULT.extract_from_pool(),
                            self.pool_DEFAULT.extract_from_pool())

    def test_get_random_bytes(self):
        self.pool_DEFAULT.entropy_count = 2
        nbytes = 16
        results = self.pool_DEFAULT.get_random_bytes(nbytes=nbytes)
        self.assertEqual(len(results), nbytes)
        self.assertEqual(self.pool_DEFAULT.entropy_count, 1)

        nbytes = 32
        results = self.pool_DEFAULT.get_random_bytes(nbytes=nbytes)
        self.assertEqual(len(results), nbytes)
        self.assertEqual(self.pool_DEFAULT.entropy_count, 0)

        self.assertRaises(NotEnoughEntropyError,
                          self.pool_DEFAULT.get_random_bytes, nbytes=16)

if __name__ == '__main__':
    unittest.main()