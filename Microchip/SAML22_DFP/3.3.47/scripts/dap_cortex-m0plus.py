# This file is autogenerated
comm_speed=2000000
erase_as_needed = True  # used in prog_write
comm_iface = True
reset_delay = 0
show_output = False
log_level = 0
use_vtor  = False
vtor_name = "0"

def begin_debug_session():  # mplab
    log.info("Debug: Init debug session")
    dev.Connect(comm_iface, comm_speed)
    reset_and_halt()
    cache_onDebugStart()

def begin_communication_session():  # mplab
    global log_level,show_output,reset_delay
    log_level    = settings.getNumeric("script.log_level",log_level)
    show_output  = settings.getBool("script.show_output",show_output)
    reset_delay = settings.getNumeric("script.reset_delay",reset_delay)

    dev.SetApiLogging(log_level)
    log.setShowOutput(show_output)

    global comm_iface, comm_speed, erase_as_needed, use_vtor,vtor_name
    comm_iface = settings.getString("communication.interface", "swd") == "swd"
    comm_speed = settings.getNumeric("communication.frequency", comm_speed)
    use_vtor   = settings.getBool("arm.use_vtor", False)
    vtor_name  = settings.getString("arm.vtor_adr", "0")
    erase_as_needed = True  # used in prog_write

def onShowPropsDFP2(t):
    ide.addBooleanProperty(t,"arm.use_vtor" , "*|programoptions|programoptions.eraseb4program","Set PC and SP to VTOR","After reset, force PC and SP to the entries defined by the VTOR", False)
    ide.addTextProperty(t,"arm.vtor_adr" , "*|programoptions|programoptions.eraseb4program","VTOR table or numerical address", "Enter address of vector table", "exception_table")
    ide.addPropCategory(t,"diagnostics" , "*|toolpack", "Diagnostics")
    ide.addBooleanProperty(t,"script.show_output" , "*|diagnostics|*","Output diagnostic logging","Show diagnostic text in the Output window", False)
    ide.addTextProperty(t,"script.log_level" , "*|diagnostics|*","Diagnostic log level","Set diagnostic level (usually 0 1 or 3)", "0")
    ide.addTextProperty(t,"script.reset_delay" , "*|debugoptions|*","Additional delay after reset","Enter additional RST settling delay in msec", "0")

def print_dhcsr_v(t, d):
    log.info(t + arm.getDHCSRString(d))

def print_dhcsr(text):
    try:
        d = dev.Read32(arm.DHCSR)
        print_dhcsr_v(text, d)
        return d
    except:
        log.log("DHCSR is unreadable")
        return 0

def verify_transfer(type_of_mem, address, data, length):  # mplab
    log.info("Prog: not implemented: Verifying %d bytes to address 0x%0x of %s memory" % (length, address, type_of_mem))

def blank_check():  # mplab
    log.info("Prog: Blank check")

def debug_read(mem_type, start, length, data):  # mplab
    log.info("Debug: Reading %d bytes at start address 0x%08x (%s)" % (length, start, mem_type))
    cache_onDataRead(start,length)
    dev.Read(start, data, 0, length)

def debug_write(mem_type, start, length, data):  # mplab
    log.info("Debug: Writing %d bytes at start address 0x%08x (%s)" % (length, start, mem_type))
    cache_onDataWrite(start,length)
    dev.Write(start, data, 0, length)

def get_pc():  # mplab
    try:
        pc = dev.ReadReg64(15)
    except:
        log.error("get_pc returned error")
        return 0
    log.info("get_pc PC=0x%08x" % pc)
    return pc

def run_target():  # mplab
    log.info("Debug: run target")
    dev.Write32(arm.DHCSR, 0xa05f0001)  # DBGKEY | C_DEBUGEN | C_HALT

def halt_target():  # mplab
    log.info("Debug: halt target")
    dev.Write32(arm.DHCSR, 0xa05f0003)  # DBGKEY | C_DEBUGEN | C_HALT

