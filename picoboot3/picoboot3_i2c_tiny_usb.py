"""
Copyright (c) 2025 Modac
SPDX-License-Identifier: MIT
"""
from .picoboot3 import Picoboot3


class Picoboot3i2cTinyUsb(Picoboot3):
  """
  I2C interface bootloader

  Attributes:
    vendor_id: I2C-Tiny-Usb vendor id
    product_id: I2C-Tiny-Usb product id
    device_address : I2C device address
    verbous: Display logs on screen if True
    activate_response : 4 Bytes of activation response. Use the value specified in the bootloader. 
    appcode_offset: App code address offset. Use the value specified in the bootloader. 
    transfer_size: Number of pages to transfer per one read or program command. 1-16. 
                   Small number is safe, large number is fast. 
  """

  def __init__(
      self,
      vendor_id,
      product_id,
      device_address,
      verbous=False,
      activate_response=b'pbt3',
      appcode_offset=32 * 1024,
      transfer_size=2,
  ):
    super().__init__(verbous=verbous,
                     activate_response=activate_response,
                     appcode_offset=appcode_offset,
                     transfer_size=transfer_size)
    self.vendor_id = vendor_id
    self.product_id = product_id
    self.device_address = device_address

    import usb.core
    self.i2c_usb_dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
    print("I2C-tiny-usb dev: {}".format(self.i2c_usb_dev))

  def receive_bytes_old(self, length):
    """
    Receive bytes from device
    
    Args:
      length: Number of bytes to read
    
    Returns:
      bytes: received data
    """
    import usb.core
    # See:
    print("I2C-tiny-usb rec: {}".format(length))
    msg = self.i2c_usb_dev.ctrl_transfer((0x02<<5)|0x80, 4 + 1 + 2, 1, self.device_address, length, 1000)
    print("I2C-tiny-usb rec msg: {}".format(msg))
    # TODO: check status
    import time
    time.sleep(100/1000)
    return bytes(msg)
  
  
  def receive_bytes(self, length):
    """
    Receive data in a single I2C transaction with 64-byte chunks.
    
    Args:
      length: Total bytes to read
    Returns:
      bytes: Received data
    """

    #print("I2C-tiny-usb rec: {}".format(length))

    import usb.core
    import time
    max_chunk = 32
    received = bytearray()
    remaining = length
    chunk_count = 0

    while remaining > 0:
        chunk_size = min(remaining, max_chunk)
        
        # Set I2C cmd
        bRequest = 4  # CMD_I2C_IO
        if chunk_count == 0:
            bRequest += 1  # CMD_I2C_BEGIN
        if chunk_size == remaining:
            bRequest += 2  # CMD_I2C_END

        msg = self.i2c_usb_dev.ctrl_transfer(
            0xC0,          # bmRequestType: Vendor Device-to-Host ((0x02<<5)|0x80)
            bRequest,             # bRequest
            1,                    # wValue: I2C_M_RD
            self.device_address,  # wIndex: Device address
            chunk_size,    # Number of bytes to read
            1000           # Timeout
        )
        #print("I2C-tiny-usb rec {}: {}".format(chunk_count, bytes(msg).hex('-')))
        
        received.extend(msg)
        #remaining -= len(msg)
        remaining -= chunk_size
        chunk_count += 1
        time.sleep(0.01)  # Short delay

    #print("I2C-tiny-usb rec msg: {}".format(bytes(received).hex('-')))
    return bytes(received)

  def send_bytes_old(self, data):
    """
    Send bytes data to device

    Args:
      data: data to be sent in bytes type (e.g. bytes([0x00, 0xFF]))
    """
    import usb.core
    # See:
    print("I2C-tiny-usb send (addr: {}): {}".format(self.device_address, data))
    msg = self.i2c_usb_dev.ctrl_transfer((0x02<<5), 4 + 1 + 2, 0, self.device_address, data, 1000)
    print("I2C-tiny-usb send ret: {}".format(msg))
    # TODO: check status
    import time
    time.sleep(100/1000)

  def send_bytes(self, data):
    """
    Send data in a single I2C transaction with 64-byte chunks.
    
    Args:
      data: Bytes to send (single I2C transaction)
    """

    #print("I2C-tiny-usb send (addr: {}): {}".format(self.device_address, data.hex('-')))

    import usb.core
    import time
    max_chunk = 32
    total_len = len(data)
    num_chunks = (total_len + max_chunk - 1) // max_chunk  # Ceiling division
    total_sent = 0

    for i in range(num_chunks):
        start = i * max_chunk
        end = start + max_chunk
        chunk = data[start:end]
        
        # Set I2C cmd
        bRequest = 4  # CMD_I2C_IO
        if i == 0:
            bRequest += 1  # CMD_I2C_BEGIN
        if i == num_chunks - 1:
            bRequest += 2  # CMD_I2C_END

        #print("I2C-tiny-usb send {}: {}".format(i, bytes(chunk).hex('-')))
        total_sent += self.i2c_usb_dev.ctrl_transfer(
            0x40,                 # bmRequestType: Vendor Host-to-Device (0x02<<5)
            bRequest,             # bRequest
            0,                    # wValue
            self.device_address,  # wIndex: Device address
            chunk,                # Data payload
            1000                  # Timeout
        )
        time.sleep(0.01)  # Short delay

    #print("I2C-tiny-usb send ret: {}".format(total_sent))