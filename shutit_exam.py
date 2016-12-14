import sys
import time
import shutit_global
import signal

PY3 = (sys.version_info[0] >= 3)

class ShutItExamSessionStage(object):

	# difficulty           - a proportion of the default difficulty=1
	# reduction_per_minute - the degree to which success value decreases every minute
	# reduction_per_reset  - the degree to which a reset affects the final score
	# reduction_per_hint   - the degree to which a hint affects the final score
	# grace_period         - the time under which a success scores full points
	#
	# A difficulty of zero means the challenge has no significance to the overall score.
	def __init__(self,
	             difficulty=1.0,
	             reduction_per_minute=0.2,
	             reduction_per_reset=0,
	             reduction_per_hint=0.5,
	             grace_period=30):
		self.difficulty           = difficulty
		self.reduction_per_minute = reduction_per_minute
		self.reduction_per_reset  = reduction_per_reset
		self.reduction_per_hint   = reduction_per_hint
		self.grace_period         = grace_period
		self.result               = ''
		self.num_resets           = 0
		self.num_hints            = 0
		self.start_time           = None
		self.end_time             = None
		self.score                = -1

	def __str__(self):
		string = ''
		string += '\nnum_resets       = ' + str(self.num_resets)
		string += '\nnum_hints        = ' + str(self.num_hints)
		string += '\nresult           = ' + str(self.result)
		string += '\nstart_time       = ' + str(self.start_time)
		string += '\nend_time         = ' + str(self.end_time)
		string += '\nscore            = ' + str(self.score)
		return string

	def start_timer(self):
		if self.start_time != None:
			shutit_global.shutit.fail('start_timer called with start_time already set')
		self.start_time = time.time()

	def end_timer(self):
		if self.start_time == None:
			shutit_global.shutit.fail('end_timer called with no start_time set')
		if self.end_time != None:
			shutit_global.shutit.fail('end_time already set')
		self.end_time = time.time()
		self.total_time = self.end_time - self.start_time

	def is_complete(self):
		if self.result == '':
			return False
		else:
			return True



class ShutItExamSession(object):

	def __init__(self):
		self.stages           = []
		self.final_score      = 0.0
		# Switch off CTRL-C etc
		signal.signal(signal.SIGINT, signal.SIG_IGN)
		signal.signal(signal.SIGQUIT, signal.SIG_IGN)
		signal.signal(signal.SIGPIPE, signal.SIG_IGN)
		signal.signal(signal.SIGTSTP, signal.SIG_IGN)

	def __str__(self):
		string = ''
		n=0
		for stage in self.stages:
			n+=1
			stage_desc = 'Stage ' + str(n) + ' of ' + str(len(self.stages))
			string += '\n' + stage_desc
			string += '\n' + str(stage)
		string += '\n\nFinal score: ' + str(self.final_score) + '%\n'
		return string
		
	def new_stage(self,difficulty=1.0,reduction_per_minute=0.2,reduction_per_reset=0,reduction_per_hint=0.5,grace_period=30):
		difficulty = float(difficulty)
		stage = ShutItExamSessionStage(difficulty,reduction_per_minute,reduction_per_reset,reduction_per_hint,grace_period)
		self.stages.append(stage)
		return stage

	def add_reset(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_reset: no stages to reset')
		stage = self.stages[-1]
		stage.num_resets += 1

	def add_skip(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_skip: no stages to skip')
		stage = self.stages[-1]
		if stage.result != '':
			shutit_global.shutit.fail('add_skip: result already determined')
		else:
			stage.result = 'SKIP'

	def add_fail(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_fail: no stages to fail')
		stage = self.stages[-1]
		if stage.result != '':
			shutit_global.shutit.fail('add_fail: result already determined')
		else:
			stage.result = 'FAIL'

	def add_ok(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_ok: no stages to ok')
		stage = self.stages[-1]
		if stage.result != '':
			shutit_global.shutit.fail('add_ok: result already determined')
		else:
			stage.result = 'OK'

	def add_hint(self):
		if self.stages == []:
			shutit_global.shutit.fail('add_hint: no stages to add hint for')
		stage = self.stages[-1]
		stage.num_hints += 1

	def start_timer(self):
		if self.stages == []:
			shutit_global.shutit.fail('start_timer: no stages to time')
		stage = self.stages[-1]
		stage.start_timer()

	def end_timer(self):
		if self.stages == []:
			shutit_global.shutit.fail('end_timer: no stages to time')
		stage = self.stages[-1]
		stage.end_timer()

	def calculate_score(self):
		max_score   = 0.0
		total_score = 0.0
		for stage in self.stages:
			max_score += stage.difficulty
			# If they succeeded, start with the diffulty score (100%)
			if stage.result == 'OK':
				stage.score = stage.difficulty
				for item in range(0,stage.num_resets):
					stage.score = stage.score - (stage.score * stage.reduction_per_reset)
				for item in range(0,stage.num_hints):
					stage.score = stage.score - (stage.score * stage.reduction_per_hint)
				# TODO: is time in seconds?
				total_time = stage.end_time - stage.start_time
				total_time -= stage.grace_period
				if total_time > 0:
					num_minutes = total_time / 60
					num_seconds = total_time % 60
					num_minutes = num_minutes + (num_seconds / 60)
					while num_minutes > 1:
						num_minutes -= 1
						stage.score = stage.score - (stage.score * self.reduction_per_minute)
					if num_minutes > 0:
						stage.score = stage.score - (stage.score * self.reduction_per_minute * num_minutes)
				total_score = total_score + stage.score
			else:
				stage.score = 0
		self.final_score = total_score / max_score * 100.00
		return self.final_score

