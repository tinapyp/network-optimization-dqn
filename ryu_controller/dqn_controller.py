import numpy as np
import logging
import tensorflow as tf
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp
import time
import pickle
import matplotlib.pyplot as plt
import networkx as nx
from .model.model_versioning import ModelVersioning


class DQNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DQNController, self).__init__(*args, **kwargs)
        self.model_versioning = ModelVersioning()
        self.model = self.load_best_model()
        self.epsilon = 0.1  # Exploration rate
        self.state_size = 10
        self.action_size = 3
        self.network_latency = {}
        self.network_throughput = {}
        self.best_topology = None

    def build_model(self):
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(24, input_dim=self.state_size, activation="relu"),
                tf.keras.layers.Dense(24, activation="relu"),
                tf.keras.layers.Dense(self.action_size, activation="linear"),
            ]
        )
        model.compile(optimizer="adam", loss="mse")
        return model

    def load_best_model(self):
        try:
            return self.model_versioning.load_model()
        except Exception as e:
            logging.error(f"Error loading best model: {str(e)}")
            return self.build_model()

    def save_best_model(self, model):
        self.model_versioning.save_model(model)

    def load_best_topology(self):
        try:
            return self.model_versioning.load_topology()
        except Exception as e:
            logging.error(f"Error loading best topology: {str(e)}")
            return None

    def save_best_topology(self, topology):
        self.model_versioning.save_topology(topology)
        self.visualize_topology(topology)

    def visualize_topology(self, topology):
        G = nx.Graph()
        for node in topology["nodes"]:
            G.add_node(node["id"])
        for edge in topology["edges"]:
            G.add_edge(edge["source"], edge["target"])

        pos = nx.spring_layout(G)
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_color="lightblue",
            node_size=500,
            font_size=10,
            font_weight="bold",
            edge_color="gray",
        )
        plt.title("Best Topology Visualization")
        plt.savefig("best_topology.png")
        plt.show()

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match["in_port"]
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        state = self.get_network_state(datapath, in_port, pkt)
        action = self.select_action(state)
        self.execute_action(action, datapath, in_port, pkt)

        reward = self.calculate_reward(state, action)
        self.train_model(state, action, reward)

    def get_network_state(self, datapath, in_port, pkt):
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        udp_pkt = pkt.get_protocol(udp.udp)

        src_ip = ipv4_pkt.src if ipv4_pkt else None
        dst_ip = ipv4_pkt.dst if ipv4_pkt else None
        protocol = "TCP" if tcp_pkt else "UDP" if udp_pkt else "OTHER"

        state = np.zeros(self.state_size)
        state[0] = hash(src_ip) % 10000 if src_ip else 0
        state[1] = hash(dst_ip) % 10000 if dst_ip else 0
        state[2] = 1 if protocol == "TCP" else 0
        state[3] = 1 if protocol == "UDP" else 0
        state[4] = in_port
        state[5] = time.time() % 10000
        state[6] = len(pkt.data)
        state[7] = self.network_latency.get((src_ip, dst_ip), 1.0)
        state[8] = self.network_throughput.get((src_ip, dst_ip), 10.0)

        logging.info(f"State extracted: {state}")
        return state

    def select_action(self, state):
        if np.random.rand() <= self.epsilon:
            return np.random.choice(self.action_size)
        q_values = self.model.predict(state.reshape(1, -1))
        return np.argmax(q_values[0])

    def execute_action(self, action, datapath, in_port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if action == 0:
            logging.info("Action 0: Drop packet.")
            match = parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, [])
        elif action == 1:
            logging.info("Action 1: Forward packet normally.")
            out_port = ofproto.OFPP_FLOOD
            actions = [parser.OFPActionOutput(out_port)]
            self.packet_out(datapath, in_port, actions, pkt)
        elif action == 2:
            logging.info("Action 2: Route packet through alternate path.")
            out_port = self.find_alternate_path(datapath, in_port, pkt)
            actions = [parser.OFPActionOutput(out_port)]
            self.packet_out(datapath, in_port, actions, pkt)

    def find_alternate_path(self, datapath, in_port, pkt):
        return (in_port + 1) % len(datapath.ports)

    def packet_out(self, datapath, in_port, actions, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        data = pkt.data
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath, priority=priority, match=match, instructions=inst
            )
        datapath.send_msg(mod)

    def calculate_reward(self, state, action):
        src_ip = state[0]
        dst_ip = state[1]
        latency = self.network_latency.get((src_ip, dst_ip), 1.0)
        throughput = self.network_throughput.get((src_ip, dst_ip), 10.0)
        return -latency + throughput

    def train_model(self, state, action, reward):
        target = reward
        target_f = self.model.predict(state.reshape(1, -1))
        target_f[0][action] = target
        self.model.fit(state.reshape(1, -1), target_f, epochs=1, verbose=0)
        self.save_best_model(self.model)
