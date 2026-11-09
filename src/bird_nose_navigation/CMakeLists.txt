cmake_minimum_required(VERSION 3.8)
project(bird_nose_navigation)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Python helpers that build Nav2's parameters (used by bird_nose_bringup).
ament_python_install_package(${PROJECT_NAME})

install(DIRECTORY config/ DESTINATION share/${PROJECT_NAME}/config)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # No license headers yet; re-enable once a license is chosen.
  set(ament_cmake_copyright_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_nav2_params test/test_nav2_params.py
    APPEND_ENV PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR})
endif()

ament_package()
