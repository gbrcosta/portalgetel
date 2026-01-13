#!/bin/bash
# Detect current serial device (prefer ttyUSB* or ttyACM*) and create udev rule
# This script must be run with sudo to write to /etc/udev/rules.d

set -e

SYMLINK_NAME="portal_rfid"
RULE_FILE="/etc/udev/rules.d/99-portal-rfid.rules"

# find first ttyUSB or ttyACM that has a sysfs entry with idVendor
DEV=""
for p in /dev/ttyUSB* /dev/ttyACM*; do
  [ -e "$p" ] || continue
  SYSFS="/sys/class/tty/$(basename "$p")/device"
  if [ -e "$SYSFS" ]; then
    # walk up to usb device dir to check idVendor
    USB_DIR=$(readlink -f "$SYSFS")
    while [ ! -e "$USB_DIR/idVendor" ] && [ "$USB_DIR" != "/" ]; do
      USB_DIR=$(dirname "$USB_DIR")
    done
    if [ -e "$USB_DIR/idVendor" ]; then
      DEV="$p"
      break
    fi
  fi
done

# fallback: pick any existing if none found above
if [ -z "$DEV" ]; then
  for p in /dev/ttyUSB* /dev/ttyACM*; do
    [ -e "$p" ] || continue
    DEV="$p"
    break
  done
fi

if [ -z "$DEV" ]; then
  echo "No serial device found (no /dev/ttyUSB* or /dev/ttyACM*). Plug the device and retry." >&2
  exit 1
fi

# resolve sysfs path
DEV_BASENAME=$(basename "$DEV")
SYSFS_PATH="/sys/class/tty/$DEV_BASENAME/device"
if [ ! -e "$SYSFS_PATH" ]; then
  echo "Cannot find sysfs entry for $DEV" >&2
  exit 1
fi

# Walk up to usb device dir
USB_DIR=$(readlink -f "$SYSFS_PATH")
while [ ! -e "$USB_DIR/idVendor" ] && [ "$USB_DIR" != "/" ]; do
  USB_DIR=$(dirname "$USB_DIR")
done

if [ ! -e "$USB_DIR/idVendor" ]; then
  echo "Could not find idVendor for device $DEV" >&2
  exit 1
fi

VENDOR=$(cat "$USB_DIR/idVendor")
PRODUCT=$(cat "$USB_DIR/idProduct")
SERIAL=""
if [ -e "$USB_DIR/serial" ]; then
  SERIAL=$(cat "$USB_DIR/serial")
fi

echo "Found device $DEV -> vendor:$VENDOR product:$PRODUCT serial:$SERIAL"

# build udev rule
if [ -n "$SERIAL" ]; then
  RULE="ATTRS{idVendor}==\"$VENDOR\", ATTRS{idProduct}==\"$PRODUCT\", ATTRS{serial}==\"$SERIAL\", SYMLINK+=\"$SYMLINK_NAME\""
else
  RULE="ATTRS{idVendor}==\"$VENDOR\", ATTRS{idProduct}==\"$PRODUCT\", SYMLINK+=\"$SYMLINK_NAME\""
fi

# write rule
cat > "$RULE_FILE" <<EOF
# udev rule created by install_udev_rule.sh
# Creates /dev/$SYMLINK_NAME for the RFID reader
ACTION=="add", $RULE
EOF

udevadm control --reload-rules
udevadm trigger --attr-match=idVendor=$VENDOR --attr-match=idProduct=$PRODUCT

echo "Wrote rule to $RULE_FILE and triggered udev. You should now see /dev/$SYMLINK_NAME when device is plugged."
