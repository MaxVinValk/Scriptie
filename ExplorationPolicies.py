import numpy as np
# Exploration modules

class ExplorationPolicy():
	
	def __init__(self):
		pass

class EpsilonGreedyPolicy(ExplorationPolicy):
	
	VALID_DECAY_MODES = ["multiplication", "linear"]
	
	def __init__(self, epsilon, decayRate, minEpsilon, decayMode = "multiplication"):
		self.epsilon = epsilon
		self.decayRate = decayRate
		self.minEpsilon = minEpsilon
		
		
		if (decayMode not in self.VALID_DECAY_MODES):
			print(f"\033[1;31mWARNING: Provided invalid decay mode {decayMode}. Defaulting to {self.VALID_DECAY_MODES[0]} instead.")
			decayMode = self.VALID_DECAY_MODES[0]
		self.decayMode = decayMode
		
		print(f"\033[0;0mInitialized eps-greedy exploration policy with start eps: {epsilon}, min eps: {minEpsilon}, decay mode: {decayMode}, and decay rate: {decayRate}")
	
	def updateEpsilon(self):
		
		if (self.epsilon < self.minEpsilon):
			return
		
		if (self.decayMode is "multiplication"):
			self.epsilon = max(self.epsilon * self.decayRate, self.minEpsilon)
			
		elif (self.decayMode is "linear"):
			self.epsilon = max(self.epsilon - self.decayRate, self.minEpsilon)
		
	
	def takeRandom(self):
		
		if np.random.random() < self.epsilon:
			return True
		return False
	
	def getEpsilon(self):
		return self.epsilon


