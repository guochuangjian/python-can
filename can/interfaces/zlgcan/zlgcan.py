# -*- coding:utf-8 -*-
#  zlgcan.py
#
#  ~~~~~~~~~~~~
#
#  ZLGCAN API
#
#  ~~~~~~~~~~~~
#
#  ------------------------------------------------------------------
#  Author : guochuangjian
#  Last change: 18.10.2020
#
#  Language: Python 2.7, 3.6+
#  ------------------------------------------------------------------
#
from ctypes import *
import platform

INVALID_DEVICE_HANDLE = 0
INVALID_CHANNEL_HANDLE = 0

"""
 Device Type
"""
ZCAN_PCI5121 = 1
ZCAN_PCI9810 = 2
ZCAN_USBCAN1 = 3
ZCAN_USBCAN2 = 4
ZCAN_PCI9820 = 5
ZCAN_CAN232 = 6
ZCAN_PCI5110 = 7
ZCAN_CANLITE = 8
ZCAN_ISA9620 = 9
ZCAN_ISA5420 = 10
ZCAN_PC104CAN = 11
ZCAN_CANETUDP = 12
ZCAN_CANETE = 12
ZCAN_DNP9810 = 13
ZCAN_PCI9840 = 14
ZCAN_PC104CAN2 = 15
ZCAN_PCI9820I = 16
ZCAN_CANETTCP = 17
ZCAN_PCIE_9220 = 18
ZCAN_PCI5010U = 19
ZCAN_USBCAN_E_U = 20
ZCAN_USBCAN_2E_U = 21
ZCAN_PCI5020U = 22
ZCAN_EG20T_CAN = 23
ZCAN_PCIE9221 = 24
ZCAN_WIFICAN_TCP = 25
ZCAN_WIFICAN_UDP = 26
ZCAN_PCIe9120 = 27
ZCAN_PCIe9110 = 28
ZCAN_PCIe9140 = 29
ZCAN_USBCAN_4E_U = 31
ZCAN_CANDTU_200UR = 32
ZCAN_CANDTU_MINI = 33
ZCAN_USBCAN_8E_U = 34
ZCAN_CANREPLAY = 35
ZCAN_CANDTU_NET = 36
ZCAN_CANDTU_100UR = 37
ZCAN_PCIE_CANFD_100U = 38
ZCAN_PCIE_CANFD_200U = 39
ZCAN_PCIE_CANFD_400U = 40
ZCAN_USBCANFD_200U = 41
ZCAN_USBCANFD_100U = 42
ZCAN_USBCANFD_MINI = 43
ZCAN_CANFDCOM_100IE = 44
ZCAN_CANSCOPE = 45
ZCAN_CLOUD = 46
ZCAN_CANDTU_NET_400 = 47
ZCAN_CANFDNET_TCP = 48
ZCAN_CANFDNET_UDP = 49
ZCAN_CANFDWIFI_TCP = 50
ZCAN_CANFDWIFI_UDP = 51
ZCAN_CANFDNET_400U_TCP = 52
ZCAN_CANFDNET_400U_UDP = 53
ZCAN_CANFDBLUE_200U = 54
ZCAN_VIRTUAL_DEVICE = 99

"""
 Interface return status
"""
ZCAN_STATUS_ERR = 0
ZCAN_STATUS_OK = 1
ZCAN_STATUS_ONLINE = 2
ZCAN_STATUS_OFFLINE = 3
ZCAN_STATUS_UNSUPPORTED = 4

"""
 CAN type
"""
ZCAN_TYPE_CAN = 0
ZCAN_TYPE_CANFD = 1

"""
 Device information
"""


