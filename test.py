#!/usr/bin/env python

import unittest
from regexp.snippet import Snippet
from regexp.string import FormatString

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
        snippet = Snippet('''<label for="${2:${1/[[:alpha:]]+|( )/(?1:_:\L$0)/g}}">$1</label><input type="${3|text,submit,hidden,button|}" name="${4:$2}" value="$5"${6: id="${7:$2}"}${TM_XHTML}>''')
        string = FormatString("storage.type.class.${1:/downcase}")
        print(snippet.taborder)
        print(snippet.replace(p, {"1": "hola mundo",
            "2": "id_cacho",
            "3": 2,
            "4": "my_name",
            "5": "hola value",
            "7": "id_input"}))
        print(string.replace(p, {}))

if __name__ == '__main__':
    unittest.main()