import os
import sys
from pathlib import Path
from pprint import pprint

# Project imports
path_root = Path(__file__).parents[1]
os.chdir(path_root)
sys.path.append(str(path_root))

from conformance_checking.rule_base import Rule_Checker
from util import import_xes_log

# %%
working_dir = Path("data")

os.chdir(working_dir)
print("changed directory to: %s" % os.getcwd())

log_file = Path("BPI_Challenge_2019-3-w-after.xes")
log_file_short = str(log_file).split(".xes")[0]

log = import_xes_log(log_file, "{http://www.xes-standard.org}")
print("length: %s" % len(log))
print(log[0])


rc = Rule_Checker()
# %%
print()
print("Check that Record Invoice Receipt is followed by Record Goods Receipt")
print()
res = rc.check_rir_rgr(log, "check")
pprint(res)
print()

print("Check that Record Invoice Receipt is followed by Clear Invoice")
print()
res = rc.check_rgr_ci(log, "check")
pprint(res)
print()

print(
    "Check that Record Invoice Receipt is followed by Clear Invoice WITHOUT Throughput"
)
print()
res = rc.check_rir_ci(log, "check", False)
pprint(res)
print()
print("Check that Record Invoice Receipt is followed by Clear Invoice WITH Throughput")
print()
res = rc.check_rir_ci(log, "check", True)
pprint(res)
print()

print("Throughput times:")
print()
res = rc.make_throughout_analysis(log, "Record Invoice Receipt", "Clear Invoice")
print("   From %s to %s" % (res["first"], res["second"]))
print("   Avg: %f, Median: %f, Standard deviation: %f, Var: %f" % res["throughput"])
print()
res = rc.make_throughout_analysis(log, "Record Invoice Receipt", "Record Goods Receipt")
print("   From %s to %s" % (res["first"], res["second"]))
print("   Avg: %f, Median: %f, Standard deviation: %f, Var: %f" % res["throughput"])
print()
res = rc.make_throughout_analysis(log, "Record Goods Receipt", "Clear Invoice")
print("   From %s to %s" % (res["first"], res["second"]))
print("   Avg: %f, Median: %f, Standard deviation: %f, Var: %f" % res["throughput"])
print()
