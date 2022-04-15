import os
import numpy as np
from datetime import datetime, timedelta


def main():
	aggregator_log = []
	with open('iot-pipeline-aggregator.log') as f:
		for i, l in enumerate(f):
			filtered = list(filter(lambda e: e !='', l.split('  ')))

			if filtered[1] != 'iot-pipeline-aggregator':
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

				aggregator_log.append(entry)

	for e in aggregator_log:
		e['timestamp'] = datetime.fromisoformat(e['timestamp'])

	# sort based on timestamp in ascending order (earlier entries have earlier
	# timestamps)
	aggregator_log = sorted(aggregator_log, key=lambda d: d['timestamp'])

	# How long does each function instance take from start to complete.
	aggregator_function_runtime =[]
	i = 0

	while i < len(aggregator_log):
		if aggregator_log[i]['id'] != aggregator_log[i+1]['id']:
			print(f'adjacent log entry ids do not match:')
			print(f'{aggregator_log[i]} and {aggregator_log[i+1]}')

		delta = aggregator_log[i+1]['timestamp'] - aggregator_log[i]['timestamp']
		diff = delta / timedelta(microseconds=1)
		diff = diff/1000
		aggregator_function_runtime.append(diff)
		i = i+2


	# hvac controller

	hvac_controller_log = []
	with open('iot-pipeline-hvac-controller.log') as f:
		for i, l in enumerate(f):
			filtered = list(filter(lambda e: e !='', l.split('  ')))

			if filtered[1] != 'iot-pipeline-hvac-controller':
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

				hvac_controller_log.append(entry)

	for e in hvac_controller_log:
		e['timestamp'] = datetime.fromisoformat(e['timestamp'])

	# sort based on timestamp in ascending order (earlier entries have earlier
	# timestamps)
	hvac_controller_log = sorted(hvac_controller_log, key=lambda d: d['timestamp'])

	# How long does each function instance take from start to complete.
	hvac_controller_function_runtime =[]
	i = 0

	while i < len(hvac_controller_log):
		if hvac_controller_log[i]['id'] != hvac_controller_log[i+1]['id']:
			print(f'adjacent log entry ids do not match:')
			print(f'{hvac_controller_log[i]} and {hvac_controller_log[i+1]}')

		delta = hvac_controller_log[i+1]['timestamp'] - hvac_controller_log[i]['timestamp']
		diff = delta / timedelta(microseconds=1)
		diff = diff/1000
		hvac_controller_function_runtime.append(diff)
		i = i+2

	# Applicatoin e2e latency
	e2e_runtime = []
	i = 0
	while i < len(aggregator_log):
		if aggregator_log[i]['start'] == False or hvac_controller_log[i+1]['start'] == True:
			print(f'[ERROR] Log order does not match:')
			print(f'{aggregator_log[i]}')
			print(f'{hvac_controller_log[i+1]}')

		td = hvac_controller_log[i+1]['timestamp'] - aggregator_log[i]['timestamp']
		diff = td / timedelta(microseconds=1)
		diff = diff/1000
		e2e_runtime.append(diff)
		i = i + 2

	# Output results
	# print(f'Aggregator function runtime: {aggregator_function_runtime}')
	print(f'Aggregator function AVERAGE runtime: {np.mean(aggregator_function_runtime)}')
	# print(f'Hvac controller function runtime: {hvac_controller_function_runtime}')
	print(f'Hvac controller function AVERAGE runtime: {np.mean(hvac_controller_function_runtime)}')
	print(f'E2E runtime: {e2e_runtime}')
	print(f'E2E AVERAGE runtime: {np.mean(e2e_runtime)}')



if __name__ == '__main__':
	main()