def step_target():  # mplab
    log.info("Debug: stepping at pc 0x%08x" % get_pc())

    dev.Write32(arm.DHCSR, 0xa05f000b)  # DBGKEY | C_DEBUGEN | C_HALT | C_MASKINTS
    dev.Write32(arm.DHCSR, 0xa05f000d)  # DBGKEY | C_DEBUGEN | C_STEP | C_MASKINTS
    dev.Write32(arm.DHCSR, 0xa05f0003)  # DBGKEY | C_DEBUGEN | C_HALT

def set_pc(pc):  # mplab
    log.info("Debug: set pc to 0x%08x" % pc)
    dev.WriteReg64(15, pc)

def print_byte_array(text, array, index, size):
    string = text
    for i in range(size):
        string += " %x" % array[i+index]
    log.info(string)

g_is_running = True
def is_target_running():  # mplab
    global g_is_running
    dhcsr = dev.Read32(arm.DHCSR)
    state = 0 == (dhcsr & 0x20000)
    if state != g_is_running:
        log.info("Debug: target is now running" if state else "Debug: target has halted")
        g_is_running = state
    if not g_is_running:
        cache_onStop()
    return g_is_running

def on_after_reset(): 
    global use_vtor,vtor_name
    if not use_vtor:
        return
    vtor = -1
    try:
        vtor = int(vtor_name,0)
    except:
        try:
            vtor=deb.GetSymbolAddress(vtor_name)
        except:
            log.error("Debug: failed to compute location of VTOR")
            return
    load_vtor(vtor) 
    pass

def load_vtor(adr):
    try:
        dev.WriteReg64(arm.PC,dev.Read32(adr + 4))
        dev.WriteReg64(arm.SP,dev.Read32(adr))
    except:
        log.error("Debug: failed to set PC and SP to vtor[0] and vtor[4], with vtor=0x%08x" % adr)


def on_program_done():
    on_after_reset()

def reset_target():  # mplab
    log.info("Debug: Reset target")
    reset_and_halt()
    on_after_reset() # call autoload hook

def end_debug_session():  # mplab
    log.info("Debug: End debug session")
    run_target()
    dev.Disconnect()

def hold_in_reset():  # mplab
    log.info("Prog: Hold in reset")
    dev.Connect(True, 100000)
    dev.Pins(0, dev.RESET, 1000)

def alt_hold_in_reset():  # mplab
    # Alternative if RESET pin is not connected to debugger
    log.info("Prog: Hold in reset , no reset line")
    dev.Connect(True, 100000)
    reset_and_halt()

def release_from_reset():  # mplab
    global reset_delay
    log.info("Prog: Release from reset")
    # toggle reset line
    dev.Connect(True, 100000)
    dev.Pins(0, dev.RESET, 1000)
    dev.Delay(reset_delay)
    dev.Pins(dev.RESET, dev.RESET, 1000)  # now float reset back
    dev.Delay(reset_delay)

def alt_release_from_reset():  # mplab
    log.info("Prog: Release from reset, no reset line")
    dev.Connect(True, 100000)
    dev.Write32(dev.AIRCR, 0x05fa0004)  # VECTKEY | SYSRESETREQ

def set_sw_bp_gen(address, erase_size, instruction, flags):  # mplab
    global erase_as_needed
    log.debug("Debug: set/reset bp at address 0x%0x, store instructions 0x%0x, flags = 0x%0x" % (address, instruction, flags))
    if address >= 0x20000000:
        erase_size = 4 

    erase_page_start = address & ~(erase_size-1)
    address_in_erase_page = address & (erase_size-1)

    data = bytearray(erase_size)
    cache_invalidateInstrCache()
    dev.Read(erase_page_start, data, 0, erase_size)
    return_value = data[address_in_erase_page] | (data[address_in_erase_page+1] << 8)

    # Insert software breakpoint instruction in the data
    data[address_in_erase_page] = instruction & 0xFF
    data[address_in_erase_page+1] = (instruction >> 8) & 0xFF

    if erase_size == 4:
        dev.Write(erase_page_start, data, 0, erase_size)
    else:
        erase_as_needed = True
        prog_write("Pgm", erase_page_start, erase_size, data)
    return return_value


