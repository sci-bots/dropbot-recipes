export SOURCE_ROOT=$(pwd)

# Clone source for clang release 3.9.0.
git clone -b release_39 --depth 1 https://github.com/llvm-mirror/clang clang-git
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

mkdir build
cd build
# Generate make files using cmake.
cmake -G "Unix Makefiles" ../clang-git
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
# Build clang.
make
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

cp -a ${SOURCE_ROOT}/build/lib/libclang.so* ${PREFIX}/lib
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Copy bindings/python/clang to ${PREFIX}/Lib/site-packages/clang.
cp -r ${SOURCE_ROOT}/clang-git/bindings/python/clang "${SP_DIR}"
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
