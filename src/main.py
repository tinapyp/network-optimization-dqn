from mininet.log import setLogLevel
from network.simulation import NetworkSimulation
from agent.dqn_agent import DQNAgent


def main():
    setLogLevel("info")

    sim = NetworkSimulation()
    sim.create_network()

    state_size = len(sim.switches) * 4
    action_size = 8
    agent = DQNAgent(state_size, action_size)

    episodes = 100
    batch_size = 32

    for e in range(episodes):
        state = sim.get_state()
        total_reward = 0

        for time in range(20):
            action = agent.act(state)
            sim.take_action(action)
            next_state = sim.get_state()
            reward = sim.get_reward()
            done = time == 19

            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

            if len(agent.memory) > batch_size:
                agent.replay(batch_size)

        print(f"Episode: {e+1}/{episodes}, Total Reward: {total_reward}")
        sim.update_best_topology(total_reward)

    sim.visualize_best_topology()
    sim.net.stop()


if __name__ == "__main__":
    main()
