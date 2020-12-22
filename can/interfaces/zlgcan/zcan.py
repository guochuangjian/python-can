"""
Enable zlgcan over ZLGCAN device.
"""

import logging
import time

from typing import Optional
from can import CanError, Message, BusABC
from can.bus import BusState
from can.util import len2dlc, dlc2len
from .zlgcan import *

# Set up logging
log = logging.getLogger("can.zcan")

try:
    zcanlib = ZCAN()
    log.info("Loaded zlgcan library")
except OSError as e:
    log.info("Load zlgcan library error!")

class ZlgcanBus(BusABC):
    def __init__(
        self,
        channel,
        device = ZCAN_USBCANFD_200U,
        device_index = 0,
        bitrate=500000,
        **kwargs
    ):
        
        """ZLGCAN interface to CAN.

        On top of the usual :class:`~can.Bus` methods provided,
        the ZLGCAN interface includes the :meth:`~can.interface.zcan.ZlgcanBus.SetValue`
        and :meth:`~can.interface.zcan.ZlgcanBus.GetValue methods.

        :param str channel:
            The can interface name. An example would be 'USBCANFD-200U'
            Default is 'USBCANFD-200U'

        :param can.bus.BusState state:
            BusState of the channel.
            Default is ACTIVE

        :param int bitrate:
            Bitrate of channel in bit/s.
            Default is 500 kbit/s.
        """
        super().__init__(channel=channel, **kwargs)

        if isinstance(channel, (list, tuple)):
            self.channels = channel
        elif isinstance(channel, int):
            self.channels = [channel]
        else:
            # Assume comma separated string of channels
            self.channels = [int(ch.strip()) for ch in channel.split(",")]

        self.device = zcanlib.OpenDevice(device, device_index, 0)
        if self.device == INVALID_DEVICE_HANDLE:
            log.error("open device failed")
            return

        self.is_fd_device = True

        self.chn_handles = {}
        ip = zcanlib.GetIProperty(self.device)
        for chn in self.channels:
            if self.is_fd_device:
                #fixme 从设备列表检查是否支持该设备，该设备是否支持canfd
                #fixme 波特率应查询是否在表内
                #fixme 只有usbcanfd支持该命令
                ret = zcanlib.SetValue(ip, str(chn) + "/canfd_abit_baud_rate", str(bitrate)) 
                if ret != ZCAN_STATUS_OK:
                    log.error("set nominal baudrate failed")

                #fixme canfd数据域波特率获取 
                ret = zcanlib.SetValue(ip, str(chn) + "/canfd_dbit_baud_rate", str(bitrate)) 
                if ret != ZCAN_STATUS_OK:
                    log.error("set data baudrate failed")

                #if "resistance_enable" 
                ret = zcanlib.SetValue(ip, str(chn) + "/initenal_resistance", "1")
            else:
                ret = zcanlib.SetValue(ip, str(chn) + "/baud_rate", str(bitrate)) 
                if ret != ZCAN_STATUS_OK:
                    log.error("set baudrate failed")

            chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
            if self.is_fd_device:
                chn_init_cfg.can_type = ZCAN_TYPE_CANFD
                chn_init_cfg.config.canfd.mode = 0 #正常模式，是否考虑只听模式支持
            else:
                chn_init_cfg.can_type = ZCAN_TYPE_CAN
                chn_init_cfg.config.can.mode = 0 #正常模式，是否考虑只听模式支持
                chn_init_cfg.config.can.acc_code = 0
                chn_init_cfg.config.can.acc_mask = 0xFFFFFFFF
            handle = zcanlib.InitCAN(self.device, chn, chn_init_cfg)
            if handle is None:
                log.error("init channel%d failed" % chn) 
                continue
            ret = zcanlib.StartCAN(handle)
            if ret != ZCAN_STATUS_OK:
                log.error("start channel%d failed" % chn) 
                continue

            self.chn_handles[chn] = handle 

        zcanlib.ReleaseIProperty(ip) 

    def _can_dev_recv(self, timeout):
        pass

    def _recv_check(self):
        for chn, handle in self.chn_handles.items():
            if zcanlib.GetReceiveNum(handle, ZCAN_TYPE_CAN):
                return chn, False
            if self.is_fd_device:
                if zcanlib.GetReceiveNum(handle, ZCAN_TYPE_CANFD):
                    return chn, True
        return None, False

    def _recv_can_msg(self, chn, timeout=0):
        can_msg, msg_num = zcanlib.Receive(self.chn_handles[chn], 1, timeout)
        if msg_num == 0:
            return None
        return Message(
                timestamp=can_msg[0].timestamp, 
                arbitration_id=can_msg[0].frame.can_id, 
                is_extended_id=can_msg[0].frame.eff,
                is_remote_frame=can_msg[0].frame.rtr,
                is_error_frame=can_msg[0].frame.err,
                channel=chn,
                dlc=can_msg[0].frame.can_dlc,
                data=can_msg[0].frame.data
                )

    def _recv_canfd_msg(self, chn, timeout=0):
        canfd_msg, msg_num = zcanlib.ReceiveFD(self.chn_handles[chn], 1, timeout)
        if msg_num == 0:
            return None        
        return Message(
                timestamp=canfd_msg[0].timestamp, 
                arbitration_id=canfd_msg[0].frame.can_id, 
                is_extended_id=canfd_msg[0].frame.eff,
                is_remote_frame=False,
                is_error_frame=canfd_msg[0].frame.err,
                channel=chn,
                dlc=canfd_msg[0].frame.len,
                data=canfd_msg[0].frame.data,
                is_fd=True,
                bitrate_switch=canfd_msg[0].frame.brs,
                error_state_indicator=canfd_msg[0].frame.esi
                )

    def _recv_internal(self, timeout):
        #return self._canfd_dev_recv(self, timeout) self.is_fd_device else self._can_dev_recv(self, timeout)
        end_time = time.perf_counter() + timeout if timeout else 0
        chn, is_rcv_canfd = self._recv_check()
        if chn:
            return (self._recv_canfd_msg(chn) if is_rcv_canfd else self._recv_can_msg(chn), False)
        while time.perf_counter() < end_time:
            for chn in self.chn_handles.keys():
                can_msg = self._recv_can_msg(chn, 0)
                if can_msg:
                    return can_msg, False
                if self.is_fd_device:
                    canfd_msg = self._recv_canfd_msg(chn, 0)
                    if canfd_msg:
                        return canfd_msg, False
            time.sleep(0.001)
        return None, False

    def _can_send(self, msg, timeout):
        td = ZCAN_Transmit_Data()
        td.frame.transmit_type = 0
        td.frame.can_id = msg.arbitration_id
        td.frame.err = 0
        td.frame.rtr = 1 if msg.is_remote_frame else 0
        td.frame.eff = 1 if msg.is_extended_id else 0
        td.frame.can_dlc = msg.dlc
        td.frame.__pad = 0 
        td.frame.__res0 = 0 
        td.frame.__res1 = 0 
        if not msg.is_remote_frame:
            for i in range(msg.dlc):
                td.frame.data[i] = msg.data[i]
        
        if len(self.chn_handles) == 0:
            log.error("no channel to send") #fixme raise error
            return

        handle = list(self.chn_handles.values())[0]
        if msg.channel is not None:
            if self.chn_handles.has_key(msg.channel):
                handle = self.chn_handles(chn)
            else:
                log.error("no channel to send")

        ret = zcanlib.Transmit(handle, td, 1)
        if ret != 1:
            log.error("send can frame failed") #fixme raise error

    def _canfd_send(self, msg, timeout):
        td = ZCAN_TransmitFD_Data()
        td.transmit_type = 0
        td.frame.err = 0
        td.frame.rtr = 0
        td.frame.eff = 1 if msg.is_extended_id else 0
        td.frame.len = msg.dlc
        td.frame.brs = 1 if msg.bitrate_switch else 0

        if len(self.chn_handles) == 0:
            log.error("no channel to send")
            return
        
        handle = list(self.chn_handles.values())[0]
        if msg.channel is not None:
            if self.chn_handles.has_key(msg.channel):
                handle = self.chn_handles(chn)
            else:
                log.error("no channel to send")

        ret = zcanlib.TransmitFD(handle, td, 1)
        if ret != 1:
            log.error("send canfd frame failed")

        zcanlib.TransmitFD(self.chn_handle, canfd_msg, 1)

    def send(self, msg, timeout=None):
        if msg.is_fd:
            self._canfd_send(msg, timeout)
        else:
            self._can_send(msg, timeout)

    def flush_tx_buffer(self):
        pass
        #zcanlib.ClearBuffer(self.chn_handle)

    def shutdown(self):
        for handle in list(self.chn_handles.values()):
            zcanlib.ResetCAN(handle)
        zcanlib.CloseDevice(self.device)
