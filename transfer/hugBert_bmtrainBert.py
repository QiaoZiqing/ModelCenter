# coding=utf-8
# Copyright 2020 The OpenBMB team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import torch
import json

from collections import OrderedDict
from transformers import BertModel, BertConfig, BertTokenizer, BertLMHeadModel
from model_center.model.config import BertConfig as myConfig

base_path = '/home/hx/ModelCenter'

def convert_tokenizer(version : str):
    tokenizer : BertTokenizer = BertTokenizer.from_pretrained(version)
    vocab_size = tokenizer.vocab_size
    s = [''] * vocab_size
    for word in tokenizer.vocab:
        id = tokenizer.vocab[word]
        s[id] = word
    fo = open(os.path.join(base_path, 'configs', 'bert', version, 'vocab.txt'), 'w')
    for word in s:
        print(word, file=fo)
    fo.close()

def convert_model(version : str):
    config : BertConfig = BertConfig.from_pretrained(version)
    default_config = myConfig()
    config_json = {}
    config_json['dim_head'] = int(config.hidden_size / config.num_attention_heads)
    if default_config.dim_model != config.hidden_size:
        config_json['dim_model'] = config.hidden_size
    if default_config.dim_ff != config.intermediate_size:
        config_json['dim_ff'] = config.intermediate_size
    if default_config.num_heads != config.num_attention_heads:
        config_json['num_heads'] = config.num_attention_heads
    if default_config.num_layers != config.num_hidden_layers:
        config_json['num_layers'] = config.num_hidden_layers
    if default_config.vocab_size != config.vocab_size:
        config_json['vocab_size'] = config.vocab_size

    try:
        os.mkdir(os.path.join(base_path, 'configs', 'bert', version))
    except:
        pass
    print(json.dumps(config_json), file = open(os.path.join(base_path, 'configs', 'bert', version, 'config.json'), 'w'))

    num_layers = config.num_hidden_layers
    bert = BertModel.from_pretrained(version)
    dict = bert.state_dict()
    new_dict = OrderedDict()

    new_dict['input_embedding.weight'] = dict['embeddings.word_embeddings.weight']
    new_dict['position_embedding.weight'] = dict['embeddings.position_embeddings.weight']
    new_dict['token_type_embedding.weight'] = dict['embeddings.token_type_embeddings.weight']
    for i in range(num_layers):
        new_dict['encoder.layers.' + str(i) + '.self_att.layernorm_before_attention.weight'] = (dict['embeddings.LayerNorm.weight'] if i == 0 
                                                                       else dict['encoder.layer.' + str(i - 1) + '.output.LayerNorm.weight'])
        new_dict['encoder.layers.' + str(i) + '.self_att.layernorm_before_attention.bias'] = (dict['embeddings.LayerNorm.bias']     if i == 0
                                                                       else dict['encoder.layer.' + str(i - 1) + '.output.LayerNorm.bias'])
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.project_q.weight'] = dict['encoder.layer.' + str(i) + '.attention.self.query.weight']
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.project_q.bias'] = dict['encoder.layer.' + str(i) + '.attention.self.query.bias']
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.project_k.weight'] = dict['encoder.layer.' + str(i) + '.attention.self.key.weight']
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.project_k.bias'] = dict['encoder.layer.' + str(i) + '.attention.self.key.bias']
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.project_v.weight'] = dict['encoder.layer.' + str(i) + '.attention.self.value.weight']
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.project_v.bias'] = dict['encoder.layer.' + str(i) + '.attention.self.value.bias']
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.attention_out.weight'] = dict['encoder.layer.' + str(i) + '.attention.output.dense.weight']
        new_dict['encoder.layers.' + str(i) + '.self_att.self_attention.attention_out.bias'] = dict['encoder.layer.' + str(i) + '.attention.output.dense.bias']
        new_dict['encoder.layers.' + str(i) + '.ffn.layernorm_before_ffn.weight'] = dict['encoder.layer.' + str(i) + '.attention.output.LayerNorm.weight']
        new_dict['encoder.layers.' + str(i) + '.ffn.layernorm_before_ffn.bias'] = dict['encoder.layer.' + str(i) + '.attention.output.LayerNorm.bias']
        new_dict['encoder.layers.' + str(i) + '.ffn.ffn.w_in.w.weight'] = dict['encoder.layer.' + str(i) + '.intermediate.dense.weight']
        new_dict['encoder.layers.' + str(i) + '.ffn.ffn.w_in.w.bias'] = dict['encoder.layer.' + str(i) + '.intermediate.dense.bias']
        new_dict['encoder.layers.' + str(i) + '.ffn.ffn.w_out.weight'] = dict['encoder.layer.' + str(i) + '.output.dense.weight']
        new_dict['encoder.layers.' + str(i) + '.ffn.ffn.w_out.bias'] = dict['encoder.layer.' + str(i) + '.output.dense.bias']

    new_dict['encoder.output_layernorm.weight'] = dict['encoder.layer.' + str(num_layers - 1) + '.output.LayerNorm.weight']
    new_dict['encoder.output_layernorm.bias'] = dict['encoder.layer.' + str(num_layers - 1) + '.output.LayerNorm.bias']
    new_dict['pooler.dense.weight'] = dict['pooler.dense.weight']
    new_dict['pooler.dense.bias'] = dict['pooler.dense.bias']

    lmhead_bert = BertLMHeadModel.from_pretrained(version)
    dict = lmhead_bert.state_dict()

    new_dict['lm_head.dense.weight'] = dict['cls.predictions.transform.dense.weight']
    new_dict['lm_head.dense.bias'] = dict['cls.predictions.transform.dense.bias']
    new_dict['lm_head.layer_norm.weight'] = dict['cls.predictions.transform.LayerNorm.weight']
    new_dict['lm_head.layer_norm.bias'] = dict['cls.predictions.transform.LayerNorm.bias']
    new_dict['lm_head.decoder.weight'] = dict['cls.predictions.decoder.weight']
    new_dict['lm_head.decoder.bias'] = dict['cls.predictions.decoder.bias']

    torch.save(new_dict, os.path.join(base_path, 'configs', 'bert', version, 'pytorch_model.pt'))

if __name__ == "__main__":
    version_list = ['bert-base-uncased', 'bert-large-uncased', 'bert-base-cased', 'bert-large-cased', 'bert-base-multilingual-cased', 'bert-base-chinese']
    for version in version_list:
        #convert_tokenizer(version)
        convert_model(version)
