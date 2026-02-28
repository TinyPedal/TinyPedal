#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2026 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Garage setting function
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from ..validator import generator_init

# Note: CompoundSetting value can desync, so ignored from output
LMU_CARSETUP_MAP = MappingProxyType({
    "GENERAL": {
        "Symmetric": "symmetric",
        "CGHeightSetting": "VM_WEIGHT_VERTICAL",
        "CGRightSetting": "VM_WEIGHT_LATERAL",
        "CGRearSetting": "VM_WEIGHT_DISTRIB",
        "WedgeSetting": "VM_WEIGHT_WEDGE",
        "FrontTireCompoundSetting": "VM_FRONT_TIRE_COMPOUND",
        "RearTireCompoundSetting": "VM_REAR_TIRE_COMPOUND",
        "FuelSetting": "VM_FUEL_LEVEL",
        "FuelCapacitySetting": "VM_FUEL_CAPACITY",
        "VirtualEnergySetting": "VM_VIRTUAL_ENERGY",
        "NumPitstopsSetting": "VM_NUM_PITSTOPS",
        "Pitstop1Setting": "VM_PITSTOP_1",
        "Pitstop2Setting": "VM_PITSTOP_2",
        "Pitstop3Setting": "VM_PITSTOP_3",
    },
    "LEFTFENDER": {
        "FenderFlareSetting": "VM_LEFT_FENDER_FLARE",
    },
    "RIGHTFENDER": {
        "FenderFlareSetting": "VM_RIGHT_FENDER_FLARE",
    },
    "FRONTWING": {
        "FWSetting": "VM_FRONT_WING",
    },
    "REARWING": {
        "RWSetting": "VM_REAR_WING",
    },
    "BODYAERO": {
        "WaterRadiatorSetting": "VM_WATER_RADIATOR",
        "OilRadiatorSetting": "VM_OIL_RADIATOR",
        "BrakeDuctSetting": "VM_BRAKE_DUCTS",
        "BrakeDuctRearSetting": "VM_BRAKE_DUCTS_REAR",
    },
    "SUSPENSION": {
        "FrontWheelTrackSetting": "VM_FRONT_WHEEL_TRACK",
        "RearWheelTrackSetting": "VM_REAR_WHEEL_TRACK",
        "FrontAntiSwaySetting": "VM_FRONT_ANTISWAY",
        "RearAntiSwaySetting": "VM_REAR_ANTISWAY",
        "FrontToeInSetting": "VM_FRONT_TOEIN",
        "FrontToeOffsetSetting": "VM_FRONT_TOEOFFSET",
        "RearToeInSetting": "VM_REAR_TOEIN",
        "RearToeOffsetSetting": "VM_REAR_TOEOFFSET",
        "LeftCasterSetting": "VM_LEFT_CASTER",
        "RightCasterSetting": "VM_RIGHT_CASTER",
        "LeftTrackBarSetting": "VM_LEFT_TRACK_BAR",
        "RightTrackBarSetting": "VM_RIGHT_TRACK_BAR",
        "Front3rdPackerSetting": "VM_FRONT_3RD_PACKERS",
        "Front3rdSpringSetting": "VM_FRONT_3RD_SPRING",
        "Front3rdTenderSpringSetting": "VM_FRONT_3RD_TENDERSPRING",
        "Front3rdTenderTravelSetting": "VM_FRONT_3RD_TENDERSPRINGTRAVEL",
        "Front3rdSlowBumpSetting": "VM_FRONT_3RD_SLOWBUMP",
        "Front3rdFastBumpSetting": "VM_FRONT_3RD_FASTBUMP",
        "Front3rdSlowReboundSetting": "VM_FRONT_3RD_SLOWREBOUND",
        "Front3rdFastReboundSetting": "VM_FRONT_3RD_FASTREBOUND",
        "Rear3rdPackerSetting": "VM_REAR_3RD_PACKERS",
        "Rear3rdSpringSetting": "VM_REAR_3RD_SPRING",
        "Rear3rdTenderSpringSetting": "VM_REAR_3RD_TENDERSPRING",
        "Rear3rdTenderTravelSetting": "VM_REAR_3RD_TENDERSPRINGTRAVEL",
        "Rear3rdSlowBumpSetting": "VM_REAR_3RD_SLOWBUMP",
        "Rear3rdFastBumpSetting": "VM_REAR_3RD_FASTBUMP",
        "Rear3rdSlowReboundSetting": "VM_REAR_3RD_SLOWREBOUND",
        "Rear3rdFastReboundSetting": "VM_REAR_3RD_FASTREBOUND",
        "ChassisAdj00Setting": "VM_CHASSIS_ADJ_00",
        "ChassisAdj01Setting": "VM_CHASSIS_ADJ_01",
        "ChassisAdj02Setting": "VM_CHASSIS_ADJ_02",
        "ChassisAdj03Setting": "VM_CHASSIS_ADJ_03",
        "ChassisAdj04Setting": "VM_CHASSIS_ADJ_04",
        "ChassisAdj05Setting": "VM_CHASSIS_ADJ_05",
        "ChassisAdj06Setting": "VM_CHASSIS_ADJ_06",
        "ChassisAdj07Setting": "VM_CHASSIS_ADJ_07",
        "ChassisAdj08Setting": "VM_CHASSIS_ADJ_08",
        "ChassisAdj09Setting": "VM_CHASSIS_ADJ_09",
        "ChassisAdj10Setting": "VM_CHASSIS_ADJ_10",
        "ChassisAdj11Setting": "VM_CHASSIS_ADJ_11",
    },
    "CONTROLS": {
        "SteerLockSetting": "VM_STEER_LOCK",
        "RearBrakeSetting": "VM_BRAKE_BALANCE",
        "BrakeMigrationSetting": "VM_BRAKE_MIGRATION",
        "BrakePressureSetting": "VM_BRAKE_PRESSURE",
        "HandfrontbrakePressSetting": "VM_HANDFRONTBRAKE_PRESSURE",
        "HandbrakePressSetting": "VM_HANDBRAKE_PRESSURE",
        "TCSetting": "VM_TRACTION_CONTROL",
        "ABSSetting": "VM_ANTILOCK_BRAKES",
        "TractionControlMapSetting": "VM_TRACTIONCONTROLMAP",
        "TCPowerCutMapSetting": "VM_TRACTIONCONTROLPOWERCUTMAP",
        "TCSlipAngleMapSetting": "VM_TRACTIONCONTROLSLIPANGLEMAP",
        "AntilockBrakeSystemMapSetting": "VM_ANTILOCKBRAKESYSTEMMAP",
    },
    "ENGINE": {
        "RevLimitSetting": "VM_REV_LIMITER",
        "EngineBoostSetting": "VM_ENGINE_BOOST",
        "RegenerationMapSetting": "VM_REGEN_LEVEL",
        "ElectricMotorMapSetting": "VM_ELECTRIC_MOTOR_MAP",
        "EngineMixtureSetting": "VM_ENGINE_MIXTURE",
        "EngineBrakingMapSetting": "VM_ENGINE_BRAKEMAP",
    },
    "DRIVELINE": {
        "FinalDriveSetting": "VM_GEAR_FINAL",
        "ReverseSetting": "VM_GEAR_REVERSE",
        "Gear1Setting": "VM_GEAR_1",
        "Gear2Setting": "VM_GEAR_2",
        "Gear3Setting": "VM_GEAR_3",
        "Gear4Setting": "VM_GEAR_4",
        "Gear5Setting": "VM_GEAR_5",
        "Gear6Setting": "VM_GEAR_6",
        "Gear7Setting": "VM_GEAR_7",
        "Gear8Setting": "VM_GEAR_8",
        "Gear9Setting": "VM_GEAR_9",
        "RatioSetSetting": "VM_RATIO_SET",
        "DiffPumpSetting": "VM_DIFF_PUMP",
        "DiffPowerSetting": "VM_DIFF_POWER",
        "DiffCoastSetting": "VM_DIFF_COAST",
        "DiffPreloadSetting": "VM_DIFF_PRELOAD",
        "FrontDiffPumpSetting": "VM_FRONT_DIFF_PUMP",
        "FrontDiffPowerSetting": "VM_FRONT_DIFF_POWER",
        "FrontDiffCoastSetting": "VM_FRONT_DIFF_COAST",
        "FrontDiffPreloadSetting": "VM_FRONT_DIFF_PRELOAD",
        "RearSplitSetting": "VM_TORQUE_SPLIT",
        "GearAutoUpShiftSetting": "VM_GEAR_AUTOUPSHIFT",
        "GearAutoDownShiftSetting": "VM_GEAR_AUTODOWNSHIFT",
    },
    "FRONTLEFT": {
        "CamberSetting": "WM_CAMBER-W_FL",
        "PressureSetting": "WM_PRESSURE-W_FL",
        "PackerSetting": "WM_PACKERS-W_FL",
        "SpringSetting": "WM_SPRING-W_FL",
        "TenderSpringSetting": "WM_TENDERSPRING-W_FL",
        "TenderTravelSetting": "WM_TENDERSPRINGTRAVEL-W_FL",
        "SpringRubberSetting": "WM_SRUBBER-W_FL",
        "RideHeightSetting": "WM_RIDEHEIGHT-W_FL",
        "SlowBumpSetting": "WM_SLOWBUMP-W_FL",
        "FastBumpSetting": "WM_FASTBUMP-W_FL",
        "SlowReboundSetting": "WM_SLOWREBOUND-W_FL",
        "FastReboundSetting": "WM_FASTREBOUND-W_FL",
        "BrakeDiscSetting": "WM_BRAKEDISC-W_FL",
        "BrakePadSetting": "WM_BRAKEPAD-W_FL",
        #"CompoundSetting": "WM_COMPOUND-W_FL",
    },
    "FRONTRIGHT": {
        "CamberSetting": "WM_CAMBER-W_FR",
        "PressureSetting": "WM_PRESSURE-W_FR",
        "PackerSetting": "WM_PACKERS-W_FR",
        "SpringSetting": "WM_SPRING-W_FR",
        "TenderSpringSetting": "WM_TENDERSPRING-W_FR",
        "TenderTravelSetting": "WM_TENDERSPRINGTRAVEL-W_FR",
        "SpringRubberSetting": "WM_SRUBBER-W_FR",
        "RideHeightSetting": "WM_RIDEHEIGHT-W_FR",
        "SlowBumpSetting": "WM_SLOWBUMP-W_FR",
        "FastBumpSetting": "WM_FASTBUMP-W_FR",
        "SlowReboundSetting": "WM_SLOWREBOUND-W_FR",
        "FastReboundSetting": "WM_FASTREBOUND-W_FR",
        "BrakeDiscSetting": "WM_BRAKEDISC-W_FR",
        "BrakePadSetting": "WM_BRAKEPAD-W_FR",
        #"CompoundSetting": "WM_COMPOUND-W_FR",
    },
    "REARLEFT": {
        "CamberSetting": "WM_CAMBER-W_RL",
        "PressureSetting": "WM_PRESSURE-W_RL",
        "PackerSetting": "WM_PACKERS-W_RL",
        "SpringSetting": "WM_SPRING-W_RL",
        "TenderSpringSetting": "WM_TENDERSPRING-W_RL",
        "TenderTravelSetting": "WM_TENDERSPRINGTRAVEL-W_RL",
        "SpringRubberSetting": "WM_SRUBBER-W_RL",
        "RideHeightSetting": "WM_RIDEHEIGHT-W_RL",
        "SlowBumpSetting": "WM_SLOWBUMP-W_RL",
        "FastBumpSetting": "WM_FASTBUMP-W_RL",
        "SlowReboundSetting": "WM_SLOWREBOUND-W_RL",
        "FastReboundSetting": "WM_FASTREBOUND-W_RL",
        "BrakeDiscSetting": "WM_BRAKEDISC-W_RL",
        "BrakePadSetting": "WM_BRAKEPAD-W_RL",
        #"CompoundSetting": "WM_COMPOUND-W_RL",
    },
    "REARRIGHT": {
        "CamberSetting": "WM_CAMBER-W_RR",
        "PressureSetting": "WM_PRESSURE-W_RR",
        "PackerSetting": "WM_PACKERS-W_RR",
        "SpringSetting": "WM_SPRING-W_RR",
        "TenderSpringSetting": "WM_TENDERSPRING-W_RR",
        "TenderTravelSetting": "WM_TENDERSPRINGTRAVEL-W_RR",
        "SpringRubberSetting": "WM_SRUBBER-W_RR",
        "RideHeightSetting": "WM_RIDEHEIGHT-W_RR",
        "SlowBumpSetting": "WM_SLOWBUMP-W_RR",
        "FastBumpSetting": "WM_FASTBUMP-W_RR",
        "SlowReboundSetting": "WM_SLOWREBOUND-W_RR",
        "FastReboundSetting": "WM_FASTREBOUND-W_RR",
        "BrakeDiscSetting": "WM_BRAKEDISC-W_RR",
        "BrakePadSetting": "WM_BRAKEPAD-W_RR",
        #"CompoundSetting": "WM_COMPOUND-W_RR",
    },
})


