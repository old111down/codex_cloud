"""Materialize manually reviewed coverage inventory and execution provenance."""
import ast
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'papers/pegasus';E=ROOT/'evidence/pegasus';SRC=ROOT/'upstream/pegasus'
record=next(r for r in json.loads((ROOT/'catalog/round2/network_screening.json').read_text()) if r['id']=='pegasus')
meta=dict(record)
meta.update(paper_id='pegasus',source_record='papers/pegasus/metadata.json',reproduction_level='R1',
    gpu_dependency='CPU torch2.4.1+cpu replacement-weight MLP/synthetic quickdemo tested atR1; fullGPUtraining and GPUperformance notexecuted, minimumGPUresources Unknown',
    data_public='Publicdataset links and currentreplacementweights verified inartifact; originalsoftwareCSV/JSON notacquired (PeerRushDriveHEAD returnedHTML). CurrentMLPcheckpoint CPU smoke passed; originalpaperweights explicitlylost; originalsplit/data licenses Unknown.',
    audited_version='arXiv:2506.05779v1 2025-06-06,15pages; author SIGCOMM2025 PDF byte-identical; finalACM inaccessible',
    coverage_scope='Publicversion all Methods3–5,Implementation6,Evaluation7.1–7.5,Discussion8,Conclusion9;Fig1–9/Table1–6; noAppendix',
    main_tasks_implementation_complete='Six main model families have code; full claimed experiments/original weights/data/performance protocols are incomplete or unverified',
    execution_status='R1 CPU strict current-weight MLP/synthetic quickdemo/P4 textgenerator; originalCNNL realtest blocked by missingdata',
    paper_metrics_reproduced=False,
    component_levels={'software_CPU_synthetic':'R1','P4_text_generation':'R1','real_network_data':'R0','P4_compile':'R0','BMv2':'R0','hardware':'R0'},
    upstream_git_status=subprocess.check_output(['git','-C',str(SRC),'status','--porcelain'],text=True).strip(),
    critical_findings=['Original paper weights reported lost; current weights retrained','Conflicting software/hardware equivalence statements','Publicpaper seven-class text versus six-class implementation','Overlapping-window validation split mechanism','README setup command/workingdirectory errors'],
    audit_protocol_deviation='Initial CNNL command deserialized checkpoint before file-specific pickle review; exact sequence retained; subsequentMLP reviewed beforeload',
    unknowns=['FinalACM-only changes Unknown','All originaldata Accuracy/PR/RC/F1/AUC/performance Unknown','Originalweights irretrievable from publishedartifact according toauthor; replacement equivalence Unknown','Actualtrain/test leakage Unknown; validation-grain diagnostic only','BMv2andTofino notexecuted'],
    retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
(P/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')

manifest=[];symbols=[];parse_errors=[]
for p in sorted(SRC.rglob('*')):
    if '.git' in p.parts or not p.is_file():continue
    rel=str(p.relative_to(SRC))
    manifest.append({'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    if p.suffix=='.py':
        try: tree=ast.parse(p.read_text())
        except (UnicodeError,SyntaxError) as err:
            parse_errors.append({'path':rel,'error':str(err)});continue
        for n in ast.walk(tree):
            if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
                symbols.append({'path':rel,'name':n.name,'start':n.lineno,'end':n.end_lineno})
(E/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(E/'source_symbols.json').write_text(json.dumps({'symbols':symbols,'parse_errors':parse_errors},indent=2)+'\n')
inventory=[]
for page,t in enumerate((E/'paper.txt').read_text().split('\f'),1):
    for m in re.finditer(r'\b(Figure|Table)\s+(\d+):\s*([^\n]*)',t):
        inventory.append({'kind':m[1],'number':int(m[2]),'pdf_page':page,'caption_start':m[3]})
(E/'paper_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')

rows=[]
def row(cid,section,claim,code,data='OriginalCSV/JSON notacquired',config='Originalmanifest/split/weights notfullyavailable',entry='Unknown',executable='Notrun onoriginaldata/hardware; paperequivalenceUnknown',status='部分覆盖',missing='Originalweights lost, originaldata/protocol/hardware equivalence unverified',evidence=''):
    rows.append(dict(claim_id=cid,paper_section=section,claim=claim,code_paths=code,data_paths=data,config=config,entrypoint=entry,executable=executable,status=status,missing=missing,evidence=evidence or 'evidence/pegasus/paper.txt; evidence/pegasus/source_manifest.json; evidence/pegasus/source_symbols.json'))
row('T1','Table1 / §1 p2','Design-contribution matrix foraccuracy/scalability/generality','software/model/; hardware/normal_version/',data='Notapplicable',status='不适用',executable='Qualitative table; supportingclaims auditedseparately',missing='Notanexecutable experiment')
row('T2','Table2 / §1 p2','Derivedaccuracy gains17.2/22.8/17.9%,modelsize248x/237x,input29x/212x','software/model/; Table5-relatedquickdemo',missing='No originalbaseline weights/configs and exactpaperresults comparison; modelsizedefinitions needverification')
row('T3','Table3 / §4.1 p4','Partition/Map/SumReduce primitives','hardware/p4_syntax/pegasus_parser.py; codegen.py; software/model/*::MM_final',data='Conceptualoperators',missing='Primitive definitions present; no fulloperator-level hardwareequivalence suite')
row('T4','Table4 / §5 p7','Emb/FC/Conv/Act/Norm/Pool/Rec operatorstohardwareprimitives','software/model/; software/util/reset.py; hardware/normal_version/',data='Operatorinputs',missing='Six families present; no separate fullsuite validating everylistedoperator/everyhardwareconfiguration')
row('F1','Fig1 / §3.2 p4','Architecture:DLlayers→operators→primitives→MAT','software/convert/; hardware/p4_syntax/; hardware/normal_version/',missing='Cross-layer equivalence and completeoriginaldatasets notvalidated')
row('F2','Fig2 / §4.2 p4','Fuzzyindex lookup illustration','software/util/quanti.py::model_quanti/get_ans; software/model/*::MM_final',data='Illustrative2-Dinput',missing='Functions exist; exactillustration test notarchived')
row('F3','Fig3 / §4.2 p5','GreedySSEsplits andleafcentroids','software/util/quanti.py::_cumsse_cols/optimal_split_val/get_sub_bucket/get_ans',data='Clusteringtrainactivations absent',missing='Algorithmimplementation present; originallearnedclusters/seedoutputs absent')
row('F4','Fig4 / §4.3 p5','Partition/Map/SumReduce MATfusion','hardware/p4_syntax/templates/; software/util/reset.py',data='Operatorinputs',missing='P4templates present; no fullP4semantic comparison')
row('F5','Fig5 / §4.3 p6','Basiclinearreordering/fusion; advancednonlinear/removal/SumReduce reduction','software/util/reset.py; software/model/cnnmmodel.py; bigcnnmodel.py; splitAutoencoder.py',missing='Implementations present; no standaloneablation protocol/alloriginalintermediates')
row('F6','Fig6 / §6.2 p8','PegasusSyntax translation forMLP/CNN','hardware/p4_syntax/pegasus_parser.py::parse; codegen.py::gen_p4',data='mlp16.p4gexample',config='Exactrawentry logged',entry='python codegen.py mlp16.p4g output.p4',executable='MLPtextgenerator executed successfully',missing='P4text only; no compiler/packet/hardwaretest',evidence='evidence/pegasus/paper.txt; logs/pegasus/readme_p4_syntax.json; logs/pegasus/readme_p4_syntax.log')
row('METHOD-QUANT','§4.4 p6–7','Backprop centroid/threshold refinement andadaptivefixed-point quantization','software/train_net/autoquanti.py::quanti_sequence; software/util/quanti.py; software/util/reset.py; software/convert/',missing='Training/conversion code exists; exactoriginalweights/quantizationparameters and errorbounds unverified')
row('DATA-SPLIT','§7.1 p9','75/10/15 flow-leveltrain/validation/test; packet-levelmacro-F1 metric','software/util/data_loader.py::FlowDataset; train_net/runmodel.py::build_data_loader',entry='Originaltrainingfunctions',missing='Externalsplitfiles notacquired; function splitsvalidation afterwindowexpansion, seededflowgrouping absent',evidence='evidence/pegasus/paper.txt; evidence/pegasus/split_grain_diagnostic.json; logs/pegasus/split_grain_diagnostic.log')
row('LABEL-ISCX','§7.1 p9','Publicpaper sayssevenISCXclassesbut enumeratessix; sourceuses6','software/util/data_loader.py::ISCXVPN_rule/FlowDataset; bigcnn_data_loader.py; quickdemo/*.py',data='ISCXinputJSON absent',missing='Code excludesbrowsing andshiftsremaining6labels; seventhclass/precisefinalpaperdefinition Unknown')
models={'Leo':('No completebaselineimplementation',''),'N3IC':('No completebaselineimplementation',''),'MLP-B':('software/model/mlpmodel.py','mlptest'),'BoS':('No completebaselineimplementation',''),'RNN-B':('software/model/rnnmodel.py','rnntest'),'CNN-B':('software/model/cnnmodel.py','cnnBtest'),'CNN-M':('software/model/cnnmmodel.py','cnnMtest'),'CNN-L':('software/model/bigcnnmodel.py','cnnLtest')}
f1s={'Leo':[.8728,.7848,.7475],'N3IC':[.8241,.7745,.6388],'MLP-B':[.8823,.8581,.7574],'BoS':[.8678,.8276,.6907],'RNN-B':[.9090,.8707,.7617],'CNN-B':[.9057,.8659,.7520],'CNN-M':[.9207,.8829,.7780],'CNN-L':[.9966,.9380,.9872]}
for j,dataset in enumerate(['PeerRush','CICIOT','ISCXVPN']):
    for model,(code,entry) in models.items():
        row('T5-'+dataset+'-'+model,'Table5 / §7.2–7.3 p10',dataset+'/'+model+' PR/RC/macro-F1; paperF1='+str(f1s[model][j]),code+(('; software/quickdemo/'+entry+'.py') if entry else ''),data=dataset+' originaltestCSV/JSON absent',entry=('python -m quickdemo.'+entry) if entry else 'Absent completebaselineentry',status='部分覆盖' if entry else '缺失',missing='Originalweights lost; replacementweights/data/metricaveraging notpaper-equivalent' if entry else 'Baseline training/weights/exacthardwareandparameter setup notprovided')
for model,dir_ in [('Leo',None),('BoS',None),('MLP-B','MLP_32'),('RNN-B','RNN'),('CNN-B','CNN-B'),('CNN-M','CNN-M'),('CNN-L','CNN-L'),('AutoEncoder','AutoEncoder')]:
    row('T6-'+model,'Table6 / §7.4 p10–11',model+' statefulbits/flow,SRAM,TCAM,actiondatabusutilization','hardware/normal_version/'+dir_ if dir_ else 'No completebaselineP4 inartifact',data='Originalhardwarecompiler/resourceoutputs absent',entry='OriginalTofino2 build/resourceevaluation',status='部分覆盖' if dir_ else '缺失',missing='No actualSDEcompile or comparablephysicalresourcecapture; sourceP4isnotevidenceofreportedresourcepercentages')
for dataset in ['PeerRush','CICIOT','ISCXVPN']:
    for bits in [28,44,72]:
        row('F7-'+dataset+'-'+str(bits),'Fig7 / §7.3 p10–11; repoFigure8',dataset+' CNN-Lmacro-F1 andstateusagefor'+str(bits)+'bits/flow','software/model/bigcnnmodel.py; hardware/running_version/; figure_generation/code/Figure8.py',data='Figure8.py hardcodedarchivevalues; originalconfigurationtestdata absent',entry='Modelretraining/modifiedquantization/P4evaluation; plotonlyentrypresent',missing='Archivedfigure constants do not rerun width-specificmodels/hardware; exactall3configuration manifests absent')
for dataset in ['PeerRush','CICIOT','ISCXVPN']:
    for attack in ['Htbot','Flood','Cridex','Virut','Neris','Geodo']:
        row('F8-'+dataset+'-'+attack,'Fig8 / §7.4 p10–11; repoFigure9',dataset+' normaltrafficwith'+attack+' attack ROC/AUC at1:4attack:benign mixture','software/quickdemo/autoencodertest.py::run/test; model/splitAutoencoder.py; figure_generation/code/Figure9.py',data='ArchivedROCJSON available; originalnormal/maliciousdatasets absent',entry='python -m quickdemo.autoencodertest',missing='Replacementweights/currentexternaldata notoriginal; freshAUCnotrun; archivedROCplot notnewexperiment')
for dataset in ['PeerRush','CICIOT','ISCXVPN']:
    row('F9-ACC-'+dataset,'Fig9a–c / §7.5 p12; repoFigure10a_b_c',dataset+' MLP/RNN/CNNB/M/LhardwarevsCPU/GPUmacro-F1','software/model/; quickdemo/; figure_generation/code/Figure10a_b_c.py',data='Plotarrayshardcoded; originalnewpredictions absent',missing='No currentpaper-equivalentweights/testdata/hardware; fullprecisionbaseline alignment notverified')
row('F9-THROUGHPUT','Fig9d / §7.5 p12; repoFigure10d','5modelsprogrammableswitchvsCPU/fourTeslaV100throughput;3800x/600xgain','figure_generation/code/Figure10d.py',data='Hardcodedarchivearrays',entry='Onlyplotterpresent; livebenchmarkentryabsent',status='缺失',missing='No realCPU/GPU/multithreaded/fourGPU/timingprotocolororiginalhardware throughputmeasurement; replotnotreplication')
row('WEIGHTS-PROVENANCE','Artifactdocumentation; affectsallTable5/6/Fig7–9','Originalpaper.pthlost,currentweightsretrained; software/hardwareequivalence statements conflict','README.md; software/README.md; figure_generation/README.md',data='Currentweights present; originalweightsnotavailable',entry='Currentquickdemo only',status='缺失',missing='Exactpapercheckpoint provenance cannotberecovered fromthisartifact; claimed smallimpactnotverified',evidence='evidence/round2/network_search/pegasus/README.pinned.md; evidence/round2/network_search/pegasus/software__README.md; evidence/pegasus/paper.txt')
row('BMV2-SCOPE','ArtifactBMv2documentation','BMv2releaseMLP-Bonly,generatedpacketsbypassfeatureextraction','bmv2/readme.md; bmv2/p4_*/; bmv2/send_recieve/',data='GeneratedPCAPsprovided; notrawsoftwaretestdataset',entry='SystemVM/veth/P4runtime instructions',missing='Notexecuted; noall6models orrealfeaturepipeline; noadministratorinstallersrun')
row('APPENDIX','Completepublic15pageversion','NoAppendixpresent; finalACM-onlymaterialUnknown','Notapplicable',data='Notapplicable',status='不适用',executable='Allavailablepublicpagesread',missing='FinalACM403; authorPDFequalsarXivv1',evidence='evidence/pegasus/retrieval_log.json; evidence/pegasus/paper_inventory.json')
for cid,claim,evidence in [
 ('RUN-MLP','StrictloadedreviewedreplacementMLPstate_dictwithsynthetic9x10inputandfinite9x3output','evidence/pegasus/model_smoke_metrics.json; logs/pegasus/model_smoke.log'),
 ('RUN-ORIGINAL-MLP','UnmodifiedMLPquickdemo onsyntheticCSVexit0; syntheticF1=.3485,notnetworkmetric','logs/pegasus/unmodified_mlp_synthetic.json; logs/pegasus/unmodified_mlp_synthetic.log'),
 ('RUN-P4GEN','OriginalP4GMLP16textgenerationexit0; notcompile','logs/pegasus/readme_p4_syntax.json; logs/pegasus/readme_p4_syntax.log'),
 ('RUN-SPLIT','One40packetsyntheticflow becomes33windows; splitfunctionallowsflow/packetsharingintrian/validation','evidence/pegasus/split_grain_diagnostic.json; logs/pegasus/split_grain_diagnostic.log')]:
    row(cid,'Auditexecution,notpaperresult',claim,'Seeactualharness/originalentryinlogs',data='Explicitlysynthetic',config='BoundedCPU; nooriginaldata',entry='LogJSONargv',executable='Executedwithdocumentedlimits',status='已验证',missing='No paperresult/networkdataset/hardwarevalidation',evidence=evidence)
with (P/'coverage_matrix.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

runs=[]
for rid,phase,kind,metrics,level,reason,limit in [
 ('conda_create','environment','none',{},'R0','None','CorrectedREADMEcreate-n typo and isolatedprefix'),
 ('torch_cpu_install','environment','none',{},'R0','None','ExplicitofficialCPUwheel,READMEtorchunpinned'),
 ('readme_dependencies','environment','none',{},'R0','None','Originalrequirementsfileinsoftwaredirectory; notliteralrootrecipe'),
 ('readme_cpu_cnnl','original_command','realtestfilemissing',{},'R0','MissingPeerRushtestJSON','Checkpointdeserializedbeforemissingdatafailure; file-specificstaticreviewafterrun recorded'),
 ('model_smoke','smoke','synthetic',{'output_rows':9,'output_classes':3,'strict_state_dict_load':True},'R1','None','Officialreplacementweights,notoriginalpaper; no realdata metric'),
 ('unmodified_mlp_synthetic','smoke','synthetic',{'synthetic_macro_f1_printed':.3485},'R1','None','Notnetworkaccuracy; arbitrarysyntheticlabels'),
 ('readme_p4_syntax','P4_model_generation','providedmodeldescription',{},'R1','None','P4textonly; no compiler/packet/hardwaretest'),
 ('split_grain_diagnostic','data_processing_diagnostic','synthetic',{'single_flow_windows':33,'input_flows':1,'val_ratio':.2},'R1','Train/validationflowandpacketsharingmechanismconfirmed','Defaultvalratio=.1; actualexternaltestoverlap/impactUnknown'),
 ('readme_literal_conda_typo','original_setup_command','none',{},'R0','conda create-n invalidcommand','Post-hoc literalrecipeaudit; noextraenvironmentcreated'),
 ('readme_literal_root_requirements','original_setup_command','none',{},'R0','Rootrequirements.txtmissing','Actualworkingdirectorycorrectionrequired'),
 ('retrieve_evidence','evidence_retrieval','publicauthorPDF+checkpointmetadata',{},'R0','ACM403; DriveHEADonlyHTML','No actualdatasetdownload; staticpicklechecknotformalsafetyproof')]:
    runs.append(dict(run_id=rid,phase=phase,input_kind=kind,metrics=metrics,level=level,paper_comparable=False,failure_reason=reason,limitations=limit,evidence_files=['logs/pegasus/'+rid+'.json','logs/pegasus/'+rid+'.log']))
(P/'execution_summary.json').write_text(json.dumps({'paper_id':'pegasus','round':'autonomous_20261109','runs':runs},ensure_ascii=False,indent=2)+'\n')
artifacts=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((P/'runtime-artifacts').rglob('*')) if p.is_file()]
(E/'runtime_artifact_manifest.json').write_text(json.dumps(artifacts,indent=2)+'\n')
print('Pegasuscoverage rows:',len(rows),'sourceblobs:',len(manifest),'syntaxparseerrors:',len(parse_errors))