class ZCAN_DEVICE_INFO(Structure):
    _fields_ = [
        ("hw_Version", c_ushort),
        ("fw_Version", c_ushort),
        ("dr_Version", c_ushort),
        ("in_Version", c_ushort),
        ("irq_Num", c_ushort),
        ("can_Num", c_ubyte),
        ("str_Serial_Num", c_ubyte * 20),
        ("str_hw_Type", c_ubyte * 40),
        ("reserved", c_ushort * 4),
    ]

    def __str__(self):
        return (
            "Hardware Version:%s\nFirmware Version:%s\nDriver Interface:%s\nInterface Interface:%s\nInterrupt Number:%d\nCAN Number:%d\nSerial:%s\nHardware Type:%s\n"
            % (
                self.hw_version,
                self.fw_version,
                self.dr_version,
                self.in_version,
                self.irq_num,
                self.can_num,
                self.serial,
                self.hw_type,
            )
        )

    def _version(self, version):
        return ("V%02x.%02x" if version // 0xFF >= 9 else "V%d.%02x") % (
            version // 0xFF,
            version & 0xFF,
        )

    @property
    def hw_version(self):
        return self._version(self.hw_Version)

    @property
    def fw_version(self):
        return self._version(self.fw_Version)

    @property
    def dr_version(self):
        return self._version(self.dr_Version)

    @property
    def in_version(self):
        return self._version(self.in_Version)

    @property
    def irq_num(self):
        return self.irq_Num

    @property
    def can_num(self):
        return self.can_Num

    @property
    def serial(self):
        serial = ""
        for c in self.str_Serial_Num:
            if c > 0:
                serial += chr(c)
            else:
                break
        return serial

    @property
    def hw_type(self):
        hw_type = ""
        for c in self.str_hw_Type:
            if c > 0:
                hw_type += chr(c)
            else:
                break
        return hw_type


class _ZCAN_CHANNEL_CAN_INIT_CONFIG(Structure):
    _fields_ = [
        ("acc_code", c_uint),
        ("acc_mask", c_uint),
        ("reserved", c_uint),
        ("filter", c_ubyte),
        ("timing0", c_ubyte),
        ("timing1", c_ubyte),
        ("mode", c_ubyte),
    ]


class _ZCAN_CHANNEL_CANFD_INIT_CONFIG(Structure):
    _fields_ = [
        ("acc_code", c_uint),
        ("acc_mask", c_uint),
        ("abit_timing", c_uint),
        ("dbit_timing", c_uint),
        ("brp", c_uint),
        ("filter", c_ubyte),
        ("mode", c_ubyte),
        ("pad", c_ushort),
        ("reserved", c_uint),
    ]


class _ZCAN_CHANNEL_INIT_CONFIG(Union):
    _fields_ = [
        ("can", _ZCAN_CHANNEL_CAN_INIT_CONFIG),
        ("canfd", _ZCAN_CHANNEL_CANFD_INIT_CONFIG),
    ]


class ZCAN_CHANNEL_INIT_CONFIG(Structure):
    _fields_ = [("can_type", c_uint), ("config", _ZCAN_CHANNEL_INIT_CONFIG)]


class ZCAN_CHANNEL_ERR_INFO(Structure):
    _fields_ = [
        ("error_code", c_uint),
        ("passive_ErrData", c_ubyte * 3),
        ("arLost_ErrData", c_ubyte),
    ]


class ZCAN_CHANNEL_STATUS(Structure):
    _fields_ = [
        ("errInterrupt", c_ubyte),
        ("regMode", c_ubyte),
        ("regStatus", c_ubyte),
        ("regALCapture", c_ubyte),
        ("regECCapture", c_ubyte),
        ("regEWLimit", c_ubyte),
        ("regRECounter", c_ubyte),
        ("regTECounter", c_ubyte),
        ("Reserved", c_ubyte),
    ]


class ZCAN_CAN_FRAME(Structure):
    _fields_ = [
        ("can_id", c_uint, 29),
        ("err", c_uint, 1),
        ("rtr", c_uint, 1),
        ("eff", c_uint, 1),
        ("can_dlc", c_ubyte),
        ("__pad", c_ubyte),
        ("__res0", c_ubyte),
        ("__res1", c_ubyte),
        ("data", c_ubyte * 8),
    ]


