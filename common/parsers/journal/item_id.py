
class ItemId(object):
    '''
    2**1 = 2
    2**2 = 4
    2**3 = 8
    2**4 = 16
    2**5 = 32
    2**6 = 64
    2**7 = 128
    2**8 = 256
    2**9 = 512
    2**10 = 1024
    2**11 = 2048
    2**12 = 4096
    2**13 = 8192
    2**14 = 16384
    2**15 = 32768
    2**16 = 65536
    2**17 = 131072
    2**18 = 262144
    2**19 = 524288
    2**20 = 1048576
    2**21 = 2097152
    2**22 = 4194304
    2**23 = 8388608
    2**24 = 16777216
    2**25 = 33554432
    2**26 = 67108864
    2**27 = 134217728
    2**28 = 268435456
    2**29 = 536870912
    2**30 = 1073741824
    2**31 = 2147483648
    '''

    MASK_1_BITS = 0x0001;
    MASK_2_BITS = 0x0003;
    MASK_3_BITS = 0x0007;
    MASK_4_BITS = 0x000F;
    MASK_5_BITS = 0x001F;
    MASK_6_BITS = 0x003F;
    MASK_7_BITS = 0x007F;
    MASK_8_BITS = 0x00FF;
    MASK_9_BITS = 0x01FF;
    
    CALENDAR_BITS = MASK_3_BITS; #8
    YEAR_BITS     = MASK_7_BITS; #128
    MONTH_BITS    = MASK_4_BITS; #16
    DAY_BITS      = MASK_5_BITS; #32
    ITEM_BITS     = MASK_8_BITS; #256
    SUB_ITEM_BITS = MASK_4_BITS; #16
    
    CALENDAR_SHIFT = 28;
    YEAR_SHIFT     = 21;
    MONTH_SHIFT    = 17;
    DAY_SHIFT      = 12;
    ITEM_SHIFT     = 4;
    SUB_ITEM_SHIFT = 0;
    
    CALENDAR_MASK = (CALENDAR_BITS << CALENDAR_SHIFT);
    YEAR_MASK     = (YEAR_BITS << YEAR_SHIFT);
    MONTH_MASK    = (MONTH_BITS << MONTH_SHIFT);
    DAY_MASK      = (DAY_BITS << DAY_SHIFT);
    ITEM_MASK     = (ITEM_BITS << ITEM_SHIFT);
    SUB_ITEM_MASK = (SUB_ITEM_BITS << SUB_ITEM_SHIFT);

    key = 0

    def __init__(self, cal, year, month, day, event, subEvent):
        '''
        Constructor
        '''
        self.set_calendar(cal)
        self.set_year(year)
        self.set_month(month)
        self.set_day(day)
        self.set_event(event)
        self.set_subevent(subEvent)
        

    def toString(self):
        return "key: " + str(self.get_internal_key()) + ": " + \
        str(self.get_calendar()) + " - " + \
        str(self.get_month()) + "/" + \
        str(self.get_day()) + "/" + \
        str(self.get_year()) + " - " + str(self.get_event()) + ":" + str(self.getSubevent());
    
    def get_internal_key(self):
        return self.key
    
    def clear(self):
        self.key = 0;

    def get_calendar(self):
        return ((self.key & self.CALENDAR_MASK) >> self.CALENDAR_SHIFT);

    def set_calendar(self, calendar):
        if calendar > self.CALENDAR_BITS:
            print("error!!! - should be exception - call Rich K")
            #throw new RuntimeException();
        self.key = (self.key & ~self.CALENDAR_MASK); # clear old value
        self.key = (self.key | (calendar << self.CALENDAR_SHIFT)); # set new value

    def get_year(self):
        return (1950 + ((self.key & self.YEAR_MASK) >> self.YEAR_SHIFT)); # used to be >>>

    def set_year(self, year):
        self.key = (self.key & ~self.YEAR_MASK); # clear old value
        year = year - 1950;
        self.key = (self.key | (year << self.YEAR_SHIFT)); # set new value

    def get_month(self):
            return ((self.key & self.MONTH_MASK) >> self.MONTH_SHIFT); # used tobe >>>

    def set_month(self, month):
        self.key = (self.key & ~self.MONTH_MASK); # clear old value
        self.key = (self.key | (month << self.MONTH_SHIFT)); # set new value

    def get_day(self):
        return ((self.key & self.DAY_MASK) >> self.DAY_SHIFT); #used tobe >>>

    def set_day(self, day):
        self.key = (self.key & ~self.DAY_MASK);  # clear old value
        self.key = (self.key | (day << self.DAY_SHIFT)); # set new value

    def get_event(self):
        return ((self.key & self.ITEM_MASK) >> self.ITEM_SHIFT); #used to be >>>

    def get_subevent(self):
        return ((self.key & self.SUB_ITEM_MASK) >> self.SUB_ITEM_SHIFT); #should be >>>

    def set_event(self, event):
        if event > self.ITEM_BITS:
            # throw new RuntimeException();
            print("error!!! - should be exception - call Rich K")
        self.key = (self.key & ~self.ITEM_MASK); # clear old value
        self.key = (self.key | (event << self.ITEM_SHIFT)); # set new value

    def set_subevent(self, subevent):
        self.key = (self.key & ~self.SUB_ITEM_MASK); # clear old value
        self.key = (self.key | (subevent << self.SUB_ITEM_SHIFT)); # set new value
