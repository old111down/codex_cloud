"""Build the explicitly curated paper/code inventory (no inferred success)."""
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
rows=[]
def add(cid,section,claim,code="Unknown",data="Unknown",config="Unknown",entry="Unknown",run="No — not executed end-to-end",status="部分覆盖",missing="Unknown",evidence=""):
    rows.append(dict(claim_id=cid,paper_section=section,claim=claim,code_paths=code,data_paths=data,
                     config=config,entrypoint=entry,executable=run,status=status,missing=missing,evidence=evidence))

main="upstream/mousika/"
v2="upstream/mousika-v2/"
ip="evidence/mousika/access_research/infocom2022.pdf"
tp="evidence/mousika/access_research/ton2023.pdf"
inv="evidence/mousika/access_research/infocom_inventory.md"
tinv="evidence/mousika/access_research/ton_inventory.md"
mc=main+"Distillation/bdt_test.py:125-268; "+main+"Distillation/SoftTree.py:10-187; "+main+"Distillation/Tree.py:10-174"
vc=v2+"Distillation/bdt_test.py:34-113; "+v2+"Distillation/SoftTree.py:8-162"
p4=main+"P4/flowcontrol.p4:14-21,96,208-270; "+main+"rule2entry/code/entry2dataplane.py:13-17,41-60,66-97"
enc=main+"rule2entry/code/rule2entry.py:13-46,51-66,103-113"
tasks=[("flow","UNIV1 elephant/mice packet classification","Distillation/Dataset/univ.zip","CSV provided; raw-to-CSV/top-20%-flow label derivation absent"),
       ("traffic","ISCX six-class application packet classification","Unknown — no processed ISCX files in either branch","Email/Chat/Streaming/File Transfer/VoIP/P2P loader, labels, preprocessing and run config absent"),
       ("malware","Bot-IoT binary packet classification","Unknown — no Bot-IoT files in either branch","Bot-IoT subset, label mapping, preprocessing and run config absent")]

add("I-F01","INFOCOM Fig.1 p2","PISA architecture",p4,"不适用","不适用","不适用","不适用 — conceptual figure","不适用","No empirical reproduction claim",ip+" p2; "+inv)
add("I-F02","INFOCOM Fig.2 p4 / III-A","Teacher→BDT→ternary→switch framework",mc+"; "+enc+"; "+p4,main+tasks[0][2],"Default RF/UNIV only","Distillation/bdt_test.py → rule2entry.py → SDE",missing="Only CPU components smoked; no completed deployment path",evidence=ip+" p4; logs/mousika/synthetic_smoke_scoped.log")
add("I-ALG1","INFOCOM Algorithm1 p4 / III-B","BDT Gini, recursion, leaf termination",mc,main+tasks[0][2],"min_sample_leaf=5; n_features=all","TreeClassifier.fit / SoftTreeClassifier.fit","Yes — narrow synthetic component only","部分覆盖","Full dataset behavior and complete paper equation equivalence Unknown",ip+" pp4-5; logs/mousika/synthetic_smoke_scoped.log")
for listing,claim,line in [(1,"Feature concatenation table / first pipeline stage","208-239"),(2,"Ternary classification table / second pipeline stage","241-270")]:
    add(f"I-L{listing}",f"INFOCOM Listing{listing} p6 / III-C",claim,main+f"P4/flowcontrol.p4:{line}","Packet PHV","Tofino TNA architecture","README SDE configure/make",missing="SDE/p4c absent; common/headers.p4 and common/util.p4 not in repo; actual stage allocation unverified",evidence=ip+" p6; "+p4)
add("I-T1","INFOCOM Table I p6 / III-C","Worked mask/value/class ternary entry",enc,"Example and bundled text rules","112-bit converter","Rule2Binary.get_ternary / parse_file","Yes — generic vectors and 5 bundled rulesets only","部分覆盖","Exact Table I P4 packet forwarding not executed",ip+" p6; logs/mousika/synthetic_smoke_scoped.log")
for fig,metric in [(3,"accuracy: DT, BDT, GRU/LSTM/RF teachers and distilled BDT"),(4,"tree growth time, excludes pretrained teacher cost"),(5,"classification rule counts: BDT and 3 distilled variants")]:
    for task,name,data,miss in tasks:
        add(f"I-F{fig:02d}-{task}",f"INFOCOM Fig.{fig} p7 / IV-B",name+" — "+metric,mc,main+data if task=="flow" else data,"5 repeated rounds; RF300; teacher choices rf/gru; hard-label weight kk=0","Distillation/bdt_test.py; dt_test.py",missing=miss+"; no LSTM implementation/main entry; no full metric execution",evidence=ip+" pp6-8; "+main+"Distillation/bdt_test.py:128,139,144-146,164-168,232-267; "+main+"Distillation/train_teacher.py:14-22")
