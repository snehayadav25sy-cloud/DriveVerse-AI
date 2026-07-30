"""
dataset-engine — standalone annotation, calibration, metadata and export pipeline.

Design rule: this package NEVER imports 'carla' and NEVER connects to a CARLA
server directly. It only receives already-captured raw data (numpy arrays,
dicts of actor state) handed off by worker/simulator/carla/.
"""
