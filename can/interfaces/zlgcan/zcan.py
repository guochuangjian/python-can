"""
Enable zlgcan over ZLGCAN device.
"""

import logging
import time

from typing import Optional, Tuple
from can import Message, BusABC
from .zlgcan import *

# Set up logging
log = logging.getLogger("can.zcan")

try:
    zcanlib = ZCAN()
    log.info("Loaded zlgcan library")
except OSError:
    log.info("Load zlgcan library error!")

zcan_dev_property = {
    ZCAN_USBCAN1:{"is_fd":False, "support_can":True, "support_resistance":False},
    ZCAN_USBCAN2:{"is_fd":False, "support_can":True, "support_resistance":False},

    ZCAN_USBCAN_E_U:{"is_fd":False, "support_can":True, "support_resistance":False},
    ZCAN_USBCAN_2E_U:{"is_fd":False, "support_can":True, "support_resistance":False},
    ZCAN_USBCAN_4E_U:{"is_fd":False, "support_can":True, "support_resistance":False},
    ZCAN_USBCAN_8E_U:{"is_fd":False, "support_can":True, "support_resistance":False},

    ZCAN_CANETTCP:{"is_fd":False, "support_resistance":False, "is_net_dev":True, "is_tcp":True},
    ZCAN_WIFICAN_TCP:{"is_fd":False, "support_resistance":False, "is_net_dev":True, "is_tcp":True},

    ZCAN_CANETUDP:{"is_fd":False, "support_resistance":False, "is_net_dev":True, "is_tcp":False},
    ZCAN_WIFICAN_UDP:{"is_fd":False, "support_resistance":False, "is_net_dev":True, "is_tcp":False},

    ZCAN_USBCANFD_100U:{"is_fd":True, "support_can":True, "support_resistance":True},
    ZCAN_USBCANFD_200U:{"is_fd":True, "support_can":True, "support_resistance":True},
    ZCAN_USBCANFD_MINI:{"is_fd":True, "support_can":True, "support_resistance":True},

    ZCAN_PCIE_CANFD_100U:{"is_fd":True, "support_can":False, "support_resistance":False},
    ZCAN_PCIE_CANFD_200U:{"is_fd":True, "support_can":False, "support_resistance":False},

    ZCAN_CANDTU_100UR:{"is_fd":False, "support_resistance":True},
    ZCAN_CANDTU_200UR:{"is_fd":False, "support_resistance":True},

    ZCAN_CANDTU_NET:{"is_fd":False, "support_resistance":False, "is_net_dev":True, "is_tcp":True},
    ZCAN_CANDTU_NET_400:{"is_fd":False, "support_resistance":False, "is_net_dev":True, "is_tcp":True},

    ZCAN_CANFDNET_TCP:{"is_fd":True, "support_resistance":False, "is_net_dev":True, "is_tcp":True},
    ZCAN_CANFDWIFI_TCP:{"is_fd":True, "support_resistance":False, "is_net_dev":True, "is_tcp":True},
    ZCAN_CANFDNET_400U_TCP:{"is_fd":True, "support_resistance":False, "is_net_dev":True, "is_tcp":True},

    ZCAN_CANFDNET_UDP:{"is_fd":True, "support_resistance":False, "is_net_dev":True, "is_tcp":False},
    ZCAN_CANFDWIFI_UDP:{"is_fd":True, "support_resistance":False, "is_net_dev":True, "is_tcp":False},
    ZCAN_CANFDNET_400U_UDP:{"is_fd":True, "support_resistance":False, "is_net_dev":True, "is_tcp":True}
}

def dev_have_attr(device, attr):
        return device in zcan_dev_property and \
                attr in zcan_dev_property[device] \
                    and zcan_dev_property[device][attr]

