#!/usr/bin/env python

import sys
sys.path = [".."] + sys.path

import unittest

import test_telnet
import test_keys
import test_map

suite = unittest.TestSuite([
    test_telnet.suite,
    test_keys.suite,
    test_map.suite,
    ])

runner = unittest.TextTestRunner()
runner.run(suite)