for fig,metric in [(6,"40/100Gbps receive/transmit throughput and zero packet loss"),(7,"IIsy comparison: stage/table/table-entry counts"),(8,"IIsy comparison: TCAM/SRAM usage"),(9,"IIsy comparison: ternary crossbar/VLIW usage"),(10,"IIsy comparison: packet latency at 40/100Gbps")]:
    for task,name,data,miss in tasks:
        add(f"I-F{fig:02d}-{task}",f"INFOCOM Fig.{fig} pp7-9 / IV-C,D",name+" — "+metric,p4+"; "+enc,main+data if task=="flow" else data,"EdgeCore Wedge100BF-65X; Keysight XGS12-SDL","README SDE configure/make/run_switchd/run_p4_tests",missing="No hardware/SDE; no measurement or IIsy baseline code/config/raw logs; "+miss,evidence=ip+" pp7-9; "+inv+"; "+p4)
add("I-DATA-SPLIT","INFOCOM IV-A p6","No overlap by dates and five-tuples",main+"Distillation/utils.py:22-58,204-297",main+"Distillation/Dataset/univ.zip","split_train_test exists but load_data reads pre-split CSV","load_data","No — raw split reconstruction absent","部分覆盖","Capture dates, raw transform and independent disjointness verification Unknown; ISCX/Bot-IoT missing",ip+" p6; "+main+"Distillation/utils.py:22-58,209-261")
add("I-APPENDIX","INFOCOM complete 10-page paper","Appendix inventory","不适用","不适用","不适用","不适用","不适用","不适用","No appendix in retrieved full paper; external supplement existence Unknown",inv)

add("T-F01","ToN Fig.1 p3","P4 switch architecture",p4,"不适用","不适用","不适用","不适用 — conceptual figure","不适用","No empirical result",tinv)
add("T-F02","ToN Fig.2 p4","Extended framework",vc+"; "+enc+"; "+p4,"Unknown","RF/UNIV default","Distillation/bdt_test.py",missing="No complete three-task/five-teacher/hardware workflow",evidence=tinv)
add("T-F03","ToN Fig.3 p5 / Algorithm1 / IV","Bit BDT vs DT and Gini training",vc,"Synthetic counterexample in scripts/mousika/v2_gini_counterexample.py","class_num=2; n_features=sqrt; min_sample_leaf=20","SoftTreeClassifier.fit / __split_pair","Counterexample executed; no full reproduction","部分覆盖","Right-branch Gini missing square at line85; experimental equivalence after patch Unknown",tp+" pp5-6 Eq5; logs/mousika/v2_gini_counterexample.log")
for listing in [1,2]:
    add(f"T-L{listing}",f"ToN Listing{listing} p7 / VI","P4 initialization/classification",p4,"Packet PHV","Uses main-branch P4 per v2 README","SDE build/run",missing="No compiled/simulated/hardware run; missing include files",evidence=tp+" p7; "+v2+"readme.md")
add("T-T1","ToN Table I p7 / VI","Worked ternary match entry",enc,"Example/UNIV rules","112-bit main converter","Rule2Binary","Narrow main-branch encoding smoke only","部分覆盖","v2 model-to-switch equality not tested",tp+" p7; logs/mousika/synthetic_smoke_scoped.log")
for fig,metric in [(4,"alpha/beta RF mixing sweep"),(5,"accuracy; five teachers"),(6,"F1; five teachers"),(7,"precision; five teachers"),(8,"recall; five teachers"),(9,"BDT training time"),(10,"BDT rule counts"),(11,"delta accuracy versus delta rules")]:
    for task,name,data,miss in tasks:
        add(f"T-F{fig:02d}-{task}",f"ToN Fig.{fig} pp9-10 / VII-A,B,C",name+" — "+metric,vc+"; "+v2+"Distillation/train_teacher.py:7-14",("Unknown — not bundled in v2; main ZIP exists" if task=="flow" else data),"K=.75, T=1, class_num=2; RF10/max_depth10; hard-coded single experiment","Distillation/bdt_test.py",missing=miss+"; no sweep/outer5fold/grid-search; gbdt/mlp aliases still call RF; select_model always GRU; Gini defect; no paper metric run",evidence=tp+" pp8-10; "+v2+"Distillation/bdt_test.py:37-50,80-113; logs/mousika/readme_v2_bdt.log")
