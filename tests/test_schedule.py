import sys
sys.path.append('/home/julius/Projects/mowmow/')
import config
from datetime import timedelta

s = config.schedule()
print(s.morning['start'])
print(s.morning['end'])
print(s.evening['start'])
print(s.evening['end'])

print(s.morning['start'] + timedelta(days=1))
