cmake_minimum_required(VERSION 3.8)
project(bird_nose_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/AudioChunk.msg"
  "msg/Sample.msg"
  "msg/Detection.msg"
  "msg/BearingEstimate.msg"
  "msg/SourceEstimate.msg"
  "msg/SourceEstimateArray.msg"
  "msg/SurveyEvent.msg"
  "action/RecordSample.action"
  DEPENDENCIES std_msgs geometry_msgs
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # No license headers yet; re-enable once a license is chosen.
  set(ament_cmake_copyright_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_dependencies(rosidl_default_runtime)
ament_package()
