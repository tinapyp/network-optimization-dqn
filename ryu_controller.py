from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4
from ryu.lib import hub
import numpy as np
import tensorflow as tf
from collections import defaultdict
import time


class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = []
        self.gamma = 0.95  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.model = self._build_model()

    def _build_model(self):
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(24, input_dim=self.state_size, activation="relu"),
                tf.keras.layers.Dense(24, activation="relu"),
                tf.keras.layers.Dense(self.action_size, activation="linear"),
            ]
        )
        model.compile(
            loss="mse", optimizer=tf.keras.optimizers.Adam(learning_rate=0.001)
        )
        return model

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return np.random.randint(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])

    def train(self, state, action, reward, next_state, done):
        target = reward
        if not done:
            target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
        target_f = self.model.predict(state)
        target_f[0][action] = target
        self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay


class DQNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DQNController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.state_size = (
            4  # [bandwidth_utilization, packet_loss, latency, queue_length]
        )
        self.action_size = 3  # [increase_bandwidth, decrease_latency, load_balance]
        self.agent = DQNAgent(self.state_size, self.action_size)
        self.monitor_thread = hub.spawn(self._monitor)
        self.flow_stats = defaultdict(
            lambda: defaultdict(
                lambda: {"byte_count": 0, "duration_sec": 0, "packet_count": 0}
            )
        )
        self.port_stats = defaultdict(
            lambda: defaultdict(
                lambda: {"tx_bytes": 0, "rx_bytes": 0, "tx_packets": 0, "rx_packets": 0}
            )
        )
        self.latency = defaultdict(float)
        self.queue_stats = defaultdict(lambda: defaultdict(int))

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        req = parser.OFPQueueStatsRequest(
            datapath, 0, ofproto.OFPP_ANY, ofproto.OFPQ_ALL
        )
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug("register datapath: %016x", datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug("unregister datapath: %016x", datapath.id)
                del self.datapaths[datapath.id]

    def _get_bandwidth_utilization(self, datapath):
        total_bytes = sum(
            port_stat["tx_bytes"] + port_stat["rx_bytes"]
            for port_stat in self.port_stats[datapath.id].values()
        )
        total_capacity = (
            len(self.port_stats[datapath.id]) * 1e9
        )  # Assuming 1 Gbps ports
        return total_bytes / total_capacity

    def _get_packet_loss(self, datapath):
        total_packets_sent = sum(
            flow_stat["packet_count"]
            for flow_stat in self.flow_stats[datapath.id].values()
        )
        total_packets_received = sum(
            port_stat["rx_packets"]
            for port_stat in self.port_stats[datapath.id].values()
        )
        if total_packets_sent == 0:
            return 0
        return (total_packets_sent - total_packets_received) / total_packets_sent

    def _get_latency(self, datapath):
        return self.latency.get(datapath.id, 0)

    def _get_queue_length(self, datapath):
        return sum(self.queue_stats[datapath.id].values())

    def get_state(self, datapath):
        bandwidth_utilization = self._get_bandwidth_utilization(datapath)
        packet_loss = self._get_packet_loss(datapath)
        latency = self._get_latency(datapath)
        queue_length = self._get_queue_length(datapath)

        return np.array([[bandwidth_utilization, packet_loss, latency, queue_length]])

    def apply_action(self, datapath, action):
        if action == 0:
            self._increase_bandwidth(datapath)
        elif action == 1:
            self._decrease_latency(datapath)
        elif action == 2:
            self._load_balance(datapath)

    def _increase_bandwidth(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for port in self.port_stats[datapath.id]:
            queue_id = 0
            max_rate = int(1e9)  # 1 Gbps
            min_rate = int(1e8)  # 100 Mbps

            req = parser.OFPQueueConfigSet(
                datapath,
                port,
                [
                    parser.OFPQueuePropMinRate(queue_id=queue_id, rate=min_rate),
                    parser.OFPQueuePropMaxRate(queue_id=queue_id, rate=max_rate),
                ],
            )
            datapath.send_msg(req)

    def _decrease_latency(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Find the port with the lowest utilization
        lowest_util_port = min(
            self.port_stats[datapath.id],
            key=lambda x: self.port_stats[datapath.id][x]["tx_bytes"]
            + self.port_stats[datapath.id][x]["rx_bytes"],
        )

        # Add a flow to route traffic through this port
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP)
        actions = [parser.OFPActionOutput(lowest_util_port)]
        self.add_flow(datapath, 100, match, actions)

    def _load_balance(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Get sorted list of ports by utilization
        sorted_ports = sorted(
            self.port_stats[datapath.id],
            key=lambda x: self.port_stats[datapath.id][x]["tx_bytes"]
            + self.port_stats[datapath.id][x]["rx_bytes"],
        )

        # Distribute flows across the least utilized ports
        for i, flow_id in enumerate(self.flow_stats[datapath.id]):
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src=flow_id)
            actions = [parser.OFPActionOutput(sorted_ports[i % len(sorted_ports)])]
            self.add_flow(datapath, 100, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def calculate_reward(self, datapath):
        current_state = self.get_state(datapath)

        if hasattr(self, "previous_state"):
            bandwidth_improvement = current_state[0][0] - self.previous_state[0][0]
            packet_loss_improvement = self.previous_state[0][1] - current_state[0][1]
            latency_improvement = self.previous_state[0][2] - current_state[0][2]
            queue_length_improvement = self.previous_state[0][3] - current_state[0][3]

            reward = (
                0.3 * bandwidth_improvement
                + 0.3 * packet_loss_improvement
                + 0.3 * latency_improvement
                + 0.1 * queue_length_improvement
            )
        else:
            reward = 0

        self.previous_state = current_state
        return reward

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = msg.match["in_port"]

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=msg.match["in_port"], eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=msg.match["in_port"],
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

        # DQN part
        state = self.get_state(datapath)
        action = self.agent.act(state)
        self.apply_action(datapath, action)

        next_state = self.get_state(datapath)
        reward = self.calculate_reward(datapath)

        self.agent.train(state, action, reward, next_state, False)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        datapath = ev.msg.datapath

        for stat in body:
            flow_id = (stat.match["ipv4_src"], stat.match["ipv4_dst"])
            self.flow_stats[datapath.id][flow_id] = {
                "byte_count": stat.byte_count,
                "duration_sec": stat.duration_sec,
                "packet_count": stat.packet_count,
            }

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        datapath = ev.msg.datapath

        for stat in body:
            port_no = stat.port_no
            self.port_stats[datapath.id][port_no] = {
                "rx_bytes": stat.rx_bytes,
                "tx_bytes": stat.tx_bytes,
                "rx_packets": stat.rx_packets,
                "tx_packets": stat.tx_packets,
            }

    @set_ev_cls(ofp_event.EventOFPQueueStatsReply, MAIN_DISPATCHER)
    def _queue_stats_reply_handler(self, ev):
        body = ev.msg.body
        datapath = ev.msg.datapath

        for stat in body:
            port_no = stat.port_no
            queue_id = stat.queue_id
            self.queue_stats[datapath.id][port_no] = stat.length

    def _send_ping(self, datapath):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        echo_req = ofp_parser.OFPEchoRequest(datapath)
        start_time = time.time()
        datapath.send_msg(echo_req)

        return start_time

    @set_ev_cls(ofp_event.EventOFPEchoReply, MAIN_DISPATCHER)
    def _echo_reply_handler(self, ev):
        end_time = time.time()
        datapath = ev.msg.datapath
        latency = (end_time - self._send_ping(datapath)) * 1000  # Convert to ms
        self.latency[datapath.id] = latency


if __name__ == "__main__":
    from ryu.cmd import manager

    manager.main()
