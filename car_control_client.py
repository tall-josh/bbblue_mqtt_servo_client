#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import json
import rcpy
import rcpy.servo as servo
import rcpy.clock as clock
from rcpy.servo import esc8

s_command = 0.
t_command = 0.
new_command = False

with open("../config.json", 'r') as f:
    CONFIG = json.load(f)

BROKER        = CONFIG["BROKER_IP"]
PORT          = CONFIG["BROKER_PORT"]
TOPIC_CONTROL = CONFIG["TOPIC_CONTROL"]

def on_message(client, userdata, msg):
  global s_command, t_command, new_command
  topic=msg.topic
  payload = str(msg.payload.decode("utf-8", "ignore"))
  commands = json.loads(payload)
  s_command = commands["steering"]
  t_command = commands["throttle"]
  new_command = True
  print("st: {}, th: {}".format(s_command, t_command))

def clip_value(val, vmin, vmax):
    if val < vmin: val = vmin
    if val > vmax: val = vmax
    return val

# Starting MQTT mosquitto
print("Connecting to broker: {}:{}".format(BROKER, PORT))
print("Subscribe topic: '{}'".format(TOPIC_CONTROL))
client = mqtt.Client("car_client")
client.on_message=on_message
client.connect(BROKER, PORT)
client.loop_start()
client.subscribe(TOPIC_CONTROL)
print("Connected")

# Setup steering servo
rcpy.set_state(rcpy.RUNNING)
steering_servo = servo.Servo(CONFIG["STEERING_PIN"])
#clck = clock.Clock(steering_servo, CONFIG["PWM_PERIOD"])

def apply_steering_command(servo, s_command):
    s_command = clip_value(s_command, CONFIG["STEER_PWM_MIN"],
                                      CONFIG["STEER_PWM_MAX"])
    servo.set(s_command)

# Setup throttle esc. 0.5 is the 'zero throttle'
# command used for arming the esc
esc8.set(0.5)

def apply_throttle_command(t_command):
    t_command = clip_value(t_command, CONFIG["THROTTLE_PWM_MIN"],
                                      CONFIG["THROTTLE_PWM_MAX"])    
    esc8.set(t_command)

def main():
    global s_command, t_command, new_command
    servo.enable()
    steering_servo.start(CONFIG["PWM_PERIOD"])
    esc8.start(CONFIG["PWM_PERIOD"])
    while True:
        try:
            if new_command:
                apply_steering_command(steering_servo, s_command)
                apply_throttle_command(t_command)
                new_command = False
            time.sleep(0.01)
        except KeyboardInterrupt:
            client.loop_stop()
            client.disconnect()
            servo.disable()
            print("car_client, Fucking off...")
            break


if __name__ == "__main__":
  main()
