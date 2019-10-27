#!/bin/bash

export PATH=$AOSP/prebuilts/build-tools/linux-x86/bin/:$PATH

cd "$AOSP"; python "$ANDROIDBUILD"/src/katicache.py -i out/build-"$PROJECT".ninja -o kati.cache
cd "$AOSP"; python "$ANDROIDBUILD"/src/ninjabuild.py -kn out/combined-"$PROJECT".ninja -kc kati.cache -f "$FILEPATH" -l debug -o out.txt

cd "$AOSP"; python "$ANDROIDBUILD"/src/soongcache.py -i out/soong/build.ninja -o soong.cache
cd "$AOSP"; python "$ANDROIDBUILD"/src/ninjabuild.py -sn out/combined-"$PROJECT".ninja -sc soong.cache -f "$FILEPATH" -l debug -o out.txt
