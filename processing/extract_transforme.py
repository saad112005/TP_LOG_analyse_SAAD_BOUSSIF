import re
"""
in: list of rows
out: dateTime,ip,success,failed,Invalid user for sshd service
"""

pattern =re.compile(r'(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2}\s+(?P<server>\w+)\s+(?P<service>\w+)\[(?P<pid>\d+)\]:\s+(?P<message>\w+)')
def extract_from_rows(rows):
 matches=re.search(pattern,rows)
 if matches:
  print(matches.groupdict())
  