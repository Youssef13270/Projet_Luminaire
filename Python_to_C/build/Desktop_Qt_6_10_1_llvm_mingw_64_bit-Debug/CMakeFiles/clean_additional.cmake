# Additional clean files
cmake_minimum_required(VERSION 3.16)

if("${CONFIG}" STREQUAL "" OR "${CONFIG}" STREQUAL "Debug")
  file(REMOVE_RECURSE
  "CMakeFiles\\Python_to_C_autogen.dir\\AutogenUsed.txt"
  "CMakeFiles\\Python_to_C_autogen.dir\\ParseCache.txt"
  "Python_to_C_autogen"
  )
endif()
