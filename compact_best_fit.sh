#!/bin/bash

#./results/report/50_GEN_RUNS_BIC
#./compact_best_fit.sh ./results/report/50_GEN_RUNS_BIC 50_GEN_RUNS_BIC
#./compact_best_fit.sh ./results/report/50_GEN_RUNS 50_GEN_RUNS

rm -rf tmp_compactor
rm ./docs/code/$2.json

for RUN in 1 2 3 4 5 6 7 8 9 10
do
    mkdir -p tmp_compactor
    mkdir -p tmp_compactor/run_$RUN
    unzip -j $1/run_$RUN.zip "snapshots/50_gen/29.cc" -d "./tmp_compactor/run_$RUN/" -y
    source venv/bin/activate
    python compactor.py "./tmp_compactor/run_$RUN" 29
    cd tmp_compactor/run_$RUN
    clang-format -i -style=WebKit *_compacted.cc
    cd ../../
    python compactor_doc.py "./tmp_compactor/run_$RUN" 29 "$2.json" "run_$RUN"
done

zip -r $1/best_compacted.zip tmp_compactor

