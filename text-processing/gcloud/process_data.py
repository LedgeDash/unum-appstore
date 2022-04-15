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

	unum_parallel_instance_log = []

	for e in unum_parallel_log:
		if e['start']:
			for r in unum_parallel_log:
				if r['id'] == e['id'] and r['start'] == False:
					instance_entry = {
						'id': r['id'],
						'start timestamp': e['timestamp'],
						'end timestamp': r['timestamp']
					}

					delta = instance_entry['end timestamp'] - instance_entry['start timestamp']
					diff = delta / timedelta(microseconds=1)
					diff = diff/1000
					instance_entry['runtime'] = diff

					unum_parallel_instance_log.append(instance_entry)

	unum_parallel_instance_log = sorted(unum_parallel_instance_log, key=lambda d: d['start timestamp'])

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

	publish_instance_log = []

	for e in publish_log:
		if e['start']:
			for r in publish_log:
				if r['id'] == e['id'] and r['start'] == False:
					instance_entry = {
						'id': r['id'],
						'start timestamp': e['timestamp'],
						'end timestamp': r['timestamp']
					}

					delta = instance_entry['end timestamp'] - instance_entry['start timestamp']
					diff = delta / timedelta(microseconds=1)
					diff = diff/1000
					instance_entry['runtime'] = diff

					publish_instance_log.append(instance_entry)

	publish_instance_log = sorted(publish_instance_log, key=lambda d: d['start timestamp'])

	# Applicatoin e2e latency
	e2e_runtime = []

	for i in range(len(publish_instance_log)):
		td = publish_instance_log[i]['end timestamp'] - unum_parallel_instance_log[i]['start timestamp']
		diff = td/timedelta(microseconds=1)
		diff = diff/1000
		e2e_runtime.append(diff)


	# Output results
	print(f'E2E runtime (milliseconds): {e2e_runtime}')
	print(f'E2E AVERAGE runtime (seconds): {np.mean(e2e_runtime)/1000}')



if __name__ == '__main__':
	main()