cmake_minimum_required(VERSION 3.16)
project(Slabes LANGUAGES C)

set(CMAKE_EXPORT_COMPILE_COMMANDS YES)

set(CMAKE_C_OUTPUT_EXTENSION_REPLACE ON)
set(CMAKE_C_STANDARD 98)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/libs)

add_compile_options(-fPIC)
add_link_options(-fPIC)

if(NOT PROJ_NOT_BUILD_MAIN)
    set(LIB_FILES
        slabes/libslabes/console_display.c
    )

    foreach(SOURCE_FILE ${LIB_FILES})
        # filename without an extension
        get_filename_component(LIB_NAME ${SOURCE_FILE} NAME_WE)

        add_library(${LIB_NAME} SHARED ${SOURCE_FILE})
        set_target_properties(${LIB_NAME} PROPERTIES POSITION_INDEPENDENT_CODE ON)
        target_link_libraries(${LIB_NAME} ${MY_LIBS})
    endforeach()

    # add_executable(main ${PROJ_ROOT}/src/toml_impl.cpp ${PROJ_ROOT}/src/game.cpp ${PROJ_ROOT}/src/main.cpp)
    # set_target_properties(main PROPERTIES ENABLE_EXPORTS ON)
    # set_target_properties(main PROPERTIES SUFFIX ".out")
    # target_link_libraries(main ${MY_LIBS})
endif()
