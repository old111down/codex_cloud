import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'papers/leo'; E=ROOT/'evidence/leo'
old=next(r for r in json.loads((ROOT/'catalog/candidates.json').read_text()) if r['id']=='leo')
meta=dict(old)
meta.update(paper_id='leo',publication_date='2024-04-16',reproduction_level='R1',
 source_record='papers/leo/metadata.json',paper_metrics_reproduced=False,
 execution_status='R1 scoped CPU generators/resource model and synthetic diagnostics; no real network data or paper evaluation',
 proprietary_dependency='Historical experiments require SDE9.11.1/Tofino hardware. Public open-p4studio now exists, but original-version equivalence, hardware BSP/Serdes/P4Insight and actual build/simulation are unverified.',
 gpu_dependency='No GPU needed for inspected CART/text-generator/resource paths; no GPU used.',
 unknowns=['Real-data classifier accuracy/precision/recall/F1 and all paper performance Unknown','P4 compile/packet simulation/hardware not executed','Full paper data, split, feature quantization and experiment configuration equivalence Unknown','Counterexamples are source-level numerical evidence, not observations of original hardware datasets'],
 audited_paper='USENIX final PDF,20 physical pages including cover, printed1573–1591; all sections and AppendixA read',
 coverage_scope='Fig1–23,Table1–2,Methods4/Implementation5/Analysis6/Evaluation7/AppendixA.1–A.3',
 execution_scope='Original P4 text generator/resource model and synthetic source diagnostics only; no real-data classifier/P4 build/simulation/hardware',
 component_levels={'Python_text_generation':'R1','resource_model':'R1','real_network_data':'R0','P4_build':'R0','P4_packet_simulation':'R0','hardware':'R0'},
 main_tasks_implementation_complete='No complete demonstrated coverage; feature extraction and several evaluation/runtime-update components are partial/missing',
 critical_findings=['Integer CART threshold rounding mismatch','Unsigned16-bit subtraction/MSB domain mismatch','Generated transient control plane explicitly disabled','Original data and full experiment configurations absent'],
 upstream_git_status=subprocess.check_output(['git','-C',str(ROOT/'upstream/leo'),'status','--porcelain'],text=True).strip(),
 retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
meta['evidence_files']=list(dict.fromkeys(meta.get('evidence_files',[])+['evidence/leo/paper_inventory.json','evidence/leo/source_symbols.json','evidence/leo/threshold_counterexample.json','evidence/leo/integer_domain_counterexamples.json']))
(P/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')

rows=[]
def row(cid,section,claim,code,data='Not acquired; exact raw-data provenance Unknown',config='No complete original experiment manifest',entry='Unknown',executable='Not run; full-paper equivalence Unknown',status='部分覆盖',missing='Original data/configuration/evaluation or deployment unavailable',evidence=''):
    rows.append(dict(claim_id=cid,paper_section=section,claim=claim,code_paths=code,data_paths=data,config=config,entrypoint=entry,executable=executable,status=status,missing=missing,evidence=evidence or 'evidence/leo/paper.txt; evidence/leo/source_manifest.json; evidence/leo/source_symbols.json'))
row('DATA-PROTOCOL','§7.2 printed1582–1583','CICIDS7 classes/42 features; NB15binary/22 stated features;75/25 stratified split; entropy/balanced CART/RFE','dataset-simulation/dataset-processor-cicids2017.py::read_and_clean_dataset/preprocess_dataset/main; dataset-processor-nb15.py::preprocess_dataset/main',config='Hardcoded10 settings; NB15 bin_threshold3000 defaults multi-class; no random_state',entry='python dataset-processor-cicids2017.py / dataset-processor-nb15.py',executable='CICIDS original entry attempted: missingCSV',missing='Original CSV and seeds absent; main binary NB15 setting not default; official train/test merged and re-split',evidence='evidence/leo/paper.txt; logs/leo/readme_training_missing_data.log; evidence/leo/source_symbols.json')
row('FEATURE-EXTRACTION','§5 / §A.3.3','Switch feature extraction,quantization and per-flow state for all evaluated configurations','leo-generator/leo_templates.py::ingress_parser_deparser/apply_t markers; leo/leo-1m-flows.p4',entry='Generated P4 requires manual feature extraction',missing='README explicitly leaves extraction to user; one1M-flow example does not provide all4 Table2 configurations; numeric preprocessing absent from two dataset scripts')
row('F01','Fig1 printed1575','CICIDS depth8/10/12 vs32–512 leaves F1 sweep','dataset-simulation/dataset-processor-cicids2017.py::main',missing='Training primitives present, exact depth/leaf sweep and original figure source/results absent')
row('T01','Table1 printed1575','Qualitative prior-work/Leo capabilities comparison','iisy/resource-model.py; leo/resource-model.py; leo-generator/',data='Not applicable',status='不适用',executable='Not an executable metric table',missing='Pure qualitative table; capability claims audited separately')
row('F02','Fig2 printed1575','IIsy feature-codeword/combination-table example','iisy/iisy.p4; iisy/resource-model.py',data='Conceptual tree, no corresponding checked-in example input',missing='Exact illustrated tree/codeword outputs not archived')
row('F03','Fig3 printed1576','Geometric visualization of proof tree with3 features','iisy/resource-model.py::proposition_2_*',data='Not applicable',status='不适用',executable='Conceptual illustration, no scientific run required',missing='Underlying resource formulas audited separately')
for n,section,claim,code,missing in [
 (4,'§4.2 printed1577','Workflow: representative tree→pipeline mapping→runtime configuration','leo-generator/leo_dataplane_generator.py; leo_ctrlplane_generator.py','No fully automatic mapping feasibility test, feature extraction or complete runtime updater'),
 (5,'§4.3 printed1577','Runtime feature/constraint multiplexed ALU','leo-generator/leo_templates.py; leo_sram.py::layer_gen; leo_tcam.py::layer_gen','GeneratedP4 present; not compiled or packet-tested'),
 (6,'§4.3 printed1578','General inequality rewriting preserves decision conditions','leo-generator/leo_ctrlplane.py::parse_line/build_tree_from_file/generate_rule_commands','Parser ignores condition and rounds thresholds; confirmed boundary/domain counterexamples'),
 (7,'§4.4 printed1578','One multiplexed ALU per depth for k=1','leo-generator/leo_dataplane_generator.py --sub_tree1; leo_sram.py; leo_tcam.py','No compiled/semantic test of full illustration'),
 (8,'§4.4 printed1578','Boolean SRAM/TCAM sub-tree truth encoding','leo-generator/leo_ctrlplane.py::generate_combinations/generate_func_inputs/generate_func_inputs_tcam','No standalone exact figure truth-table/packet-validation artifacts'),
 (9,'§4.4 printed1579','Sub-tree flattening/multiplexing k=3 nodes','leo-generator/leo_dataplane_generator.py --sub_tree2; leo_ctrlplane.py::sub_tree_splitter','Text generators present; complete original figure/config/hardware stage validation absent'),
 (10,'§5 printed1580','Ingress state/egress decision tree share physical stages','leo/leo-1m-flows.p4; leo/leo.p4','Fixedexample source present; actual compiler resource allocation not measured')]:
 row(f'F{n:02d}',f'Fig{n} / {section}',claim,code,missing=missing)
row('TRANSIENT','§4.5 printed1579','Double-tree active/inactive update with atomic tree switch','leo-generator/leo_ctrlplane.py::leo_ctrlplane_gen (line399ff); leo_tcam.py::layer_gen',entry='leo_ctrlplane_generator.py --transient',executable='Original command runs but says Disabled transient control plane support for now',missing='Complete generated update transaction/controller absent; no packet consistency test',evidence='evidence/leo/paper.txt; logs/leo/readme_ctrlplane.log; evidence/leo/source_symbols.json')
for mode in ['SRAM','TCAM']:
 row('F11-'+mode,'Fig11 / §7.1 printed1582','Tree-class feasible depth/stages/table entries vs Leo/Leo-NT/IIsy-NT/pFor-SwTree-NT using '+mode,'leo-generator/leo_dataplane_generator.py; leo/resource-model.py; iisy/resource-model.py; iisy/iisy.p4',config=mode+';10features; depth sweep; with/without transient',entry='GenerateP4 then compile underSDE9.11.1',missing='No compilation harness, stage/resource rawresults or fullpFor/SwTree implementation/configurations')
for dataset in ['CICIDS','NB15']:
 for mode in ['SRAM','TCAM']:
  row('F12-'+dataset+'-'+mode,'Fig12 / §7.2 printed1583',dataset+' best supported class macro-F1 for'+mode+' vs4baselines','dataset-simulation/dataset-processor-'+('cicids2017' if dataset=='CICIDS' else 'nb15')+'.py::main',data=dataset+' CSV absent',config='Original chosen tree/feature setting for all schemes not fully archived',entry='Sample training script',missing='Missing original data, all-scheme configurations, repeat seeds; NB15main defaults multi-class instead of binary')
row('F13','Fig13 / §7.1 printed1583','TCAM depth14–22 vs maximum leaves, Leo/Leo-NT','leo-generator/leo_tcam.py::layer_gen/final_table_gen; --leaf_limit/--depth/--transient',entry='P4 generation and SDEcompile sweep',missing='CLI mechanisms present; no leaf-sweep launcher, compilation logs or plotted data')
for mode in ['SRAM','TCAM']:
 row('F14-'+mode,'Fig14 / §7.3 printed1584','CICIDS/NB15 F1 vs262K–2.1M flows and144/112/56/24bits per flow with'+mode,'leo/feature-budget-finder.py; leo/leo-1m-flows.p4; dataset-simulation/*.py',config='Budget script hardcodes9features/57bits; full four flow budgets missing',missing='No complete discretization/ranking+budget sweep pipeline; oneP4example not all combinations')
row('F15','Fig15 / AppendixA.2 printed1587','Worst-case IIsy proof-tree family','iisy/resource-model.py::proposition_2_*',data='Not applicable',status='不适用',executable='Mathematical illustration; resource code is not proof verification',missing='No claim of independent formal proof validation')
row('F16','Fig16 / AppendixA.2 printed1588','Map different tree within same representative class at runtime','leo-generator/leo_ctrlplane.py::build_tree_from_file/assign_rule_to_layers/generate_subtree_rules',missing='No supplied illustrated inputtree or complete atomic updater; generated controlplane transient disabled')
for mode in ['SRAM','TCAM']:
 row('F17-'+mode,'Fig17 / AppendixA.3.1 printed1589','Maximum supported depth vsfeature count using'+mode,'leo-generator/leo_dataplane_generator.py --features; iisy/resource-model.py; leo/resource-model.py',missing='No perfeature/dep compile-sweep results or allbaseline configurations')
 row('F18-'+mode,'Fig18 / AppendixA.3.1 printed1589','IIsy CICIDS F1 vsdepth/feature tradeoff using'+mode,'dataset-simulation/dataset-processor-cicids2017.py::main',data='CICIDS CSV absent',config='Ten hardcoded experiments correspond to IIsy tradeoff sweep',entry='python dataset-processor-cicids2017.py',missing='Raw data, original seeds/output plot absent; script exportsboxplots but no full original plotted artifacts')
 row('F19-'+mode,'Fig19 / AppendixA.3.2 printed1590','CICIDS7-class F1 vsall4methods using'+mode,'dataset-simulation/dataset-processor-cicids2017.py::main/f1_score/export',data='CICIDS CSV absent',missing='PerclassF1 primitive present; full Leo/controlplane/baseline runs and configuration selection missing')
 row('F20-'+mode,'Fig20 / AppendixA.3.2 printed1590','NB15 benign/malicious perclassF1 vsall4methods using'+mode,'dataset-simulation/dataset-processor-nb15.py::preprocess_dataset/main',data='UNSW originalCSV absent',config='binary requiresbin_threshold=-1; mainhardcodes3000',missing='No default binary run, original split or allmethod settings')
 row('F21-'+mode,'Fig21 / AppendixA.3.2 printed1590','NB15 seven-class perclassF1 vsall4methods using'+mode,'dataset-simulation/dataset-processor-nb15.py::preprocess_dataset/main',data='UNSW originalCSV absent',config='main hardcodes merge threshold3000',missing='Data/seeds and exact fullmethod parameter sets absent; classmerge output cannot verify without data')
row('F22','Fig22 / AppendixA.3.2 printed1591','Zoom top6 CICIDS classF1 fromFig19b','dataset-simulation/dataset-processor-cicids2017.py::f1_score',missing='Metric primitive present; source for original six-class zoom chart and exact outputs absent')
row('F23','Fig23 / §7.4 / AppendixA.3.3 printed1591','Processinglatency data plane~500ns vscontrol plane~500x acrossdepth2–10','leo/leo.p4; leo/leo-1m-flows.p4',entry='Realtestbed tcpreplay/timestamp/CPUclassifier',status='缺失',missing='No full traffic replay/timestamp collection/controlplane inference service/evaluation script or raw latency records; hardware notavailable')
row('T02','Table2 / AppendixA.3.3 printed1591','Four selectedfeature configurations at1.04Mflows/56bits: CICIDS/NB15 × SRAM/TCAM','leo/leo-1m-flows.p4; leo/feature-budget-finder.py; READMEfeature extraction markers',missing='One fivefeature sample present; full fourconfigs, data discretization and selectedfeature manifests absent')
row('APP-PROOFS','AppendixA.1–A.2 printed1586–1588','IIsySRAM/TCAM lowerbound derivations and numerical models','iisy/resource-model.py; iisy/worst-case-feature-table.py',data='Analytic parameters',entry='python resource-model.py p1/p2; worst-case-feature-table.py',missing='Analytic code present, original full parameter outputs absent; not independent mathematical proof verification')
for cid,claim,evidence,code in [
 ('RUN-GEN','Original README SRAM P4text generator succeeded; no compilation','logs/leo/readme_dataplane_sram.json; logs/leo/readme_dataplane_sram.log','leo-generator/leo_dataplane_generator.py'),
 ('RUN-RESOURCE','Original TCAM analytic resource model printed511 entries forconfig3,3,3,3','logs/leo/readme_resource_model.json; logs/leo/readme_resource_model.log','leo/resource-model.py'),
 ('RUN-CTRL','Synthetic tree command generation exit0 and explicit disabled transient; no BFRTcalls executed','logs/leo/readme_ctrlplane.json; logs/leo/readme_ctrlplane.log','leo-generator/leo_ctrlplane_generator.py'),
 ('DIAG-ROUND','Original thresholdparser confirmed0.5→0 and2.5→2 routingcounterexamples','evidence/leo/threshold_counterexample.json; logs/leo/threshold_counterexample.log','leo-generator/leo_ctrlplane.py::parse_line/generate_rule_commands'),
 ('DIAG-DOMAIN','Python bit-vector diagnostic confirmsunsigned16full-domain/MSBcompare counterexample','evidence/leo/integer_domain_counterexamples.json; logs/leo/integer_domain_diagnostic.log','leo-generator/leo_templates.py; leo_ctrlplane.py')]:
 row(cid,'Audit execution,notpaperresult',claim,code,data='Synthetic or no dataset',config='Exactcommand inlogJSON',entry='See logJSON',executable='Executed with documentedscope',status='已验证',missing='Not a papermetric/networkdataset/P4/hardware validation',evidence=evidence)
with (P/'coverage_matrix.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

runs=[]
for rid,phase,kind,metrics,level,reason,limitations in [
 ('conda_create','environment','none',{},'R0','None','Environment installation alone is not algorithm validation'),
 ('pip_install','environment','none',{},'R0','None','READMEversions plus explicitNumPy/Pythonpatch compatibility choice'),
 ('readme_dataplane_sram','model_generation','none',{},'R1','None','Only P4 text; no compiler or packets'),
 ('readme_resource_model','smoke','analytic parameters',{'analytic_table_entries':511},'R1','None','Model calculation, not measured hardware resources'),
 ('p4_compiler_probe','P4_build','none',{},'R0','bf-p4c missing','Version probe only; no build'),
 ('readme_training_missing_data','data_processing','original data missing',{},'R0','CICIDS CSV FileNotFoundError','No original real-data model evaluation'),
 ('threshold_counterexample','source_diagnostic','synthetic',{'boundary_counterexamples':2,'stumps_checked':3},'R1','Semantic preservation fails for original generatedpredicate','Diagnostic exit0 meanscounterexampleconfirmed, not classifier replication'),
 ('readme_ctrlplane','model_generation','synthetic',{},'R1','Transient controlplane support explicitly disabled','No generated BFRTcalls executed'),
 ('integer_domain_diagnostic','source_diagnostic','synthetic bitvectors',{'unsigned_domain_counterexamples':3},'R1','MSB subtraction fails over full unsigned16-bit domain','Not actual P4 simulation; realdata incidenceUnknown')]:
 runs.append(dict(run_id=rid,phase=phase,input_kind=kind,metrics=metrics,level=level,paper_comparable=False,failure_reason=reason,limitations=limitations,evidence_files=['logs/leo/'+rid+'.json','logs/leo/'+rid+'.log']))
(P/'execution_summary.json').write_text(json.dumps({'paper_id':'leo','round':'autonomous_20261109','runs':runs},ensure_ascii=False,indent=2)+'\n')
artifacts=[]
for p in sorted((P/'runtime-artifacts').rglob('*')):
 if p.is_file():artifacts.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(E/'runtime_artifact_manifest.json').write_text(json.dumps(artifacts,indent=2)+'\n')
print('Leo matrix rows:',len(rows))
