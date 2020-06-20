#!/usr/bin/env python3

# Copyright (c) 2018 Amitabha Banerjee
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import anki_vector
import datetime
import time
import math
import argparse

from wavefrontAgent import WavefrontAgent

_MONITORING_INTERVAL = 30

def getStates(status):
   """
      Returns a list of states, given the current status of the robot
      @param status
      @return List of states
   """
   result = []

   if status.are_motors_moving:
      result.append('MOTOR_MOVING')
   if status.are_wheels_moving:
      result.append('WHEEL_MOVING')
   if status.is_animating:
      result.append('IS_ANIMATING')
   if status.is_being_held:
      result.append('IS_BEING_HELD')
   if status.is_carrying_block:
      result.append('IS_CARRYING_BLOCK')
   if status.is_charging:
      result.append('IS_CHARGING')
   if status.is_docking_to_marker:
      result.append('IS_DOCKING_TO_MARKER')
   if status.is_falling:
      result.append('IS_FALLING')
   if status.is_in_calm_power_mode:
      result.append('IS_IN_CALM_POWER_MODE')
   if status.is_lift_in_pos:
      result.append('IS_LIFT_ON_POS')
   if status.is_on_charger:
      result.append('IS_ON_CHARGER')
   if status.is_pathing:
      result.append('IS_PATHING')
   if status.is_picked_up:
      result.append('IS_PICKED_UP')
   if status.is_robot_moving:
      result.append('IS_ROBOT_MOVING')
   return result

def createWavefrontAgent(kvDict, source=None):
   """
      Creates a Wavefrom Agent using an input key-value dictionary
      All data in this input key-value dictionary will be transmitted to
      wavefront using the current local time
      @param kvDict INput key-value dictionary
      @return A Wavefront Agent
   """
   localTime = datetime.datetime.now()
   wavefrontAgent = WavefrontAgent(localTime)
   for key, value in kvDict.items():
      wavefrontAgent.appendToStream(key, value, source)
   return wavefrontAgent

def getDistanceTravelled(previousPose, currentPose):
   """
      Get the distance between the previous pose and the current pose
      @return Returns the distance in mm
   """
   prevPosition = previousPose.position
   curPosition = currentPose.position
   distance = math.sqrt((curPosition.x - prevPosition.x)**2 + \
                        (curPosition.y - prevPosition.y)**2 + \
                        (curPosition.z - prevPosition.z)**2)
   return distance

def parse():
   parser = argparse.ArgumentParser()
   parser.add_argument("-s", "--serial",
                       help="Serial Number",
                       default=None)
   args = parser.parse_args()
   return args

def main():
   args = parse()
   serial = args.serial
   if serial:
      robot = anki_vector.Robot(serial)
   else:
      robot = anki_vector.Robot()

   previousPose = None
   print ("Starting to monitor vector. Ctrl-C to exit monitoring")
   while True:
      try:
         robot.connect()
      except anki_vector.exceptions.VectorException as vectorEx:
         print (vectorEx)
         robot.disconnect()
         time.sleep()
         continue
      except Exception as ex:
         print ("Some other exception received")
         print (ex)
         robot.disconnect()
         time.sleep(_MONITORING_INTERVAL)
         continue
      batteryState = robot.get_battery_state()
      if batteryState:
         batteryVoltage = batteryState.battery_volts
         batteryLevel = batteryState.battery_level
      else:
         batteryVoltage = None
         batteryLevel = None
      status = robot.status
      rspeed = robot.right_wheel_speed_mmps
      lspeed = robot.left_wheel_speed_mmps
      gyro = robot.gyro
      accel = robot.accel
      currentPose = robot.pose
      if previousPose:
         if (currentPose.is_comparable(previousPose)):
            distanceTravelled = getDistanceTravelled(previousPose, currentPose)
         else:
            distanceTravelled = None
      else:
         distanceTravelled = None
      previousPose = currentPose
      if currentPose:
         position = currentPose.position
      touch_data = robot.touch.last_sensor_reading
      if touch_data is not None:
         raw_touch_value = touch_data.raw_touch_value
         is_being_touched = touch_data.is_being_touched
      else:
         (is_being_touched, raw_touch_value) = (None, None)
      lastValidSensorReading = robot.proximity.last_sensor_reading
      if lastValidSensorReading:
         obstacleDistance = lastValidSensorReading.distance.distance_mm
      else:
         obstacleDistance = None
      dataValDict = {}
      dataValDict['vector.batteryvolts'] = batteryVoltage
      dataValDict['vector.batterylevel'] = batteryLevel
      dataValDict['vector.rspeed'] = rspeed
      dataValDict['vector.lspeed'] = lspeed
      dataValDict['vector.distance'] = distanceTravelled
      dataValDict['vector.touch.isTouched'] = is_being_touched
      dataValDict['vector.touch.rawTouchValue'] = raw_touch_value
      dataValDict['vector.obstacleDistance'] = obstacleDistance
      if gyro:
         (x, y, z) = gyro.x_y_z
         dataValDict['vector.gyro.x'] = x
         dataValDict['vector.gyro.y'] = y
         dataValDict['vector.gyro.z'] = z
      if accel:
         (x, y, z) = accel.x_y_z
         dataValDict['vector.accel.x'] = x
         dataValDict['vector.accel.y'] = y
         dataValDict['vector.accel.z'] = z
      wavefrontAgent = createWavefrontAgent(dataValDict, source=serial)
      stateList = getStates(status)
      if len(stateList) > 0:
         dataValDict['vector.currentstate'] = 1
         tag = ""
         for state in stateList:
            tag += ' %s=1' %(state)
         wavefrontAgent.appendToStream('vector.currentstate', 1, source=serial, tags=tag)
      wavefrontAgent.sendWithThrottle()
      try:
         robot.disconnect()
      except anki_vector.exceptions.VectorException as vectorEx:
         print (vectorEx)
         continue
      except Exception as ex:
         print ("Some other exception received")
         print (ex)
         time.sleep(_MONITORING_INTERVAL)
         continue
      time.sleep(_MONITORING_INTERVAL)

if __name__ == "__main__":
   main()
