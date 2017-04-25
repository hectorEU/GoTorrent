'''
Local queries unittest module. General
@author: Daniel Barcelona Pons
'''
import unittest

import tests_gevent
import tests_thread

# from time import sleep

if __name__ == '__main__':
    print ('## WITH THREADS')
    suite = unittest.TestLoader().loadTestsFromTestCase(tests_thread.TestBasic)
    unittest.TextTestRunner(verbosity=2).run(suite)
    print ('## WITH GREEN THREADS')
    suite = unittest.TestLoader().loadTestsFromTestCase(tests_gevent.TestBasic)
    unittest.TextTestRunner(verbosity=2).run(suite)
