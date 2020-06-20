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


# This the the IP address at which the Wavefront Proxy is installed. The
# assumption is that the Wavefront Proxy is installed on localhost. If the
# proxyis installed anywhere else, please set the IP address accordingly

_PROXY_HOST_IP = '127.0.0.1'

# The port at which Wavefront proxy is listening. This is set to the default
# port.

_PROXY_HOST_PORT = 2878

# The wait between sending two datasets to the Wavefront proxy so that the
# proxy doesnt get overwhelmed. Do not change this unless you have a large
# data to send.
_WAIT_BETWEEN_SENDS_SECONDS = 0.5

# The number of wavefront streams that are send in a batch to the proxy before
# we wait for the above duration

_SEND_BATCH_SIZE = 100

# The source that you want to use for wavefront data. If you have multiple
# vectors, you can use different sources to distinguish the data on Wavefront
_WAVEFRONT_SOURCE = 'my_vector'


import socket
import time

class WavefrontAgent:
   """An Agent that can send data in the correct format to the wavefront proxy
   All datapoints of an agent are sent for the same time instance, therefore a
   wavefront agant must be reated for every time instance for which we want to
   send data to the Wavefront proxy.
   """
   @classmethod
   def netcat(cls, content):
      """A python implementation of netcat to send
         data to wavefront proxy
         @param content Content that needs to be transmitted
         @return True/False representing success/ failure.
      """
      s = None
      try:
         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         s.connect((_PROXY_HOST_IP, _PROXY_HOST_PORT))
         s.sendall(content.encode())
         s.shutdown(socket.SHUT_WR)
      except Exception as e:
         print (e)
         return False
      if s:
         s.close()
      return True

   def sendWithThrottle(self):
      """
         Send the wavefrontStream to the Wavefront proxy. Takes breaks in
         between so as not to overwhelm the Wavefront proxy
      """
      start = 0
      size = len(self.wavefrontStream)

      while start < size:
         if (size - start) <= _SEND_BATCH_SIZE:
            content = '\n'.join(self.wavefrontStream)
         else:
            content = '\n'.join(self.wavefrontStream[start:start + _SEND_BATCH_SIZE])

         content += '\n'
         print (content)
         dataSent = WavefrontAgent.netcat(content)
         if not dataSent:
            print("Error in sending data to proxy")
         else:
            print("Succesfully sent data to Wavefront")
         time.sleep(_WAIT_BETWEEN_SENDS_SECONDS)
         start += _SEND_BATCH_SIZE

   def __init__(self, timestamp):
      self.wavefrontStream = []
      self.datetimeStr = timestamp.strftime('%s')

   def appendToStream(self, metric, value, source=None, tags=None):
      """
         Creates a new string in the format that Wavefront accepts and
         appends it to wavefrontStream
         @param metric
         @param value
         @param tags Optional tags that a metric/value can be associated with
         in wavefront
      """
      if value:
         if not source:
            source = _WAVEFRONT_SOURCE
         wavefrontStr = '%s %f %s source=%s' % (metric,
                                                value,
                                                self.datetimeStr,
                                                source)
         if tags is not None:
            wavefrontStr += tags
         self.wavefrontStream.append(wavefrontStr)
      else:
         return
