import os
import numpy as np
from datetime import datetime, timedelta


def main():
	unum_parallel_log = []
	with open('text-processing-unum-parallel-0.log') as f:
		for i, l in enumerate(f):
			filtered = list(filter(lambda e: e !='', l.split('  ')))

			if filtered[1] != 'text-processing-unum-parallel-0':
				print(f'SKIPPING {filtered}')
			elif filtered[4].startswith('Function execution took') == False and filtered[4] != 'Function execution started\n':
				print(f'SKIPPING {filtered}')
			else:
				entry = {
					'order': i,
					'id': filtered[2],
					'timestamp': filtered[3],
					'start': filtered[4] == 'Function execution started\n'
				}

				unum_parallel_log.append(entry)

	for e in unum_parallel_log:
		e['timestamp'] = datetime.fromisoformat(e['timestamp'])

	# sort based on timestamp in ascending order (earlier entries have earlier
	# timestamps)
	unum_parallel_log = sorted(unum_parallel_log, key=lambda d: d['timestamp'])

	# How long does each function instance take from start to complete.
	unum_parallel_function_runtime =[]
	i = 0

	while i < len(unum_parallel_log):
		if unum_parallel_log[i]['id'] != unum_parallel_log[i+1]['id']:
			print(f'adjacent log entry ids do not match:')
			print(f'{unum_parallel_log[i]} and {unum_parallel_log[i+1]}')

		delta = unum_parallel_log[i+1]['timestamp'] - unum_parallel_log[i]['timestamp']
		diff = delta / timedelta(microseconds=1)
		diff = diff/1000
		unum_parallel_function_runtime.append(diff)
		i = i+2


	# publish

	publish_log = []
	with open('text-processing-publish.log') as f:
		for i, l in enumerate(f):
			filtered = list(filter(lambda e: e !='', l.split('  ')))

			if filtered[1] != 'text-processing-publish':
				print(f'SKIPPING {filtered}')
			elif filtered[4].startswith('Function execution took') == False and filtered[4] != 'Function execution started\n':
				print(f'SKIPPING {filtered}')
			else:
				entry = {
					'order': i,
					'id': filtered[2],
					'timestamp': filtered[3],
					'start': filtered[4] == 'Function execution started\n'
				}

				publish_log.append(entry)

	for e in publish_log:
		e['timestamp'] = datetime.fromisoformat(e['timestamp'])

	# sort based on timestamp in ascending order (earlier entries have earlier
	# timestamps)
	publish_log = sorted(publish_log, key=lambda d: d['timestamp'])

	# How long does each function instance take from start to complete.
	publish_function_runtime =[]
	i = 0

	while i < len(publish_log):
		if publish_log[i]['id'] != publish_log[i+1]['id']:
			print(f'adjacent log entry ids do not match:')
			print(f'{publish_log[i]} and {publish_log[i+1]}')

		delta = publish_log[i+1]['timestamp'] - publish_log[i]['timestamp']
		diff = delta / timedelta(microseconds=1)
		diff = diff/1000
		publish_function_runtime.append(diff)
		i = i+2

	# Applicatoin e2e latency
	e2e_runtime = []
	i = 0
	while i < len(unum_parallel_log):
		if unum_parallel_log[i]['start'] == False or publish_log[i+1]['start'] == True:
			print(f'[ERROR] Log order does not match:')
			print(f'{unum_parallel_log[i]}')
			print(f'{publish_log[i+1]}')

		td = publish_log[i+1]['timestamp'] - unum_parallel_log[i]['timestamp']
		diff = td / timedelta(microseconds=1)
		diff = diff/1000
		e2e_runtime.append(diff)
		i = i + 2

	# Output results
	print(f'E2E runtime: {e2e_runtime}')
	print(f'E2E AVERAGE runtime: {np.mean(e2e_runtime)}')



if __name__ == '__main__':
	main()