# device specific functions

dsu_statusa = 0x41002101
dsu_ctrl = 0x41002100
    
class nvm:
    page_size = 64
    erase_size = 256
    aux_size = 256
    cmdReg = 0x41004000
    cfgReg  = 0x41004004
    stsReg = 0x41004018
    intReg = 0x41004014
    adrReg = 0x4100401c
    AUX_ERASE = 0xA505
    ROW_ERASE = 0xA502
    erase_time = 100
    UROW = 0x00804000

def cache_invalidate():
    nvm_cmd(0xA546,20)
def cache_onDebugStart():
    cache_invalidate()
def cache_onStop():
    cache_invalidate()
def cache_onDataRead(adr,size):
    cache_invalidate()
def cache_onDataWrite(adr,size):
    cache_invalidate()
def cache_invalidateInstrCache():
    cache_invalidate()


def is_nvm_ready():
    intFlag = dev.Read8(nvm.intReg)
    isReady = 0 != (intFlag & 1)
    isError = 0 != (intFlag & 2)
    if not isError: # if no ERROR bit is set
        return isReady

    status = dev.Read16(nvm.stsReg)
    log.error("NVMCtrl error bits set! (STATUS = 0x%X, INTFLAG = 0x%X)" % (status, intFlag))
    dev.Write16(nvm.stsReg, status | 0x001E) # clear error bits and load bit by setting 1
    dev.Write8(nvm.intReg, intFlag | 2) # clear error bit by setting 1
    raise Exception("NVMctrl reports an error")

# global variable keeps previous value of flash cfg register while programming
prevCfgReg = 0x0

def cfg_nvmctrl():
    global prevCfgReg
    prevCfgReg = dev.Read32(nvm.cfgReg)
    newCfgReg = (prevCfgReg & 0xFFFFFF61) | 0x1e  # 15 wait states and clear MANW
    if newCfgReg != prevCfgReg:
        dev.Write32(nvm.cfgReg, newCfgReg)

def restore_nvmctrl():
    #log.debug("reset_cfg_word: prevCfgReg = %x" % prevCfgReg)
    dev.Write32(nvm.cfgReg, prevCfgReg)

def erase_row(addr,cmd):
    dev.Write32(nvm.adrReg,addr/2)
    nvm_cmd (cmd, 20)

def begin_programming_operation(): #mplab
    global erase_as_needed
    erase_as_needed = True
    reset_extension()
    dev.Connect(comm_iface, comm_speed)
    statusa = dev.Read8(dsu_statusa) # verify CRSTEXT is set
    if 0 == (statusa & 2): #STATUSA.CRSTEXT
        log.error("Device could not enter reset extension, check cap on RST line")
        raise Exception("Reset error.")
    else:
        log.info("Prog: Device entered reset extension")
    reset_and_halt()  # clear CRSTEXT

def reset_extension():
    delay=1000
    dev.Connect(comm_iface, comm_speed) # set interface so that voltage level converter are configured 
    dev.Pins(0,dev.RESET,delay)  # 1 msec with reset high 
    dev.Pins(dev.RESET,dev.RESET,delay) # 1 msec with floating reset 
    dev.Pins(0,dev.RESET | dev.SWCLK,delay); # 1 msec with reset and clock low 
    dev.Pins(dev.RESET,dev.RESET,delay); # now float reset back
    dev.Delay(10000)


