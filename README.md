# androidbuild
Build system with Ninja for Google Android.



## Running

```bash
# Update Ninja for Android.bp/.mk (apply patch to $AOSP required)
cd "$AOSP"; source build/envsetup.sh; lunch
cd "$AOSP"; GOROOT="$AOSP"/prebuilts/go/linux-x86/ ./out/soong_ui --disable-build-ninja

# Build source in Android.bp
export PATH=$AOSP/prebuilts/build-tools/linux-x86/bin/:$PATH
cd "$AOSP"; python "$ANDROIDBUILD"/src/soongcache.py -i out/soong/build.ninja -o soong.cache
cd "$AOSP"; python "$ANDROIDBUILD"/src/ninjabuild.py -sn out/combined-"$PROJECT".ninja -sc soong.cache -f "$FILEPATH" -l debug -o out.txt

# Build source in Android.mk
export PATH=$AOSP/prebuilts/build-tools/linux-x86/bin/:$PATH
cd "$AOSP"; python "$ANDROIDBUILD"/src/katicache.py -i out/build-"$PROJECT".ninja -o kati.cache
cd "$AOSP"; python "$ANDROIDBUILD"/src/ninjabuild.py -kn out/combined-"$PROJECT".ninja -kc kati.cache -f "$FILEPATH" -l debug -o out.txt
```



## Details

### Android App

```bash
# out/soong/.intermediates/packages/apps/Settings/Settings/android_common/base.zip: g.java.buildBundleModule
ninja -f out/combined-aosp_arm64.ninja -t targets depth 2
ninja -f out/combined-aosp_arm64.ninja Settings-soong
```



### CC Binary

```bash
# out/soong/.intermediates/system/core/adb/adbd/android_arm64_armv8-a_core/versioned-stripped/adbd: g.cc.strip
ninja -f out/combined-aosp_arm64.ninja -t targets depth 2
ninja -f out/combined-aosp_arm64.ninja adbd-soong
```



### CC Library

```bash
# out/soong/.intermediates/system/core/adb/libadbd_services/android_arm_armv8-a_core_shared/versioned-stripped/libadbd_services.so: g.cc.strip
ninja -f out/combined-aosp_arm64.ninja -t targets depth 2
ninja -f out/combined-aosp_arm64.ninja libadbd_services-soong
```



### Java Library

```bash
# out/soong/.intermediates/frameworks/base/ext/android_common/turbine-combined/ext.jar: g.java.combineJar
ninja -f out/combined-aosp_arm64.ninja -t targets depth 2
ninja -f out/combined-aosp_arm64.ninja ext-soong
```

```bash
# out/soong/.intermediates/frameworks/base/framework/android_common_test_com.android.media/jarjar/framework.jar: g.java.jarjar
ninja -f out/combined-aosp_arm64.ninja -t targets depth 2
ninja -f out/combined-aosp_arm64.ninja framework-soong
```



## Stack

```
$AOSP/build/make
  envsetup.sh
    mmma
      build/soong/soong_ui.bash --build-mode --modules-in-dirs-no-deps --dir=$AOSP system/core/adb
```

```
$AOSP/build/soong
  soong_ui.bash
    scripts/microfactory.bash
      soong_build_go
        source build/blueprint/microfactory/microfactory.bash
          build_go soong_ui android/soong/cmd/soong_ui
    soong_build_go soong_ui android/soong/cmd/soong_ui
    exec out/soong_ui --build-mode --modules-in-dirs-no-deps --dir=$AOSP system/core/adb
```

```
$AOSP/build/soong/cmd
  soong_ui/main.go
    build.Build(buildCtx, config, toBuild)
```

```
$AOSP/build/soong/ui
  build/build.go
    runMakeProductConfig
    runSoong
    runKati
    createCombinedBuildNinjaFile
    runNinja
```



## Output

```
$AOSP/out/
  build-aosp_arm64.ninja
  combined-aosp_arm64.ninja
    subninja out/build-aosp_arm64.ninja
    subninja out/soong/build.ninja
  microfactory_Linux
  ninja-aosp_arm64.sh
  soong/
    build.ninja
  soong.log
  soong_ui
```



## Tools

### Ninja

```bash
git clone https://github.com/ninja-build/ninja.git

cd ninja
./configure.py --bootstrap
./ninja all
upx -9 ninja
```

```bash
ninja -t list

ninja subtools:
    browse  browse dependency graph in a web browser
     clean  clean built files
  commands  list all commands required to rebuild given targets
      deps  show dependencies stored in the deps log
     graph  output graphviz dot file for targets
      path  find dependency path between two targets
     query  show inputs/outputs for a path
   targets  list targets by their rule or depth in the DAG
    compdb  dump JSON compilation database to stdout
 recompact  recompacts ninja-internal data structures
```



### Blueprint

```bash
git clone https://github.com/google/blueprint.git

cd blueprint
./bootstrap.bash
./blueprint.bash
upx -9 ./bin/*
```



### Kati

```bash
git clone https://github.com/google/kati.git

cd kati
make
upx -9 ckati
```



## Reference

- Blueprint

  https://github.com/google/blueprint

  https://godoc.org/github.com/google/blueprint



- Kati

  https://github.com/google/kati



- Ninja

  https://android.googlesource.com/platform/external/ninja/

  https://note.qidong.name/2018/02/android-ninja-tips/

  https://www.jianshu.com/p/d118615c1943



- Soong

  https://android.googlesource.com/platform/build/soong/

  https://android.googlesource.com/platform/build/soong/+/HEAD/docs/best_practices.md

  https://android.googlesource.com/platform/build/soong/+/HEAD/docs/perf.md

  https://android.googlesource.com/platform/build/+/master/README.md

  https://android.googlesource.com/platform/build/+/master/Usage.txt

  https://android-review.googlesource.com/q/topic:%22blueprint_microfactory%22+status:merged

  https://android-review.googlesource.com/c/platform/external/ninja/+/461005

  https://ci.android.com/builds/latest/branches/aosp-build-tools/targets/linux/view/soong_build.html
