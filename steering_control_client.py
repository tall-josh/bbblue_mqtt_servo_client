#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import json
import rcpy
import rcpy.servo as servo
import rcpy.clock as clock
#from rcpy.servo import esc8

ZERO_THROTTLE=0.5
running=True
steering_servo=None

with open("config.json", 'r') as f:
  CONFIG = json.load(f)

BROKER         = CONFIG["BROKER_IP"]
PORT           = CONFIG["BROKER_PORT"]
STEERING_TOPIC = CONFIG["STEERING_TOPIC"]
THROTTLE_TOPIC = CONFIG["THROTTLE_TOPIC"]

def clip_value(val, vmin, vmax):
  if val < vmin: val = vmin
  if val > vmax: val = vmax
  return val

def init_steering(init_data):
  global steering_servo
  # Setup steering servo
  rcpy.set_state(rcpy.RUNNING)
  servo.enable()
  steering_servo = servo.Servo(init_data["channel"])
  steering_servo.start(init_data["pwm_period"])
  print("Steering initialized. YOU LOVELY PERSON!")

def apply_steering_command(s_command):
  global steering_servo
  print("st: {}".format(s_command))
  s_command = clip_value(s_command, CONFIG["STEER_PWM_MIN"],
                                    CONFIG["STEER_PWM_MAX"])
  steering_servo.set(s_command)

def on_message_steering(client, userdata, msg):
#  topic=msg.topic
  payload = str(msg.payload.decode("utf-8", "ignore"))
  command = json.loads(payload)
  if "control" in command:
    value = command["control"]
    apply_steering_command(value)
  elif "init" in command:
    init_data = commnad["init"]
    init_steering(init_data)
  else:
    print("WARNING! steering command invalid: '{}'".format(commands))

def on_disconnect_steering(client, userdata, msg):
  global steering_servo
  steering_servo.disable()

def init_throttle(init_data):
  global throttle_servo
  # Setup throttle esc. 0.5 is the 'zero throttle'
  # command used for arming the esc
  throttle_servo = servo.Servo(init_data["channel"])
  throttle_servo.set(init["pwm_zero"])
  throttle_servo.start(init["pwm_period"])
  print("Throttle initialized. NICE ONE COBBA!")

def apply_throttle_command(t_command):
  global throttle_esc
  print("th: {}".format(t_command))
  t_command = clip_value(t_command, CONFIG["THROTTLE_PWM_MIN"],
                                    CONFIG["THROTTLE_PWM_MAX"])
  throttle_esc.set(t_command)

def on_message_throttle(client, userdata, msg):
#  topic=msg.topic
  payload = str(msg.payload.decode("utf-8", "ignore"))
  command = json.loads(payload)
  if "control" in command:
    value = command["control"]
    apply_throttle_command(value)
  elif "init" in conmmand:
    init_data = command["init"]
    init_throttle(init_data)
  else:
    print("WARNING! throttle command invalid: '{}'".format(commands))

def on_disconnect_throttle(client, userdata, msg):
  global throttle_esc
  pass


def main():
  global steering_servo, throttle_esc
  # Starting MQTT mosquitto
  client_steering = mqtt.Client("steering_client")
  client_steering.on_message=on_message_steering
  client_steering.on_disconnect=on_disconnect_steering
  client_steering.connect(BROKER, PORT)
  client_steering.loop_start()
  client_steering.subscribe(STEERING_TOPIC)
  print("Steering Connected")

  client_throttle = mqtt.Client("throttle_client")
  client_throttle.on_message=on_message_throttle
  client_steering.on_disconnect=on_disconnect_steering
  client_throttle.connect(BROKER, PORT)
  client_throttle.loop_start()
  client_throttle.subscribe(THROTTLE_TOPIC)
  print("Throttle Connected")

  while running:
    try:
      time.sleep(0.01)
    except KeyboardInterrupt:
      client_steering.loop_stop()
      client_steering.disconnect()
      client_throttle.loop_stop()
      client_throttle.disconnect()
      servo.disable()
      running = False

  print("Fucking off...")

if __name__ == "__main__":
  main()
