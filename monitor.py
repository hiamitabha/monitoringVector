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

from wavefrontAgent import WavefrontAgent

_MONITORING_INTERVAL = 30

def getStates(status):
   """
      Returns a list of states, given the current status of the robot
      @param status
      @return List of states
   """
   result = []
   IS_MOVING = (0x1, 'IS_MOVING')
   IS_CARRYING_BLOCK = (0x2, 'IS_CARRYING_BLOCK')
   IS_PICKING_OR_PLACING = (0x4, 'IS_PICKING_OR_PLACING')
   IS_PICKED_UP = (0x8, 'IS_PICKED_UP')
   IS_BUTTON_PRESSED = (0x10, 'IS_BUTTON_PRESSED')
   IS_FALLING = (0x20, 'IS_FALLING')
   IS_ANIMATING = (0x40, 'IS_ANIMATING')
   IS_PATHING = (0x80, 'IS_PATHING')
   LIFT_IN_POS = (0x100, 'LIFT_IN_POS')
   HEAD_IN_POS = (0x200, 'HEAD_IN_POS')
   CALM_POWER_MODE = (0x400, 'CALM_POWER_MODE')
   IS_BATTERY_DISCONNECTED = (0x800, 'IS_BATTERY_DISCONNECTED')
   IS_ON_CHARGER = (0x1000, 'IS_ON_CHARGER')
   IS_CHARGING = (0x2000, 'IS_CHARGING')
   CLIFF_DETECTED = (0x4000, 'CLIFF_DETECTED')
   ARE_WHEELS_MOVING = (0x8000, 'ARE_WHEELS_MOVING')
   IS_BEING_HELD = (0x10000, 'IS_BEING_HELD')
   IS_MOTION_DETECTED = (0x20000, 'IS_MOTION_DETECTED')
   IS_BATTERY_OVERHEATED = (0x40000, 'IS_BATTERY_OVERHEATED')

   checkList = [IS_MOVING, IS_CARRYING_BLOCK, IS_PICKING_OR_PLACING,
                IS_PICKED_UP, IS_BUTTON_PRESSED, IS_FALLING, IS_ANIMATING,
                IS_PATHING, LIFT_IN_POS, HEAD_IN_POS, CALM_POWER_MODE,
                IS_BATTERY_DISCONNECTED, IS_ON_CHARGER, IS_CHARGING,
                CLIFF_DETECTED, ARE_WHEELS_MOVING,
                IS_BEING_HELD, IS_MOTION_DETECTED, IS_BATTERY_OVERHEATED]

   if status is not None:
      for check in checkList:
         if (status & check[0]):
            result.append(check[1])
   return result

def createWavefrontAgent(kvDict):
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
      wavefrontAgent.appendToStream(key, value)
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

def main():
   args = anki_vector.util.parse_command_args()
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
      lastValidSensorReading = robot.proximity.last_valid_sensor_reading
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
      wavefrontAgent = createWavefrontAgent(dataValDict)
      stateList = getStates(status)
      if len(stateList) > 0:
         dataValDict['vector.currentstate'] = 1
         tag = ""
         for state in stateList:
            tag += ' %s=1' %(state)
         wavefrontAgent.appendToStream('vector.currentstate', 1, tag)
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
