#!/usr/bin/env python

import unittest
from regexp.snippet import Snippet

class Processor(object):
    def __init__(self):
        self.output = ""

    def write(self, text):
        self.output += text 

class SnippetTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_parser(self):
        p = Processor()
        s = Snippet('''<label for="${2:${1/[[:alpha:]]+|( )/(?1:_:\L$0)/g}}">$1</label><input type="${3|text,submit,hidden,button|}" name="${4:$2}" value="$5"${6: id="${7:$2}"}${TM_XHTML}>''')
        print(s.replace(p, {}))
        print(p.output)
if __name__ == '__main__':
    unittest.main()