class ZlgcanBus(BusABC):
    def __init__(
        self,
        channel=0,
        device=ZCAN_USBCANFD_200U,
        device_index=0,
        bitrate=500000,
        **kwargs
    ):
        """ZLGCAN interface to CAN.

        On top of the usual :class:`~can.Bus` methods provided,
        the ZLGCAN interface includes the :meth:`~can.interface.zcan.ZlgcanBus.SetValue`
        and :meth:`~can.interface.zcan.ZlgcanBus.GetValue methods.

        :param in device:
            zlgcan device number, eg: ZCAN_USBCANFD_100U.

        :param int/int list/int tuple channel:
            The can channel.
            Default is 0.

        :param int bitrate:
            CAN bitrate (or nominal canfd bitrate) of channel in bit/s
            Default is 500 kbit/s.

        :params int data_bitrate:
            Datarate of channel in bit/s for CANFD.
            Just for CANFD device.

        :param bool res_en:
            Internal resistance enable.
            This param is valid if device has internal resistance.

        :param bool is_server:
            TCP mode. TCP server is True, TCP client is False.
            Just for TCP deivce, eg: ZCAN_CANETTCP, ZCAN_WIFICAN_TCP

        :param int local_port:
            TCP/UDP local port.
            Just for TCP/UDP device.

        :param str dst_ip:
            TCP/UDP mode remote ip addr.
            Just for TCP/UDP device.

        :param int dst_port:
            TCP/UDP mode remote port.
            Just for TCP/UDP device.
        """
        super().__init__(channel=channel, **kwargs)

        if isinstance(channel, (list, tuple)):
            channels = channel
        elif isinstance(channel, int):
            channels = [channel]
        else:
            # Assume comma separated string of channels
            channels = [int(ch.strip()) for ch in channel.split(",")]

        self.device = zcanlib.OpenDevice(device, device_index, 0)
        if self.device == INVALID_DEVICE_HANDLE:
            log.error("open device failed")
            return

        self.is_fd_device = dev_have_attr(device, "is_fd")

        self.chn_handles = {}
        ip = zcanlib.GetIProperty(self.device)
        for chn in channels:
            if not dev_have_attr(device, "is_net_dev"):
                if self.is_fd_device:
                    if zcanlib.SetValue(ip, str(chn) + "/canfd_abit_baud_rate", str(bitrate)) != ZCAN_STATUS_OK:
                        log.error("set nominal baudrate failed")

                    data_bitrate = kwargs["data_bitrate"] if "data_bitrate" in kwargs else bitrate
                    if zcanlib.SetValue(ip, str(chn) + "/canfd_dbit_baud_rate", str(data_bitrate)) != ZCAN_STATUS_OK:
                        log.error("set data baudrate failed")
                else:
                    if zcanlib.SetValue(ip, str(chn) + "/baud_rate", str(bitrate)) != ZCAN_STATUS_OK:
                        log.error("set baudrate failed")

            chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
            if self.is_fd_device:
                chn_init_cfg.can_type = ZCAN_TYPE_CANFD
                chn_init_cfg.config.canfd.mode = 0  # 正常模式，是否考虑只听模式支持
            else:
                chn_init_cfg.can_type = ZCAN_TYPE_CAN
                chn_init_cfg.config.can.mode = 0  # 正常模式，是否考虑只听模式支持
                chn_init_cfg.config.can.acc_code = 0
                chn_init_cfg.config.can.acc_mask = 0xFFFFFFFF
            h = zcanlib.InitCAN(self.device, chn, chn_init_cfg)
            if h is None:
                log.error("init channel%dfailed", chn)
                continue

            if dev_have_attr(device, "is_net_dev"):
                if dev_have_attr(device, "is_tcp"):
                    if "is_server" in kwargs and \
                        zcanlib.SetValue(ip, str(chn) + "/work_mode",
                                            "1" if kwargs["is_server"] else "0") != ZCAN_STATUS_OK:
                        raise ValueError("set work_mode attr failed or no work_mode attr.")
                if not kwargs["is_server"] and ("dst_ip" not in kwargs or "dst_port" not in kwargs):
                    raise ValueError("net device have no ip or work_port attr.")

                if (
                    "dst_ip" in kwargs
                    and zcanlib.SetValue(ip, str(chn) + "/ip", kwargs["dst_ip"])
                    != ZCAN_STATUS_OK
                ):
                    raise ValueError("set dst ip attr failed.")

                if (
                    "dst_port" in kwargs
                    and zcanlib.SetValue(
                        ip, str(chn) + "/work_port", str(kwargs["dst_port"])
                    )
                    != ZCAN_STATUS_OK
                ):
                    raise ValueError("set dst port attr failed.")

                if (
                    "local_port" in kwargs
                    and zcanlib.SetValue(
                        ip, str(chn) + "/local_port", str(kwargs["local_port"])
                    )
                    != ZCAN_STATUS_OK
                ):
                    raise ValueError("set local port attr failed.")

            if zcanlib.StartCAN(h) != ZCAN_STATUS_OK:
                raise IOError("start channel%d failed." % chn)

            if dev_have_attr(device, "support_resistance") and "res_en" in kwargs:
                if zcanlib.SetValue(ip, str(chn) + "/initenal_resistance", \
                                            "1" if kwargs["res_en"] else "0") != ZCAN_STATUS_OK:
                    raise ValueError("set channel%d resistance failed" % chn)

            self.chn_handles[chn] = h

        zcanlib.ReleaseIProperty(ip)

    def _recv_check(self):
        for chn, handle in self.chn_handles.items():
            if zcanlib.GetReceiveNum(handle, ZCAN_TYPE_CAN):
                return chn, False
            if self.is_fd_device:
                if zcanlib.GetReceiveNum(handle, ZCAN_TYPE_CANFD):
                    return chn, True
        return None, False

    def _recv_can_msg(self, chn, timeout=0) -> Optional[Message]:
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

    def _recv_canfd_msg(self, chn, timeout=0) -> Optional[Message]:
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

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:
        end_time = time.perf_counter() + timeout if timeout else 0
        chn, is_rcv_canfd = self._recv_check()
        if chn:
            return (
                self._recv_canfd_msg(chn) if is_rcv_canfd else self._recv_can_msg(chn),
                False,
            )
        while time.perf_counter() < end_time:
            for chn, _ in self.chn_handles.items():
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
            raise ValueError("no channel to send")

        handle = list(self.chn_handles.values())[0]
        if msg.channel is not None:
            if msg.channel in self.chn_handles:
                handle = self.chn_handles[msg.channel]
            else:
                raise ValueError("no channel to send")

        ret = zcanlib.Transmit(handle, td, 1)
        if ret != 1:
            raise IOError("send can frame failed.")

    def _canfd_send(self, msg, timeout):
        td = ZCAN_TransmitFD_Data()
        td.transmit_type = 0
        td.frame.can_id = msg.arbitration_id
        td.frame.err = 0
        td.frame.rtr = 0
        td.frame.eff = 1 if msg.is_extended_id else 0
        td.frame.len = msg.dlc
        td.frame.brs = 1 if msg.bitrate_switch else 0

        for i in range(msg.dlc):
            td.frame.data[i] = msg.data[i]

        if len(self.chn_handles) == 0:
            log.error("no channel to send")
            return
        handle = list(self.chn_handles.values())[0]
        if msg.channel is not None:
            if msg.channel in self.chn_handles:
                handle = self.chn_handles[msg.channel]
            else:
                log.error("no channel to send")

        ret = zcanlib.TransmitFD(handle, td, 1)
        if ret != 1:
            raise IOError("send canfd frame failed.")

    def send(self, msg: Message, timeout: Optional[float] = None):
        if msg.is_fd:
            self._canfd_send(msg, timeout)
        else:
            self._can_send(msg, timeout)

    def flush_tx_buffer(self):
        pass
        # zcanlib.ClearBuffer(self.chn_handle)

    def shutdown(self):
        for handle in list(self.chn_handles.values()):
            zcanlib.ResetCAN(handle)
        zcanlib.CloseDevice(self.device)
