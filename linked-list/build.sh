mkdir -p "${PREFIX}"/include/Arduino
cp -ra "${SRC_DIR}" "${PREFIX}"/include/Arduino/LinkedList
rm "${PREFIX}"/include/Arduino/LinkedList/build.sh
rc=$?; if [[ $rc != 0  ]]; then exit $rc; fi
