import numpy as np
import gym
import os
import tkinter as tk
import threading

# Create the Gym environment
env = gym.make("MountainCar-v0", render_mode="human")

# Tkinter GUI setup
window = tk.Tk()
window.title("AI")
window.geometry("500x400")

epi_label = tk.Label(window, text="", font=("Arial", 35))
epi_label.pack(padx=10, pady=10)

DISCRETE_OS_SIZE = [40] * len(env.observation_space.high)  # Size of each bucket
DISCRETE_OS_WIN_SIZE = (env.observation_space.high - env.observation_space.low) / DISCRETE_OS_SIZE  # Bucket range


def get_discrete_state(state):
    discrete_state = (state - env.observation_space.low) / DISCRETE_OS_WIN_SIZE
    return tuple(discrete_state.astype(int))  # Return discrete state as a tuple


def run_gym_env():
    while True:
        os.system("cls")

        # First Stage
        initial_state, _ = env.reset()
        discrete_state = get_discrete_state(initial_state)
        q_table = np.load("10000-q_table.npy")
        update_label("First 10,000 iterations")

        terminated = truncated = False

        while not (terminated or truncated):
            action = np.argmax(q_table[discrete_state])
            state, reward, terminated, truncated, info = env.step(action)
            discrete_state = get_discrete_state(state)

        # Second Stage
        initial_state, _ = env.reset()
        discrete_state = get_discrete_state(initial_state)
        q_table = np.load("15000-q_table.npy")
        update_label("First 15,000 iterations")

        terminated = truncated = False

        while not (terminated or truncated):
            action = np.argmax(q_table[discrete_state])
            state, reward, terminated, truncated, info = env.step(action)
            discrete_state = get_discrete_state(state)

        # Third Stage
        initial_state, _ = env.reset()
        discrete_state = get_discrete_state(initial_state)
        q_table = np.load("32000-q_table.npy")
        update_label("Final model!")

        terminated = truncated = False

        while not (terminated or truncated):
            action = np.argmax(q_table[discrete_state])
            state, reward, terminated, truncated, info = env.step(action)
            discrete_state = get_discrete_state(state)


def update_label(text):
    # Update the Tkinter label from the Gym loop
    epi_label.config(text=text)
    window.update_idletasks()


# Run the Gym environment loop in a separate thread
gym_thread = threading.Thread(target=run_gym_env)
gym_thread.daemon = True  # Daemonize thread to exit with the main program
gym_thread.start()

# Start the Tkinter GUI loop
window.mainloop()
