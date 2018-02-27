# Use `autoreconf` to avoid mismatch in versions of `libtool` and `aclocal.m4`.
# See [here][1] for more info.
#
# [1]: http://stackoverflow.com/questions/3096989#3205400
autoreconf --force --install
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
./configure --prefix="${PREFIX}"
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
make -j4
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
make install
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
