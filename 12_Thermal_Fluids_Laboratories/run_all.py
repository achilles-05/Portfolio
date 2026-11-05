# runs every lab analysis in this folder
import runpy
for s in ["pump_curve.py", "flowmeter_calibration.py", "pipe_friction.py", "heat_exchanger.py", "refrigeration_cop.py"]:
    print(f"----- {s} -----")
    runpy.run_path(s, run_name="__main__")
