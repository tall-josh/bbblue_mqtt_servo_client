#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import json
import rcpy
import rcpy.servo as servo
import rcpy.clock as clock
from rcpy.servo import esc8

ZERO_THROTTLE=0.5
running=True
steering_servo=None

with open("config.json", 'r') as f:
  CONFIG = json.load(f)

BROKER        = CONFIG["BROKER_IP"]
PORT          = CONFIG["BROKER_PORT"]
TOPIC_CONTROL = CONFIG["TOPIC_CONTROL"]

def on_message(client, userdata, msg):
  global running, steering_servo

  topic=msg.topic
  payload = str(msg.payload.decode("utf-8", "ignore"))
  print("MESSAGE: {}".format(payload))
  commands = json.loads(payload)
  if "steering" in commands:
    s_command = commands["steering"]
    apply_steering_command(s_command)
    try:
      t_command = commands["throttle"]
      apply_throttle_command(t_command)
    except KeyError as e:
      pass
  elif "init" in commands:
    # Setup steering servo
    rcpy.set_state(rcpy.RUNNING)
    steering_servo = servo.Servo(CONFIG["STEERING_PIN"])
    # Setup throttle esc. 0.5 is the 'zero throttle'
    # command used for arming the esc
    esc8.set(ZERO_THROTTLE)
    servo.enable()
    steering_servo.start(CONFIG["PWM_PERIOD"])
    esc8.start(CONFIG["PWM_PERIOD"])
    print("servos initialized. NICE ONE COBBA!")
  elif "stop" in commands:
    client.loop_stop()
    client.disconnect()
    servo.disable()
    running = False
  else:
    print("WARNING! command invalid: '{}'".format(commands))
    running = False
    

def clip_value(val, vmin, vmax):
  if val < vmin: val = vmin
  if val > vmax: val = vmax
  return val

def apply_steering_command(s_command):
  global steering_servo
  print("st: {}".format(s_command))
  s_command = clip_value(s_command, CONFIG["STEER_PWM_MIN"],
                                    CONFIG["STEER_PWM_MAX"])
#  print(s_command)
  steering_servo.set(s_command)


def apply_throttle_command(t_command):
  print("th: {}".format(t_command))
  t_command = clip_value(t_command, CONFIG["THROTTLE_PWM_MIN"],
                                    CONFIG["THROTTLE_PWM_MAX"])    
  esc8.set(t_command)

def main():
  # Starting MQTT mosquitto
  print("Connecting to broker: {}:{}".format(BROKER, PORT))
  print("Subscribe topic: '{}'".format(TOPIC_CONTROL))
  client = mqtt.Client("car_client")
  client.on_message=on_message
  client.connect(BROKER, PORT)
  client.loop_start()
  client.subscribe(TOPIC_CONTROL)
  print("Connected")
  while running:
    try:
      time.sleep(0.01)
    except KeyboardInterrupt:
      client.loop_stop()
      client.disconnect()
      servo.disable()
      print("car_client, Fucking off...")
      break


if __name__ == "__main__":
  main()
