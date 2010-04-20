#!/bin/sh
# Run from the root of the gcc library, i.e. one level above docs/, gcc/ and examples/
epydoc --config docs/config.cfg -v gcc --exclude='sys|path|re|demjson'
