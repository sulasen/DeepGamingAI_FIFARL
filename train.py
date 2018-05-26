import numpy as np
import time
from getkeys import key_check
from ExperienceReplay import ExperienceReplay

# parameters
# epsilon = .2  # exploration
num_actions = 4  # [ shoot_low, shoot_high, left_arrow, right_arrow]
max_memory = 500  # Maximum number of experiences we are storing
hidden_size = 100  # Size of the hidden layers
batch_size = 1  # Number of experiences we use for training per batch
grid_size = 10  # Size of the playing field

exp_replay = ExperienceReplay(max_memory=max_memory)


def save_model(model):
    # serialize model to JSON
    model_json = model.to_json()
    with open("model.json", "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights("model.h5")
    print("Saved model to disk")


def train(game, model, epochs, verbose=1):
    # Train
    # Reseting the win counter
    win_cnt = 0
    # We want to keep track of the progress of the AI over time, so we save its win count history
    win_hist = []
    # Epochs is the number of games we play
    for e in range(epochs):
        loss = 0.
        epsilon = 1 / ((e + 1) ** 1 / 2)
        # Resetting the game
        game.reset()
        game_over = False
        # get tensorflow running first to acquire cudnn handle
        input_t = game.observe()
        paused = True
        
        while not game_over:
            if not paused:
                # The learner is acting on the last observed game screen
                # input_t is a vector containing representing the game screen
                input_tm1 = input_t

                """
                We want to avoid that the learner settles on a local minimum.
                Imagine you are eating in an exotic restaurant. After some experimentation you find 
                that Penang Curry with fried Tempeh tastes well. From this day on, you are settled, and the only Asian 
                food you are eating is Penang Curry. How can your friends convince you that there is better Asian food?
                It's simple: Sometimes, they just don't let you choose but order something random from the menu.
                Maybe you'll like it.
                The chance that your friends order for you is epsilon
                """
                if np.random.rand() <= epsilon:
                    # Eat something random from the menu
                    action = int(np.random.randint(0, num_actions, size=1))
                else:
                    # Choose yourself
                    # q contains the expected rewards for the actions
                    q = model.predict(input_tm1)
                    # We pick the action with the highest expected reward
                    action = np.argmax(q[0])

                # apply action, get rewards and new state
                input_t, reward, game_over = game.act(action)
                # If we managed to catch the fruit we add 1 to our win counter
                if reward == 1:
                    win_cnt += 1

                """
                The experiences < s, a, r, s’ > we make during gameplay are our training data.
                Here we first save the last experience, and then load a batch of experiences to train our model
                """

                # store experience
                exp_replay.remember([input_tm1, action, reward, input_t], game_over)

                # Load batch of experiences
                inputs, targets = exp_replay.get_batch(model, batch_size=batch_size)

                # train model on experiences
                batch_loss = model.train_on_batch(inputs, targets)

                # print(loss)
                loss += batch_loss

            # menu control
            keys = key_check()
            if 'P' in keys:
                if paused:
                    paused = False
                    print('unpaused!')
                    time.sleep(1)
                else:
                    print('Pausing!')
                    paused = True
                    time.sleep(1)
            elif 'O' in keys:
                print('Quitting!')
                return

        if verbose > 0:
            print("Epoch {:03d}/{:03d} | Loss {:.4f} | Win count {}".format(e, epochs, loss, win_cnt))
            save_model(model)
        win_hist.append(win_cnt)
    return win_hist
