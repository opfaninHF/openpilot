"""Ford neutral frames must never bypass subsequent steering safety checks."""
import unittest

from opendbc.car.structs import CarParams
from opendbc.safety.tests.common import CANPackerSafety
from opendbc.safety.tests.libsafety import libsafety_py


class TestFordResetPermissions(unittest.TestCase):
  def prepare(self, canfd):
    self.packer = CANPackerSafety("ford_lincoln_base_pt")
    self.safety = libsafety_py.libsafety
    self.safety.set_current_safety_param_sp(0)
    self.safety.set_safety_hooks(CarParams.SafetyModel.ford, 1 | (2 if canfd else 0))
    self.safety.init_tests()
    self.canfd = canfd

  def command(self, enabled, angle=0.0, offset=0.0):
    values = {
      "LatCtlPathOffst_L_Actl": offset,
      "LatCtlPath_An_Actl": angle,
      "LatCtlCurv_No_Actl": 0.0,
    }
    if self.canfd:
      values.update({"LatCtl_D2_Rq": int(enabled), "LatCtlCrv_NoRate2_Actl": 0.0})
      name = "LateralMotionControl2"
    else:
      values.update({"LatCtl_D_Rq": int(enabled), "LatCtlCurv_NoRate_Actl": 0.0})
      name = "LateralMotionControl"
    return self.safety.safety_tx_hook(self.packer.make_can_msg_safety(name, 0, values))

  def test_neutral_cannot_unlock_active_steering(self):
    for canfd in (False, True):
      with self.subTest(canfd=canfd):
        self.prepare(canfd)
        self.safety.set_controls_allowed(False)
        self.assertTrue(self.command(False))
        self.assertFalse(self.command(True, angle=0.1))

  def test_neutral_cannot_unlock_disabled_nonzero_steering(self):
    for canfd in (False, True):
      with self.subTest(canfd=canfd):
        self.prepare(canfd)
        self.safety.set_controls_allowed(False)
        self.assertTrue(self.command(False))
        self.assertFalse(self.command(False, angle=0.1))

  def test_neutral_cannot_override_path_angle_limit(self):
    for canfd in (False, True):
      with self.subTest(canfd=canfd):
        self.prepare(canfd)
        self.safety.set_controls_allowed(True)
        self.assertTrue(self.command(False))
        self.assertFalse(self.command(True, angle=0.5))

  def test_neutral_cannot_override_path_offset_limit(self):
    for canfd in (False, True):
      with self.subTest(canfd=canfd):
        self.prepare(canfd)
        self.safety.set_controls_allowed(True)
        self.assertTrue(self.command(False))
        self.assertFalse(self.command(True, offset=5.0))

  def test_neutral_without_control_is_still_allowed(self):
    for canfd in (False, True):
      with self.subTest(canfd=canfd):
        self.prepare(canfd)
        self.safety.set_controls_allowed(False)
        self.assertTrue(self.command(False))

  def test_small_authorized_angle_command_is_allowed(self):
    for canfd in (False, True):
      with self.subTest(canfd=canfd):
        self.prepare(canfd)
        self.safety.set_controls_allowed(True)
        addr, data, bus = self.packer.make_can_msg("Lane_Assist_Data1", 0, {"LkaActvStats_D2_Req": 0})
        data = bytearray(data)
        data[4] |= 1
        data[5:7] = b"\x00\x00"
        self.assertTrue(self.safety.safety_tx_hook(libsafety_py.make_CANPacket(addr, bus, bytes(data))))
        self.assertTrue(self.command(False))
        self.assertTrue(self.command(True, angle=0.0005))


if __name__ == "__main__":
  unittest.main()
