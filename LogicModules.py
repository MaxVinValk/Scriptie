import numpy as np
import random
import time

from ConsoleMessages import ConsoleMessages as cm

from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.optimizers import Adam

from ModTensorBoard import ModifiedTensorBoard

from collections import deque

class LogicModule():

	def __init__(self, explorationPolicy):
		self.explorationPolicy = explorationPolicy

	def setupModule(self, stateDims, actionSize):
		pass

	def getAction(self, state):
		pass

	def train(self, origState, resState, action, reward, done):
		pass

	def endSimulationUpdate(self):
		pass

	def getExplorationPolicy(self):
		return self.explorationPolicy

	def save(self, fileName):
		pass

	def load(self, fileName):
		pass



class QLearningTabModule(LogicModule):

	def __init__(self, explorationPolicy, discountFactor, learningRate, tableInFile = None, **kwargs):
		self.DISCOUNT_FACTOR = discountFactor
		self.LEARNING_RATE = learningRate
		self.tableInFile = tableInFile

		print(f"{cm.NORMAL}Initialized Tabular Q-Learning with discount Factor: {discountFactor} and learning Rate: {learningRate}")


		super(QLearningTabModule, self).__init__(explorationPolicy)

	def setupModule(self, stateDims, actionSize):

		self.actionSize = actionSize;

		if (self.tableInFile == None):
			print(f"{cm.NORMAL}Setting up Q-table of size:{stateDims + [actionSize]}")
			self.qTable = np.random.uniform(low=-2, high = 0, size = stateDims + [actionSize])
		else:
			print(f"Loading table: {self.tableInFile}")
			self.loadTable(self.tableInFile)

	def getAction(self, state):
		return self.explorationPolicy.getAction(self.qTable[tuple(state)])


	def train(self, origState, resState, action, reward, done):

		# Get max future
		if done:
			maxFutureQValue = 0
		else:
			maxFutureQValue = np.max(tuple(resState))

		currentQValue = self.qTable[tuple(origState + [action])]

		self.qTable[tuple(origState + [action])] = currentQValue + self.LEARNING_RATE * (reward + self.DISCOUNT_FACTOR * maxFutureQValue)

	def endSimulationUpdate(self):
		self.explorationPolicy.endSimulationUpdate()

	def load(self, fileName):
		self.qTable = np.load(fileName)

	def save(self, fileName):
		np.save(fileName, self.qTable)






class QLearningNeuralModule(LogicModule):

	REPLAY_MEMORY_SIZE = 50_000
	MIN_REPLAY_MEMORY_SIZE = 1000
	MINIBATCH_SIZE = 256
	UPDATE_TARGET_EVERY = 1000

	ONE_HOT_ENCODING = True


	def __init__(self, explorationPolicy, discountFactor, learningRate, modelInFile = None, **kwargs):
		self.explorationPolicy = explorationPolicy
		self.DISCOUNT_FACTOR = discountFactor
		self.LEARNING_RATE = learningRate

		self.targetUpdateCounter = 0

		random.seed(1)


	def setupModule(self, stateDims, actionSize):

		self.stateDims = np.array(stateDims)

		self.model = self._createModel(stateDims, actionSize)
		self.targetModel = self._createModel(stateDims, actionSize)
		self.targetModel.set_weights(self.model.get_weights())

		self.replayMemory = deque(maxlen=self.REPLAY_MEMORY_SIZE)
		self.tensorboard = ModifiedTensorBoard(log_dir=f"logs/{int(time.time())}")

		self.targetUpdateCounter = 0


	def _createModel(self, stateDims, actionSize):

		if self.ONE_HOT_ENCODING:
			inSize = sum(stateDims)
		else:
			inSize = len(stateDims)

		print(f"{cm.INFO}Creating a CNN with input size {inSize}{cm.NORMAL}")
		print(f"{cm.INFO}and output size {actionSize} {cm.NORMAL}")

		model = Sequential()
		model.add(Dense(64, input_dim = inSize))
		model.add(Activation("elu"))

		model.add(Dense(16))
		model.add(Activation("elu"))

		model.add(Dense(actionSize))
		model.add(Activation("linear"))

		model.compile(loss="mse", optimizer=Adam(lr=self.LEARNING_RATE), metrics=['accuracy'])

		return model


	def _normalizeState(self, state):

		if self.ONE_HOT_ENCODING:
			newState = [0] * int(sum(self.stateDims))

			currentIdx = 0

			for idx in range(0, len(state)):

				checkIdx = currentIdx + state[idx]
				newState[checkIdx] = 1
				currentIdx += self.stateDims[idx]

			return newState

		else:
			return state / self.stateDims

	def getAction(self, state):
		normalizedState = np.array([self._normalizeState(state)])

		values = self.targetModel.predict(normalizedState)[0]
		return self.explorationPolicy.getAction(values)

	def train(self, origState, resState, action, reward, done):

		#Add memory to replayMemory
		self.replayMemory.append((self._normalizeState(origState), self._normalizeState(resState), action, reward, done))

		#Check if we have enough memories
		if len(self.replayMemory) < self.MIN_REPLAY_MEMORY_SIZE:
			return

		miniBatch = random.sample(self.replayMemory, self.MINIBATCH_SIZE)

		currentStates = np.array([transition[0] for transition in miniBatch])
		currentQScores = self.model.predict(currentStates)

		#Can be left out as we do not care for a sequence of actions and we have deterministic rewards

		resStates = np.array([transition[1] for transition in miniBatch])
		futureQScores = self.targetModel.predict(resStates)

		X = []
		y = []

		for index, (batchOrigState, batchResState, batchAction, batchReward, batchDone) in enumerate(miniBatch):

			if not batchDone:
				maxFutureQ = np.max(futureQScores[index])
				newQ = reward + self.DISCOUNT_FACTOR * maxFutureQ
			else:
				newQ = reward

			currentQ = currentQScores[index]
			currentQ[action] = newQ

			X.append(currentStates[index])
			y.append(currentQ)

		# Fit on all samples as one batch, log only on terminal state
		self.model.fit(np.array(X), np.array(y), batch_size=self.MINIBATCH_SIZE, verbose=0, shuffle=False, callbacks=[self.tensorboard] if done else None)

		# updating to determine if we want to update target_model yet
		if done:
			self.targetUpdateCounter += 1

			if self.targetUpdateCounter > self.UPDATE_TARGET_EVERY:
				self.targetModel.set_weights(self.model.get_weights())
				self.targetUpdateCounter = 0



	def endSimulationUpdate(self):
		self.explorationPolicy.endSimulationUpdate()




	def save(self, fileName):
		pass

	def load(self, fileName):
		pass