class ZCAN_CANFD_FRAME(Structure):
    _fields_ = [
        ("can_id", c_uint, 29),
        ("err", c_uint, 1),
        ("rtr", c_uint, 1),
        ("eff", c_uint, 1),
        ("len", c_ubyte),
        ("brs", c_ubyte, 1),
        ("esi", c_ubyte, 1),
        ("__res", c_ubyte, 6),
        ("__res0", c_ubyte),
        ("__res1", c_ubyte),
        ("data", c_ubyte * 64),
    ]


class ZCAN_Transmit_Data(Structure):
    _fields_ = [("frame", ZCAN_CAN_FRAME), ("transmit_type", c_uint)]


class ZCAN_Receive_Data(Structure):
    _fields_ = [("frame", ZCAN_CAN_FRAME), ("timestamp", c_ulonglong)]


class ZCAN_TransmitFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("transmit_type", c_uint)]


class ZCAN_ReceiveFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("timestamp", c_ulonglong)]


class ZCAN_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [
        ("enable", c_ushort),
        ("index", c_ushort),
        ("interval", c_uint),
        ("obj", ZCAN_Transmit_Data),
    ]


class ZCANFD_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [
        ("enable", c_ushort),
        ("index", c_ushort),
        ("interval", c_uint),
        ("obj", ZCAN_TransmitFD_Data),
    ]


class IProperty(Structure):
    _fields_ = [
        ("SetValue", c_void_p),
        ("GetValue", c_void_p),
        ("GetPropertys", c_void_p),
    ]


class ZCAN(object):
    def __init__(self):
        if platform.system() == "Windows":
            self.__dll = windll.LoadLibrary("./zlgcan.dll")
        else:
            print("No support now!")
        if self.__dll == None:
            print("DLL couldn't be loaded!")

    def OpenDevice(self, device_type, device_index, reserved):
        try:
            return self.__dll.ZCAN_OpenDevice(device_type, device_index, reserved)
        except:
            print("Exception on OpenDevice!")
            raise

    def CloseDevice(self, device_handle):
        try:
            return self.__dll.ZCAN_CloseDevice(device_handle)
        except:
            print("Exception on CloseDevice!")
            raise

    def GetDeviceInf(self, device_handle):
        try:
            info = ZCAN_DEVICE_INFO()
            ret = self.__dll.ZCAN_GetDeviceInf(device_handle, byref(info))
            return info if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_GetDeviceInf")
            raise

    def DeviceOnLine(self, device_handle):
        try:
            return self.__dll.ZCAN_IsDeviceOnLine(device_handle)
        except:
            print("Exception on ZCAN_ZCAN_IsDeviceOnLine!")
            raise

    def InitCAN(self, device_handle, can_index, init_config):
        try:
            return self.__dll.ZCAN_InitCAN(device_handle, can_index, byref(init_config))
        except:
            print("Exception on ZCAN_InitCAN!")
            raise

    def StartCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_StartCAN(chn_handle)
        except:
            print("Exception on ZCAN_StartCAN!")
            raise

    def ResetCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_ResetCAN(chn_handle)
        except:
            print("Exception on ZCAN_ResetCAN!")
            raise

    def ClearBuffer(self, chn_handle):
        try:
            return self.__dll.ZCAN_ClearBuffer(chn_handle)
        except:
            print("Exception on ZCAN_ClearBuffer!")
            raise

    def ReadChannelErrInfo(self, chn_handle):
        try:
            ErrInfo = ZCAN_CHANNEL_ERR_INFO()
            ret = self.__dll.ZCAN_ReadChannelErrInfo(chn_handle, byref(ErrInfo))
            return ErrInfo if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_ReadChannelErrInfo!")
            raise

    def ReadChannelStatus(self, chn_handle):
        try:
            status = ZCAN_CHANNEL_STATUS()
            ret = self.__dll.ZCAN_ReadChannelStatus(chn_handle, byref(status))
            return status if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_ReadChannelStatus!")
            raise

    def GetReceiveNum(self, chn_handle, can_type=ZCAN_TYPE_CAN):
        try:
            return self.__dll.ZCAN_GetReceiveNum(chn_handle, can_type)
        except:
            print("Exception on ZCAN_GetReceiveNum!")
            raise

    def Transmit(self, chn_handle, std_msg, len):
        try:
            return self.__dll.ZCAN_Transmit(chn_handle, byref(std_msg), len)
        except:
            print("Exception on ZCAN_Transmit!")
            raise

    def Receive(self, chn_handle, rcv_num, wait_time=c_int(-1)):
        try:
            rcv_can_msgs = (ZCAN_Receive_Data * rcv_num)()
            ret = self.__dll.ZCAN_Receive(
                chn_handle, byref(rcv_can_msgs), rcv_num, wait_time
            )
            return rcv_can_msgs, ret
        except:
            print("Exception on ZCAN_Receive!")
            raise

    def TransmitFD(self, chn_handle, fd_msg, len):
        try:
            return self.__dll.ZCAN_TransmitFD(chn_handle, byref(fd_msg), len)
        except:
            print("Exception on ZCAN_TransmitFD!")
            raise

    def ReceiveFD(self, chn_handle, rcv_num, wait_time=c_int(-1)):
        try:
            rcv_canfd_msgs = (ZCAN_ReceiveFD_Data * rcv_num)()
            ret = self.__dll.ZCAN_ReceiveFD(
                chn_handle, byref(rcv_canfd_msgs), rcv_num, wait_time
            )
            return rcv_canfd_msgs, ret
        except:
            print("Exception on ZCAN_ReceiveFD!")
            raise

    def GetIProperty(self, device_handle):
        try:
            self.__dll.GetIProperty.restype = POINTER(IProperty)
            return self.__dll.GetIProperty(device_handle)
        except:
            print("Exception on ZCAN_GetIProperty!")
            raise

    def SetValue(self, iproperty, path, value):
        try:
            func = CFUNCTYPE(c_uint, c_char_p, c_char_p)(iproperty.contents.SetValue)
            return func(c_char_p(path.encode("utf-8")), c_char_p(value.encode("utf-8")))
        except:
            print("Exception on IProperty SetValue")
            raise

    def GetValue(self, iproperty, path):
        try:
            func = CFUNCTYPE(c_char_p, c_char_p)(iproperty.contents.GetValue)
            return func(c_void_p(path.encode("utf-8")))
        except:
            print("Exception on IProperty GetValue")
            raise

    def ReleaseIProperty(self, iproperty):
        try:
            return self.__dll.ReleaseIProperty(iproperty)
        except:
            print("Exception on ZCAN_ReleaseIProperty!")
            raise


