#!/usr/bin/env python3

import sys
sys.path = [".."] + sys.path

import unittest

import test_telnet

suite = unittest.TestSuite([
    test_telnet.suite
    ])

runner = unittest.TextTestRunner()
runner.run(suite)
