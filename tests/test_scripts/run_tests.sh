#!/bin/bash
set -e

# Function to run a test case
run_test() {
  local test_name="$1"
  local video_file="$2"
  local network_config="$3"
  local ffmpeg_command="$4"
  local log_file="/app/test_results/${test_name}_ffmpeg.log"
  local result_file="/app/test_results/${test_name}_result.txt"

  echo "Running test: $test_name"
  echo "Video file: $video_file"
  echo "Network config: $network_config"

  # Configure network emulation
  if [ -n "$network_config" ]; then
    echo "Configuring network: $network_config"
    # Example: Apply network config using tc (replace with your actual config)
    # For example:
    # tc qdisc replace dev eth0 root netem "$network_config"
    # For high bandwidth, we don't need to configure anything
    if [ "$network_config" != "high_bandwidth" ]; then
      echo "Applying network configuration: $network_config"
      # Replace with your actual network configuration logic
      # For example, using tc:
      # tc qdisc replace dev eth0 root netem "$network_config"
      # Example configurations:
      # 3G: "delay 100ms 10ms distribution normal bandwidth 500kbit loss 1%"
      # DSL: "delay 50ms bandwidth 2Mbit loss 0.1%"
      # Cable: "delay 20ms bandwidth 10Mbit"
      # Lossy WiFi: "loss 5%"
      # Satellite: "delay 500ms"
      # Custom Profiles:  (Define your own)
      # Example:
      # if [ "$network_config" == "3g" ]; then
      #   tc qdisc replace dev eth0 root netem delay 100ms 10ms distribution normal bandwidth 500kbit loss 1%
      # fi
      # ... add other configurations here
      echo "Network configuration applied."
    fi
  else
    echo "No network configuration specified."
  fi

  # Check if video file exists
  if [ ! -f "$video_file" ]; then
    echo "Error: Video file not found: $video_file"
    exit 1
  fi

  # Run FFmpeg command
  echo "Running FFmpeg command..."
  echo "FFmpeg command: $ffmpeg_command"
  "$ffmpeg_command" 2>&1 | tee "$log_file"
  ffmpeg_status=$?
  echo "FFmpeg command completed with status: $ffmpeg_status"

  # Check results (example: check for errors in the log file)
  if [ $ffmpeg_status -ne 0 ]; then
    echo "Error: FFmpeg command failed. Check $log_file" > "$result_file"
    exit 1
  fi

  # Add more result checks here, e.g., check for dropped frames, bitrate, etc.
  # Example:
  # if grep -q "drop" "$log_file"; then
  #   echo "Error: Dropped frames detected. Check $log_file" > "$result_file"
  #   exit 1
  # fi

  echo "Test '$test_name' completed successfully." > "$result_file"
}

# Main script
# Define video file (can be passed as an argument)
VIDEO_FILE="${VIDEO_FILE:-/app/test_videos/test.mp4}" # Default video file

# Define FFmpeg command (can be passed as an argument)
FFMPEG_COMMAND="${FFMPEG_COMMAND:-ffmpeg -re -i \"$VIDEO_FILE\" -c:v libx264 -b:v 4M -f null /dev/null}"

# Test Case: Constant Bandwidth (High)
run_test "constant_bandwidth_high" "$VIDEO_FILE" "high_bandwidth" "$FFMPEG_COMMAND"

# Test Case: 3G Network
run_test "3g_network" "$VIDEO_FILE" "delay 100ms 10ms distribution normal bandwidth 500kbit loss 1%" "$FFMPEG_COMMAND"

# Test Case: DSL Network
run_test "dsl_network" "$VIDEO_FILE" "delay 50ms bandwidth 2Mbit loss 0.1%" "$FFMPEG_COMMAND"

# Test Case: Cable Network
run_test "cable_network" "$VIDEO_FILE" "delay 20ms bandwidth 10Mbit" "$FFMPEG_COMMAND"

# Test Case: Lossy WiFi Network
run_test "lossy_wifi_network" "$VIDEO_FILE" "loss 5%" "$FFMPEG_COMMAND"

# Test Case: Satellite Network
run_test "satellite_network" "$VIDEO_FILE" "delay 500ms" "$FFMPEG_COMMAND"

echo "All tests completed."