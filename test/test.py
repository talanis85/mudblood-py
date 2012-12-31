#!/usr/bin/env python

import sys
sys.path = [".."] + sys.path

import unittest

import test_telnet
import test_keys

suite = unittest.TestSuite([
    test_telnet.suite,
    test_keys.suite,
    ])

runner = unittest.TextTestRunner()
runner.run(suite)
