export LIB_NAME=FastDigital
mkdir -p "${PREFIX}"/include/Arduino
cp -ra "${SRC_DIR}" "${PREFIX}"/include/Arduino/${LIB_NAME}
rm "${PREFIX}"/include/Arduino/${LIB_NAME}/build.sh
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
