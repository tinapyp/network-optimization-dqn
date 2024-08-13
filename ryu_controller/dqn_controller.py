import numpy as np
import logging
import tensorflow as tf
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp
import time

class DQNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DQNController, self).__init__(*args, **kwargs)
        self.model = self.load_model()
        self.epsilon = 0.1  # Exploration rate
        self.state_size = 10  # Example state size
        self.action_size = 3  # Number of possible actions
        self.network_latency = {}
        self.network_throughput = {}

    def load_model(self):
        try:
            model = tf.keras.models.load_model('ryu_controller/model/dqn_model.h5')
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            model = self.build_model()
        return model

    def build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(24, input_dim=self.state_size, activation='relu'),
            tf.keras.layers.Dense(24, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def save_model(self):
        try:
            model_version = self.get_model_version()
            self.model.save(f'ryu_controller/model/dqn_model_v{model_version}.h5')
            logging.info(f"Model saved with version {model_version}.")
        except Exception as e:
            logging.error(f"Error saving model: {str(e)}")

    def get_model_version(self):
        import os
        model_dir = 'ryu_controller/model/'
        existing_models = [f for f in os.listdir(model_dir) if f.startswith('dqn_model_v')]
        version_numbers = [int(f.split('v')[-1].split('.h5')[0]) for f in existing_models]
        return max(version_numbers) + 1 if version_numbers else 1

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
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
        state[5] = time.time() % 10000  # Simplified time-stamp feature

        # Include more features such as network load, delay, etc.
        logging.info(f"State extracted: {state}")
        return state

    def select_action(self, state):
        if np.random.rand() <= self.epsilon:
            action = np.random.choice(self.action_size)
        else:
            q_values = self.model.predict(state.reshape(1, -1))
            action = np.argmax(q_values[0])
        logging.info(f"Action selected: {action}")
        return action

    def execute_action(self, action, datapath, in_port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if action == 0:
            logging.info("Action 0: Drop packet.")
            # Create drop action
            match = parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, [])
        elif action == 1:
            logging.info("Action 1: Forward packet normally.")
            # Normal forward logic
            out_port = ofproto.OFPP_FLOOD
            actions = [parser.OFPActionOutput(out_port)]
            self.packet_out(datapath, in_port, actions, pkt)
        elif action == 2:
            logging.info("Action 2: Route packet through alternate path.")
            # Alternate path logic
            out_port = self.find_alternate_path(datapath, in_port, pkt)
            actions = [parser.OFPActionOutput(out_port)]
            self.packet_out(datapath, in_port, actions, pkt)

    def find_alternate_path(self, datapath, in_port, pkt):
        # Implement actual logic to find an alternate path
        # For simplicity, let's just forward to a specific port
        out_port = (in_port + 1) % len(datapath.ports)
        return out_port

    def packet_out(self, datapath, in_port, actions, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        data = pkt.data
        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def calculate_reward(self, state, action):
        latency = self.calculate_latency(state)
        throughput = self.calculate_throughput(state)
        reward = -latency + throughput
        logging.info(f"Reward calculated: {reward}")
        return reward

    def calculate_latency(self, state):
        # Implement the actual latency calculation
        src_ip = state[0]
        dst_ip = state[1]
        latency = self.network_latency.get((src_ip, dst_ip), 1.0)  # Default latency is 1ms
        logging.info(f"Latency calculated: {latency} ms")
        return latency

    def calculate_throughput(self, state):
        # Implement the actual throughput calculation
        src_ip = state[0]
        dst_ip = state[1]
        throughput = self.network_throughput.get((src_ip, dst_ip), 10.0)  # Default throughput is 10Mbps
        logging.info(f"Throughput calculated: {throughput} Mbps")
        return throughput

    def train_model(self, state, action, reward):
        # Implement training logic
        target = reward  # Simplified target for example
        target_f = self.model.predict(state.reshape(1, -1))
        target_f[0][action] = target
        self.model.fit(state.reshape(1, -1), target_f, epochs=1, verbose=0)
        self.save_model()