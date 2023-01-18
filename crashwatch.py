#!/bin/python
# Crashwatch is a python script that monitors a file (e.g. Linux kernel log)
# for an error message or any phrase, and runs a command whenever that phrase
# is found.

import os, sys, platform, logging, time, subprocess

# Loads and returns configuration from a given file path, or returns False if invalid
def load_config(path):
  config = {}

  # If the file exists, load it
  if os.path.exists(path):
    try:
      with open(path,'r') as config_file:
        # Go through each line, separate key from value, and store them in the config variable
        for line in config_file.readlines():
          separator_pos = line.find('=')
          # Skip invalid lines
          if separator_pos==-1:
            continue
          key = line[0:separator_pos].strip()
          value = line[separator_pos+1:].strip()
          config[key] = value
      # Check that the required parameters were included in the configuration file, otherwise return False
      if ("trigger-file" in config and
          "trigger-phrase" in config and
          "command" in config and
          "poll-rate" in config) == False:
        return False
      # Convert to appropriate variable types
      config["poll-rate"] = float(config["poll-rate"])
      config["skip-initial-triggers"] = "skip-initial-triggers" in config and (config["skip-initial-triggers"].strip().lower()=="true")
    # If there's an error reading the file, return False
    except:
      return False
  # If the file doesn't exist, return False
  else:
    return False

  return config

# Uses a modified version of the KMP algorithm to determine how many characters of a pattern
# were matched in some text. This function is called separately for each character.
def kmp(pattern, prefix_array, current_char, pos, prefix):
  pos-=1
  while pos!=-1 and (prefix+1==len(pattern) or pattern[prefix+1]!=current_char):
    pos = prefix
    prefix = prefix_array[max(prefix,0)]
  if pos==-1:
    return -1
  else:
    return prefix+1

# Main function
if __name__ == "__main__":
  # Load config
  config_path = "crashwatch.conf"
  config = load_config(config_path)
  if config == False:
    if platform.system() == "Windows":
      config_path = os.environ.get("AppData") + "\\crashwatch.conf"
      config = load_config(config_path)
    elif platform.system() == "Linux":
      config_path = os.environ.get("HOME") + "/.config/crashwatchrc"
      config = load_config(config_path)
      if config == False:
        config_path = "/etc/crashwatch.conf"
        config = load_config(config_path)
    else:
      config_path = "/etc/crashwatch.conf"
      config = load_config(config_path)


  # Set up logging
  log_format = "%(asctime)s %(message)s"
  log_handlers = []
  log_level = logging.INFO
  # Output to stderr, if not running in Windows non-console mode
  if sys.stderr!=None:
    log_handlers.append(logging.StreamHandler())

  # Exit if no valid config file could be loaded
  if config == False:
    logging.basicConfig(handlers=log_handlers, format=log_format, level=log_level)
    logging.critical("No valid config file could be loaded.")
    sys.exit()

  # Output to log file if a log directory was specified in the config file
  if "log-dir" in config:
    # Make directory if it doesn't already exist
    os.makedirs(config["log-dir"], exist_ok=True)
    log_handlers.append(logging.FileHandler(time.strftime(config["log-dir"]+"/crashwatch-%Y%m%d-%H%M%S.log")))
  logging.basicConfig(handlers=log_handlers, format=log_format, level=log_level)

  # Print config info
  logging.info(f"Loaded configuration file from '{config_path}':")
  logging.info("trigger-file="+config["trigger-file"])
  logging.info("trigger-phrase="+config["trigger-phrase"])
  logging.info("command="+config["command"])
  logging.info("poll-rate="+str(config["poll-rate"]))
  logging.info("skip-initial-triggers="+str(config["skip-initial-triggers"]))
  if "log-dir" in config:
    logging.info("log-dir="+config["log-dir"])

  # Open file that will be monitored
  monitor = open(config["trigger-file"])

  # Prepare KMP algorithm
  pattern_length = len(config["trigger-phrase"])
  pattern_prefixes = [0]*pattern_length
  pattern_prefixes[0] = -1
  current_pos = 0
  current_prefix = -1
  for c in config["trigger-phrase"]:
    if current_pos!=0:
      current_prefix = kmp(config["trigger-phrase"], pattern_prefixes, c, current_pos, current_prefix)
      pattern_prefixes[current_pos] = current_prefix
    current_pos+=1

  # Start polling and reading trigger file
  f = open(config["trigger-file"])
  if config["skip-initial-triggers"]:
    f.read()
  while True:
    for c in f.read():
      current_prefix = kmp(config["trigger-phrase"], pattern_prefixes, c, current_pos, current_prefix)
      current_pos+=1
      # When the whole phrase is matched, run the set command
      if current_prefix==pattern_length-1:
        logging.info("Phrase matched, running command.")
        if platform.system() == "Windows":
          subprocess.run(["cmd","/C",config["command"]])
        else:
          subprocess.run(["sh","-c",config["command"]])
    # Wait until next poll
    time.sleep(config["poll-rate"])