def lmu_car_setup_json_to_svm(source: dict, reference: Mapping):
    """Parse car setup JSON to SVM (LMU format)"""
    from ..api_control import api

    if not isinstance(source, dict):
        return ""

    class_name = api.read.vehicle.class_name()
    if not class_name:
        return ""

    yield f'VehicleClassSetting="{class_name}"'
    yield "UpgradeSetting=(0,0,0,0)"
    yield ""

    for name, setting in reference.items():
        # Setting category
        yield f"[{name}]"
        # Setting entry & value
        for key, option in setting.items():
            refer = source.get(option)
            if refer is None:
                continue
            if isinstance(refer, dict):
                value = refer.get("value")
                if value is not None:
                    yield f"{key}={value}"
                    continue
            if isinstance(refer, bool):
                yield f"{key}={int(refer)}"
                continue
        yield ""


def export_lmu_car_setup(source: dict) -> tuple[str, ...]:
    """Export lmu car setup"""
    return tuple(lmu_car_setup_json_to_svm(source, LMU_CARSETUP_MAP))


@generator_init
def _process_rf2_car_setup():
    """Process rf2 car setup"""
    data = {}
    count = 0
    unique_key = (
        "VM_OIL_RADIATOR", # aerodynamics
        "VM_BRAKE_PRESSURE", # brakes
        "VM_STEER_LOCK", # chassis
        "VM_DIFF_PRELOAD", # drivetrain
        "VM_TRACTION_CONTROL", # electronics
        "VM_FUEL_LEVEL", # fuel
        "VM_ENGINE_MIXTURE", # gears
        "VM_FRONT_ANTISWAY", # suspension
        "WM_CAMBER-W_FL", # tires
    )
    while True:

        if count < len(unique_key):
            source = yield ()
        else:
            source = yield tuple(lmu_car_setup_json_to_svm(data, LMU_CARSETUP_MAP))
            data.clear()
            count = 0

        if isinstance(source, dict):
            # Check if any old data and reset
            for key in unique_key:
                if key in source and key in data:
                    data.clear()
                    count = 0
                    break
            data.update(source)
            count += 1


export_rf2_car_setup = _process_rf2_car_setup().send
