#-*- coding:utf-8 -*-
import tensorflow as tf
from tensorflow.contrib import rnn
from common.layers import get_initializer
from encoder import EncoderBase
import pdb
import copy

class RCNN(EncoderBase):
    def __init__(self, **kwargs):
        super(RCNN, self).__init__(**kwargs)
        self.rnn_type = "bi_lstm"
        self.embedding_size = kwargs['embedding_size']
        self.num_hidden = 256
        self.num_layers = 2
        self.fc_num_hidden = 256
        self.placeholder = {}

    def __call__(self, embed, name = 'encoder', features = None,
                 reuse = tf.AUTO_REUSE, **kwargs):
        length_name = name + "_length" 
        self.placeholder[length_name] = tf.placeholder(dtype=tf.int32, 
                                                    shape=[None], 
                                                    name = length_name)
        if features != None:
            self.placeholder[length_name] = features[length_name]

        with tf.variable_scope("birnn", reuse = reuse):
            fw_cells = [tf.contrib.rnn.LSTMCell(self.num_hidden,state_is_tuple=True)\
                                    for n in range(self.num_layers)]
            bw_cells = [tf.contrib.rnn.LSTMCell(self.num_hidden,state_is_tuple=True)\
                                    for n in range(self.num_layers)]
            stack_fw = tf.contrib.rnn.MultiRNNCell(fw_cells)
            stack_bw = tf.contrib.rnn.MultiRNNCell(bw_cells)
            (output_fw,output_bw), _ = tf.nn.bidirectional_dynamic_rnn(\
                            stack_fw,
                            stack_bw,
                            embed,
                            sequence_length=self.placeholder[length_name], 
                            dtype=tf.float32)
        with tf.name_scope("context"):
            shape = [tf.shape(output_fw)[0], 1, tf.shape(output_fw)[2]]
            c_left = tf.concat([tf.zeros(shape), output_fw[:, :-1]], axis=1, name="context_left")
            c_right = tf.concat([output_bw[:, 1:], tf.zeros(shape)], axis=1, name="context_right")

        with tf.variable_scope("word-representation", reuse = reuse):
            x = tf.concat([c_left, embed, c_right], axis=2, name="x")
            embedding_size = 2*self.num_hidden + self.embedding_size

            #W2 = tf.Variable(tf.random_uniform([embedding_size, self.num_hidden], -1.0, 1.0), name="W2")
            #b2 = tf.Variable(tf.constant(0.1, shape=[self.num_hidden]), name="b2")
            #y2 = tf.tanh(tf.einsum('aij,jk->aik', x, W2) + b2)
            y2 = tf.layers.dense(x, self.fc_num_hidden, activation=tf.nn.tanh)
            y3 = tf.reduce_max(y2, axis=1)

            logits = tf.layers.dense(y3, self.num_output, activation=None)
            return logits

    def get_features(self, name = 'encoder'):
        features = {}
        length_name = name + "_length" 
        features[length_name] = tf.placeholder(dtype=tf.int32, 
                                                    shape=[None], 
                                                    name = length_name)
        return features
