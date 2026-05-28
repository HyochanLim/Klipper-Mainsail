# Five-channel filament mixing support
#
# Copyright (C) 2026 <hyochan5211@gmail.com> 내가 혼자서 만들었어욤 >.<
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging

CHANNELS = ('C', 'M', 'Y', 'K', 'W')
DEFAULT_RATIOS = {'C': 1., 'M': 0., 'Y': 0., 'K': 0., 'W': 0.} # 기본 색깔은 Cyan만 사용하도록 설정.


def copy_ratios(ratios):
    return {channel: float(ratios[channel]) for channel in CHANNELS}


def read_ratios(gcmd):
    ratios = {}
    for channel in CHANNELS:
        ratios[channel] = gcmd.get_float(channel, 0., minval=0.)
    return ratios


def ratio_sum(ratios):
    total = 0.
    for channel in CHANNELS:
        total += ratios[channel]
    return total


def normalize_ratios(ratios):
    total = ratio_sum(ratios)
    if total <= 0.:
        return copy_ratios(DEFAULT_RATIOS)
    return {channel: ratios[channel] / total for channel in CHANNELS}


def active_channels(ratios):
    active = []
    for channel in CHANNELS:
        if ratios[channel] > 0.:
            active.append(channel)
    return active


def mixed_rotation_distance(base_distance, ratio):
    return base_distance / ratio


class FilamentMixing:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.extruder_name = config.get('extruder', 'extruder')
        self.stepper_names = {
            'C': config.get('c_stepper'),
            'M': config.get('m_stepper'),
            'Y': config.get('y_stepper'),
            'K': config.get('k_stepper'),
            'W': config.get('w_stepper'),
        }
        self.steppers = {}
        self.base_rotation_distances = {}
        self.toolhead = None
        self.current_tool = None
        self.current_ratios = copy_ratios(DEFAULT_RATIOS)

        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('SET_FILAMENT_MIXING',
                               self.cmd_SET_FILAMENT_MIXING,
                               desc=self.cmd_SET_FILAMENT_MIXING_help)

        self.printer.register_event_handler('klippy:connect',
                                            self._handle_connect)
        self.printer.register_event_handler('klippy:ready',
                                            self._handle_ready)

    def _handle_connect(self):
        self.toolhead = self.printer.lookup_object('toolhead')
        for channel in CHANNELS:
            stepper = self.printer.lookup_object(self.stepper_names[channel])
            if not hasattr(stepper, 'extruder_stepper'):
                raise self.printer.config_error(
                    "Filament mixing stepper '%s' is not an extruder_stepper"
                    % (self.stepper_names[channel],))
            self.steppers[channel] = stepper.extruder_stepper
            rotation_distance, _steps = (
                stepper.extruder_stepper.stepper.get_rotation_distance())
            self.base_rotation_distances[channel] = rotation_distance

    def _handle_ready(self):
        self._apply_ratios(self.current_ratios)

    def get_status(self, eventtime):
        return {
            'tool': self.current_tool,
            'ratios': copy_ratios(self.current_ratios),
            'active_channels': active_channels(self.current_ratios),
        }

    def _set_channel_ratio(self, channel, ratio):
        extruder_stepper = self.steppers[channel]

        if ratio <= 0.:
            extruder_stepper.sync_to_extruder(None)
            return

        base_distance = self.base_rotation_distances[channel]
        rotation_distance = mixed_rotation_distance(base_distance, ratio)
        extruder_stepper.stepper.set_rotation_distance(rotation_distance)
        extruder_stepper.sync_to_extruder(self.extruder_name)

    def _apply_ratios(self, ratios):
        self.toolhead.flush_step_generation()
        for channel in CHANNELS:
            self._set_channel_ratio(channel, ratios[channel])

    cmd_SET_FILAMENT_MIXING_help = "Set five-channel filament mixing ratios"

    def cmd_SET_FILAMENT_MIXING(self, gcmd):
        self.current_tool = gcmd.get_int('TOOL', self.current_tool,
                                         minval=0)
        requested_ratios = read_ratios(gcmd)
        requested_sum = ratio_sum(requested_ratios)

        if requested_sum <= 0.:
            logging.warning(
                "SET_FILAMENT_MIXING received zero total ratio; using C=1")
            gcmd.respond_info(
                "SET_FILAMENT_MIXING received zero total ratio; using C=1")
            self.current_ratios = copy_ratios(DEFAULT_RATIOS)
        else:
            self.current_ratios = normalize_ratios(requested_ratios)

        self._apply_ratios(self.current_ratios)


def load_config(config):
    return FilamentMixing(config)
