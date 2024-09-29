#/bin/bash

SRC_DIR=/systems/in-mem/GeminiGraph
TOOLKIT_DIR=/systems/in-mem/gemini/toolkit
CONVERTER=/gemini_converter

$CC -o /gemini-converter gemini-converter.c
cd $SRC_DIR
make -j

cd $CONVERTER
make -j