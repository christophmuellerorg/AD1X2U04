import math

class AD122U04(object):

    # Parameters specific to the AD122U04
    READ_DATA_BYTES = 3
    READ_DATA_BITS = 24
    PART_NO = "AD122U04"

    # Command set
    CMD_SYNC = 0x55
    CMD_RESET = 0x6
    CMD_START = 0x8
    CMD_POWERDOWN = 0x2
    CMD_RDATA = 0x10
    CMD_RREG = 0x20
    CMD_WREG = 0x40
    
    def __init__(self, serial):
        """
        Parameters
        ----------
        serial : pyserial compatible serial interface
        """
        self.serial = serial
        self.serial.open()
    
    # Valid MUX configurations
    MUX_CTRL = {
        (0,1): 0x0,
        (0,2): 0x1,
        (0,3): 0x2,
        (1,0): 0x3,
        (1,2): 0x4,
        (1,3): 0x5,
        (2,3): 0x6,
        (3,2): 0x7,
        0: 0x8, 
        1: 0x9,
        2: 0xA,
        3: 0xB,
        "VREFDIFF": 0xC,
        "ASUPPLYDIFF": 0xD,
        "ASUPPLYCENTER": 0xE
        }
    
    def set_mux(self, value):
        """ Sets the MUX value
        Parameters
        ----------
            value : a key from MUX_CTRL
                valid values:
                (0,1): differential ADC between AN0 and AN1
                (0,2): differential ADC between AN0 and AN2
                (0,3): differential ADC between AN0 and AN3
                (1,0): differential ADC between AN1 and AN0
                (1,2): differential ADC between AN1 and AN2
                (1,3): differential ADC between AN1 and AN3
                (2,3): differential ADC between AN2 and AN3
                (3,2): differential ADC between AN3 and AN2
                0: single ended ADC from AN0
                1: single ended ADC from AN1
                2: single ended ADC from AN2
                3: single ended ADC from AN3
                "VREFDIFF": Differential ADC between the negative and positive VREF
                "ASUPPLYDIFF": Differential ADC between the two analog supplies
                "ASUPPLYCENTER": Differential ADC half way between the analog supplies
        
        Raises
        ------
        ValueError
            If the value is no key in MUX_CTRL
        """
        if value in self.MUX_CTRL:
            reg_0 = self.read_reg(0) & 0x0f
            mux_code = self.MUX_CTRL[value]
            self.write_reg(0, (mux_code<<4) | reg_0)
        else:
            raise ValueError("Invalid MUX setting. Valid settings are: {}".format(", ".join([str(i) for i in self.MUX_CTRL.keys()])))
    
    def get_mux(self):
        """ 
        Returns 
        -------
        str / int / tuple (int, int)
            Corresponding to the key in from MUX_CTRL
        """
        reg_0 = self.read_reg(0)>>4
        for key, value in self.MUX_CTRL.items():
            if value == reg_0:
                return key
            
    def set_gain(self,value):
        """ Sets the gain to the value provided (actual gain, not the register content)
        Parameters
        ----------
        value : int
            limited to one of the supported values (1,2,4,8,16,32,64,128)
        """
        if value in [1,2,4,8,16,32,64,128]:
            reg_0 = self.read_reg(0) & 0xf1
            self.write_reg(0, ((int(math.log2(value))<<1) | reg_0))
        else:
            raise ValueError("Invalid gain. Valid values are powers of two in the range of 1 to 128")
    
    def get_gain(self):
        """ Returns the gain
        """
        gain_reg_value = ( self.read_reg(0) & 0xf) >> 1
        return 2**gain_reg_value


    def set_disable_pga(self, value):
        """ Disables the PGA
        Parameters
        ----------
        value : boolean
            True to disable the PGA, False to enables it. Note that the PGA 
            can only be disabled for a gain of 1, 2, and 4, this setting will 
            be ignored for higher gains. 
        """
        reg_0 = self.read_reg(0) & 0xfe
        if value:
            self.write_reg(0,reg_0 | 0x1)
        else:
            self.write_reg(0,reg_0)

    def get_disable_pga(self):
        """ Returnse the PGA status 
        Returns
        -------
        boolean
            True: PGA disabled
            False: PGA enabled
        """
        return (self.read_reg(0) & 0x1)==1

    DATA_RATES_NORMAL_MODE = {
        20: 0x0,
        45: 0x1,
        90: 0x2,
        175: 0x3,
        330: 0x4,
        600: 0x5,
        1000: 0x6
    }

    DATA_RATES_TURBO_MODE = {
        40: 0x0,
        90: 0x1,
        180: 0x2,
        350: 0x3,
        660: 0x4,
        1200: 0x5,
        2000: 0x6
    }

    def set_data_rate(self, dr):
        """
        Sets the data rate for contineous conversion mode. 
        Based on the supplied value turbo or normal mode is 
        automatically selected, with the latter one takin 
        precedence.  
        
        Parameters
        ----------
        dr : int
            valid data rate for normal or turbo mode:
            DATA_RATES_NORMAL_MODE 
                20, 45, 90, 175, 330, 600, 1000
            DATA_RATES_TURBO_MODE
                40, 90, 180, 350, 660, 1200, 2000

        Raises
        ------
        ValueError 
            if the data rate is not supported in either normal 
            or turbo mode
        """
        reg_1 = self.read_reg(0) & 0x0f
        if dr in self.DATA_RATES_NORMAL_MODE:
            drv = self.DATA_RATES_NORMAL_MODE[dr]
            self.write_reg(1,(drv<<5) | reg_1)
        elif dr in self.DATA_RATES_TURBO_MODE:
            drv = self.DATA_RATES_TURBO_MODE[dr]
            self.write_reg(1,((drv<<5) + 16) | reg_1)
        else:
            raise ValueError("Invalid data rate.")
    def get_data_rate(self):
        """ Get the current data rate
        Returns
        -------
        tuple (int, bool)
            (data rate, turbo mode)

        """
        reg_1 = (self.read_reg(0) & 0xf0) >> 4
        turbomode = bool(reg_1 & 0x1)
        drv = reg_1 >> 1
        dr = 0
        if turbomode:
            for key, value in self.DATA_RATES_TURBO_MODE.items():
                if value == drv:
                    dr = key
                    break
        else: 
            for key, value in self.DATA_RATES_NORMAL_MODE.items():
                if value == drv:
                    dr = key
                    break
        return (dr, turbomode)
    
    VREF = {
        "INTERNAL": 0x0,
        "EXTERNAL": 0x1,
        "ANALOGSUPPLY": 0x2
    }
    
    def set_vref(self, value):
        """ 
        Sets the reference voltage
        Parameter
        ---------
        value : str
            a valid key from VREF (INTERNAL, EXTERNAL, ANALOGSUPPLY)
        
        Raises
        ------
        ValueError

        """
        reg_1 = (self.read_reg(0) & 0xf1)
        if value in self.VREF:
            self.write_reg(1, reg_1 | (self.VREF[value] << 1))
        else:
            raise ValueError("Invalid value {} - choose one of {}".format(value, ", ".join(VREF.keys())))
        
    def get_vref(self):
        """ 
        """
        vref = (self.read_reg(0) & 0x07) >> 1
        if vref == 0x3:
            vref = 0x2
        for key, value in self.VREF.items():
            if value == vref:
                return key
        
    def set_gpio(self,io, value):
        pass

    def set_gpio_dir(self, io, dir):
        pass

    def get_gpio(self, io):
        pass

    def reset(self):
        self.serial.write(bytearray([self.CMD_SYNC, self.CMD_RESET]))
    
    def start(self):
        self.serial.write(bytearray([self.CMD_SYNC, self.CMD_START]))
    
    def powerdown(self):
        self.serial.write(bytearray([self.CMD_SYNC, self.CMD_POWERDOWN]))
    
    def read_reg(self,reg):
        """ 
        Low level function to read a register
        Paramter
        --------
        reg : int

        Returns
        -------
        int
            The register read address
        """
        _reg = self.CMD_RREG | (0xf & (reg*2))
        self.serial.write(bytearray([self.CMD_SYNC, _reg]))
        return int.from_bytes(self.serial.read(), signed=False, byteorder="little")
        
    def write_reg(self,reg, data):
        """
        Low level function to write a register

        Parameter
        ---------
        reg : int
            The register write address

        data : int
            The data to write to the register
        """
        _reg = self.CMD_WREG | (0xf & (reg*2))
        word = bytearray([int(self.CMD_SYNC), int(_reg), data])
        self.serial.write(word)
        return    
    
    def read_raw_data(self):
        self.serial.write(bytearray([self.CMD_SYNC, self.CMD_RDATA]))
        data = self.serial.read(self.READ_DATA_BYTES)
        return data
    
    def read_data(self):
        self.start()
        data = self.read_raw_data()
        return int.from_bytes(data,'little',signed=True)

# untested, but should work as the part is very similar, except for 2 instead of 3 data bytes
class AD112U04(AD122U04):
    READ_DATA_BYTES = 2
    READ_DATA_BITS = 16
    PART_NO = "AD112U04"