def erase():#mplab
    global erase_as_needed
    log.info("Prog: Erase")
    dsu_ce = 0x10
    dev.Write8(dsu_ctrl, dsu_ce) # 0x41002100,0x10

    n = 0
    while n < nvm.erase_time:
        statusa=dev.Read8(dsu_statusa) # 0x41002101
        if statusa & 1: #statusa_done
            if statusa & 0x1c:
                log.error("DSU.STATUSA indicates an error %x"  % statusa)
                raise Exception("Erase error")
            break
        dev.Delay(100000)
        n=n+1
    erase_as_needed = False # tell prog_write not to erase rows prior to write

def reset_and_halt():
    halt_target()
    dev.Write32(arm.DEMCR, 0x01000001) # TRCENA  | VC_CORERESET
    dev.Write32(arm.AIRCR, 0x05fa0004) # VECTKEY | SYSRESETREQ
    n = 0
    retries = 10
    seenReset = False
    while n<retries:
        dhcsr = dev.Read32(arm.DHCSR)
        #print_dhcsr_v("arm.DHCSR",dhcsr)
        if (dhcsr & 0x02000000): # wait for S_RESET_ST
            seenReset=True
            dev.Write32(arm.DHCSR, 0xa05f0003) # DBGKEY|C_HALT|C_DEBUGEN
            dev.Write8(dsu_statusa, 2) # release the cpu 0x41002101,0x2  STATUSA.CRSTEXT
            dhcsr = print_dhcsr("Prog: Cleared CRSTEXT")
        hasHalted = 0 != (dhcsr & 0x20000) # S_HALT
        if seenReset:
            if hasHalted: # wait for S_HALT
                break
        dev.Delay(100000)
        n=n+1
    dev.Write32(arm.DEMCR, 0x01000000) # TRCENA
    if n==retries:
        raise Exception("The device did not come out of reset")

def nvm_cmd(command, t):
    dev.Write16(nvm.cmdReg, command)
    wait_nvm_ready(t)

def wait_nvm_ready(t):
    while t > 0 :
        if is_nvm_ready():
            return
        dev.Delay(1000)
        t  = t - 1
    if t == 0:
        raise Exception("The NVM controller operation did not finish")

def write_row(adr, ofs, data,len):
    dev.Write(adr, data, ofs , len)
    wait_nvm_ready(10)

def prog_write(type_of_mem, address, length, data):#mplab
    global erase_as_needed
    log.info("Prog: Writing %d bytes to address 0x%08x of %s memory" % (length, address, type_of_mem))
    if str(type_of_mem) != "Pgm" and  str(type_of_mem) != "Cfg":
        dev.Write(address, data, 0, length)
        return

    cfg_nvmctrl()
    if address == nvm.UROW: # user page / fuses / configuration bits
        if length > nvm.aux_size:
            raise Exception("Prog: Error in prog_write of config bits, length (%X) > aux page size" % length)
        erase_row(address,nvm.AUX_ERASE) # not cleared by chip erase
        dev.Read32(address) # fix for MPLABX-4768. For the particular project provided in the Jira ticket, MPLAB need to to a read before write, otherwise the PC will be 0
        write_row(address, 0, data, min(length, nvm.erase_size))
    else:
        written = 0
		# a flash row has 'erase_size' bytes
        while written < length:
            if erase_as_needed:
                erase_row(address, nvm.ROW_ERASE) # if device is not pre-erased, erase row
            write_row(address,written,data, min(length - written, nvm.erase_size))
            #dev.Read(address,data1,0,nvm.erase_size)
            written += nvm.erase_size
            address += nvm.erase_size
    restore_nvmctrl()

def prog_read(type_of_mem, address, length, data):#mplab
    log.info("Prog: Reading %d bytes from address 0x%08x of %s memory..." % (length, address, type_of_mem))
    dev.Read(address,data,0,length)

def end_of_operations():#mplab
    global erase_as_needed
    log.info("Prog: End of operations")
    erase_as_needed = True
    #reset_and_halt()
    dev.Disconnect()

def set_sw_bp(address, instruction, flags):#mplab
    return set_sw_bp_gen(address,nvm.erase_size,instruction,flags)