export NANO_SRC=nanopb-0.3.7
export NANO_SRC_DIR=nanopb

# Download Windows (32-bit) binary.
"${PYTHON}" -m wget https://koti.kapsi.fi/~jpa/nanopb/download/${NANO_SRC}.tar.gz
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Extract release from ZIP archive.
tar xzf ${NANO_SRC}.tar.gz
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Convert `nanopb_generator.py` to Python module
mkdir nanopb_generator
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
cp "${NANO_SRC_DIR}"/generator/nanopb_generator.py nanopb_generator/__main__.py
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
echo "" > nanopb_generator/__init__.py
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Generate nanopb Python protobuf definitions.
export NANO_PROTO_DIR="${NANO_SRC_DIR}"/generator/proto
protoc --python_out=${NANO_PROTO_DIR} --proto_path=${NANO_PROTO_DIR} ${NANO_PROTO_DIR}/nanopb.proto
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
protoc --python_out=${NANO_PROTO_DIR} --proto_path=${NANO_PROTO_DIR} ${NANO_PROTO_DIR}/plugin.proto
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
cp -ra ${NANO_PROTO_DIR} nanopb_generator/proto
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Copy `nanopb_generator` Python module to site-packages
cp -ra nanopb_generator "$SP_DIR"/nanopb_generator
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Create batch file to run `nanopb_generator` Python module as a script
echo python -m nanopb_generator --protoc-plugin > "${PREFIX}"/bin/protoc-gen-nanopb.sh
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
# Create batch file to call protoc compiler with `nanopb_generator` plugin
echo "#!/bin/bash" > "${PREFIX}"/bin/nanopb
echo protoc --plugin=protoc-gen-nanopb=protoc-gen-nanopb.sh >> "${PREFIX}"/bin/nanopb
chmod a+x "${PREFIX}"/bin/nanopb
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi

# Copy nanopb C source and headers to Arduino
export INSTALL_DIR=$("${PYTHON}" -c "from __future__ import print_function; import platformio_helpers as pioh; print(pioh.conda_arduino_include_path(), end='')")
mkdir -p "${INSTALL_DIR}"/nanopb/src
cp -ra "${RECIPE_DIR}"/library.properties "${INSTALL_DIR}/nanopb
cp -ra "${RECIPE_DIR}"/nanopb.h "${INSTALL_DIR}/nanopb/src
cp -ra "${NANO_SRC_DIR}"/*.h "${INSTALL_DIR}/nanopb/src
cp -ra "${NANO_SRC_DIR}"/*.c "${INSTALL_DIR}/nanopb/src
cp -ra "${NANO_SRC_DIR}"/*.txt "${INSTALL_DIR}/nanopb/src
cp -ra "${NANO_SRC_DIR}"/*.md "${INSTALL_DIR}/nanopb/src
cp -ra "${NANO_SRC_DIR}"/AUTHORS "${INSTALL_DIR}/nanopb/src
cp -ra "${NANO_SRC_DIR}"/BUILD "${INSTALL_DIR}/nanopb/src
cp -ra "${NANO_SRC_DIR}"/CHANGELOG.txt "${INSTALL_DIR}/nanopb/src
