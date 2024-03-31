"""Device driver for the Waveshare Pico OLED 1.3inch display.

This driver is based on the SH1107 driver from peter-l5/SH1107 library.
https://github.com/peter-l5/SH1107
Pin definitions can be found in https://www.waveshare.com/wiki/Pico-OLED-1.3
@Author: HCui91
@Repo: https://github.com/HCui91/pico_tfl_departure_board
"""
from sh1107 import SH1107_SPI
from machine import SPI, Pin

# Pin definition
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9


class PICO_OLED_1P3INCH(SH1107_SPI):

    white = 0xffff
    black = 0x0000

    def __init__(self, rotate=0, external_vcc=False, delay_ms=0):
        width = 128
        height = 64
        cs = Pin(CS, Pin.OUT)
        res = Pin(RST, Pin.OUT)

        cs(1)
        spi = SPI(1)
        spi = SPI(1, 2000_000)
        spi = SPI(1, 20000_000, polarity=0, phase=0,
                  sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        dc = Pin(DC, Pin.OUT)
        dc(1)

        self.key0 = Pin(15, Pin.IN, Pin.PULL_UP)
        self.key1 = Pin(17, Pin.IN, Pin.PULL_UP)

        super().__init__(width, height, spi, dc, res, cs, rotate, external_vcc, delay_ms)

    def clear(self, now=False):
        self.fill(self.black)
        if now:
            self.show()
        return True