for fig,metric in [(12,"Python versus P4 accuracy parity"),(13,"three physical switches at nominal100Gbps IMIX throughput"),(14,"three physical switches latency")]:
    for task,name,data,miss in tasks:
        hardware_config=("Python vs P4(H3C S9850-32H) parity" if fig==12 else "EdgeCore Wedge100BF-65X, H3C S9850-32H, OpenMesh BF-48×6Z; Keysight")
        add(f"T-F{fig:02d}-{task}",f"ToN Fig.{fig} p11 / VII-D",name+" — "+metric,p4+"; "+enc,main+data if task=="flow" else data,hardware_config,"SDE build/run and external generator",missing="Hardware/toolchain/device build configs/measurement harness absent; v2 original data processing absent; "+miss,evidence=tp+" pp10-11; "+tinv)
add("T-F15","ToN Fig.15 p11 / VII-E","Malware detection resource comparison: IIsy, Planter, pForest, Mousikav2",p4,"Unknown","H3C hardware; baselines absent","Unknown",status="部分覆盖",missing="No baseline code/config, resource compiler reports, hardware or raw measurements",evidence=tp+" pp11-12; "+tinv)
for task,name,data,miss in tasks:
    add("T-F16-"+task,"ToN Fig.16 p12 / VII-E",name+" — Python/P4 baseline accuracy",p4,main+data if task=="flow" else data,"IIsy/Planter/pForest; only4/10 RF trees on hardware","Unknown",status="缺失",missing="Baseline implementations/experiments not in this repo; physical deployment not executed; main data only, v2 original processing absent",evidence=tp+" p12; "+tinv)
add("T-F17","ToN Fig.17 p12 / VII-E","Scalability sweep: entries vs nodes/features/depth",vc+"; "+p4,"Unknown","Unknown — no sweep config","Unknown",status="缺失",missing="No sweep runner/data/raw compiler resource results",evidence=tp+" p12; "+tinv)
add("T-F18","ToN Fig.18 p12 / VII-F","ISCX Deep Packet and SAM teachers/distilled BDT comparison","Unknown — no Deep Packet or SAM source in this repo","Unknown — ISCX absent","Unknown","Unknown",status="缺失",missing="Both baselines, processed data, teacher checkpoints and comparison script absent",evidence=tp+" p12; "+tinv)
add("T-OUTER5FOLD","ToN VII-A p8","Five-fold outer evaluation protocol",v2+"Distillation/bdt_test.py:37-38,57-58,87-90","Unknown","KFold2 is internal soft-label generation; no outer5fold","Unknown",status="缺失",missing="No outer5fold evaluator or fold ids; train/test CSV only",evidence=tp+" p8; "+tinv)
add("T-GRID","ToN VII-A p8","Teacher grid search per dataset",v2+"Distillation/bdt_test.py:42; "+v2+"Distillation/train_teacher.py:17-18","Unknown","Fixed RF and NN hyperparameters","Unknown",status="缺失",missing="Grid ranges/selected configurations/runs not supplied",evidence=tp+" p8; "+tinv)
add("T-HYBRID","ToN VII-F p12 discussion before VIII","Hybrid switch/server mitigation suggestion","Unknown","不适用","不适用","不适用","不适用 — discussion/future suggestion","不适用","Not an evaluated implementation claim",tinv)
add("T-APPENDIX","ToN complete14-page paper","Appendix inventory","不适用","不适用","不适用","不适用","不适用","不适用","No appendix in retrieved full paper; external supplement existence Unknown",tinv)

add("RUN-SMOKE","Audit execution only","32 synthetic vectors: original Tree/SoftTree predictions; SoftTree export/ternary semantics; all5 bundled rulesets equal",mc+"; "+enc,"Synthetic; bundled rule text", "CPU Conda", "scripts/mousika/smoke.py","Yes — scoped smoke","已验证","Tree export→converter separately fails on decimal label1.0; no paper metric implication","logs/mousika/synthetic_smoke.log; logs/mousika/synthetic_smoke_scoped.log")
out=ROOT/"papers/mousika/coverage_matrix.csv"
with out.open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(f"Wrote {len(rows)} curated coverage records")