###############################################################################
"""
USBCANFD-MINI Demo
"""


def can_start(zcanlib, device_handle, chn):
    ip = zcanlib.GetIProperty(device_handle)
    ret = zcanlib.SetValue(ip, str(chn) + "/clock", "60000000")
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d CANFD clock failed!" % (chn))
    ret = zcanlib.SetValue(ip, str(chn) + "/canfd_standard", "0")
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d CANFD standard failed!" % (chn))
    ret = zcanlib.SetValue(ip, str(chn) + "/initenal_resistance", "1")
    if ret != ZCAN_STATUS_OK:
        print("Open CH%d resistance failed!" % (chn))
    zcanlib.ReleaseIProperty(ip)

    chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
    chn_init_cfg.can_type = ZCAN_TYPE_CANFD
    chn_init_cfg.config.canfd.abit_timing = 101166  # 1Mbps
    chn_init_cfg.config.canfd.dbit_timing = 101166  # 1Mbps
    chn_init_cfg.config.canfd.mode = 0
    chn_handle = zcanlib.InitCAN(device_handle, chn, chn_init_cfg)
    if chn_handle is None:
        return None
    zcanlib.StartCAN(chn_handle)
    return chn_handle


if __name__ == "__main__":
    zcanlib = ZCAN()
    handle = zcanlib.OpenDevice(ZCAN_USBCANFD_MINI, 0, 0)
    if handle == INVALID_DEVICE_HANDLE:
        print("Open Device failed!")
        exit(0)
    print("device handle:%d." % (handle))

    info = zcanlib.GetDeviceInf(handle)
    print("Device Information:\n%s" % (info))

    # Start CAN
    chn_handle = can_start(zcanlib, handle, 0)
    print("channel handle:%d." % (chn_handle))

    # Send CAN Messages
    transmit_num = 10
    msgs = (ZCAN_Transmit_Data * transmit_num)()
    for i in range(transmit_num):
        msgs[i].transmit_type = 2  # Send Self
        msgs[i].frame.eff = 0  # extern frame
        msgs[i].frame.rtr = 0  # remote frame
        msgs[i].frame.can_id = i
        msgs[i].frame.can_dlc = 8
        for j in range(msgs[i].frame.can_dlc):
            msgs[i].frame.data[j] = j
    ret = zcanlib.Transmit(chn_handle, msgs, transmit_num)
    print("Tranmit Num: %d." % ret)

    # Send CANFD Messages
    transmit_canfd_num = 10
    canfd_msgs = (ZCAN_TransmitFD_Data * transmit_canfd_num)()
    for i in range(transmit_num):
        canfd_msgs[i].transmit_type = 2  # Send Self
        canfd_msgs[i].frame.eff = 0  # extern frame
        canfd_msgs[i].frame.rtr = 0  # remote frame
        canfd_msgs[i].frame.brs = 1  # BRS
        canfd_msgs[i].frame.can_id = i
        canfd_msgs[i].frame.len = 8
        for j in range(canfd_msgs[i].frame.len):
            canfd_msgs[i].frame.data[j] = j
    ret = zcanlib.TransmitFD(chn_handle, canfd_msgs, transmit_canfd_num)
    print("Tranmit CANFD Num: %d." % ret)

    # Receive Messages
    while True:
        rcv_num = zcanlib.GetReceiveNum(chn_handle, ZCAN_TYPE_CAN)
        rcv_canfd_num = zcanlib.GetReceiveNum(chn_handle, ZCAN_TYPE_CANFD)
        if rcv_num:
            print("Receive CAN message number:%d" % rcv_num)
            rcv_msg, rcv_num = zcanlib.Receive(chn_handle, rcv_num)
            for i in range(rcv_num):
                print(
                    "[%d]:ts:%d, id:%d, dlc:%d, eff:%d, rtr:%d, data:%s"
                    % (
                        i,
                        rcv_msg[i].timestamp,
                        rcv_msg[i].frame.can_id,
                        rcv_msg[i].frame.can_dlc,
                        rcv_msg[i].frame.eff,
                        rcv_msg[i].frame.rtr,
                        "".join(
                            str(rcv_msg[i].frame.data[j]) + " "
                            for j in range(rcv_msg[i].frame.can_dlc)
                        ),
                    )
                )
        elif rcv_canfd_num:
            print("Receive CANFD message number:%d" % rcv_canfd_num)
            rcv_canfd_msgs, rcv_canfd_num = zcanlib.ReceiveFD(
                chn_handle, rcv_canfd_num, 1000
            )
            for i in range(rcv_canfd_num):
                print(
                    "[%d]:ts:%d, id:%d, len:%d, eff:%d, rtr:%d, esi:%d, brs: %d, data:%s"
                    % (
                        i,
                        rcv_canfd_msgs[i].timestamp,
                        rcv_canfd_msgs[i].frame.can_id,
                        rcv_canfd_msgs[i].frame.len,
                        rcv_canfd_msgs[i].frame.eff,
                        rcv_canfd_msgs[i].frame.rtr,
                        rcv_canfd_msgs[i].frame.esi,
                        rcv_canfd_msgs[i].frame.brs,
                        "".join(
                            str(rcv_canfd_msgs[i].frame.data[j]) + " "
                            for j in range(rcv_canfd_msgs[i].frame.len)
                        ),
                    )
                )
        else:
            break

    # Close CAN
    zcanlib.ResetCAN(chn_handle)
    # Close Device
    zcanlib.CloseDevice(handle)
