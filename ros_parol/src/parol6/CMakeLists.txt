cmake_minimum_required(VERSION 3.5)
project(parol6)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf launch meshes
  DESTINATION share/${PROJECT_NAME}
)

# Make this package's share directory discoverable by Gazebo Sim so that
# package://parol6/meshes/*.STL references resolve at runtime.
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")

ament_package()
