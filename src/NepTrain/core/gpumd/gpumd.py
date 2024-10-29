#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# @Time    : 2024/10/29 15:06
# @Author  : 兵
# @email    : 1747193328@qq.com

import math
import os.path
from xmlrpc.client import Fault

import numpy as np
from ase import Atoms

from ase.io import write as ase_write
from ase.io import read as ase_read
from .io import RunInput
from NepTrain import utils, Config,module_path
from .select import select_structures
atoms_index=0

@utils.iter_path_to_atoms(["*.vasp","*.xyz"],show_progress=False)
def calculate_vasp(atoms:Atoms,argparse):
    global atoms_index
    atoms_index+=1
    trainxyz=ase_read(argparse.train_xyz_path,":",do_not_split_by_at_sign=True)
    new_atoms=[]
    max_selected=argparse.max_selected
    min_distance=argparse.min_distance
    for temperature in argparse.temperature:

        run = RunInput(argparse.nep_txt_path)
        run.read_run(argparse.run_in_path)
        run.set_time_temp(argparse.time,temperature)
        directory=os.path.join(argparse.directory,f"{atoms_index}-{atoms.symbols}@{temperature}k-{argparse.time}ps")

        print(f"GPUMD采样中，温度：{temperature}k。时间：{argparse.time*run.time_step}ps " )

        run.calculate(atoms,directory)

        selected = select_structures(trainxyz + new_atoms, os.path.join(directory,"dump.xyz"), max_selected=max_selected,
                                     min_distance=min_distance)
        print(f"得到{len(selected)}个结构" )

        for i, atom in enumerate(selected):
            atom.info["Config_type"] = f"{atom.symbols}-epoch-{argparse.time}ps-{temperature}k-{i + 1}"
        new_atoms.extend(selected)

        ase_write(os.path.join(directory,"selected.xyz"),selected)
    print(f"结构：{atoms.symbols}，本次主动学习共得到{len(new_atoms)}个结构" )
    return new_atoms
def run_gpumd(argparse):

    result = calculate_vasp(argparse.model_path,argparse)
    path=os.path.dirname(argparse.out_file_path)
    if path and  not os.path.exists(path):
        os.makedirs(path)
    count=0
    for learn_result in result:
        ase_write(argparse.out_file_path, learn_result, format="extxyz", append=True)
        count+=len(learn_result)
    print(f"本次主动学习共添加{count}个结构，以追加模式写入到：{argparse.out_file_path}！")

    print("所有计算均顺利完成！")

if __name__ == '__main__':
    calculate_vasp("./")

