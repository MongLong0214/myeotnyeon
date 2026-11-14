"""bc: converted card values are rounded to 2 significant figures; upper-bound source values need a MAX label (CEO bc004)."""
import unittest

from factory.shorts import bc


class T(unittest.TestCase):
    def test_approx(self):
        self.assertEqual(bc.approx(22000 * .4536), '10,000')
        self.assertEqual(bc.approx(3 * 2.54), '7.6')
        self.assertEqual(bc.approx(4500 * .4536), '2,000')

    def test_max_quote(self):
        spec = {'facts': [{'id': 'F1', 'quotes': [{'text': 'Males weigh up to 9,920 pounds'}]},
                          {'id': 'F2', 'quotes': [{'text': 'Adults weigh about 1,650 pounds'}]}]}
        self.assertTrue(bc.max_quote(spec, 'F1.weight', '9,920 pounds'))
        self.assertIsNone(bc.max_quote(spec, 'F2.weight', '1,650 pounds'))


if __name__ == '__main__':
    unittest.main()
