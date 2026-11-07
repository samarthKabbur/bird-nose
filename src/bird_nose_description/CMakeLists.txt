cmake_minimum_required(VERSION 3.8)
project(bird_nose_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf/ DESTINATION share/${PROJECT_NAME}/urdf)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # No license headers yet; re-enable once a license is chosen.
  set(ament_cmake_copyright_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
